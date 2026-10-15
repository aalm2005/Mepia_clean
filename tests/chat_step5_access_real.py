"""Acceso opt-in con Auth/Data API reales y modelo simulado. Nunca producción.

RUN_CHAT_ACCESS_INTEGRATION=1, ENVIRONMENT=dev y MEPIA_TEST_PROJECT_REF
son obligatorios. Crea y elimina solo dos identidades y filas sintéticas nuevas.
No guarda tokens, contraseñas, correos ni datos de negocios en el informe.
"""
import argparse
import json
import logging
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import jwt
from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi.testclient import TestClient
from supabase import create_client

from agents.chat_conversation import ChatConversationNode
from agents.chat_provider_gemini import GeminiCompletion
from agents.chat_response import ChatJsonCompletionAdapter
from api.chat import create_chat_router
from api.core.auth import AuthService
from tests.chat_offline_eval import fixture_id, load_fixture
from tests.test_chat_api import SimulatedSDK


def run(config_path, output):
    logging.disable(logging.CRITICAL)
    cfg = {**dotenv_values(config_path), **os.environ}
    from urllib.parse import urlparse
    expected = cfg.get('MEPIA_TEST_PROJECT_REF')
    if (cfg.get('RUN_CHAT_ACCESS_INTEGRATION') != '1' or cfg.get('ENVIRONMENT') != 'dev'
            or not expected or urlparse(cfg.get('SUPABASE_URL', '')).hostname != expected + '.supabase.co'
            or cfg.get('SUPABASE_JWT_ALGORITHM') != 'ES256'):
        print('Bloqueado: habilitación, proyecto de pruebas y firma ES256 son obligatorios.')
        return 2
    required = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_PUBLIC_KEY']
    if any(not cfg.get(k) for k in required):
        print('Bloqueado: faltan credenciales de pruebas en el archivo privado.')
        return 2
    report = {'environment': 'MEPIA - PRUEBAS', 'started_at': datetime.now(timezone.utc).isoformat(),
              'auth_and_database': 'real', 'provider': 'simulated', 'real_model_calls': 0,
              'checks': [], 'cleanup': [], 'success': False}
    stage = 'initialization'
    users, bids, audits = [], [], []
    admin = create_client(cfg['SUPABASE_URL'], cfg['SUPABASE_SERVICE_ROLE_KEY'])
    sdk = SimulatedSDK()
    db_calls = []
    class TrackedDB:
        def table(self, table):
            db_calls.append(table)
            return admin.table(table)
    def check(name, condition):
        report['checks'].append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    def snapshot():
        return {table: sorted(row['id'] for row in admin.table(table).select('id').execute().data)
                for table in ['businesses', 'audit_results']}
    baseline = None
    try:
        stage = 'baseline'
        baseline = snapshot()
        report['initial_counts'] = {t: len(v) for t, v in baseline.items()}
        stage = 'temporary_sessions'
        session_clients, sessions = [], []
        for index in range(2):
            password = secrets.token_urlsafe(40)
            email = 'mepia-step5-' + uuid4().hex + f'-{index}@example.com'
            user = admin.auth.admin.create_user({'email': email, 'password': password, 'email_confirm': True}).user
            users.append(user.id)
            client = create_client(cfg['SUPABASE_URL'], cfg['SUPABASE_PUBLIC_KEY'])
            response = client.auth.sign_in_with_password({'email': email, 'password': password})
            check(f'password_login_user_{index}', response.user.id == user.id and response.session is not None)
            client.postgrest.auth(response.session.access_token)
            session_clients.append(client)
            sessions.append(response.session.access_token)
        stage = 'jwks_signature_and_claims'
        auth = AuthService(cfg['SUPABASE_URL'], algorithm='ES256')
        for index, access_token in enumerate(sessions):
            check(f'jwks_signature_and_claims_user_{index}', auth.user_id(access_token) == users[index])
        report['jwt_algorithm'] = 'ES256'
        stage = 'synthetic_rows'
        bids = [str(uuid4()) for _ in range(4)]
        owners = [users[0], users[1], users[0], None]
        admin.table('businesses').insert([{'id': bid, 'business_name': '__mepia_step5_' + uuid4().hex,
            'owner_id': owner, 'industry_sector': 'integration_test', 'currency': 'MXN'}
            for bid, owner in zip(bids, owners)]).execute()
        rows = []
        for bid in bids[:3]:
            for raw in load_fixture()['datasets']['main']:
                row = dict(raw)
                row['id'] = fixture_id(raw['id'] + bid)
                row['business_id'] = bid
                row['source_s3_result_id'] = fixture_id((raw.get('source_s3_result_id') or raw['id']) + bid)
                row['module'] = 'chat_step5_access_synthetic'
                row['pipeline_layer'] = 'sequential' if row['node_id'] == 'S3' else 'loop'
                rows.append(row)
                audits.append(row['id'])
        admin.table('audit_results').insert(rows).execute()
        stage = 'rls'
        anon = create_client(cfg['SUPABASE_URL'], cfg['SUPABASE_PUBLIC_KEY'])
        for table in ['businesses', 'audit_results']:
            check(f'rls_anonymous_{table}', anon.table(table).select('id').execute().data == [])
        for index, client in enumerate(session_clients):
            allowed = {bid for bid, owner in zip(bids, owners) if owner == users[index]}
            visible = client.table('businesses').select('id').execute().data
            check(f'rls_owned_businesses_user_{index}', {r['id'] for r in visible} == allowed)
            visible = client.table('audit_results').select('id,business_id').execute().data
            check(f'rls_owned_audits_user_{index}', len(visible) == len(allowed) * 2
                  and all(r['business_id'] in allowed for r in visible))
        stage = 'http_router'
        def node():
            adapter = ChatJsonCompletionAdapter(GeminiCompletion(api_key='synthetic', model='synthetic', max_calls=2, client=sdk))
            return ChatConversationNode(writer=adapter, verifier=adapter)
        app = FastAPI()
        app.include_router(create_chat_router(auth=auth, db_factory=TrackedDB, node_factory=node))
        def headers(index):
            return {'Authorization': 'Bearer ' + sessions[index]}
        with TestClient(app) as http:
            for name, credential in [('anonymous', None), ('public_key_as_session', cfg['SUPABASE_PUBLIC_KEY']),
                                     ('service_key_as_session', cfg['SUPABASE_SERVICE_ROLE_KEY'])]:
                start_db, start_model = len(db_calls), len(sdk.calls)
                response = http.get('/me/businesses', headers={'Authorization': 'Bearer ' + credential} if credential else {})
                check(f'http_rejects_{name}', response.status_code == 401
                      and len(db_calls) == start_db and len(sdk.calls) == start_model)
            tampered = sessions[0].split('.')
            tampered[2] = ('A' if tampered[2][0] != 'A' else 'B') + tampered[2][1:]
            start_db = len(db_calls)
            check('http_bad_signature_before_database', http.get('/me/businesses',
                headers={'Authorization': 'Bearer ' + '.'.join(tampered)}).status_code == 401 and len(db_calls) == start_db)
            for index in range(2):
                response = http.get('/me/businesses', headers=headers(index))
                check(f'http_owned_businesses_user_{index}', response.status_code == 200 and
                    {b['id'] for b in response.json()['businesses']} == {b for b, o in zip(bids, owners) if o == users[index]})
            for name, bid in [('foreign', bids[1]), ('unowned', bids[3]), ('missing', str(uuid4()))]:
                start_db, start_model = len(db_calls), len(sdk.calls)
                response = http.post(f'/business/{bid}/chat', headers=headers(0), json={'question': 'ticket promedio'})
                check(f'http_rejects_{name}_before_evidence', response.status_code == 403 and
                      db_calls[start_db:] == ['businesses'] and len(sdk.calls) == start_model)
            response = http.post(f'/business/{bids[0]}/chat', headers=headers(0), json={'question': '¿Cuál fue el ticket promedio?'})
            check('http_owned_chat_real_grounding', response.status_code == 200 and
                  response.json()['answer']['business_id'] == bids[0] and
                  '125 MXN' in response.json()['answer']['parts'][0]['message'])
            cid = response.json()['conversation_id']
            response = http.get(f'/business/{bids[0]}/chat/{cid}', headers=headers(0))
            check('history_owner_can_read', response.status_code == 200 and len(response.json()['turns']) == 1)
            for name, index, bid, expected_status in [('foreign_business', 1, bids[0], 403),
                ('other_user_own_business', 1, bids[1], 404), ('same_user_other_business', 0, bids[2], 404)]:
                start_db, start_model = len(db_calls), len(sdk.calls)
                response = http.get(f'/business/{bid}/chat/{cid}', headers=headers(index))
                check(f'history_rejects_{name}', response.status_code == expected_status and
                      db_calls[start_db:] == ['businesses'] and len(sdk.calls) == start_model)
            response = http.post(f'/business/{bids[0]}/chat', headers=headers(0),
                json={'question': '¿Qué significa eso?', 'conversation_id': cid})
            check('history_followup_same_scope', response.status_code == 200 and response.json()['conversation_id'] == cid)
            stage = 'ownership_revocation'
            admin.table('businesses').update({'owner_id': None}).eq('id', bids[0]).execute()
            check('rls_revocation_immediate', session_clients[0].table('businesses').select('id').eq('id', bids[0]).execute().data == [])
            for method in ['GET', 'DELETE', 'POST']:
                start_db, start_model = len(db_calls), len(sdk.calls)
                path = f'/business/{bids[0]}/chat' + ('' if method == 'POST' else '/' + cid)
                response = http.request(method, path, headers=headers(0),
                    json={'question': 'ticket promedio', 'conversation_id': cid} if method == 'POST' else None)
                check(f'http_revocation_{method.lower()}', response.status_code == 403 and
                      db_calls[start_db:] == ['businesses'] and len(sdk.calls) == start_model)
        report['simulated_sdk_calls'] = len(sdk.calls)
    except Exception as error:
        code = getattr(error, 'code', None)
        report['failure'] = {'stage': stage, 'type': type(error).__name__,
                             'http_status': getattr(error, 'status_code', None),
                             'code': code if isinstance(code, str) and len(code) < 30 else None}
    finally:
        for table, identifiers in [('audit_results', audits), ('businesses', bids)]:
            if identifiers:
                try:
                    admin.table(table).delete().in_('id', identifiers).execute()
                    report['cleanup'].append({'resource': table, 'success': True})
                except Exception as error:
                    report['cleanup'].append({'resource': table, 'success': False, 'type': type(error).__name__})
        for uid in users:
            try:
                admin.auth.admin.delete_user(uid)
                report['cleanup'].append({'resource': 'temporary_auth_user', 'success': True})
            except Exception as error:
                report['cleanup'].append({'resource': 'temporary_auth_user', 'success': False, 'type': type(error).__name__})
        if baseline is not None:
            try:
                final = snapshot()
                report['final_counts'] = {t: len(v) for t, v in final.items()}
                report['original_ids_preserved'] = baseline == final
            except Exception as error:
                report['cleanup'].append({'resource': 'final_verification', 'success': False, 'type': type(error).__name__})
        report['success'] = ('failure' not in report and report.get('original_ids_preserved', False)
            and all(item['success'] for item in report['cleanup']))
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        Path(output).write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    sys.exit(run(args.config, args.output))
