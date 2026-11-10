"""Escenario E2E aislado, sin .env ni red externa; extiende Auth simulado existente."""
from copy import deepcopy
from fastapi import Request
from tests.chat_step5_server import app, db, sdk
from tests.test_analysis_history import run, metric
from tests.test_chat_api import BIZ_A, BIZ_B

first=run(day='2026-10-12',saved='2026-10-13T10:00:00Z',value='12')
selected=run(day='2026-10-14',saved='2026-10-15T10:00:00Z',value='0.00')
latest=run(day='2026-10-14',saved='2026-10-15T11:00:00Z',value='25')
failed=run(saved='2026-10-15T12:00:00Z',status='failed',value='999')
foreign=run(bid=BIZ_B,value='666')
no_data=run(day='2026-10-11',saved='2026-10-12T10:00:00Z',status='partial')
no_data['result_data']['sequential_results']['calc_results']=[]
db.rows.extend([first,selected,latest,failed,foreign,no_data])
baseline=deepcopy(db.rows)
requests=[]
delay_ms=0

@app.middleware('http')
async def observe(request:Request, call_next):
    import asyncio
    if '/analyses' in request.url.path:
        requests.append({'method':request.method,'path':request.url.path})
        if delay_ms and request.url.path.endswith('/'+selected['id']): await asyncio.sleep(delay_ms/1000)
    return await call_next(request)

@app.get('/__test__/analyses')
def analyses():
    return {'no_data':no_data['id'],'first':first['id'],'selected':selected['id'],'latest':latest['id'],'failed':failed['id'],'foreign':foreign['id'],
        'requests':requests,'model_calls':len(sdk.calls),'rows_unchanged':db.rows==baseline}

@app.post('/__test__/delay')
async def delay(request:Request):
    global delay_ms
    delay_ms=(await request.json())['ms']
    return {'ok':True}
