// Recorrido navegador → Next.js → FastAPI → grounding → SDK simulado.
const assert = require('node:assert/strict');
const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');
const {restoreGeneratedTypes} = require('./chat_step5_workspace.cjs');
const { chromium } = require(process.env.MEPIA_PLAYWRIGHT_MODULE || 'playwright');
const base = 'http://127.0.0.1:3015';
const api = 'http://127.0.0.1:8015';
const output = path.resolve(process.env.MEPIA_STEP5_E2E_OUTPUT || '.test_tmp/step5_integrated');
const distDir = path.resolve(process.env.MEPIA_STEP5_E2E_DIST_DIR || path.join(output, 'next'));
assert(distDir.startsWith(path.resolve('.test_tmp') + path.sep), 'La caché de pruebas debe estar dentro de .test_tmp');
const children = [];
const checks = [];
let browser;
let page;
const errors = [];
const authResponses = [];
const extendedChecks = [];
const tsconfigPath = path.resolve('tsconfig.json');
const tsconfigBefore = fs.readFileSync(tsconfigPath, 'utf8');
const nextEnvPath = path.resolve('next-env.d.ts');
const nextEnvBefore = fs.readFileSync(nextEnvPath, 'utf8');
const pause = (ms) => new Promise(r => setTimeout(r, ms));
function start(exe, args, name, env = {}) {
  const log = fs.openSync(path.join(output, name + '.log'), 'w');
  const child = spawn(exe, args, { cwd: process.cwd(), windowsHide: true,
    env: { ...process.env, ...env }, stdio: ['ignore', log, log] });
  children.push(child); return child;
}
async function ready(url) {
  for (let i = 0; i < 120; i++) {
    try { if ((await fetch(url)).ok) return; } catch {}
    await pause(500);
  }
  throw new Error('Servidor local no respondió');
}
async function check(name, fn) { await fn(); checks.push({ name, passed: true }); console.log('PASS ' + name); }
async function requireFreePort(port) {
  const probe = net.createServer();
  await new Promise((resolve, reject) => {
    probe.once('error', () => reject(new Error('Puerto de pruebas ocupado: ' + port)));
    probe.listen(port, '127.0.0.1', () => probe.close(resolve));
  });
}
(async () => {
  fs.mkdirSync(output, { recursive: true });
  if (process.env.MEPIA_STEP5_EXTENDED_CHECKS === '1') {
    const workspace = spawnSync(process.execPath, ['--test', 'tests/chat_step5_workspace_test.cjs'], {windowsHide:true,encoding:'utf8'});
    fs.writeFileSync(path.join(output, 'workspace-tests.log'), workspace.stdout + workspace.stderr);
    assert.equal(workspace.status, 0, 'Restauración de referencias del workspace');
  }
  assert(process.env.MEPIA_TEST_PYTHON, 'Configura MEPIA_TEST_PYTHON');
  await requireFreePort(8015);
  await requireFreePort(3015);
  start(process.env.MEPIA_TEST_PYTHON, ['-B', '-m', 'uvicorn', 'tests.chat_step5_server:app', '--host', '127.0.0.1', '--port', '8015'], 'e2e-api',
    { PYTHONDONTWRITEBYTECODE: '1' });
  await ready(api + '/__test__/state');
  start(process.execPath, ['node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '3015'], 'e2e-next', {
    NEXT_TELEMETRY_DISABLED: '1', NEXT_PUBLIC_SUPABASE_URL: api,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: 'synthetic-public-key', AGENTS_API_URL: api,
    MEPIA_NEXT_DIST_DIR: path.relative(process.cwd(), distDir) });
  await ready(base + '/chat');
  const state = await (await fetch(api + '/__test__/state')).json();
  await check('Proxy anónimo: 401, cero DB y modelo', async () => {
    const res = await fetch(base + '/api/chat/' + state.business_a, { method: 'POST', body: JSON.stringify({ question: 'ticket promedio' }) });
    assert.equal(res.status, 401);
    const current = await (await fetch(api + '/__test__/state')).json();
    assert.equal(current.model_calls, 0); assert.deepEqual(current.table_calls, []);
  });
  browser = await chromium.launch({ headless: true,
    ...(process.env.MEPIA_TEST_BROWSER ? { channel: process.env.MEPIA_TEST_BROWSER } : {}) });
  const context = await browser.newContext({ viewport: { width: 1100, height: 850 } });
  page = await context.newPage();
  page.context().setDefaultTimeout(90000);
  page.setDefaultTimeout(90000); // Compilación fría local; rendimiento se mide aparte.
  page.on('response', res => { if (res.url().includes('/auth/v1/')) authResponses.push({ path: new URL(res.url()).pathname, status: res.status() }); });
  page.on('pageerror', e => errors.push(e.message));
  await page.context().route('**/*', async route => {
    const req = route.request(); const url = req.url();
    if (url.startsWith(base) || url.startsWith(api) || url.startsWith('http://localhost:3015')) return route.continue();
    return route.abort(); // Sin servicios externos, incluidas fuentes web.
  });
  await page.goto(base + '/chat');
  await check('Entrada general: todas las páginas privadas requieren login', async () => {
    for (const route of ['/', '/dashboard', '/upload', '/onboarding', '/chat', '/salud', '/reportes']) {
      await page.goto(base + route);
      await page.waitForURL(url => url.pathname === '/login');
      await page.getByRole('heading', {name: 'Bienvenido a MEPIA', exact: true}).waitFor();
      const next = new URL(page.url()).searchParams.get('next');
      if (route === '/') assert(['/', '/dashboard'].includes(next));
      else assert.equal(next, route);
      assert.equal(await page.getByRole('navigation', {name: 'Navegación principal'}).count(), 0);
    }
    assert.equal((await fetch(base + '/login')).status, 200);
    for (const path of ['/api/onboarding?business_id=' + state.business_a, '/api/audit/status/' + state.business_a]) {
      assert.equal((await fetch(base + path)).status, 401);
    }
  });
  await check('Cookie inventada no permite entrar a MEPIA', async () => {
    const forged = JSON.stringify({ access_token: 'forged-token', refresh_token: 'forged-refresh',
      expires_at: Math.floor(Date.now()/1000)+3600, user: { id: state.business_a } });
    const res = await fetch(base + '/api/onboarding?business_id=' + state.business_a, { headers: { Cookie: 'sb-127-auth-token=' + encodeURIComponent(forged) } });
    assert.equal(res.status, 401);
    await page.context().addCookies([{name: 'sb-127-auth-token', value: encodeURIComponent(forged), url: base}]);
    await page.goto(base + '/dashboard');
    await page.waitForURL(url => url.pathname === '/login');
    await page.getByLabel('Correo', {exact: true}).waitFor();
    assert.equal((await page.context().cookies()).some(cookie => cookie.name === 'sb-127-auth-token'), false);
  });
  await check('Una cookie antigua válida tampoco sustituye la sesión de la pestaña', async () => {
    const session = await (await fetch(api + '/__test__/session/a')).json();
    const cookie = encodeURIComponent(JSON.stringify(session));
    const res = await fetch(base + '/api/onboarding?business_id=' + state.business_a, {headers: {Cookie: 'sb-127-auth-token=' + cookie}});
    assert.equal(res.status, 401);
    await page.context().addCookies([{name: 'sb-127-auth-token', value: cookie, url: base}]);
    await page.goto(base + '/');
    await page.waitForURL(url => url.pathname === '/login');
    await page.getByLabel('Correo', {exact: true}).waitFor();
  });
  await check('Una sesión manipulada en almacenamiento no permite mostrar MEPIA ni llamar la API', async () => {
    const session = await (await fetch(api + '/__test__/session/a')).json();
    const pieces = session.access_token.split('.');
    pieces[2] = (pieces[2][0] === 'a' ? 'b' : 'a') + pieces[2].slice(1);
    session.access_token = pieces.join('.');
    session.expires_at = Math.floor(Date.now()/1000) + session.expires_in;
    const res = await fetch(base + '/api/onboarding?business_id=' + state.business_a, {headers: {Authorization:'Bearer ' + session.access_token}});
    assert.equal(res.status, 401);
    const other = await page.context().newPage();
    other.on('pageerror', e => errors.push(e.message));
    try {
      await other.addInitScript(session => {
        const tab = crypto.randomUUID();
        sessionStorage.setItem('mepia.tab.id', tab);
        sessionStorage.setItem('mepia.auth.' + tab, JSON.stringify(session));
      }, session);
      await other.goto(base + '/dashboard');
      await other.waitForURL(url => url.pathname === '/login');
      await other.getByLabel('Correo', {exact: true}).waitFor();
      assert.equal(await other.getByRole('navigation', {name:'Navegación principal'}).count(), 0);
    } finally { await other.close(); }
  });
  async function login(who) {
    await page.getByLabel('Correo', { exact: true }).fill(who + '@example.invalid');
    await page.getByLabel('Contraseña', { exact: true }).fill('synthetic-test-password');
    await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).click();
    await page.getByText('Sesión iniciada', { exact: true }).waitFor();
    await page.waitForFunction(() => document.querySelector('select')?.value);
    await page.getByLabel('Negocio', { exact: true }).selectOption(who === 'a' ? state.business_a : state.business_b);
  }
  await check('Inicio de sesión y solo negocios propios', async () => {
    await login('a');
    assert.equal(new URL(page.url()).origin, base);
    const values = await page.locator('select option').evaluateAll(options => options.map(o => o.value));
    assert.deepEqual(values.sort(), [state.business_a, state.business_c].sort());
  });
  await check('API legada verifica Bearer y no confunde sesión válida con acceso anónimo', async () => {
    const session = await (await fetch(api + '/__test__/session/a')).json();
    const res = await fetch(base + '/api/onboarding?business_id=' + state.business_a, {headers:{Authorization:'Bearer ' + session.access_token}});
    assert.equal(res.status, 404); // El upstream sintético no registra onboarding: el proxy sí pasó su guard.
  });
  await check('Dashboard es el inicio único, sin bienvenida y conserva sesión al recargar', async () => {
    await page.goto(base + '/login');
    await page.waitForURL(url => url.pathname === '/dashboard');
    await page.getByText('Sesión iniciada', {exact: true}).waitFor();
    assert.equal(await page.getByRole('link', {name: 'Inicio', exact: true}).count(), 0);
    assert.equal(await page.getByRole('button', {name: 'Iniciar', exact: true}).count(), 0);
    await page.reload();
    await page.getByText('Sesión iniciada', {exact: true}).waitFor();
    assert.equal(new URL(page.url()).pathname, '/dashboard');
    await page.goto(base + '/');
    await page.waitForURL(url => url.pathname === '/dashboard');
    assert.equal(new URL(page.url()).origin, base);
    await page.getByText('Sesión iniciada', {exact: true}).waitFor();
    assert.equal((await page.context().cookies()).some(cookie => /auth-token/.test(cookie.name)), false);
    assert.equal(await page.evaluate(() => Object.keys(localStorage).some(key => /auth-token|mepia\.auth\./.test(key))), false);
    assert.equal(await page.evaluate(() => Object.keys(sessionStorage).some(key => key.startsWith('mepia.auth.'))), true);
  });
  await check('Otra pestaña exige login y no cierra la sesión de la pestaña original', async () => {
    const other = await page.context().newPage();
    try {
      await other.goto(base + '/dashboard');
      await other.waitForURL(url => url.pathname === '/login');
      await other.getByLabel('Correo', {exact: true}).waitFor();
      assert.equal(await other.getByRole('navigation', {name:'Navegación principal'}).count(), 0);
      await other.getByLabel('Correo', {exact: true}).fill('b@example.invalid');
      await other.getByLabel('Contraseña', {exact: true}).fill('synthetic-test-password');
      await other.getByRole('button', {name:'Iniciar sesión',exact:true}).click();
      await other.getByText('Sesión iniciada',{exact:true}).waitFor();
      await other.waitForFunction(() => document.querySelector('select')?.value);
      assert.equal(await other.getByLabel('Negocio',{exact:true}).inputValue(),state.business_b);
      assert.notEqual(await page.evaluate(() => sessionStorage.getItem('mepia.tab.id')), await other.evaluate(() => sessionStorage.getItem('mepia.tab.id')));
      await page.reload();
      await page.getByText('Sesión iniciada', {exact: true}).waitFor();
      await page.waitForFunction(() => document.querySelector('select')?.value);
      assert.notEqual(await page.getByLabel('Negocio',{exact:true}).inputValue(),state.business_b);
      await other.getByRole('button',{name:'Cerrar sesión',exact:true}).click();
      await other.waitForURL(url => url.pathname === '/login');
      await page.reload();
      await page.getByText('Sesión iniciada',{exact:true}).waitFor();
    } finally { await other.close(); }
  });
  await check('Chat desde el menú común, sin un segundo login', async () => {
    await page.getByRole('heading', {name: /Auditoría/i}).waitFor();
    await page.screenshot({ path: path.join(output, 'home-dashboard.png'), fullPage: true });
    await page.getByRole('navigation', { name: 'Navegación principal' }).getByRole('link', { name: 'Chat IA', exact: true }).click();
    await page.waitForURL('**/chat');
    await page.getByRole('heading', { name: /Chat IA/ }).waitFor();
    assert.equal(await page.getByLabel('Correo', { exact: true }).count(), 0);
    assert.equal(await page.getByRole('button', { name: 'Iniciar sesión', exact: true }).count(), 0);
    await page.reload();
    await page.waitForURL('**/chat');
    await page.getByText('Sesión iniciada', { exact: true }).waitFor();
    await page.getByLabel('Pregunta sobre tus métricas').waitFor();
    await page.waitForFunction(() => document.querySelector('select')?.value);
    await page.getByLabel('Negocio', { exact: true }).selectOption(state.business_a);
  });
  await check('Salud y Reportes comparten sesión y menú de Chat IA', async () => {
    for (const [route, heading] of [['Salud del Negocio', 'Salud del negocio'], ['Reportes', 'MEPIA — Reporte de Auditoría Forense']]) {
      await page.getByRole('navigation', { name: 'Navegación principal' }).getByRole('link', { name: route, exact: true }).click();
      await page.getByRole('heading', { name: heading, exact: true }).waitFor();
      assert.equal(await page.getByLabel('Correo', { exact: true }).count(), 0);
      await page.getByText('Sesión iniciada', { exact: true }).waitFor();
    }
    await page.getByRole('navigation', { name: 'Navegación principal' }).getByRole('link', { name: 'Chat IA', exact: true }).click();
    await page.getByLabel('Pregunta sobre tus métricas').waitFor();
  });
  await check('Fecha de documentos prevalece y una fecha distinta detiene el análisis', async () => {
    const run = '00000000-0000-4000-8000-000000000051';
    let auditCalls = 0, auditDate, owner;
    await page.route('**/api/onboarding?*', route => route.fulfill({json: {onboarding_complete: true}}));
    await page.route('**/api/upload', route => route.fulfill({json: route.request().postData().includes('.xml')
      ? {needs_human_review:false, file_id:'synthetic-invoice', extracted_fields:{transaction_date:'2026-10-14'}}
      : {needs_human_review:false, file_id:'synthetic-pos', date:'2026-10-14'}}));
    await page.route('**/api/audit', route => {
      auditCalls++; auditDate=route.request().postDataJSON().date;
      return route.fulfill({json: {run_id:run}});
    });
    await page.route('**/api/audit/status/'+run, route => route.fulfill({json:{run_id:run,pipeline_status:'partial'}}));
    await page.route('**/api/audit/result/'+run, route => route.fulfill({json:{
      run_id:run,business_id:owner,date:'2026-10-14',archetype:'Operative Genius',pipeline_status:'partial',
      sequential_results:{active_metrics:['cash_reconciliation'],calc_results:[
        {metric:'conciliacion_caja',value:'0.00',unit:'MXN',status:'ok',context:'Caja de demostración'}],
        forensic_report:{risk_level:'low',anomalies:[]},audit_insights:[]},
      dormant_metrics:[{metric:'avg_ticket',missing:['tickets']}],blocked_metrics:[],metric_status_available:true,
      escalation:{triggered:false},completed_at:'2026-10-15T00:00:00Z'}}));
    await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('link',{name:'Documentos',exact:true}).click();
    owner=await page.getByLabel('Negocio',{exact:true}).inputValue();
    assert.equal(await page.locator('#audit-date').inputValue(),'');
    await page.locator('input[type=file]').nth(0).setInputFiles(path.resolve('output/pdf/demo_mepia_20261014/01_ventas_demo_2026-10-14.pdf'));
    await page.locator('input[type=file]').nth(1).setInputFiles(path.resolve('output/pdf/demo_mepia_20261014/02_compra_demo_2026-10-14.xml'));
    await page.locator('#audit-date').fill('2024-01-15');
    await page.getByRole('button',{name:/Analizar 2 archivos/}).click();
    await page.getByRole('alert').filter({hasText:'La fecha elegida no coincide'}).waitFor();
    assert.equal(auditCalls,0);
    await page.locator('#audit-date').fill('');
    await page.getByRole('button',{name:/Analizar 2 archivos/}).click();
    await page.waitForURL(url=>url.searchParams.get('run_id')===run);
    await page.locator('.kpi-value').nth(4).filter({hasText:/^0\s*MXN$/}).waitFor();
    assert.equal(auditCalls,1);assert.equal(auditDate,'2026-10-14');
    await page.getByText('avg_ticket',{exact:true}).waitFor();
    await page.getByText('tickets',{exact:true}).waitFor();
    await page.screenshot({path:path.join(output,'demo-zero.png'),fullPage:true});
    await page.getByRole('navigation',{name:'Navegación principal'}).getByRole('link',{name:'Chat IA',exact:true}).click();
    await page.getByLabel('Pregunta sobre tus métricas').waitFor();
    const dashboard=page.getByRole('navigation',{name:'Navegación principal'}).getByRole('link',{name:'Dashboard',exact:true});
    assert.equal(await dashboard.getAttribute('href'),'/dashboard?run_id='+run);
    await dashboard.click();
    await page.locator('.kpi-value').nth(4).filter({hasText:/^0\s*MXN$/}).waitFor();
    assert.equal(new URL(page.url()).searchParams.get('run_id'),run);
    await page.reload();
    await page.locator('.kpi-value').nth(4).filter({hasText:/^0\s*MXN$/}).waitFor();
    assert.equal(auditCalls,1);
    await page.unroute('**/api/upload');await page.unroute('**/api/audit');await page.unroute('**/api/onboarding?*');
    await page.unroute('**/api/audit/status/'+run);await page.unroute('**/api/audit/result/'+run);
  });
  await check('Dashboard presenta métricas sintéticas sin alterar porcentaje y separa unidades', async () => {
    const run = '00000000-0000-4000-8000-000000000001';
    const syntheticResult = {
      run_id: run, business_id: state.business_a, date: '2026-10-14', archetype: 'Operative Genius', pipeline_status: 'completed',
      sequential_results: {active_metrics: ['contribution_margin', 'cash_reconciliation'],
        calc_results: [{metric: 'contribution_margin', value: 0.5, unit: '%', status: 'warning', context: 'Resultado de prueba'},
          {metric: 'cash_reconciliation', value: 50, unit: 'MXN', status: 'critical', context: 'Resultado de prueba'}],
        forensic_report: {risk_level: 'low', anomalies: []}, audit_insights: []},
      escalation: {triggered: false, reason: null, layer2_run_id: null}, dormant_metrics: [], blocked_metrics: [], metric_status_available:false, completed_at: '2026-10-14T12:00:00Z',
    };
    await page.route('**/api/audit/status/' + run, route => route.fulfill({json: {run_id: run, pipeline_status: 'completed'}}));
    let auditBusiness;
    await page.route('**/api/audit/result/' + run, async route => {
      // Al recargar, la lista propia puede comenzar por A o C; fijar el fixture
      // al negocio elegido antes de la primera respuesta, no asumir su orden.
      auditBusiness ??= await page.getByLabel('Negocio', {exact: true}).inputValue();
      await route.fulfill({json: {...syntheticResult, business_id: auditBusiness}});
    });
    await page.goto(base + '/dashboard?run_id=' + run);
    await page.getByText('0.5%', {exact: true}).waitFor();
    await page.getByText('Este análisis no conserva el detalle de los datos faltantes.',{exact:true}).waitFor();
    assert.equal(await page.getByText('Todas las métricas activas',{exact:true}).count(),0);
    await page.getByRole('heading', {name: 'Métricas calculadas · %', exact: true}).waitFor();
    await page.getByRole('heading', {name: 'Métricas calculadas · MXN', exact: true}).waitFor();
    await page.waitForFunction(() => document.querySelectorAll('.recharts-surface').length >= 2);
    assert.equal(await page.locator('.kpi-value.text-red-400').evaluate(el => getComputedStyle(el).color), 'rgb(248, 113, 113)');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({path: path.join(output, 'dashboard.png'), fullPage: true});
    await page.getByLabel('Negocio', {exact: true}).selectOption(auditBusiness === state.business_a ? state.business_c : state.business_a);
    await page.waitForURL(url => url.pathname === '/dashboard' && !url.search);
    await page.getByText('Aquí aparecerán los resultados cuando completes un análisis.', {exact: true}).waitFor();
    assert.equal(await page.getByText('0.5%', {exact: true}).count(), 0);
    await page.getByLabel('Negocio', {exact: true}).selectOption(state.business_a);
    await page.unroute('**/api/audit/status/' + run);
    await page.unroute('**/api/audit/result/' + run);
    const foreignRun = '00000000-0000-4000-8000-000000000002';
    await page.route('**/api/audit/status/' + foreignRun, route => route.fulfill({json: {run_id: foreignRun, pipeline_status: 'completed'}}));
    await page.route('**/api/audit/result/' + foreignRun, route => route.fulfill({json: {...syntheticResult, run_id: foreignRun, business_id: state.business_b}}));
    await page.goto(base + '/dashboard?run_id=' + foreignRun);
    await page.getByText('Este análisis no corresponde al negocio seleccionado.', {exact: true}).waitFor();
    assert.equal(await page.getByText('0.5%', {exact: true}).count(), 0);
    await page.unroute('**/api/audit/status/' + foreignRun);
    await page.unroute('**/api/audit/result/' + foreignRun);
    await page.getByLabel('Negocio', {exact: true}).selectOption(state.business_a);
    await page.waitForURL(url => url.pathname === '/dashboard' && !url.search);
    await page.getByRole('navigation', {name: 'Navegación principal'}).getByRole('link', {name: 'Chat IA', exact: true}).click();
    await page.getByLabel('Pregunta sobre tus métricas').waitFor();
  });
  await check('Saludo natural sin llamadas de generación ni fuentes vacías', async () => {
    const before = await (await fetch(api + '/__test__/state')).json();
    await page.getByLabel('Pregunta sobre tus métricas').fill('Hola');
    await page.getByRole('button', {name: 'Enviar pregunta'}).click();
    await page.locator('article').first().waitFor();
    assert.match(await page.locator('article').innerText(), /¡Hola! Puedo ayudarte/);
    assert.equal(await page.getByText('Fuentes y trazabilidad', {exact: true}).count(), 0);
    assert.equal(await page.getByText('Mostramos los datos disponibles; no se obtuvo una explicación validada.', {exact: true}).count(), 0);
    const after = await (await fetch(api + '/__test__/state')).json();
    assert.equal(after.model_calls, before.model_calls);
    await page.getByRole('button', {name: 'Recargar historial'}).click();
    await page.getByRole('button', {name: 'Enviar pregunta'}).isEnabled();
    assert.match(await page.locator('article').innerText(), /¡Hola! Puedo ayudarte/);
    await page.getByRole('button', {name: 'Nueva conversación'}).click();
    assert.equal(await page.locator('article').count(), 0);
  });
  await check('Pregunta con cifra/unidad, fuentes y linaje', async () => {
    await page.getByLabel('Pregunta sobre tus métricas').fill('¿Cuál fue el ticket promedio?');
    await page.getByRole('button', { name: 'Enviar pregunta' }).click();
    await page.locator('article').first().waitFor();
    assert.match(await page.locator('article').innerText(), /125 MXN/);
    await page.getByText('Fuentes y trazabilidad', { exact: true }).click();
    assert.match(await page.locator('article').innerText(), /Ejecución S3/);
    assert.match(await page.locator('article').innerText(), new RegExp(state.business_a));
  });
  await check('Continuación conceptual e historial recuperable', async () => {
    await page.getByLabel('Pregunta sobre tus métricas').fill('¿Qué significa eso?');
    await page.getByRole('button', { name: 'Enviar pregunta' }).click();
    await page.waitForFunction(() => document.querySelectorAll('article').length === 2);
    assert.match(await page.locator('article').nth(1).innerText(), /catálogo/);
    await page.getByRole('button', { name: 'Recargar historial' }).click();
    await page.getByRole('button', { name: 'Enviar pregunta' }).isEnabled();
    assert.equal(await page.locator('article').count(), 2);
  });
  await check('Cambio de negocio limpia historial visible', async () => {
    await page.getByLabel('Negocio', { exact: true }).selectOption(state.business_c);
    assert.equal(await page.locator('article').count(), 0);
  });
  await check('Negocio ajeno: 403 sin evidencia ni modelo', async () => {
    const session = await (await fetch(api + '/__test__/session/a')).json();
    const before = await (await fetch(api + '/__test__/state')).json();
    const res = await fetch(base + '/api/chat/' + state.business_b, { method: 'POST',
      headers: { Authorization: 'Bearer ' + session.access_token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: 'ticket promedio' }) });
    assert.equal(res.status, 403);
    const after = await (await fetch(api + '/__test__/state')).json();
    assert.equal(after.model_calls, before.model_calls);
    assert.deepEqual(after.table_calls.slice(before.table_calls.length), ['businesses']);
  });
  await check('Rechazo de cálculo y eliminación del historial', async () => {
    await page.getByLabel('Pregunta sobre tus métricas').fill('Divide 100 entre 2');
    await page.getByRole('button', { name: 'Enviar pregunta' }).click();
    await page.locator('article').first().waitFor();
    assert.match(await page.locator('article').innerText(), /No puedo hacer ese cálculo/);
    await page.getByRole('button', { name: 'Eliminar conversación' }).click();
    await page.waitForFunction(() => document.querySelectorAll('article').length === 0);
  });
  await check('Cambio de usuario sin conversaciones ajenas', async () => {
    await page.getByRole('button', { name: 'Cerrar sesión' }).click();
    await page.waitForURL(url => url.pathname === '/login' && !url.search);
    await page.getByLabel('Correo', { exact: true }).waitFor();
    await login('b');
    await page.getByRole('navigation', {name:'Navegación principal'}).getByRole('link', {name:'Chat IA',exact:true}).click();
    await page.getByLabel('Pregunta sobre tus métricas').waitFor();
    assert.equal(await page.locator('article').count(), 0);
    assert.deepEqual(await page.locator('select option').evaluateAll(options => options.map(o => o.value)), [state.business_b]);
  });
  if (process.env.MEPIA_STEP5_EXTENDED_CHECKS === '1') {
    // Las respuestas se retienen en la red; nunca se invoca un proveedor real.
    await check('C07: respuestas tardías descartadas por negocio, fecha y usuario', async () => {
      await page.getByRole('button', {name: 'Cerrar sesión', exact: true}).click();
      await page.waitForURL(url => url.pathname === '/login' && !url.search);
      await login('a');
      await page.getByRole('navigation', {name: 'Navegación principal'}).getByRole('link', {name: 'Chat IA', exact: true}).click();
      await page.getByLabel('Pregunta sobre tus métricas').waitFor();
      for (const scope of ['business', 'date', 'user']) {
        await page.getByLabel('Negocio', {exact: true}).selectOption(state.business_a);
        await page.locator('input[type=date]').fill('');
        await page.getByRole('button', {name: 'Nueva conversación', exact: true}).click();
        let release, captured, finished;
        const gate = new Promise(resolve => { release = resolve; });
        const ready = new Promise(resolve => { captured = resolve; });
        const done = new Promise(resolve => { finished = resolve; });
        const pattern = '**/api/chat/**';
        const handler = async route => {
          if (route.request().method() !== 'POST') return route.continue();
          try {
            const upstream = await route.fetch();
            const body = await upstream.json();
            body.answer.parts[0].message = 'RESPUESTA_ANTIGUA_NO_VISIBLE';
            captured();
            await gate;
            await route.fulfill({response: upstream, json: body});
          } catch (error) {
            // Cambiar de ámbito aborta deliberadamente la petición anterior.
            if (!/closed|cancel|abort|fetch|disposed/i.test(error.message)) throw error;
          } finally { finished(); }
        };
        await page.route(pattern, handler);
        await page.getByLabel('Pregunta sobre tus métricas').fill('¿Cuál fue el ticket promedio?');
        await page.getByRole('button', {name: 'Enviar pregunta', exact: true}).click();
        let waitTimer;
        try { await Promise.race([ready, new Promise((_, reject) => { waitTimer = setTimeout(() => reject(new Error('No se capturó la petición tardía')), 30000); })]); }
        finally { clearTimeout(waitTimer); }
        assert.equal(await page.getByRole('button', {name: 'Enviar pregunta', exact: true}).isDisabled(), true);
        if (scope === 'business') await page.getByLabel('Negocio', {exact: true}).selectOption(state.business_c);
        if (scope === 'date') await page.locator('input[type=date]').fill('2026-09-23');
        if (scope === 'user') {
          await page.getByRole('button', {name: 'Cerrar sesión', exact: true}).click();
          await page.waitForURL(url => url.pathname === '/login' && !url.search);
          await login('b');
          await page.getByRole('navigation', {name: 'Navegación principal'}).getByRole('link', {name: 'Chat IA', exact: true}).click();
          await page.getByLabel('Pregunta sobre tus métricas').waitFor();
        }
        release();
        await done;
        await page.unroute(pattern, handler);
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        assert.equal(await page.locator('article').count(), 0);
        assert.equal(await page.getByText('RESPUESTA_ANTIGUA_NO_VISIBLE', {exact: true}).count(), 0);
      }
      extendedChecks.push('C07', 'C08', 'S10_busy');
    });
    await check('C04 y S08: nueva conversación, aviso de respaldo y teclado', async () => {
      await page.getByLabel('Negocio', {exact: true}).selectOption(state.business_b);
      const send = async () => {
        const response = page.waitForResponse(res => res.url().includes('/api/chat/') && res.request().method() === 'POST');
        await page.getByLabel('Pregunta sobre tus métricas').fill('¿Cuál fue el ticket promedio?');
        await page.getByLabel('Pregunta sobre tus métricas').press('Enter');
        const body = await (await response).json();
        await page.locator('article').first().waitFor();
        return body.conversation_id;
      };
      const first = await send();
      await page.getByRole('button', {name: 'Nueva conversación', exact: true}).click();
      assert.equal(await page.locator('article').count(), 0);
      const second = await send();
      assert.notEqual(first, second);
      await page.getByRole('button', {name: 'Nueva conversación', exact: true}).click();
      const pattern = '**/api/chat/**';
      const fallback = async route => {
        if (route.request().method() !== 'POST') return route.continue();
        const upstream = await route.fetch();
        const body = await upstream.json();
        body.answer.parts[0].generation_status = 'fallback';
        body.answer.parts[0].claims = [];
        await route.fulfill({response: upstream, json: body});
      };
      await page.route(pattern, fallback);
      await send();
      await page.getByText('Mostramos los datos disponibles; no se obtuvo una explicación validada.', {exact: true}).waitFor();
      const details = page.getByText('Ver datos disponibles', {exact: true});
      await details.focus();
      await details.press('Enter');
      assert.match(await page.locator('article pre').innerText(), /125/);
      await page.unroute(pattern, fallback);
      extendedChecks.push('C04', 'S08_notice', 'P06_keyboard_partial');
    });
    await check('S05: proxy rechaza cuerpo excesivo antes del proveedor', async () => {
      const session = await (await fetch(api + '/__test__/session/b')).json();
      const before = await (await fetch(api + '/__test__/state')).json();
      const res = await fetch(base + '/api/chat/' + state.business_b, {method: 'POST',
        headers: {Authorization: 'Bearer ' + session.access_token, 'Content-Type': 'application/json'},
        body: JSON.stringify({question: 'x'.repeat(16001)})});
      assert.equal(res.status, 413);
      const after = await (await fetch(api + '/__test__/state')).json();
      assert.equal(after.model_calls, before.model_calls);
      extendedChecks.push('S05_proxy_size');
    });
  }
  await check('Menú móvil, Salud, Reportes y chat utilizables sin desbordamiento', async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Abrir menú', exact: true }).click();
    await page.getByRole('navigation', { name: 'Navegación principal' }).getByRole('link', { name: 'Dashboard', exact: true }).click();
    await page.getByRole('heading', { name: /Auditoría/i }).waitFor();
    for (const [name, heading] of [['Salud del Negocio', 'Salud del negocio'], ['Reportes', 'MEPIA — Reporte de Auditoría Forense']]) {
      await page.getByRole('button', { name: 'Abrir menú', exact: true }).click();
      await page.getByRole('navigation', { name: 'Navegación principal' }).getByRole('link', { name, exact: true }).click();
      await page.getByRole('heading', { name: heading, exact: true }).waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    }
    await page.getByRole('button', { name: 'Abrir menú', exact: true }).click();
    await page.getByRole('navigation', { name: 'Navegación principal' }).getByRole('link', { name: 'Chat IA', exact: true }).click();
    await page.getByLabel('Pregunta sobre tus métricas').waitFor();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(output, 'chat-mobile.png'), fullPage: true });
    await page.setViewportSize({ width: 1100, height: 850 });
  });
  await check('Cerrar sesión devuelve al login y bloquea enlaces directos', async () => {
    await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click();
    await page.waitForURL(url => url.pathname === '/login' && !url.search);
    await page.getByRole('heading', { name: 'Bienvenido a MEPIA', exact: true }).waitFor();
    await page.goto(base + '/chat');
    await page.getByLabel('Correo', { exact: true }).waitFor();
    assert.equal(new URL(page.url()).pathname, '/login');
    await login('a');
  });
  await check('Cerrar y abrir de nuevo la pestaña exige credenciales', async () => {
    const context = page.context();
    await page.close();
    page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', res => { if (res.url().includes('/auth/v1/')) authResponses.push({path: new URL(res.url()).pathname, status: res.status()}); });
    await page.goto(base + '/dashboard');
    await page.waitForURL(url => url.pathname === '/login');
    await page.getByLabel('Correo', {exact: true}).waitFor();
    assert.equal(await page.getByLabel('Correo', {exact: true}).inputValue(), '');
    assert.equal(await page.getByText('Sesión iniciada', {exact: true}).count(), 0);
    await login('a');
    await page.waitForURL(url => url.pathname === '/dashboard');
    await page.getByRole('link', {name: 'Chat IA', exact: true}).click();
    await page.getByLabel('Pregunta sobre tus métricas').waitFor();
  });
  await page.screenshot({ path: path.join(output, 'chat-ui.png'), fullPage: true });
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'e2e.json'), JSON.stringify({ passed: true, checks, extended_checks: extendedChecks, page_errors: errors, external_api_calls: 0 }, null, 2));
})().catch(async e => {
  const diagnostic = {};
  if (page) {
    try {
      diagnostic.url = page.url(); diagnostic.visible_text = (await page.locator('body').innerText()).slice(0, 2500);
      diagnostic.cookie_metadata = (await page.context().cookies()).map(item => ({ name: item.name, length: item.value.length, secure: item.secure }));
      diagnostic.tab_session_metadata = await page.evaluate(() => {
        const tab = sessionStorage.getItem('mepia.tab.id');
        let stored; try { stored = JSON.parse(sessionStorage.getItem('mepia.auth.' + tab) || 'null'); } catch {}
        return {tab_present: !!tab, session_present: !!stored, user_present: !!stored?.user,
          expires_at: stored?.expires_at, now: Math.floor(Date.now()/1000)};
      });
      await page.screenshot({ path: path.join(output, 'failure.png'), fullPage: true });
    } catch {}
  }
  fs.writeFileSync(path.join(output, 'e2e.json'), JSON.stringify({ passed: false, checks, error: e.message, diagnostic, auth_responses: authResponses, page_errors: errors }, null, 2));
  console.error(e.message); process.exitCode = 1;
}).finally(async () => {
  if (browser) await browser.close();
  for (const child of children) {
    if (process.platform === 'win32') await new Promise(resolve => {
      const killer = spawn('taskkill.exe', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true, stdio: 'ignore' });
      killer.on('exit', resolve);
    }); else child.kill();
  }
  restoreGeneratedTypes({root:process.cwd(),distDir,tsconfigBefore,nextEnvBefore});
});
