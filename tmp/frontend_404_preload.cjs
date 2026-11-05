const fs = require('node:fs');
const path = require('node:path');
const { errorMonitor } = require('node:events');
const { threadId } = require('node:worker_threads');

const frontend = path.resolve(__dirname, '../frontend');
const filename = path.resolve(__dirname, 'frontend_404_trace_events.ndjson');
const workerName = /^pool_entry-\[turbopack-node\]_transforms_webpack-loaders_ts_[a-z0-9_.-]+\.js$/i;
const cwd = process.cwd();
const isLocal = p => p === frontend || p.startsWith(frontend + path.sep);
const isWorker = arg => workerName.test(path.basename(arg)) && isLocal(path.resolve(cwd, arg));
const args = process.argv.slice(1);
const worker = args.some(isWorker);
function safeArg(arg, i) {
  if (isWorker(arg)) return arg;
  if (worker && i > 0 && isWorker(args[i-1]) && /^\d{1,5}$/.test(arg)) return arg;
  if (['run', 'build', 'next', '--webpack', '--trace-warnings', '-e', '--eval', '--require', '-r', '-'].includes(arg)) return arg;
  if (arg === __filename || /[\\/](?:npm-cli\.js|next[\\/]dist[\\/]bin[\\/]next|next[\\/]dist[\\/]compiled[\\/]jest-worker[\\/](?:processChild|threadChild)\.js)$/i.test(arg)) return arg;
  return '[masked]';
}
function write(event, extra = {}) {
  fs.appendFileSync(filename, JSON.stringify({time:new Date().toISOString(), pid:process.pid, ppid:process.ppid, threadId, event, ...extra})+'\n');
}
write('start', {cwd:isLocal(cwd) ? cwd : '[other cwd]', execPath:process.execPath, argv:args.map(safeArg),
  execArgv:process.execArgv.map(a=>safeArg(a,-1)), worker,
  mode:['development','production','test'].includes(process.env.NODE_ENV) ? process.env.NODE_ENV : null});
if (worker) {
  require('node:diagnostics_channel').subscribe('net.client.socket', ({socket})=>{
    write('socket');
    socket.once('connect',()=>write('connected',{loopback:socket.remoteAddress==='127.0.0.1',port:socket.remotePort}));
    socket.once(errorMonitor,e=>write('socket-error',{code:typeof e.code==='string' && /^[A-Z_]+$/.test(e.code) ? e.code : 'other'}));
    socket.once('close',hadError=>write('closed',{hadError,bytesWritten:socket.bytesWritten,bytesRead:socket.bytesRead}));
  });
}
process.once('beforeExit',code=>write('before-exit',{code}));
process.once('exit',code=>write('exit',{code}));
