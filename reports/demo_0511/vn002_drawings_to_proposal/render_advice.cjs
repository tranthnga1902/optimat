// Chạy nút hỏi của MaterialAdvisor với phản hồi đã kiểm. Không gửi HTTP hay tạo phiên xét duyệt.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');
const frontend = path.resolve(__dirname, '../../../frontend');
const pkg = name => require(path.join(frontend, 'node_modules', name));
const ts = pkg('typescript'), react = pkg('react'), jsx = pkg('react/jsx-runtime');
const {renderToStaticMarkup} = pkg('react-dom/server');
const read = name => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
const receipt = read('live_receipt.json'), context = read(receipt.context_file), answer = read('answer.validated.json');
const values = [];
let index, evidence, calls = [];
const hooks = {
  useRef(initial) { const i=index++; return values[i] ??= {current: initial}; },
  useState(initial) {
    const i=index++;
    if (!(i in values)) values[i]=initial;
    return [values[i], next => {values[i]=next;}];
  },
  useEffect() {},
};
const response = body => ({ok:true, status:200, json:async()=>body});
async function recordedFetch(url, {body}) {
  const request = JSON.parse(body);
  assert.equal(request.contextHash, receipt.context_sha256);
  assert.equal(request.requestId, answer.requestId);
  assert.deepEqual(JSON.parse(request.contextJson), context);
  calls.push(url);
  if (url === '/api/assistant/material-session') return response({binding:answer.binding,contextHash:answer.contextHash});
  assert.equal(url, '/api/assistant/materials');
  return response(answer);
}
const source = fs.readFileSync(path.join(frontend, 'src/components/MaterialAdvisor.tsx'), 'utf8');
const compiled = ts.transpileModule(source,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.CommonJS}}).outputText;
const exported = {};
vm.runInNewContext(compiled,{exports:exported,require:name=>{
  if(name==='react') return hooks;
  if(name==='react/jsx-runtime') return jsx;
  if(name==='./AssistantWindow') return {AssistantWindow:({open,children})=>open ? children : null};
  throw Error(name);
},TextEncoder,AbortController,crypto:{subtle:webcrypto.subtle,randomUUID:()=>answer.requestId},fetch:recordedFetch});
const render = () => { index=0; return exported.MaterialAdvisor({context,open:true,initialQuestion:'Đề xuất toàn bộ phần thô',onResult:r=>{evidence=r;}}); };
const button = tree => {
  if(!react.isValidElement(tree)) return;
  if(tree.type==='button' && tree.props.children==='Tư vấn chọn vật liệu') return tree;
  return react.Children.toArray(tree.props.children).map(button).find(Boolean);
};
(async()=>{
  const ask = button(render());
  assert.ok(ask && !ask.props.disabled);
  await ask.props.onClick();
  assert.deepEqual(calls,['/api/assistant/material-session','/api/assistant/materials']);
  assert.equal(evidence.contextHash, receipt.context_sha256);
  assert.equal(evidence.contextJson, JSON.stringify(context));
  assert.equal(evidence.response, answer);
  assert.ok(Number.isFinite(Date.parse(evidence.receivedAt)));
  const result = renderToStaticMarkup(render());
  assert.equal((result.match(/<article\b/g)||[]).length,answer.facts.materials.length);
  assert.match(result,/Trong phạm vi tra cứu hiện tại chỉ có mã này/);
  assert.match(result,/báo giá của nhà cung cấp cho đúng TH10/);
  assert.match(result,/Chưa có công tác nào được xác nhận/);
  const html = `<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>VN002 · Kết quả kiểm tư vấn</title><style>
body{max-width:970px;margin:3rem auto;padding:0 1.25rem;background:#f6f7f5;color:#18332e;font:16px/1.55 system-ui}h1,h3,h4{line-height:1.2}article,details{padding:1rem;background:white;border:1px solid #cbd6d1;border-radius:8px;margin:1rem 0}h4{font-size:1.2rem;margin:0}textarea,button,label{display:none}fieldset{border:0;margin:0;padding:0}small{color:#415a53}
</style><main><small>OPTIMAT AI · KIỂM DEMO 05/11</small><h1>Phương án phần thô · VN002</h1>
<p>Bản xem lại kết quả. Phần dưới dùng giao diện trả lời của ứng dụng và phản hồi OpenAI thật đã qua kiểm tra. Có ${context.works.length} dòng công tác và ${context.materials.length} dòng vật tư. Hồ sơ chưa có xác nhận khối lượng trên trình duyệt.</p>
<fieldset disabled>${result}</fieldset></main></html>`;
  fs.writeFileSync(path.join(__dirname,'KET_QUA.html'),html,'utf8');
  console.log('Rendered all material rows with the captured response via MaterialAdvisor; no HTTP, 0 approvals.');
})().catch(err=>{console.error(err);process.exitCode=1;});
