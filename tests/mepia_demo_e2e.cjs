const {dismissTutorialWhenPresent}=require("./tutorial_test_helpers.cjs");
// Smoke test of the manual demo: real browser/UI, only loopback and fake data.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.MEPIA_PLAYWRIGHT_MODULE||'playwright');
const base='http://127.0.0.1:3037',api='http://127.0.0.1:8025';
const out=path.resolve(process.argv[2]);fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[];let browser,page,failed;
async function check(name,fn){await fn();checks.push({name,passed:true});console.log('PASS '+name);}
(async()=>{
 const session=await(await fetch(api+'/__test__/session/a')).json();
 assert.equal((await fetch(api+'/__demo__/reset',{method:'POST',headers:{Authorization:'Bearer '+session.access_token}})).status,200);
 browser=await chromium.launch({headless:true,channel:'msedge'});
 const context=await browser.newContext({viewport:{width:1360,height:950}});context.setDefaultTimeout(60000);
 await context.route('**/*',route=>[base,api].some(origin=>route.request().url().startsWith(origin+'/'))?route.continue():route.abort());
 page=await context.newPage(); await dismissTutorialWhenPresent(page);page.on('pageerror',e=>errors.push(e.message));
 await check('Panel identifica datos ficticios y prepara cero sin API',async()=>{
  await page.goto(base+'/__demo__');await page.getByRole('heading',{name:'MEPIA · Datos de demostración',exact:true}).waitFor();
  await page.locator('#scenario').selectOption('zero');await page.locator('#prepare').click();
  await page.getByRole('status').filter({hasText:'"scenario": "zero"'}).waitFor();
 });
 await check('Login y lectura real de historial, gráficas y negocio ficticio',async()=>{
  await page.getByRole('link',{name:'Abrir MEPIA',exact:true}).click();
  await page.getByLabel('Correo',{exact:true}).fill('a@example.invalid');await page.getByLabel('Contraseña',{exact:true}).fill('synthetic-test-password');
  await page.getByRole('button',{name:'Iniciar sesión',exact:true}).click();
  await page.getByText('Sesión iniciada',{exact:true}).waitFor();await page.getByLabel('Análisis guardado',{exact:true}).waitFor();
  await page.waitForFunction(()=>document.querySelector('#mepia-business')?.textContent.includes('DEMOSTRACIÓN'));
  const data=await(await fetch(api+'/__demo__/state')).json();
  await page.getByLabel('Negocio',{exact:true}).selectOption(data.business_a);
  const zero=data.runs.find(r=>r.business_id===data.business_a&&r.date==='2026-10-14');
  await page.getByLabel('Análisis guardado',{exact:true}).selectOption(zero.run_id);
  await page.getByRole('heading',{name:'Evolución de indicadores diarios',exact:true}).waitFor();
  await page.screenshot({path:path.join(out,'historial.png'),fullPage:true});
 });
 await check('Documentos PDF/XML → análisis ficticio nuevo → resultado guardado cero',async()=>{
  await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('link',{name:'Documentos',exact:true}).click();
  await page.getByText('Personalizar configuración avanzada →',{exact:true}).waitFor();
  const fixture=path.resolve('output/pdf/demo_mepia_20261014');
  const inputs=page.locator('input[type=file]');
  await inputs.nth(0).setInputFiles(path.join(fixture,'01_ventas_demo_2026-10-14.pdf'));
  await inputs.nth(1).setInputFiles(path.join(fixture,'02_compra_demo_2026-10-14.xml'));
  await page.getByRole('button',{name:/Analizar 2 archivos con Agentes IA/}).click();
  await page.waitForURL(u=>u.pathname==='/dashboard'&&u.searchParams.has('run_id'));
  await page.waitForFunction(()=>[...document.querySelectorAll('.kpi-value')].some(el=>/^0\s*MXN$/.test(el.textContent.trim())));
  const state=await(await fetch(api+'/__demo__/state')).json();assert.equal(state.analyses_created,1);assert.equal(state.real_provider_calls,0);
  assert.equal(await page.getByLabel('Análisis guardado',{exact:true}).inputValue(),new URL(page.url()).searchParams.get('run_id'));
  await page.screenshot({path:path.join(out,'resultado.png'),fullPage:true});
 });
 await check('Chat consulta evidencia guardada y vuelve a la misma selección',async()=>{
  const id=new URL(page.url()).searchParams.get('run_id');
  await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('link',{name:'Chat IA',exact:true}).click();
  await page.locator('input[type=date]').fill('2026-10-14');
  await page.getByLabel('Pregunta sobre tus métricas').fill('¿Cuál fue la conciliación de caja?');await page.getByRole('button',{name:'Enviar pregunta',exact:true}).click();
  await page.locator('article').first().waitFor();assert.match(await page.locator('article').innerText(),/0(?:\.00)? MXN/);
  await page.screenshot({path:path.join(out,'chat.png'),fullPage:true});
  await page.reload();await page.getByText('Sesión iniciada',{exact:true}).waitFor();
  await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('link',{name:'Dashboard',exact:true}).click();
  await page.waitForURL(u=>u.searchParams.get('run_id')===id);
 });
 await check('Negocio vacío limpia y no afirma evaluación sin anomalías',async()=>{
  const state=await(await fetch(api+'/__demo__/state')).json();await page.getByLabel('Negocio',{exact:true}).selectOption(state.business_empty);
  await page.getByText(/No hay análisis guardados para este negocio/).waitFor();assert.equal(await page.locator('.kpi-value').count(),0);
  assert.equal(await page.getByText('Sin anomalías detectadas en los indicadores evaluados.',{exact:true}).count(),0);
  await page.getByRole('button',{name:'Cerrar sesión',exact:true}).click();await page.waitForURL(u=>u.pathname==='/login');
  const final=await(await fetch(api+'/__demo__/state')).json();assert.equal(final.real_provider_calls,0);assert.deepEqual(errors,[]);
 });
})().catch(async e=>{failed=e;console.error(e.stack);if(page)await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});process.exitCode=1;})
.finally(async()=>{if(browser)await browser.close();fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:!failed,checks,errors,error:failed?.message,real_provider_calls:0},null,2));});
