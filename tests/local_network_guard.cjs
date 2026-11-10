// Only loaded by the isolated test/demo launchers, never by the normal app.
const net = require('node:net');
const fs = require('node:fs');
const path = require('node:path');
const original = net.Socket.prototype.connect;
function local(host) {
  return host == null || host === '' || host === 'localhost' || host === '::1' ||
    /^127\.\d+\.\d+\.\d+$/.test(host) || /^::ffff:127\./i.test(host);
}
function record(event) {
  if (!process.env.MEPIA_NETWORK_AUDIT_DIR) return;
  fs.mkdirSync(process.env.MEPIA_NETWORK_AUDIT_DIR, {recursive:true});
  fs.appendFileSync(path.join(process.env.MEPIA_NETWORK_AUDIT_DIR, `node-${process.pid}.jsonl`), JSON.stringify({event,pid:process.pid})+'\n');
}
net.Socket.prototype.connect = function (...args) {
  let first = args[0];
  if (Array.isArray(first)) first = first[0];
  const host = first && typeof first === 'object' ? first.host : typeof args[1] === 'string' ? args[1] : undefined;
  if (!local(host)) {
    record('external_connect_blocked');
    throw new Error('MEPIA: conexión externa bloqueada en pruebas locales');
  }
  return original.apply(this,args);
};
record('guard_installed');
