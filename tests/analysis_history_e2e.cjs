const {dismissTutorialWhenPresent}=require("./tutorial_test_helpers.cjs");
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const net=require('node:net');const {spawn}=require('node:child_process');
const {chromium}=require(process.env.MEPIA_PLAYWRIGHT_MODULE||'playwright');
const {restoreGeneratedTypes}=require('./chat_step5_workspace.cjs');
const base='http://127.0.0.1:3025',api='http://127.0.0.1:8025';
const out=path.resolve(process.env.MEPIA_HISTORY_E2E_OUTPUT||'.test_tmp/history_20261019/e2e');const dist=path.join(out,'next');
assert(out.startsWith(path.resolve('.test_tmp')+path.sep),'Salida debe estar en .test_tmp');
const beforeConfig=fs.readFileSync('tsconfig.json','utf8'),beforeEnv=fs.readFileSync('next-env.d.ts','utf8');
const children=[],checks=[],errors=[];let browser,page,failed;
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function start(exe,args,name,env={}){const log=fs.openSync(path.join(out,name+'.log'),'w');const child=spawn(exe,args,{cwd:process.cwd(),windowsHide:true,env:{...process.env,...env},stdio:['ignore',log,log]});children.push(child);}
async function ready(url){for(let i=0;i<120;i++){try{if((await fetch(url)).ok)return;}catch{}await pause(500);}throw Error('Servidor de prueba no responde');}
async function free(port){const srv=net.createServer();await new Promise((resolve,reject)=>{srv.once('error',reject);srv.listen(port,'127.0.0.1',()=>srv.close(resolve));});}
async function check(name,fn){await fn();checks.push({name,passed:true});console.log('PASS '+name);}
async function zero(){await page.waitForFunction(()=>[...document.querySelectorAll('.kpi-value')].some(el=>el.textContent.trim().startsWith('0')));}
async function choose(id){await page.getByLabel('Análisis guardado',{exact:true}).selectOption(id);await page.waitForURL(u=>u.searchParams.get('run_id')===id);}
(async()=>{
  fs.mkdirSync(out,{recursive:true});assert(process.env.MEPIA_TEST_PYTHON);await free(3025);await free(8025);
  start(process.env.MEPIA_TEST_PYTHON,['-B','-m','uvicorn','tests.analysis_history_server:app','--host','127.0.0.1','--port','8025'],'api',{PYTHONDONTWRITEBYTECODE:'1'});
  await ready(api+'/__test__/state');
  start(process.execPath,['node_modules/next/dist/bin/next','dev','--hostname','127.0.0.1','--port','3025'],'next',{
    NEXT_TELEMETRY_DISABLED:'1',NEXT_PUBLIC_SUPABASE_URL:api,NEXT_PUBLIC_SUPABASE_ANON_KEY:'synthetic-public-key',AGENTS_API_URL:api,MEPIA_NEXT_DIST_DIR:path.relative(process.cwd(),dist)});
  await ready(base+'/login');
  const state=await(await fetch(api+'/__test__/state')).json();const data=await(await fetch(api+'/__test__/analyses')).json();
  await check('Proxy anónimo bloquea historial, resultado y tendencias',async()=>{
    for(const suffix of ['', '/latest','/'+data.selected,'/'+data.selected+'/trends'])assert.equal((await fetch(base+'/api/analyses/'+state.business_a+suffix)).status,401);
  });
  browser=await chromium.launch({headless:true,channel:process.env.MEPIA_TEST_BROWSER||'msedge'});
  const context=await browser.newContext({viewport:{width:1360,height:1000}});context.setDefaultTimeout(60000);
  await context.route('**/*',route=>{const url=route.request().url();return url.startsWith(base)||url.startsWith(api)?route.continue():route.abort();});
  page=await context.newPage(); await dismissTutorialWhenPresent(page);page.on('pageerror',e=>errors.push(e.message));
  await check('Acceso común y recuperación automática del último análisis terminado',async()=>{
    await page.goto(base+'/dashboard');await page.waitForURL(u=>u.pathname==='/login');
    await page.getByLabel('Correo',{exact:true}).fill('a@example.invalid');await page.getByLabel('Contraseña',{exact:true}).fill('synthetic-test-password');
    await page.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
    await page.getByText('Sesión iniciada',{exact:true}).waitFor();await page.waitForFunction(()=>document.querySelector('#mepia-business')?.value);
    await page.getByLabel('Negocio',{exact:true}).selectOption(state.business_a);
    await page.waitForURL(u=>u.searchParams.get('run_id')===data.latest);
    await page.waitForFunction(()=>[...document.querySelectorAll('.kpi-value')].some(el=>el.textContent.trim().startsWith('25')));
    assert.equal(await page.getByText('Sin anomalías detectadas en los indicadores evaluados.',{exact:true}).count(),1);
  });
  await check('Historial distingue fecha, guardado, estado y varias ejecuciones del mismo día',async()=>{
    const options=await page.locator('#analysis-history option').allTextContents();
    assert(options.some(t=>t.includes(data.selected.slice(0,8))&&t.includes('Guardado:')));
    assert(options.some(t=>t.includes(data.latest.slice(0,8))));assert(options.some(t=>t.includes('Fallido')));
    await choose(data.selected);await zero();
  });
  await check('Tendencia real usa fechas y un único análisis por fecha, con cero válido',async()=>{
    const session=await(await fetch(api+'/__test__/session/a')).json();
    const response=await fetch(base+'/api/analyses/'+state.business_a+'/'+data.selected+'/trends',{headers:{Authorization:'Bearer '+session.access_token}});
    assert.equal(response.status,200);const trend=await response.json();
    assert.deepEqual(trend.series[0].points.map(p=>p.value),[null,'12',null,'0.00']);
    await page.getByRole('heading',{name:'Evolución de indicadores diarios',exact:true}).waitFor();
    await page.waitForFunction(()=>document.querySelectorAll('.recharts-line-dot').length>=2);
    assert.equal(await page.getByText(/Acepta filas tabulares|arrays tabulares|Excel\/CSV/).count(),0);
    await page.screenshot({path:path.join(out,'dashboard.png'),fullPage:true});
  });
  await check('Dashboard, Salud, Reportes, chat y recarga conservan la misma selección',async()=>{
    const nav=page.getByRole('navigation',{name:'Navegación principal'});
    for(const label of ['Salud del Negocio','Reportes','Chat IA','Dashboard']){
      await nav.getByRole('link',{name:label,exact:true}).click();
      if(label!=='Chat IA')await page.waitForURL(u=>u.searchParams.get('run_id')===data.selected);
    }
    await zero();await page.reload();await zero();assert.equal(new URL(page.url()).searchParams.get('run_id'),data.selected);
    await page.goto(base+'/chat');await page.getByText('Sesión iniciada',{exact:true}).waitFor();await page.reload();
    await nav.getByRole('link',{name:'Dashboard',exact:true}).click();await zero();
    assert.equal(new URL(page.url()).searchParams.get('run_id'),data.selected);
  });
  await check('Una sola fecha y ausencia de cálculos explican lo que falta',async()=>{
    await choose(data.first);await page.getByText(/Datos insuficientes: hay 1 fecha/).waitFor();
    await choose(data.no_data);await page.getByText('Este análisis no conserva información suficiente para confirmar si hubo anomalías. Revisa los datos e indicadores pendientes.',{exact:true}).waitFor();
    assert.equal(await page.getByText('Sin anomalías detectadas en los indicadores evaluados.',{exact:true}).count(),0);
    await page.getByText(/No hay indicadores diarios comparables/).waitFor();
  });
  await check('Enlace ajeno, inexistente y vacío dan error sin sustituirlo por otro análisis',async()=>{
    for(const id of [data.foreign,'00000000-0000-4000-8000-000000000000','']){
      await page.goto(base+'/dashboard?run_id='+id);
      await page.getByRole('alert').filter({hasText:id?'Este análisis no existe o no corresponde':'La referencia del análisis no es válida'}).waitFor();
      assert.equal(new URL(page.url()).searchParams.get('run_id'),id);assert.equal(await page.locator('.kpi-value').count(),0);
    }
    const session=await(await fetch(api+'/__test__/session/a')).json();
    assert.equal((await fetch(base+'/api/analyses/'+state.business_b,{headers:{Authorization:'Bearer '+session.access_token}})).status,403);
  });
  await check('Fallo de historial se muestra como error y permite reintentar',async()=>{
    const pattern='**/api/analyses/'+state.business_a+'?page=0';
    await page.route(pattern,route=>route.fulfill({status:503,json:{detail:'No fue posible recuperar los análisis guardados. Intenta de nuevo.'}}));
    await page.goto(base+'/dashboard?run_id='+data.selected);
    await page.getByRole('alert').filter({hasText:'No fue posible recuperar los análisis guardados'}).waitFor();
    assert.equal(await page.getByText(/No hay análisis guardados para este negocio/).count(),0);
    await page.unroute(pattern);
    await page.route(pattern,route=>route.abort());
    await page.reload();
    await page.getByRole('alert').filter({hasText:'No fue posible conectar con MEPIA'}).waitFor();
    await page.unroute(pattern);await page.getByRole('button',{name:'Reintentar',exact:true}).click();
    await page.getByLabel('Análisis guardado',{exact:true}).selectOption(data.selected);await zero();
  });
  await check('Cambio de negocio limpia datos y descarta respuesta tardía; vacío no afirma ausencia de anomalías',async()=>{
    await fetch(api+'/__test__/delay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ms:1800})});
    const pending=page.waitForRequest(r=>r.url().includes('/api/analyses/'+state.business_a+'/'+data.selected)&&!r.url().includes('/trends'));
    await page.goto(base+'/dashboard?run_id='+data.selected);await pending;
    await page.getByText('Cargando el análisis guardado…',{exact:true}).waitFor();
    assert.equal(await page.getByText('Sin anomalías detectadas en los indicadores evaluados.',{exact:true}).count(),0);
    await page.getByLabel('Negocio',{exact:true}).selectOption(state.business_c);
    assert.equal(await page.locator('.kpi-value').count(),0);
    await page.getByText(/No hay análisis guardados para este negocio/).waitFor();await pause(2100);
    assert.equal(await page.locator('.kpi-value').count(),0);assert.equal(await page.getByText('Sin anomalías detectadas en los indicadores evaluados.',{exact:true}).count(),0);
    await page.reload();await page.getByText(/No hay análisis guardados para este negocio/).waitFor();
    assert.equal(await page.getByLabel('Negocio',{exact:true}).inputValue(),state.business_c);
    await page.screenshot({path:path.join(out,'empty.png'),fullPage:true});
    await fetch(api+'/__test__/delay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ms:0})});
  });
  await check('Cerrar sesión limpia referencias y no deja resultados visibles',async()=>{
    await page.getByLabel('Negocio',{exact:true}).selectOption(state.business_a);await page.waitForURL(u=>u.searchParams.get('run_id')===data.latest);
    await choose(data.selected);await zero();await page.getByRole('button',{name:'Cerrar sesión',exact:true}).click();
    await page.waitForURL(u=>u.pathname==='/login');assert.equal(await page.locator('.kpi-value').count(),0);
    assert.equal(await page.evaluate(()=>sessionStorage.getItem('mepia.analysis.selection')),null);
  });
  await check('Cero modelos, cero cambios de filas y solo GET en las consultas',async()=>{
    const final=await(await fetch(api+'/__test__/analyses')).json();assert.equal(final.model_calls,0);assert.equal(final.rows_unchanged,true);
    assert(final.requests.length>0&&final.requests.every(r=>r.method==='GET'));assert.deepEqual(errors,[]);
  });
})().catch(async error=>{failed=error;console.error(error.stack);if(page)await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});process.exitCode=1;})
.finally(async()=>{
  if(browser)await browser.close();
  for(const child of children) {
    if(process.platform==='win32') await new Promise(resolve=>{
      const killer=spawn('taskkill.exe',['/pid',String(child.pid),'/t','/f'],{windowsHide:true,stdio:'ignore'});killer.once('exit',resolve);
    }); else child.kill();
  }
  await Promise.all(children.map(child=>child.exitCode!==null?Promise.resolve():new Promise(resolve=>{child.once('exit',resolve);setTimeout(resolve,3000);})));
  restoreGeneratedTypes({root:process.cwd(),distDir:dist,tsconfigBefore:beforeConfig,nextEnvBefore:beforeEnv});
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:!failed,checks,errors,error:failed?.message,external_calls:0},null,2));
});
