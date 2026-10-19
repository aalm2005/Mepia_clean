// Navegador y proxies reales, Auth/DB sintéticos. Nunca usa servicios externos.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {spawn, spawnSync} = require('node:child_process');
const net = require('node:net');
const {chromium} = require(process.env.MEPIA_PLAYWRIGHT_MODULE || 'playwright');
const {restoreGeneratedTypes} = require('./chat_step5_workspace.cjs');
const root = process.cwd();
const output = path.resolve(process.env.MEPIA_ONBOARDING_E2E_OUTPUT || '.test_tmp/onboarding_e2e');
assert(output.startsWith(path.resolve('.test_tmp') + path.sep));
const base = 'http://127.0.0.1:3018', api = 'http://127.0.0.1:8018';
const children = [], checks = [], errors = [];
const originals = {tsconfig: fs.readFileSync('tsconfig.json', 'utf8'), nextEnv: fs.readFileSync('next-env.d.ts', 'utf8')};
let browser;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
async function free(port) {
  const probe = net.createServer();
  await new Promise((resolve, reject) => {probe.once('error', reject); probe.listen(port, '127.0.0.1', () => probe.close(resolve));});
}
function start(exe, args, name, env = {}) {
  const log = fs.openSync(path.join(output, name + '.log'), 'w');
  const child = spawn(exe, args, {cwd: root, windowsHide: true, env: {...process.env, ...env}, stdio: ['ignore', log, log]});
  children.push(child);
}
async function ready(url) {
  for (let i = 0; i < 180; i++) {try {if ((await fetch(url)).ok) return;} catch {} await pause(500);}
  throw new Error('Servidor sintético no disponible');
}
async function check(name, fn) {await fn(); checks.push({name, passed: true}); console.log('PASS ' + name);}
async function state() {return (await fetch(api + '/__test__/onboarding')).json();}
function rows(data, table) {return data.tables[table].filter(row => row.business_id === data.business_a);}
(async () => {
  fs.mkdirSync(output, {recursive: true});
  await free(8018); await free(3018);
  assert(process.env.MEPIA_TEST_PYTHON);
  start(process.env.MEPIA_TEST_PYTHON, ['-B', '-m', 'uvicorn', 'tests.onboarding_step_server:app', '--host', '127.0.0.1', '--port', '8018', '--no-access-log'], 'api', {PYTHONDONTWRITEBYTECODE: '1'});
  await ready(api + '/__test__/onboarding');
  start(process.execPath, ['node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '3018'], 'next', {
    NEXT_TELEMETRY_DISABLED: '1', NEXT_PUBLIC_SUPABASE_URL: api, NEXT_PUBLIC_SUPABASE_ANON_KEY: 'synthetic-public-key',
    AGENTS_API_URL: api, MEPIA_NEXT_DIST_DIR: path.relative(root, path.join(output, 'next')),
  });
  await ready(base + '/login');
  const initial = await state();
  const session = await (await fetch(api + '/__test__/session/a')).json();
  const authHeaders = {Authorization: 'Bearer ' + session.access_token, 'Content-Type': 'application/json'};
  browser = await chromium.launch({headless: true, ...(process.env.MEPIA_TEST_BROWSER ? {channel: process.env.MEPIA_TEST_BROWSER} : {})});
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  const page = await context.newPage(); page.setDefaultTimeout(90000);
  page.on('pageerror', error => errors.push(error.message));
  await context.route('**/*', route => {
    const url = route.request().url();
    return url.startsWith(base) || url.startsWith(api) ? route.continue() : route.abort();
  });
  await check('Entrada con sesión propia y acceso directo a Documentos', async () => {
    await page.goto(base + '/login');
    await page.getByLabel('Correo', {exact: true}).fill('a@example.invalid');
    await page.getByLabel('Contraseña', {exact: true}).fill('synthetic-test-password');
    await page.getByRole('button', {name: 'Iniciar sesión', exact: true}).click();
    await page.getByText('Sesión iniciada', {exact: true}).waitFor();
    await page.getByLabel('Negocio', {exact: true}).selectOption(initial.business_a);
    const saved = page.waitForResponse(response => response.url() === base + '/api/onboarding' && response.request().method() === 'POST');
    await page.getByRole('navigation', {name: 'Navegación principal'}).getByRole('link', {name: 'Documentos', exact: true}).click();
    await page.getByText('Personalizar configuración avanzada →', {exact: true}).waitFor();
    assert.equal((await saved).status(), 201);
    assert.equal(await page.locator('input[type=file]').count(), 2);
  });
  await check('Ajustes iniciales persistidos sin gastos ficticios', async () => {
    const current = await state();
    assert.equal(rows(current, 'business_onboarding').length, 1);
    assert.equal(rows(current, 'business_fixed_costs').length, 0);
    const response = await fetch(base + '/api/onboarding?business_id=' + initial.business_a, {headers: authHeaders});
    const loaded = await response.json();
    assert.equal(response.status, 200);
    assert.equal(loaded.onboarding_complete, true);
    assert.equal(loaded.has_cost_structure, false);
    assert.deepEqual(loaded.settings.expected_cost_structure, []);
  });
  await check('Volver a Documentos conserva los ajustes personalizados', async () => {
    await fetch(api + '/__test__/onboarding/seed-own', {method: 'POST'});
    const before = await state();
    await page.getByRole('navigation', {name: 'Navegación principal'}).getByRole('link', {name: 'Dashboard', exact: true}).click();
    await page.getByRole('navigation', {name: 'Navegación principal'}).getByRole('link', {name: 'Documentos', exact: true}).click();
    await page.getByText('Personalizar configuración avanzada →', {exact: true}).waitFor();
    await page.getByText('Personalizar configuración avanzada →', {exact: true}).click();
    await page.getByRole('radio', {name: 'Calidad', exact: true}).waitFor();
    assert(await page.getByRole('radio', {name: 'Calidad', exact: true}).isChecked());
    const after = await state();
    assert.equal(rows(after, 'mepia_memory').length, rows(before, 'mepia_memory').length);
  });
  for (const percent of [0, 0.1, 0.5, 1, 5, 100]) {
    await check('Guardar sin editar conserva tolerancia ' + percent + '%', async () => {
      await fetch(api + '/__test__/onboarding/seed-own?percent=' + percent, {method: 'POST'});
      await page.goto(base + '/onboarding');
      await page.getByLabel('Negocio', {exact: true}).selectOption(initial.business_a);
      await page.waitForFunction(() => document.querySelector('input[type=radio][value=quality]')?.checked);
      await page.getByRole('button', {name: 'Siguiente →', exact: true}).click();
      await page.getByRole('button', {name: 'Siguiente →', exact: true}).click();
      assert.equal(Number(await page.getByLabel('Tolerancia fila 1', {exact: true}).inputValue()), percent);
      await page.getByRole('button', {name: 'Siguiente →', exact: true}).click();
      const saved = page.waitForResponse(response => response.url() === base + '/api/onboarding' && response.request().method() === 'PUT');
      await page.getByRole('button', {name: 'Guardar configuración ✓', exact: true}).click();
      assert.equal((await saved).status(), 200);
      const active = rows(await state(), 'business_fixed_costs').filter(row => row.is_active);
      assert.equal(active.length, 1);
      assert.equal(active[0].tolerance_pct, percent / 100);
    });
  }
  for (const method of ['GET', 'POST', 'PUT']) {
    await check('Negocio ajeno: ' + method + ' devuelve 403 sin datos ni cambios', async () => {
      const before = await state();
      const response = await fetch(base + '/api/onboarding' + (method === 'GET' ? '?business_id=' + initial.business_b : ''), {
        method, headers: authHeaders,
        body: method === 'GET' ? undefined : JSON.stringify({business_id: initial.business_b, brand_identity: {}, audit_tolerances: {}, audit_rules: {}}),
      });
      assert.equal(response.status, 403);
      assert(!JSON.stringify(await response.json()).includes('Renta'));
      assert.deepEqual((await state()).tables, before.tables);
    });
  }
  await check('Acceso anónimo denegado en Next y directamente en Python', async () => {
    assert.equal((await fetch(base + '/api/onboarding?business_id=' + initial.business_a)).status, 401);
    assert.equal((await fetch(api + '/business/' + initial.business_a + '/onboarding/status')).status, 401);
  });
  await check('Proxy valida identificadores y cuerpo antes de reenviar', async () => {
    assert.equal((await fetch(base + '/api/onboarding?business_id=../invalid', {headers: authHeaders})).status, 400);
    assert.equal((await fetch(base + '/api/onboarding', {method: 'POST', headers: authHeaders, body: '{invalid'})).status, 400);
  });
  assert.deepEqual(errors, []);
  assert.equal((await (await fetch(api + '/__test__/state')).json()).model_calls, 0);
  fs.writeFileSync(path.join(output, 'e2e.json'), JSON.stringify({passed: true, checks, page_errors: errors, external_api_calls: 0}, null, 2));
})().catch(error => {
  fs.mkdirSync(output, {recursive: true});
  fs.writeFileSync(path.join(output, 'e2e.json'), JSON.stringify({passed: false, checks, page_errors: errors, error: String(error)}, null, 2));
  console.error(String(error)); process.exitCode = 1;
}).finally(async () => {
  if (browser) await browser.close();
  for (const child of children.reverse()) {
    if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(child.pid), '/t', '/f'], {windowsHide: true, stdio: 'ignore'});
    else child.kill();
  }
  restoreGeneratedTypes({root, distDir: path.join(output, 'next'),
    tsconfigBefore: originals.tsconfig, nextEnvBefore: originals.nextEnv});
});
