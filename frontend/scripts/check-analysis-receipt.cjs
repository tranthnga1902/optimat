const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const assert = require('node:assert/strict');
const { webcrypto, createHash } = require('node:crypto');
const ts = require('typescript');
globalThis.crypto = webcrypto;
const file = path.resolve(__dirname, '../src/app/(user)/do-boc/read-progress.ts');
const loaded = new Module(file, module);
loaded.filename = file;
loaded.paths = module.paths;
loaded._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS },
}).outputText, file);
const { readProgress, verifyAnalysisReceipt } = loaded.exports;
const digest = text => createHash('sha256').update(text, 'utf8').digest('hex');
const ref = {file_id:901, revision_id:1, sha256:'a'.repeat(64), role:'KT'};
const req = JSON.stringify({files:[ref],profile_version:8,progressive:true,client_analysis_id:'token'});
const complete = JSON.stringify({type:'complete',data:{view:{file:'mẫu',plans:[]}}});
const receipt = {receipt_version:1, analysis_id:'abcdef12-3456-4789-abcd-ef1234567890',client_analysis_id:'token',
  project_id:777,profile_version:8,files:[ref],started_at:'2026-01-01',completed_at:'2026-01-01',
  request_hash_scope:'utf8_http_request_body',request_sha256:digest(req),
  response_hash_scope:'utf8_ndjson_complete_line_without_newline',response_sha256:digest(complete)};
const response = (line, proof = receipt) => new Response(line+'\n'+(proof ? JSON.stringify({type:'receipt',receipt:proof})+'\n' : ''));
(async () => {
  const value = await readProgress(response(complete), () => {}, true);
  await verifyAnalysisReceipt(value.analysis_receipt, 777, 8, [ref], 'token', req);
  for (const bad of [{...receipt,project_id:778}, {...receipt,profile_version:9},
    {...receipt,files:[{...ref,sha256:'b'.repeat(64)}]}, {...receipt,client_analysis_id:'different'}])
    await assert.rejects(verifyAnalysisReceipt(bad,777,8,[ref],'token',req));
  await assert.rejects(verifyAnalysisReceipt(receipt,777,8,[ref],'token',req+' '));
  await assert.rejects(readProgress(response(complete.replace('mẫu','khác')),()=>{},true));
  await assert.rejects(readProgress(response(complete,null),()=>{},true));
  const large = JSON.stringify({type:'complete',data:{file:'Móng tầng trệt',cad:'nét'.repeat(900000)}});
  const bytes = Buffer.from(large+'\n'+JSON.stringify({type:'receipt',receipt:{...receipt,response_sha256:digest(large)}}));
  let offset = 0;
  const split = new ReadableStream({pull(controller) {
    if (offset >= bytes.length) return controller.close();
    controller.enqueue(bytes.subarray(offset, offset + 4093));
    offset += 4093;
  }});
  const read = await readProgress(new Response(split),()=>{},true);
  assert.equal(read.cad.length,2700000);
  assert.equal(read.file,'Móng tầng trệt');
  console.log('PASS: receipt, request, project, profile, revision, hash và stream lỗi.');
})().catch(error => { console.error(error); process.exitCode=1; });
