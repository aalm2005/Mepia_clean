"""Puerta de la demo: misma UI; escrituras simuladas con Bearer en memoria."""
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
import httpx

app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
NEXT='http://127.0.0.1:3036'
API='http://127.0.0.1:8025'
DROP={'connection','keep-alive','transfer-encoding','content-encoding','content-length','host'}
PANEL='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>MEPIA · Pruebas sin API</title><style>body{font:17px system-ui;max-width:850px;margin:35px auto;padding:20px;background:#eff4fb;color:#142c4e}button,a,select,input{font:inherit;margin:8px;padding:10px}section{background:white;padding:20px;margin:18px 0;border-radius:12px}a{display:inline-block}#notice{white-space:pre-wrap}</style>
<h1>MEPIA · Datos de demostración</h1><p>Todo es ficticio y temporal. Cero llamadas a proveedores reales; no usa la base principal.</p>
<section><h2>1. Abrir las pantallas</h2><p>Cuenta A: <b>a@example.invalid</b><br>Cuenta B: <b>b@example.invalid</b><br>Contraseña de ambas: <b>synthetic-test-password</b></p><a href="/login">Abrir MEPIA</a><p>La cuenta A tiene un restaurante con análisis y otro vacío. La cuenta B permite comprobar separación de cuentas.</p></section>
<section><h2>2. Preparar el próximo análisis ficticio</h2><label>Escenario <select id="scenario"><option value="normal">Completado</option><option value="zero">Cero válido</option><option value="anomalies">Con anomalía</option><option value="incomplete">Sin datos suficientes</option><option value="failed">Fallido</option></select></label><label>Fecha <input id="day" type="date" value="2026-10-14"></label><button id="prepare">Aplicar escenario</button><button id="create">Crear análisis ficticio sin documentos</button><p>También puedes cargar los archivos de demo en Documentos. La extracción es local; el resultado del análisis es prefabricado y no se deriva de esos importes.</p></section>
<section><h2>3. Reiniciar y comprobar</h2><button id="reset">Reiniciar solo datos de demostración</button><button id="state">Ver estado</button><p>Reiniciar borra únicamente los datos temporales de este proceso. Si una selección antigua da error, entra de nuevo a MEPIA o elige otra corrida del historial.</p><p id="notice" role="status"></p></section>
<script>async function token(){let r=await fetch('/__demo__/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'a@example.invalid',password:'synthetic-test-password'})});return(await r.json()).access_token;}
async function action(path,body){let r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+await token()},body:JSON.stringify(body||{})});let data=await r.json();if(!r.ok)throw Error(data.detail||'No se pudo completar la demostración');return data;}
async function show(fn){try{document.getElementById('notice').textContent=JSON.stringify(await fn(),null,2);}catch(e){document.getElementById('notice').textContent=e.message;}}
document.getElementById('prepare').onclick=()=>show(()=>action('/__demo__/scenario',{scenario:document.getElementById('scenario').value}));
document.getElementById('create').onclick=()=>show(async()=>{await action('/__demo__/scenario',{scenario:document.getElementById('scenario').value});let s=await(await fetch('/__demo__/state')).json();let r=await action('/__demo__/create',{business_id:s.business_a,date:document.getElementById('day').value});return {run_id:r.run_id,date:r.date,status:r.pipeline_status,notice:'Elige esta corrida en el historial o abre Dashboard con su run_id.'};});
document.getElementById('reset').onclick=()=>show(()=>action('/__demo__/reset'));document.getElementById('state').onclick=()=>show(async()=>await(await fetch('/__demo__/state')).json());</script></html>'''


@app.get('/__demo__',response_class=HTMLResponse)
def panel():return PANEL


@app.api_route('/{path:path}',methods=['GET','POST','PATCH','PUT','DELETE','OPTIONS','HEAD'])
async def proxy(path:str,request:Request):
    if path=='api/upload' and request.method in ('POST','PATCH'):target=API+'/__demo__/upload'
    elif path=='api/audit' and request.method=='POST':target=API+'/__demo__/run'
    elif path=='__demo__/auth':target=API+'/auth/v1/token?grant_type=password'
    elif path.startswith('__demo__/'):target=API+'/'+path
    else:target=NEXT+'/'+path
    if request.url.query and '?' not in target:target+='?'+request.url.query
    headers={k:v for k,v in request.headers.items() if k.lower() not in DROP}
    headers['accept-encoding']='identity'
    async with httpx.AsyncClient(trust_env=False,timeout=90,follow_redirects=False) as client:
        upstream=await client.request(request.method,target,headers=headers,content=await request.body())
    content=upstream.content
    outgoing={k:v for k,v in upstream.headers.items() if k.lower() not in DROP}
    if 'text/html' in upstream.headers.get('content-type','') and b'<body' in content:
        # Visible throughout the real UI; never part of a production component.
        banner=b'<style data-mepia-demo>body::after{content:"DEMOSTRACION: datos ficticios, sin API real. Panel: /__demo__";position:fixed;bottom:0;left:0;right:0;z-index:2147483647;background:#713f12;color:white;text-align:center;padding:6px;font:14px system-ui;pointer-events:none}</style>'
        content=content.replace(b'</head>',banner+b'</head>',1)
    return Response(content,status_code=upstream.status_code,headers=outgoing)
