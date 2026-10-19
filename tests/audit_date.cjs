const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
const mod = {exports: {}};
const code = ts.transpileModule(fs.readFileSync('utils/audit-date.ts', 'utf8'),
  {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020}}).outputText;
new Function('exports', 'require', 'module', code)(mod.exports, require, mod);
const {resolveAuditDate: date} = mod.exports;
const day = '2026-10-14';
const cases = [
  () => assert.equal(date('', [day], [day]), day),
  () => assert.equal(date('', [day, day], ['2026-10-01']), day),
  () => assert.equal(date(day, [day], ['2026-10-01']), day),
  () => assert.throws(() => date('2024-01-15', [day], [day]), /no coincide/),
  () => assert.throws(() => date('', [day,'2026-10-13'], []), /días distintos/),
  () => assert.throws(() => date('', [], []), /Selecciona la fecha/),
  () => assert.equal(date('', [], [day]), day),
  () => assert.throws(() => date('', [], [day,'2026-10-13']), /Selecciona la fecha/),
  () => assert.equal(date(day, [], []), day),
  () => assert.throws(() => date('2026-02-30', [], []), /fecha válida/),
  () => assert.throws(() => date('invalid', [], []), /fecha válida/),
];
for (const run of cases) run();
console.log(JSON.stringify({passed: cases.length, external_calls: 0}));
