"""Exact analysis selection, isolation and lineage; simulated SDK only."""
from copy import deepcopy
import json
from uuid import uuid4
import pytest

from tests.test_chat_api import setup, send, BIZ_A, BIZ_B
from agents.chat_grounding import ChatGroundingService

DAY='2026-11-04'

def pair(db, value, created):
    sid,run=str(uuid4()),str(uuid4())
    db.rows += [
        {'id':sid,'source_s3_result_id':sid,'business_id':BIZ_A,'date':DAY,'node_id':'S3','node_status':'success',
         'created_at':created,'result_data':{'results':[{'metric':'ticket_promedio','value':str(value),'unit':'MXN','status':'ok','context':'Ticket promedio del día.'}]}},
        {'id':run,'source_s3_result_id':sid,'business_id':BIZ_A,'date':DAY,'node_id':'N05','node_status':'success',
         'created_at':created,'result_data':{'pipeline_status':'completed','source_s3_result_id':sid}},
    ]
    return run,sid

def test_older_analysis_same_day_uses_its_exact_s3(setup):
    client,db,sdk,_,_=setup
    old,sid=pair(db,'77.00','2026-11-10T10:00:00Z')
    newer,new_sid=pair(db,'199.00','2026-11-10T11:00:00Z')
    response=send(client,analysis_run_id=old)
    assert response.status_code==200,response.text
    answer=response.json()['answer']
    refs=[r for p in answer['parts'] for r in p['evidence']]
    assert answer['resolved_date']==DAY
    assert any(r['audit_result_id']==sid for r in refs)
    assert not any(r['audit_result_id']==new_sid for r in refs)
    assert '77.00' in json.dumps(answer)

@pytest.mark.parametrize('problem,code',[
    ('missing',404),('foreign',404),('running',409),('failed',409),('source_missing',409),
    ('source_conflict',409),('source_foreign',409),('date_mismatch',422),('invalid_uuid',422),
])
def test_rejected_selection_never_reaches_model(setup,problem,code):
    client,db,sdk,_,factory=setup
    run,sid=pair(db,'77.00','2026-11-10T10:00:00Z')
    row=db.rows[-1]
    kwargs={'analysis_run_id':run}
    if problem=='missing':kwargs['analysis_run_id']=str(uuid4())
    if problem=='foreign':row['business_id']=BIZ_B
    if problem in ('running','failed'):row['result_data']['pipeline_status']=problem
    if problem=='source_missing':row['source_s3_result_id']=None;row['result_data'].pop('source_s3_result_id')
    if problem=='source_conflict':row['result_data']['source_s3_result_id']=str(uuid4())
    if problem=='source_foreign':db.rows[-2]['business_id']=BIZ_B
    if problem=='date_mismatch':kwargs['requested_date']='2026-11-05'
    if problem=='invalid_uuid':kwargs['analysis_run_id']='not-a-uuid'
    response=send(client,**kwargs)
    assert response.status_code==code,response.text
    assert sdk.calls==factory==[]

def test_selected_run_does_not_reuse_history_from_another_same_day_run(setup):
    client,db,sdk,_,_=setup
    old,_=pair(db,'77.00','2026-11-10T10:00:00Z')
    newer,_=pair(db,'199.00','2026-11-10T11:00:00Z')
    first=send(client,analysis_run_id=old)
    assert first.status_code==200
    before=len(sdk.calls)
    second=send(client,analysis_run_id=newer,conversation_id=first.json()['conversation_id'])
    assert second.status_code==200,second.text
    if len(sdk.calls)>before:
        data=json.loads(sdk.calls[before]['messages'][1]['content'])['untrusted_data']
        assert not data.get('history')

def test_exact_source_never_falls_back_to_latest(setup):
    _,db,_,_,_=setup
    _,sid=pair(db,'77.00','2026-11-10T10:00:00Z')
    _,new_sid=pair(db,'199.00','2026-11-10T11:00:00Z')
    packet=ChatGroundingService(db).build_packet(BIZ_A,DAY,sid)
    assert packet.source_s3_result_id==sid and packet.metrics[0]['value']=='77.00'
    missing=ChatGroundingService(db).build_packet(BIZ_A,DAY,str(uuid4()))
    assert missing.source_s3_result_id is None and missing.metrics==[]
    assert new_sid not in [r.audit_result_id for r in missing.evidence]
