"""Pruebas MEPIA por secciones. Solo simulaciones y loopback, sin .env privados.

Uso: python scripts/test_mepia_local.py --node RUTA_NODE --playwright RUTA_MODULO
Se ejecuta con el Python del proyecto, con pytest/dependencias instaladas.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = {
    '01_acceso': ('test_chat_api.py', 'test_chat_app.py', 'test_chat_auth_es256.py'),
    '02_interfaz': ('test_dashboard_results.py',),
    '03_documentos': ('test_onboarding_api.py', 'test_persist_ingestion.py', 'test_pbt_n01_pos.py', 'test_video_demo.py'),
    '04_motor': ('test_pbt_s3_calc_engine.py', 'test_validation_rules.py', 'test_pbt_s4_forensic.py', 'test_pbt_n05_orchestrator.py', 'test_pbt_n06_parallel.py', 'test_pbt_n09_financial.py', 'test_pbt_n13_revisor.py', 'test_pbt_layer3_graph.py', 'test_n14_persistence.py'),
    '05_historial_graficas': ('test_analysis_history.py', 'test_audit_results_migration.py'),
    '06_chatbot': ('test_chat_grounding.py', 'test_chat_tools.py', 'test_chat_lineage_persistence.py', 'test_chat_conversation.py', 'test_chat_response.py', 'test_chat_offline_eval.py', 'test_chat_semantic_judge.py'),
    '07_fallos': ('test_chat_provider_gemini.py', 'test_chat_provider_openai.py', 'test_chat_step5_automation.py'),
    '08_integracion_real_separada': ('test_chat_grounding_supabase_integration.py',),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment(output, python=None):
    env = dict(os.environ)
    for key in list(env):
        if any(word in key.upper() for word in ('OPENAI', 'ANTHROPIC', 'GEMINI', 'SUPABASE', 'CHAT_MODEL', 'MEPIA_CHAT_EVAL')):
            env.pop(key)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTHONUTF8='1',
               PYTHON_DOTENV_DISABLED='1', RUN_SUPABASE_INTEGRATION='0',
               NEXT_TELEMETRY_DISABLED='1', ENVIRONMENT='dev',
               NEXT_PUBLIC_SUPABASE_URL='http://127.0.0.1:8025',
               NEXT_PUBLIC_SUPABASE_ANON_KEY='synthetic-public-key', AGENTS_API_URL='http://127.0.0.1:8025',
               OPENAI_API_KEY='synthetic-no-external-provider', ANTHROPIC_API_KEY='',
               CHAT_GEMINI_API_KEY='synthetic-no-external-provider', CHAT_MODEL='synthetic-model',
               SUPABASE_URL='https://synthetic-project.invalid', SUPABASE_SERVICE_ROLE_KEY='synthetic-service-key',
               SUPABASE_JWT_SECRET='synthetic-signing-key-for-tests-only',
               MEPIA_NETWORK_AUDIT_DIR=str(output / 'network'),
               MEPIA_TEST_PYTHON=python or sys.executable,
               MEPIA_TEST_BROWSER='msedge')
    guard = output / 'guard'
    guard.mkdir(parents=True, exist_ok=True)
    (guard / 'sitecustomize.py').write_text('from tests.local_network_guard import install\ninstall()\n', encoding='utf-8')
    env['PYTHONPATH'] = os.pathsep.join((str(guard), str(ROOT)))
    env['NODE_OPTIONS'] = f'--require="{(ROOT / "tests/local_network_guard.cjs").as_posix()}"'
    return env


def run(name, command, output, env, timeout=600):
    print('INICIO '+name, flush=True)
    started = time.monotonic()
    with (output / f'{name}.log').open('w',encoding='utf-8') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    record = {'exit_code':result.returncode, 'seconds':round(time.monotonic()-started,2), 'log':f'{name}.log'}
    print('FIN '+name+' '+json.dumps(record),flush=True)
    return record


def pytest_sections(xml):
    result = {name:Counter() for name in SECTIONS}
    items = []
    for case in ET.parse(xml).iter('testcase'):
        file = next((part+'.py' for part in case.attrib.get('classname','').split('.') if part.startswith('test_')),'')
        section = next((k for k,names in SECTIONS.items() if file in names),'09_infraestructura_demo')
        status = 'failed' if case.find('failure') is not None else 'error' if case.find('error') is not None else 'skipped' if case.find('skipped') is not None else 'passed'
        result.setdefault(section,Counter())[status]+=1
        items.append({'section':section,'class':case.attrib.get('classname'), 'name':case.attrib.get('name'), 'status':status})
    return {k:dict(v) for k,v in result.items()}, items


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',default=shutil.which('node'))
    parser.add_argument('--playwright',default=os.environ.get('MEPIA_PLAYWRIGHT_MODULE'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--phase',choices=('unit','browser','tutorial','all'),default='all')
    args=parser.parse_args(argv)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output=(args.output or ROOT/'.test_tmp'/f'qa_{stamp}').resolve()
    if not output.is_relative_to((ROOT/'.test_tmp').resolve()):parser.error('Salida debe estar en .test_tmp del repositorio')
    output.mkdir(parents=True,exist_ok=False)
    env=environment(output)
    if args.playwright:env['MEPIA_PLAYWRIGHT_MODULE']=args.playwright
    manifest=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').strip('\0').split('\0')
    baseline={n:digest(ROOT/n) for n in manifest if (ROOT/n).is_file()}
    (output/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'started_at_utc':datetime.now(timezone.utc).isoformat(), 'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
            'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(), 'mode':'simulated_only', 'real_provider_calls':0,
            'external_database_access':False,'checks':{}, 'sections':{}, 'complete_human_acceptance':False}
    def save(): (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        if args.phase in ('unit','all'):
            report['checks']['pytest']=run('pytest',[sys.executable,'-B','-m','pytest','tests','-q','-p','no:cacheprovider','--basetemp',str(output/'tmp'),'--junitxml',str(output/'pytest.xml')],output,env)
            if (output/'pytest.xml').exists():
                report['sections'], report['testcases']=pytest_sections(output/'pytest.xml')
            save()
            for name,script,extra in [('fechas','tests/audit_date.cjs',[]),('presentacion','tests/frontend_integration.cjs',[str(output/'presentation.json')]),('historial_presentacion','tests/analysis_history_presentation.cjs',[str(output/'history-presentation.json')]),('restauracion','tests/chat_step5_workspace_test.cjs',[])]:
                report['checks'][name]=run(name,[args.node,*(['--test'] if name=='restauracion' else []),script,*extra],output,env)
                save()
            # Only deterministic S3, no --full-pipeline and no overwrite of legacy evidence.
            code='from tests.eval_test.eval_runner import run_level_1,summary_to_dict; import json; from pathlib import Path; r=summary_to_dict(run_level_1()); Path('+repr(str(output/'motor_oracles.json'))+').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps({k:v for k,v in r.items() if k!="cases"})); raise SystemExit(0 if r["failed_cases"]==0 else 1)'
            report['checks']['oraculos_motor']=run('oraculos_motor',[sys.executable,'-B','-c',code],output,env)
            report['checks']['chat_offline']=run('chat_offline',[sys.executable,'-B','-m','tests.chat_offline_eval','--mode','simulated','--output',str(output/'chat_offline')],output,env)
            report['checks']['matriz_chat']=run('matriz_chat',[sys.executable,'-B','-m','tests.chat_step5_automation','--mode','simulated','--cases','all','--max-model-calls','0','--output',str(output/'chat_matrix')],output,env)
            save()
        if args.phase in ('browser','all'):
            for name,script,key,folder,extra in [
                ('navegador_general','tests/chat_step5_e2e.cjs','MEPIA_STEP5_E2E_OUTPUT','browser_general',{'MEPIA_STEP5_EXTENDED_CHECKS':'1'}),
                ('navegador_historial','tests/analysis_history_e2e.cjs','MEPIA_HISTORY_E2E_OUTPUT','browser_history',{}),
                ('navegador_ajustes','tests/onboarding_step_e2e.cjs','MEPIA_ONBOARDING_E2E_OUTPUT','browser_settings',{})]:
                run_env=dict(env,**{key:str(output/folder)},**extra)
                report['checks'][name]=run(name,[args.node,script],output,run_env,timeout=900)
                save()
            build_code=ROOT/'tests/local_build.cjs'
            report['checks']['build_tipos']=run('build_tipos',[args.node,str(build_code),str(output/'build')],output,env,timeout=900)
            save()
        if args.phase in ('browser','tutorial','all'):
            report['checks']['navegador_tutorial']=run(
                'navegador_tutorial', [args.node, 'tests/tutorial_e2e.cjs', str(output/'browser_tutorial')],
                output, env, timeout=900)
            save()
    finally:
        report['baseline_modified']=[n for n,h in baseline.items() if not (ROOT/n).is_file() or digest(ROOT/n)!=h]
        report['network_events']=dict(Counter(json.loads(line)['event'] for p in (output/'network').glob('*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()))
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        report['passed']=all(r['exit_code']==0 for r in report['checks'].values()) and not report['baseline_modified']
        save()
    print('REPORTE '+str(output/'report.json'),flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
