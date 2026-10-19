// Regresiones del contrato de presentación S3 al integrar el frontend del equipo.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
const mod = {exports: {}};
const code = ts.transpileModule(fs.readFileSync('utils/mapCalcResultsToKpis.ts', 'utf8'),
  {compilerOptions: {module: ts.ModuleKind.CommonJS}}).outputText;
new Function('exports', 'require', 'module', code)(mod.exports, require, mod);
const {mapCalcResultsToKpis, calcResultsToChartRows} = mod.exports;
const metric = (value, unit = '%', status = 'ok', name = 'contribution_margin') => ({metric: name, value, unit, status, context: 'Resultado emitido'});
const checks = [];
function check(name, fn) {fn(); checks.push({name, passed: true}); console.log('PASS ' + name);}
for (const value of [0, 0.5, 1, -2, 101, 12.345678])
  check('Porcentaje emitido ' + value + ' sin reescalar', () => assert.equal(mapCalcResultsToKpis([metric(value)])[1].value, value.toLocaleString('es-MX', {maximumFractionDigits: 20}) + '%'));
check('Montos y unidad sin redondear a enteros', () => {
  const item = mapCalcResultsToKpis([metric(1234.56789, 'MXN', 'warning')])[1];
  assert.equal(item.value, '1,234.56789'); assert.equal(item.unit, 'MXN'); assert.equal(item.status, 'warning');
});
check('Costo operativo no presentado como margen', () => assert.equal(mapCalcResultsToKpis([metric(80, 'MXN', 'ok', 'operative_cost')])[1].value, '—'));
check('Etiqueta conserva la métrica emitida', () => assert.equal(mapCalcResultsToKpis([metric(5)])[1].label, 'contribution_margin'));
check('Datos incompletos e incompatibles no muestran cifras', () => {
  for (const status of ['unit_mismatch', 'incomplete_data']) assert.equal(mapCalcResultsToKpis([metric(10, 'MXN', status)])[1].value, '—');
});
check('Gráficas excluyen nulos, no finitos y datos inválidos', () => {
  assert.deepEqual(calcResultsToChartRows([metric(null), metric(NaN), metric(Infinity), metric(10, '%', 'unit_mismatch'), metric(10, '%', 'incomplete_data')]), []);
});
check('Filas de gráficas preservan valor, unidad y estado', () => {
  const values = [metric(0.5, '%', 'warning'), metric(50, 'MXN', 'critical')];
  const rows = calcResultsToChartRows(values);
  assert.deepEqual(rows.map(row => [row.value, row.unit, row.status]), [[0.5, '%', 'warning'], [50, 'MXN', 'critical']]);
});
check('Cero decimal de Pydantic aparece en la tarjeta de caja', () => {
  assert.equal(mapCalcResultsToKpis([metric('0.00', 'MXN', 'ok', 'conciliacion_caja')])[4].value, '0');
});
check('Porcentaje decimal recibido como texto no se reescala', () => {
  assert.equal(mapCalcResultsToKpis([metric('0.5')])[1].value, '0.5%');
});
check('Gráficas admiten decimales textuales finitos', () => {
  assert.deepEqual(calcResultsToChartRows([metric('0.00', 'MXN')]).map(r => r.value), [0]);
});
check('Texto inválido, vacío y booleanos no se vuelven cero', () => {
  for (const value of ['', ' ', 'NaN', 'Infinity', 'MXN 3', true, [], '1e999']) {
    assert.equal(mapCalcResultsToKpis([metric(value)])[1].value, '—');
    assert.deepEqual(calcResultsToChartRows([metric(value)]), []);
  }
});
const reportPath = process.argv[2] || '.test_tmp/frontend_merge_20261014/presentation_tests.json';
fs.mkdirSync(require('node:path').dirname(reportPath), {recursive: true});
fs.writeFileSync(reportPath, JSON.stringify({passed: true, checks, external_calls: 0}, null, 2));
