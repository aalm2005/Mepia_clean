const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {restoreGeneratedTypes} = require('./chat_step5_workspace.cjs');

function fixture() {
  const base = path.resolve('.test_tmp/workspace_cleanup_tests');
  fs.mkdirSync(base, {recursive:true});
  const root = fs.mkdtempSync(path.join(base, 'run-'));
  const original = {compilerOptions:{strict:true}, include:['next-env.d.ts','**/*.ts']};
  const tsconfigBefore = '\uFEFF' + JSON.stringify(original,null,2).replaceAll('\n','\r\n') + '\r\n';
  const nextEnvBefore = '/// <reference types="next" />\r\n/// <reference path="./.next/types/routes.d.ts" />\r\n';
  const distDir = path.join(root,'.test_tmp/cache');
  const changed = {...original, include:['**/*.ts','next-env.d.ts','.test_tmp/cache/types/**/*.ts']};
  fs.writeFileSync(path.join(root,'tsconfig.json'),JSON.stringify(changed,null,2));
  fs.writeFileSync(path.join(root,'next-env.d.ts'),nextEnvBefore.replace('./.next/','./.test_tmp/cache/'));
  return {root, distDir, tsconfigBefore, nextEnvBefore};
}

test('restores bytes after generated path, include reorder, BOM and CRLF', () => {
  const f=fixture();restoreGeneratedTypes(f);
  assert.equal(fs.readFileSync(path.join(f.root,'tsconfig.json'),'utf8'),f.tsconfigBefore);
  assert.equal(fs.readFileSync(path.join(f.root,'next-env.d.ts'),'utf8'),f.nextEnvBefore);
});
test('preserves another edit while removing only owned references', () => {
  const f=fixture();const file=path.join(f.root,'tsconfig.json');
  const current=JSON.parse(fs.readFileSync(file,'utf8'));current.compilerOptions.noUncheckedIndexedAccess=true;
  current.include.push('team/**/*.ts');fs.writeFileSync(file,JSON.stringify(current));
  fs.appendFileSync(path.join(f.root,'next-env.d.ts'),'// another edit\r\n');
  restoreGeneratedTypes(f);
  const restored=JSON.parse(fs.readFileSync(file,'utf8'));
  assert.equal(restored.compilerOptions.noUncheckedIndexedAccess,true);
  assert(restored.include.includes('team/**/*.ts'));
  assert(!restored.include.some(v=>v.includes('.test_tmp/cache')));
  assert(fs.readFileSync(path.join(f.root,'next-env.d.ts'),'utf8').endsWith('// another edit\r\n'));
});
test('does not rewrite an unrelated route reference', () => {
  const f=fixture();const file=path.join(f.root,'next-env.d.ts');
  const other=f.nextEnvBefore.replace('./.next/','./team-cache/');fs.writeFileSync(file,other);
  restoreGeneratedTypes(f);assert.equal(fs.readFileSync(file,'utf8'),other);
});
