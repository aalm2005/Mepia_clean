"""N05 real con generadores simulados, persistencia y recuperación exacta S3."""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import agents.ceo_orchestrator as ceo
from agents.calc_engine import CalcResult
from agents.gatekeeper import GatekeeperResult, DormantMetric, BlockedMetric
from api.audit_results import restore_result
from tests.test_video_demo import DB
from tests.test_n14_persistence import load_synthetic_api

DAY = '2026-10-14'


def orchestrator(monkeypatch, db, partial=True):
    gate = GatekeeperResult(business_id=db.bid, date=DAY, active_metrics=['cash_reconciliation'],
        dormant_metrics=[DormantMetric(metric='avg_ticket', missing=['tickets'])] if partial else [],
        blocked_metrics=[BlockedMetric(metric='inventory_variance', reason='needs_human_review')] if partial else [])
    monkeypatch.setattr(ceo, 'GatekeeperAgent', lambda db: SimpleNamespace(get_status=lambda *args: gate))
    source = str(uuid4())
    calc = CalcResult(metric='conciliacion_caja', value=Decimal('0.00'), unit='MXN', status='ok', context='Caja de prueba')
    monkeypatch.setattr(ceo, 'run_calc_engine', lambda *args: SimpleNamespace(run_id=source, results=[calc]))
    report = {'business_id':db.bid, 'date':DAY, 'risk_level':'low', 'anomalies':[],
        'evidence_sources':[], 'observed_causality':None, 'generated_at':'2026-10-15T00:00:00Z'}
    monkeypatch.setattr(ceo, 'ForensicCFOAgent', lambda: SimpleNamespace(run=lambda **kw: SimpleNamespace(
        risk_level='low', model_dump=lambda **kw: report)))
    instance = ceo.N05CEOOrchestrator.__new__(ceo.N05CEOOrchestrator)
    instance._db = db
    instance._get_rag_context = lambda *args: ''
    instance._synthesize_insights = lambda **kw: []
    instance._evaluate_escalation = lambda **kw: ceo.EscalationInfo(triggered=False)
    return instance, source


@pytest.mark.parametrize('partial', [False, True])
def test_completed_run_round_trip_preserves_decimals_states_and_lineage(monkeypatch, partial):
    db=DB(); instance, source=orchestrator(monkeypatch,db,partial)
    result=instance.run(db.bid,DAY,'Operative Genius',False,'short')
    row=db.store['audit_results'][0]
    assert row['source_s3_result_id']==source
    assert row['result_data']['sequential_results']['calc_results'][0]['value']=='0.00'
    assert restore_result(row,db)==result.model_dump(mode='json')
    assert result.metric_status_available is True
    assert bool(result.dormant_metrics)==partial and bool(result.blocked_metrics)==partial


def test_persistence_failure_does_not_report_success_or_expose_database_text(monkeypatch):
    db=DB(); instance,_=orchestrator(monkeypatch,db)
    db.table=lambda name: SimpleNamespace(insert=lambda row: SimpleNamespace(
        execute=lambda: (_ for _ in ()).throw(RuntimeError('synthetic-private-detail'))))
    with pytest.raises(ceo.N05PersistenceError) as error:
        instance.run(db.bid,DAY,'Operative Genius',False,'short')
    assert 'synthetic-private' not in str(error.value)


def legacy(db):
    source=str(uuid4())
    row={'id':str(uuid4()),'business_id':db.bid,'date':DAY,'node_id':'N05',
        'created_at':'2026-10-15T00:00:00Z','source_s3_result_id':source,
        'result_data':{'source_s3_result_id':source,'audit_insights':[],
                       'forensic_report':{'risk_level':'low','anomalies':[]}}}
    s3={'id':source,'business_id':db.bid,'date':DAY,'node_id':'S3','node_status':'success',
        'result_data':{'results':[{'metric':'conciliacion_caja','value':'0.00','unit':'MXN','status':'ok','context':'Prueba'}],
                       'skipped_metrics':['avg_ticket']}}
    db.store['audit_results']=[row,s3]
    return row,s3


def test_legacy_recovers_only_linked_s3_without_inventing_s2_or_writing():
    db=DB(); row,s3=legacy(db)
    # Otro S3 más reciente para la misma fecha no puede sustituir al enlazado.
    other=deepcopy(s3);other['id']=str(uuid4());other['result_data']['results'][0]['value']='999'
    db.store['audit_results'].append(other)
    before=deepcopy(db.store)
    result=restore_result(row,db)
    assert result['sequential_results']['calc_results']==s3['result_data']['results']
    assert result['metric_status_available'] is False
    assert result['dormant_metrics']==[] and result['sequential_results']['active_metrics']==[]
    assert db.writes==[] and db.store==before


@pytest.mark.parametrize('bad', ['missing','conflict','invalid','business','date','node','status'])
def test_legacy_never_borrows_unlinked_or_incompatible_evidence(bad):
    db=DB(); row,s3=legacy(db)
    if bad=='missing': row.pop('source_s3_result_id');row['result_data'].pop('source_s3_result_id')
    elif bad=='conflict': row['result_data']['source_s3_result_id']=str(uuid4())
    elif bad=='invalid': row['source_s3_result_id']=row['result_data']['source_s3_result_id']='invalid'
    elif bad=='business': s3['business_id']=str(uuid4())
    elif bad=='date': s3['date']='2026-10-13'
    elif bad=='node': s3['node_id']='N14'
    elif bad=='status': s3['node_status']='failed'
    result=restore_result(row,db)
    assert result['sequential_results']['calc_results']==[]
    assert result['metric_status_available'] is False and db.writes==[]


def test_http_get_returns_saved_complete_result_and_unknown_id_is_404(monkeypatch):
    api=load_synthetic_api(monkeypatch)
    db=DB(); row,s3=legacy(db)
    monkeypatch.setattr(api,'get_supabase',lambda:db)
    app=FastAPI();app.get('/result/{run_id}')(api.orchestrator_result)
    client=TestClient(app)
    response=client.get('/result/'+row['id'])
    assert response.status_code==200
    assert response.json()['sequential_results']['calc_results'][0]['value']=='0.00'
    assert response.json()['metric_status_available'] is False
    assert client.get('/result/'+str(uuid4())).status_code==404
    assert db.writes==[]
