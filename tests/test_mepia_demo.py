"""Demo manual: autorización, documentos reales de fixture y resultados ficticios."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from tests import mepia_demo_server as demo
from tests.test_chat_api import headers, USER_B, BIZ_A, BIZ_B, BIZ_C


@pytest.fixture
def client():
    demo.reset()
    with TestClient(demo.app) as browser:yield browser
    demo.reset()


@pytest.mark.parametrize('endpoint',['scenario','reset','run','create','upload'])
def test_anonymous_never_mutates_demo(client,endpoint):
    before=len(demo.db.rows)
    response=client.post('/__demo__/'+endpoint,json={'business_id':BIZ_A,'date':'2026-10-14'})
    assert response.status_code in (401,403)
    assert len(demo.db.rows)==before


def test_other_owner_cannot_create_or_reset(client):
    before=len(demo.db.rows)
    assert client.post('/__demo__/run',headers=headers(USER_B),json={'business_id':BIZ_A,'date':'2026-10-14'}).status_code==403
    assert client.post('/__demo__/reset',headers=headers(USER_B)).status_code==403
    assert len(demo.db.rows)==before


@pytest.mark.parametrize('scenario,status',[('normal','completed'),('zero','completed'),('anomalies','completed'),('incomplete','partial'),('failed','failed')])
def test_created_result_stays_scoped_readable_and_finite(client,scenario,status):
    assert client.post('/__demo__/scenario',headers=headers(),json={'scenario':scenario,'delay_ms':0}).status_code==200
    response=client.post('/__demo__/run',headers=headers(),json={'business_id':BIZ_A,'date':'2026-10-14'})
    assert response.status_code==200,response.text
    body=response.json();assert body['pipeline_status']==status
    result=client.get('/business/'+BIZ_A+'/analyses/'+body['run_id'],headers=headers())
    assert result.status_code==200
    assert client.get('/business/'+BIZ_B+'/analyses/'+body['run_id'],headers=headers(USER_B)).status_code==404
    if scenario=='zero':assert result.json()['sequential_results']['calc_results'][0]['value']=='0.00'
    if scenario=='incomplete':assert result.json()['forensic_status_available'] is False
    if scenario=='anomalies':assert len(result.json()['sequential_results']['forensic_report']['anomalies'])==1
    if scenario=='failed':assert result.json()['forensic_status_available'] is False
    assert demo.sdk.calls==[]


def test_document_parsers_use_demo_bytes_and_never_write_disk(client):
    folder=Path(__file__).resolve().parents[1]/'output/pdf/demo_mepia_20261014'
    for name,kind in [('01_ventas_demo_2026-10-14.pdf','pos'),('02_compra_demo_2026-10-14.xml','factura')]:
        data=(folder/name).read_bytes()
        response=client.post('/__demo__/upload',headers=headers(),data={'business_id':BIZ_A,'type':kind},files={'file':(name,data)})
        assert response.status_code==200,response.text
        result=response.json()
        if kind=='pos':assert result[0]['date']=='2026-10-14'
        else:assert result['extracted_fields']['transaction_date']=='2026-10-14'
        assert (folder/name).read_bytes()==data
    assert len(demo.documents)==2 and demo.sdk.calls==[]


def test_empty_business_no_fabricated_chat_result_and_reset(client):
    assert client.get('/business/'+BIZ_C+'/analyses',headers=headers()).json()['items']==[]
    response=client.post('/business/'+BIZ_C+'/chat',headers=headers(),json={'question':'¿Cuál fue el ticket promedio?'})
    assert response.status_code==200
    assert response.json()['answer']['parts'][0]['status']=='missing_data'
    cid=response.json()['conversation_id']
    original=len(demo.db.rows)
    client.post('/__demo__/scenario',headers=headers(),json={'scenario':'normal','delay_ms':0})
    client.post('/__demo__/run',headers=headers(),json={'business_id':BIZ_A,'date':'2026-10-20'})
    assert len(demo.db.rows)>original
    client.post('/__demo__/reset',headers=headers())
    assert len(demo.db.rows)==original and demo.state['analyses_created']==0
    assert client.get('/business/'+BIZ_C+'/chat/'+cid,headers=headers()).status_code==404


@pytest.mark.parametrize('payload',[{'business_id':BIZ_A,'date':'no-date'},{'business_id':BIZ_A}])
def test_bad_date_rejected_before_creation(client,payload):
    before=len(demo.db.rows)
    assert client.post('/__demo__/run',headers=headers(),json=payload).status_code==422
    assert len(demo.db.rows)==before
