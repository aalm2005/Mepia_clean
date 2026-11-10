"""Servidor de demostración en memoria. Nunca registrar en api.main/chat_app."""
import asyncio
from copy import deepcopy
from datetime import date, datetime, timezone
from hashlib import sha256
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from api.audit_results import restore_result
from api.onboarding import create_onboarding_router
from api.chat import create_chat_router
from api.analysis_history import create_analysis_router
from api.core.chat_history import ChatHistoryStore
from tests import chat_step5_server as synthetic
from tests.onboarding_fixtures import OnboardingDB
from tests.test_analysis_history import run, metric
from tests.test_chat_api import AUTH, USER_A, USER_B, BIZ_A, BIZ_B, BIZ_C

app = FastAPI(title='MEPIA · Solo datos de demostración')
db = OnboardingDB()
sdk = synthetic.sdk
history = ChatHistoryStore()
app.add_middleware(CORSMiddleware,
                   allow_origins=['http://127.0.0.1:3037','http://localhost:3037'],allow_methods=['*'],allow_headers=['*'])
app.include_router(create_chat_router(auth=AUTH,db_factory=lambda:db,node_factory=synthetic.node,history=history))
app.include_router(create_analysis_router(auth=AUTH,db_factory=lambda:db))
app.include_router(create_onboarding_router(auth=AUTH,db_factory=lambda:db))
app.post('/auth/v1/token')(synthetic.auth_token)
app.get('/auth/v1/user')(synthetic.auth_user)
app.post('/auth/v1/logout')(synthetic.auth_logout)
app.get('/__test__/session/{who}')(synthetic.session)
documents = {}
state = {'scenario':'normal','delay_ms':700,'analyses_created':0,'external_calls':0}
SCENARIOS={'normal','zero','anomalies','incomplete','failed'}


def authorize(request, business=None):
    raw=request.headers.get('authorization','')
    if not raw.startswith('Bearer '): raise HTTPException(401,'Inicia sesión de demostración')
    user=AUTH.user_id(raw[7:])
    if business is not None: AUTH.verify_business_access(db,user,str(business))
    return user


def add_analysis(day, value='0.00', scenario='normal', bid=BIZ_A, saved=None):
    stamp=saved or datetime.now(timezone.utc).isoformat()
    row=run(day=day,saved=stamp,value=value,bid=bid)
    data=row['result_data'];sequence=data['sequential_results']
    data['pipeline_status']='failed' if scenario=='failed' else 'partial' if scenario=='incomplete' else 'completed'
    sequence['calc_results']=[metric(value),metric('125','ticket_promedio','MXN'),metric('24','volumen_tickets','tickets')]
    sequence['active_metrics']=['cash_reconciliation','avg_ticket','ticket_volume']
    sequence['forensic_report']['observed_causality']=None
    if scenario=='anomalies':
        sequence['calc_results'][0]['status']='critical'
        sequence['forensic_report'].update(risk_level='high',anomalies=[{
            'anomaly_id':str(uuid4()),'type':'source_discrepancy','severity':'high',
            'description':'DEMOSTRACIÓN: diferencia de caja preparada para probar una alerta.',
            'quantified_impact':value+' MXN','data_points':['Dato ficticio; no procede de un negocio real.'],
            'metric_origin':'conciliacion_caja'}])
    sequence['audit_insights']=[{'anomaly_ref':'demo','copilot_phrase':'DEMOSTRACIÓN: explicación preparada; no fue generada por IA.',
        'archetype':'Operative Genius','recommended_action':'Comprueba que la cifra, fecha y unidad coincidan con este escenario ficticio.',
        'context_weight':'normal','alert_level':'critical' if scenario=='anomalies' else 'info',
        'module':'Conciliación de caja','raw_result':value+' MXN'}]
    if scenario=='incomplete':
        sequence['calc_results']=[];sequence['active_metrics']=[]
        data['dormant_metrics']=[{'metric':'cash_reconciliation','missing':['conteo de caja']}]
    source_id=str(uuid4())
    row['source_s3_result_id']=source_id
    data['source_s3_result_id']=source_id
    db.rows.extend([{'id':source_id,'business_id':bid,'date':day,'node_id':'S3','node_status':'success',
                    'created_at':stamp,'source_s3_result_id':source_id,
                    'result_data':{'results':deepcopy(sequence['calc_results'])}},row])
    return row


def reset():
    with history._lock:
        if any(item.lock.locked() for item in history._conversations.values()):
            raise HTTPException(409,'Espera a que termine la consulta antes de reiniciar la demostración')
        history._conversations.clear()
    db.rows.clear();documents.clear();sdk.calls.clear()
    for rows in db.settings.values():rows.clear()
    for item in db.businesses:
        item['business_name']={BIZ_A:'DEMOSTRACIÓN · Restaurante A',BIZ_B:'DEMOSTRACIÓN · Restaurante B',BIZ_C:'DEMOSTRACIÓN · Negocio sin análisis'}[item['id']]
    for day,value in [('2026-10-12','12'),('2026-10-13','8'),('2026-10-14','0.00')]:
        add_analysis(day,value,saved=day+'T12:00:00Z')
    add_analysis('2026-10-14','25',saved='2026-10-14T13:00:00Z')
    add_analysis('2026-10-15','-150','anomalies',saved='2026-10-15T12:00:00Z')
    add_analysis('2026-10-16',scenario='incomplete',saved='2026-10-16T12:00:00Z')
    add_analysis('2026-10-17',scenario='failed',saved='2026-10-17T12:00:00Z')
    add_analysis('2026-10-14','666',bid=BIZ_B,saved='2026-10-14T12:00:00Z')
    state.update(scenario='normal',delay_ms=700,analyses_created=0)


