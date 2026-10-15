const fs = require('node:fs');
const path = require('node:path');

// Retira las referencias del run y conserva el resto de las ediciones.
function restoreGeneratedTypes({root, distDir, tsconfigBefore, nextEnvBefore}) {
  const parse = text => JSON.parse(text.replace(/^\uFEFF/, ''));
  const configPath = path.join(root, 'tsconfig.json');
  const nextEnvPath = path.join(root, 'next-env.d.ts');
  const relative = path.relative(root, distDir).replaceAll('\\', '/');
  const ownTypes = relative + '/types/**/*.ts';
  const before = parse(tsconfigBefore);
  const current = parse(fs.readFileSync(configPath, 'utf8'));
  if (!(before.include || []).some(v => v.replaceAll('\\', '/') === ownTypes)) {
    current.include = (current.include || []).filter(v => v.replaceAll('\\', '/') !== ownTypes);
  }
  // Next puede reubicar next-env.d.ts al actualizar include. El orden no
  // modifica su significado; si no cambió nada más, recuperar los bytes previos.
  const comparable = value => ({...value, include:[...(value.include || [])].sort()});
  fs.writeFileSync(configPath, JSON.stringify(comparable(current)) === JSON.stringify(comparable(before))
    ? tsconfigBefore : JSON.stringify(current, null, 2) + '\n');
  const currentEnv = fs.readFileSync(nextEnvPath, 'utf8');
  const ownRoute = './' + relative + '/types/routes.d.ts';
  if (currentEnv.includes(ownRoute) && !nextEnvBefore.includes(ownRoute)) {
    const pattern = /^\/\/\/ <reference path="[^"]+" \/>\r?$/m;
    const oldReference = nextEnvBefore.match(pattern);
    const restored = oldReference ? currentEnv.replace(pattern, oldReference[0])
      : currentEnv.replace(pattern, '').replace(/\n\n\n/, '\n\n');
    const normalize = s => s.replace(/^\uFEFF/, '').replaceAll('\r\n', '\n');
    fs.writeFileSync(nextEnvPath, normalize(restored) === normalize(nextEnvBefore) ? nextEnvBefore : restored);
  }
}
module.exports = {restoreGeneratedTypes};
