"""Historial/tendencias reales sobre filas simuladas: cero DB/proveedores externos."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4
import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.analysis_history import create_analysis_router, trends_for, pipeline_status, numeric
from api.audit_results import restore_result
from tests.test_chat_api import AUTH, DB, BIZ_A, BIZ_B, BIZ_C, USER_A, USER_B, headers, token

def metric(value='0.00', name='conciliacion_caja', unit='MXN', status='ok'):
    return {'metric':name,'value':value,'unit':unit,'status':status,'context':'Dato simulado'}

def run(day='2026-10-14', saved='2026-10-15T10:00:00Z', status='completed', value='0.00', bid=BIZ_A):
    return {'id':str(uuid4()),'business_id':bid,'node_id':'N05','node_status':'success','date':day,'created_at':saved,
        'result_data':{'pipeline_status':status,'archetype':'Operative Genius',
            'sequential_results':{'active_metrics':['cash_reconciliation'],'calc_results':[metric(value)],
                'forensic_report':{'business_id':bid,'date':day,'risk_level':'low','anomalies':[],
                    'evidence_sources':['S3'],'generated_at':saved},'audit_insights':[]},
            'dormant_metrics':[],'blocked_metrics':[], 'escalation':{'triggered':False,'reason':None,'layer2_run_id':None}}}

@pytest.fixture
def setup():
    db=DB(); db.rows=[]
    app=FastAPI(); app.include_router(create_analysis_router(auth=AUTH,db_factory=lambda:db))
    with TestClient(app) as client: yield client, db

def path(bid=BIZ_A, suffix=''): return f'/business/{bid}/analyses'+suffix

@pytest.mark.parametrize('suffix',['','/latest','/'+str(uuid4()),'/'+str(uuid4())+'/trends','/'+str(uuid4())+'/layer3'])
@pytest.mark.parametrize('authorization',[None,'Bearer invalid','Basic fake','expired'])
def test_session_before_database(setup,suffix,authorization):
    client,db=setup
    if authorization=='expired':authorization='Bearer '+token(exp=1)
    res=client.get(path(suffix=suffix),headers={'Authorization':authorization} if authorization else {})
    assert res.status_code==401 and db.calls==[]

@pytest.mark.parametrize('bid',[BIZ_B,str(uuid4())])
@pytest.mark.parametrize('suffix',['','/latest','/'+str(uuid4()),'/'+str(uuid4())+'/trends','/'+str(uuid4())+'/layer3'])
def test_foreign_missing_owner_or_revocation_blocks_evidence(setup,bid,suffix):
    client,db=setup
    res=client.get(path(bid,suffix),headers=headers())
    assert res.status_code==403 and db.calls==['businesses']

def test_revocation_rechecked_on_every_read(setup):
    client,db=setup;row=run();db.rows=[row]
    assert client.get(path(suffix='/'+row['id']),headers=headers()).status_code==200
    db.businesses[0]['owner_id']=None;db.calls=[]
    assert client.get(path(suffix='/'+row['id']),headers=headers()).status_code==403
    assert db.calls==['businesses']

@pytest.mark.parametrize('table',['businesses','audit_results'])
def test_failure_is_sanitized_and_not_empty_success(setup,table):
    client,db=setup;db.fail=table
    res=client.get(path(),headers=headers())
    assert res.status_code==503 and 'synthetic-private' not in res.text

def test_empty_and_pagination_order_same_day_no_dedup(setup):
    client,db=setup
    assert client.get(path(),headers=headers()).json()['items']==[]
    assert client.get(path(suffix='/latest'),headers=headers()).json()['analysis'] is None
    rows=[run() for _ in range(28)];db.rows=rows+[run(bid=BIZ_B)]
    expected=sorted([r['id'] for r in rows],reverse=True)
    first=client.get(path(),headers=headers());second=client.get(path(suffix='?page=1'),headers=headers())
    assert first.headers['cache-control']=='private, no-store'
    assert first.json()['next_page']==1 and second.json()['next_page'] is None
    items=first.json()['items']+second.json()['items']
    assert [i['run_id'] for i in items]==expected and len({i['run_id'] for i in items})==28
    assert all(i['status']=='completed' and i['created_at'] for i in items)

def test_latest_skips_running_failed_and_reads_past_first_page(setup):
    client,db=setup;old=run(saved='2026-10-10T00:00:00Z')
    db.rows=[run(status='running') for _ in range(101)]+[run(status='failed'),old,run(bid=BIZ_B)]
    assert client.get(path(suffix='/latest'),headers=headers()).json()['analysis']['run_id']==old['id']
    db.rows.append(run(saved='2026-10-20T00:00:00Z',status='partial'))
    assert client.get(path(suffix='/latest'),headers=headers()).json()['analysis']['status']=='partial'

def test_explicit_id_isolated_and_saved_legacy_lineage_read_only(setup):
    client,db=setup;foreign=run(bid=BIZ_B);selected=run();before=deepcopy([selected,foreign]);db.rows=deepcopy(before)
    for rid in [str(uuid4()),foreign['id']]:
        res=client.get(path(suffix='/'+rid),headers=headers());assert res.status_code==404
        assert 'no existe o no corresponde' in res.json()['detail']
    res=client.get(path(suffix='/'+selected['id']),headers=headers())
    assert res.status_code==200 and res.json()['sequential_results']['calc_results'][0]['value']=='0.00'
    assert res.json()['forensic_status_available'] is True
    assert db.rows==before
    assert client.get(path(suffix='/not-a-uuid'),headers=headers()).status_code==422

def test_trends_exact_selected_run_per_day_order_no_addition_and_no_future(setup):
    client,db=setup
    early=run(day='2026-10-12',value='10');selected=run(value='0.00');newer=run(saved='2026-10-15T11:00:00Z',value='999')
    failed=run(day='2026-10-12',saved='2026-10-18T00:00:00Z',status='failed',value='888')
    future=run(day='2026-10-16',value='777')
    db.rows=[newer,future,early,selected,failed,run(bid=BIZ_B,value='666')];before=deepcopy(db.rows)
    res=client.get(path(suffix='/'+selected['id']+'/trends'),headers=headers())
    assert res.status_code==200
    series=res.json()['series'][0]
    assert [(p['date'],p['value']) for p in series['points']]==[('2026-10-12','10'),('2026-10-13',None),('2026-10-14','0.00')]
    assert series['valid_periods']==2 and series['missing_periods']==1
    assert series['points'][-1]['run_id']==selected['id'] and db.rows==before

def test_unit_meaning_null_zero_duplicate_and_unsupported_not_summed(setup):
    client,db=setup;a=run(day='2026-10-13');b=run()
    a['result_data']['sequential_results']['calc_results']=[metric('0'),metric('20','merma','%'),metric('100','health_score','MXN')]
    b['result_data']['sequential_results']['calc_results']=[metric('7',unit='%'),metric(None,name='ticket_promedio'),metric('20','merma','%')]
    db.rows=[a,b]
    data=client.get(path(suffix='/'+b['id']+'/trends'),headers=headers()).json()
    assert data['ignored_results']==4
    cash=next(s for s in data['series'] if s['metric']=='conciliacion_caja')
    assert cash['valid_periods']==1 and [p['value'] for p in cash['points']]==['0',None]
    b['result_data']['sequential_results']['calc_results']=[metric('9'),metric('11')]
    data=client.get(path(suffix='/'+b['id']+'/trends'),headers=headers()).json()
    assert data['series'][0]['points'][-1]['value'] is None

@pytest.mark.parametrize('bad',[None,'','NaN','Infinity',True,[],{},'1e1000'])
def test_invalid_values_are_not_zero(bad): assert numeric(bad) is None

@pytest.mark.parametrize('status',['incomplete_data','unit_mismatch'])
def test_bad_status_does_not_become_a_point(setup,status):
    client,db=setup;row=run();row['result_data']['sequential_results']['calc_results'][0]['status']=status;db.rows=[row]
    data=client.get(path(suffix='/'+row['id']+'/trends'),headers=headers()).json()
    assert data['series'][0]['valid_periods']==0

def test_truncation_is_visible(setup):
    client,db=setup;row=run();db.rows=[run() for _ in range(301)]+[row]
    assert client.get(path(suffix='/'+row['id']+'/trends'),headers=headers()).json()['limited'] is True

@pytest.mark.parametrize('bad',['absent','missing_date','missing_business','invalid_value','no_calculations','failed'])
def test_absence_of_forensic_evidence_never_means_no_anomalies(setup,bad):
    _,db=setup;row=run();seq=row['result_data']['sequential_results']
    if bad=='absent':seq.pop('forensic_report')
    elif bad=='missing_date':seq['forensic_report'].pop('date')
    elif bad=='missing_business':seq['forensic_report'].pop('business_id')
    elif bad=='invalid_value':seq['calc_results'][0]['value']='NaN'
    elif bad=='no_calculations':seq['calc_results']=[]
    elif bad=='failed':row['result_data']['pipeline_status']='failed'
    assert restore_result(row,db)['forensic_status_available'] is False

def test_failed_node_overrules_success_payload(setup):
    client,db=setup;row=run();row['node_status']='failed';db.rows=[row]
    assert pipeline_status(row)=='failed'
    assert client.get(path(suffix='/latest'),headers=headers()).json()['analysis'] is None
    assert client.get(path(suffix='/'+row['id']),headers=headers()).json()['forensic_status_available'] is False

def test_layer3_parent_resolution_failure_and_business_filter(setup):
    from agents.layer3_execution import execute_layer3
    from agents.n14_informe_final import N14PersistenceError
    client,db=setup;row=run(status='escalated');parent,lid=str(uuid4()),str(uuid4())
    row['result_data']['escalation']={'triggered':True,'reason':'test','layer2_run_id':parent}
    start={'id':str(uuid4()),'business_id':BIZ_A,'node_id':'N10','created_at':row['created_at'],
           'result_data':{'layer2_run_id':parent,'layer3_run_id':lid}}
    foreign={'id':str(uuid4()),'business_id':BIZ_B,'node_id':'N14','created_at':row['created_at'],
             'node_status':'success','result_data':{'layer3_run_id':lid,'draft_status':'approved'}}
    db.rows=[row,start,foreign]
    url=path(suffix='/'+row['id']+'/layer3')
    assert client.get(url,headers=headers()).json()['status']=='running'
    async def fail(_):raise N14PersistenceError()
    asyncio.run(execute_layer3(SimpleNamespace(ainvoke=fail),{'layer3_run_id':lid,'layer2_run_id':parent}))
    result=client.get(url,headers=headers())
    assert result.status_code==200 and result.json()['status']=='failed'
    assert result.json()['layer3_run_id']==lid

def test_legacy_uses_only_exact_s3_and_does_not_invent_forensics(setup):
    client,db=setup;row=run();source=str(uuid4())
    row['source_s3_result_id']=source;row['result_data']={'pipeline_status':'completed','source_s3_result_id':source}
    db.rows=[row,{'id':source,'business_id':BIZ_A,'date':row['date'],'node_id':'S3','node_status':'success','result_data':{'results':[metric()]}}]
    res=client.get(path(suffix='/'+row['id']),headers=headers()).json()
    assert res['sequential_results']['calc_results'][0]['value']=='0.00'
    assert res['metric_status_available'] is False and res['forensic_status_available'] is False