reset()


@app.get('/__demo__/state')
def demo_state():
    return {'demo':True,'data':'Ficticios y temporales; no certifican análisis reales.',
            **state,'business_a':BIZ_A,'business_b':BIZ_B,'business_empty':BIZ_C,
            'analyses':sum(row['node_id']=='N05' for row in db.rows),
            'runs':[{'run_id':r['id'],'business_id':r['business_id'],'date':r['date'],'status':r['result_data']['pipeline_status']} for r in db.rows if r['node_id']=='N05'],
            'simulated_sdk_calls':len(sdk.calls),'real_provider_calls':0,'private_environment_loaded':False}


@app.post('/__demo__/scenario')
async def scenario(request:Request):
    if authorize(request)!=USER_A:raise HTTPException(403,'Control del escenario reservado a la cuenta A de demostración')
    body=await request.json()
    choice=body.get('scenario','normal')
    if choice not in SCENARIOS:raise HTTPException(422,'Escenario de demostración desconocido')
    state['scenario']=choice
    state['delay_ms']=min(3000,max(0,int(body.get('delay_ms',700))))
    return demo_state()


@app.post('/__demo__/reset')
def reset_demo(request:Request):
    if authorize(request)!=USER_A:raise HTTPException(403,'Solo la cuenta A puede reiniciar esta demostración')
    reset();return demo_state()


@app.post('/__demo__/upload')
async def upload(request:Request):
    form=await request.form();bid=str(form.get('business_id',''));authorize(request,bid)
    file=form.get('file');kind=form.get('type')
    if file is None or kind not in ('pos','factura'):raise HTTPException(422,'Selecciona un POS PDF o factura XML/PDF')
    raw=await file.read(5*1024*1024+1)
    if len(raw)>5*1024*1024:raise HTTPException(413,'El documento de demostración excede 5 MB')
    fid=str(uuid4());common={'file_id':fid,'storage_path':'demostracion/en-memoria','uploaded_at':datetime.now(timezone.utc).isoformat()}
    try:
        if kind=='pos':
            from agents.pos_parser import extract_pos_data
            extracted=extract_pos_data(raw)
            results=[]
            for item in extracted:
                result={**common,**item.model_dump(mode='json'),'extraction_status':'needs_human_review' if item.needs_human_review else 'success'}
                documents[fid]={'business_id':bid,'type':kind,'date':result.get('date'),'sha256':sha256(raw).hexdigest()}
                results.append(result)
            return results
        from agents.factura_parser import extract_factura_xml,extract_factura_pdf
        parsed=extract_factura_xml(raw) if str(file.filename).lower().endswith('.xml') else extract_factura_pdf(raw)
        fields=parsed.extracted_fields.model_dump(mode='json') if parsed.extracted_fields else None
        documents[fid]={'business_id':bid,'type':kind,'date':(fields or {}).get('transaction_date'),'sha256':sha256(raw).hexdigest()}
        return {**common,'needs_human_review':parsed.needs_human_review,'extraction_status':'needs_human_review' if parsed.needs_human_review else 'success',
                'extracted_fields':fields,'missing_fields':parsed.missing_fields,'ocr_confidence':parsed.ocr_confidence,'transaction_id':None}
    except HTTPException:raise
    except Exception:raise HTTPException(422,'No se pudo leer este documento. Usa los archivos ficticios de demostración.') from None


@app.patch('/__demo__/upload')
async def review(request:Request):
    body=await request.json();item=documents.get(body.get('file_id'))
    if item is None:raise HTTPException(404,'Documento de demostración no encontrado')
    authorize(request,item['business_id'])
    return {'file_id':body['file_id'],'needs_human_review':False,'extraction_status':'success'}


@app.post('/__demo__/run')
async def analyze(request:Request):
    body=await request.json();bid=str(body.get('business_id',''));authorize(request,bid)
    try:day=date.fromisoformat(body['date']).isoformat()
    except (ValueError,KeyError,TypeError):raise HTTPException(422,'Elige una fecha válida') from None
    await asyncio.sleep(state['delay_ms']/1000)
    choice=state['scenario'];value='-150' if choice=='anomalies' else '0.00' if choice=='zero' else '25'
    row=add_analysis(day,value,choice,bid)
    row['result_data']['archetype']=body.get('archetype','Operative Genius')
    state['analyses_created']+=1
    return restore_result(row,db)


@app.post('/__demo__/create')
async def create(request:Request):
    # Same protected path for the control panel, without requiring an upload.
    return await analyze(request)
