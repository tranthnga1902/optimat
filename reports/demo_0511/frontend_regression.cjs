const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../frontend');
const ts = require(path.join(root, 'node_modules/typescript'));
const source = path.join(root, 'src/app/(user)/do-boc');
const saved = new Map();
const store = { get: (k, d) => saved.has(k) ? saved.get(k) : d, set: (k, v) => saved.set(k, v) };
let failReviewWrite = false;
const localStorage = { getItem: k => saved.has(k) ? JSON.stringify(saved.get(k)) : null, setItem: (k, v) => {
  if (k === 'optimat-review' && failReviewWrite) throw Error('QuotaExceededError');
  saved.set(k, JSON.parse(v));
} };
let slots = [], cursor = 0, layout = [], effects = [], timerId = 0;
const timers = new Map();
const useState = initial => { const i = cursor++; if (!(i in slots)) slots[i] = initial; return [slots[i], value => { slots[i] = typeof value === 'function' ? value(slots[i]) : value; }]; };
const react = {
  useState, useRef: initial => { const i = cursor++; return slots[i] ??= { current: initial }; },
  useMemo: fn => fn(), useCallback: fn => fn,
  useLayoutEffect: fn => layout.push(fn),
  useEffect: (fn, deps) => {
    const i = cursor++, previous = slots[i];
    if (!deps || !previous || deps.some((value, at) => !Object.is(value, previous[at]))) {
      slots[i] = deps || null;
      effects.push(fn);
    }
  },
};
const jsx = (type, props) => ({ type, props });
const components = new Proxy({}, { get: (_, k) => k });
let fetchImpl;
const navigations = [];
let adjustment = false, roughOnly = false;
let cleanups = [];
const listeners = new Map();
class Element {}
class HTMLAnchorElement extends Element { constructor(pathname) { super(); this.pathname=pathname; this.origin="http://test"; } closest() {return this;} }
const context = {
  console, localStorage, structuredClone, URLSearchParams, Element, HTMLAnchorElement, location: { search: '', origin:'http://test', pathname:'/do-boc' }, document:{addEventListener:(k,v)=>listeners.set(k,v),removeEventListener(){}},
  window: { addEventListener() {}, removeEventListener() {} },
  setTimeout: fn => { timers.set(++timerId, fn); return timerId; }, clearTimeout: id => timers.delete(id),
  FormData, AbortController, AbortSignal, Headers, Response, ReadableStream, TextDecoder, TextEncoder, fetch: (...args) => fetchImpl(...args),
};
function load(file, dependency) {
  const exports = {};
  const js = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true } }).outputText;
  vm.runInNewContext(js, { ...context, exports, require: dependency }, { filename: file });
  return exports;
}
const model = load(path.join(source, 'model.ts'), () => { throw Error('Unexpected dependency'); });
const progress = load(path.join(source, 'read-progress.ts'), () => { throw Error('Unexpected progress dependency'); });
const review = load(path.join(source, 'Review.tsx'), name => {
  if (name === 'react') return react;
  if (name === 'react/jsx-runtime') return { jsx, jsxs: jsx, Fragment: 'Fragment' };
  if (name === './model') return model;
  if (name === './read-progress') return progress;
  if (name === 'next/navigation') return {useRouter: () => ({push: url => navigations.push(url)})};
  if (name === '@/lib/store') return { store, useStored: (k, d) => store.get(k, d) };
  if (name === './viewport') return { useViewport: () => ({ svgRef: {}, scaleRef: {}, vbRef: {current: {w: 100}}, movedRef: {}, fitSize() {}, focusOn() {}, toWorld() {}, onPointerDown() {} }) };
  if (name.endsWith('.css')) return {};
  if (name === 'next/link') return 'Link';
  return components;
});
function render() { cursor = 0; layout = []; effects = []; const tree = review.Review({adjustment,roughOnly}); layout.forEach(f => f()); effects.forEach(f => {const cleanup=f();if(typeof cleanup === "function")cleanups.push(cleanup);}); return tree; }
function find(tree, predicate) {
  if (!tree || typeof tree !== 'object') return;
  if (Array.isArray(tree)) { for (const child of tree) { const found = find(child, predicate); if (found) return found; } return; }
  if (predicate(tree)) return tree;
  return find(tree.props?.children, predicate);
}
const response = body => ({ ok: true, headers: new Headers({'content-type':'application/json'}), json: async () => body });
const deferred = () => { let resolve; const promise = new Promise(r => resolve = r); return { promise, resolve }; };
const p = { plan: {name: 'Tầng 1', height_source: 'cao độ tầng trên'}, height_mm: 3300, size: [100,100], layers: [], segs: [], walls: [], openings: [],
  stairs: [{ id: 'S1', steps: 20, flight_width_mm: 1000, tread_mm: 250, landing_area_m2: 1, source: 'auto' },
    { id: 'S2', steps: 18, flight_width_mm: 900, tread_mm: 260, landing_area_m2: 0.5, source: 'auto', kind: 'ban' }] };
const data = { file: 'demo.dxf', plans: [p], materials: [], families: [] };
const clone = value => JSON.parse(JSON.stringify(value));
const result = model.roughRequest(data, {0: {...model.initState(p),scope:"count"}}, {}, null);
assert.equal(result.plans[0].stairs.length, 2);
assert.equal(result.plans[0].stairs[0].id, 'S1');
assert.deepEqual(clone(result.plans[0].stairs[1]), p.stairs[1]);
assert.equal(result.plans[0].height_source, 'cao độ tầng trên');
const missingStairData = clone(data);
missingStairData.plans[0].stairs[0].steps = null;
const missingStairRequest = model.roughRequest(missingStairData, {0: {...model.initState(missingStairData.plans[0]),scope:"count"}}, {}, null);
assert.equal(missingStairRequest.plans[0].stairs.length, 2, 'first stair with missing steps must remain visible as missing, alongside second stair');
assert.equal(missingStairRequest.plans[0].stairs[0].steps, null);
assert.equal(missingStairRequest.plans[0].stairs[0].id, 'S1');
assert.equal(missingStairRequest.plans[0].stairs[0].source, 'auto');
const clearedStair = model.initPlanParams(p);
clearedStair.stair_steps = '';
const clearedRequest = model.roughRequest(data, {0: {...model.initState(p),scope:"count"}}, {0: clearedStair}, null);
assert.equal(clearedRequest.plans[0].stairs.length, 2, 'clearing steps is missing input, not explicit deletion');
assert.equal(clearedRequest.plans[0].stairs[0].steps, null);
assert.equal(clearedRequest.plans[0].stairs[0].source, 'manual');
const noStairData = clone(data); noStairData.plans[0].stairs = [];
assert.equal(model.roughRequest(noStairData, {0: {...model.initState(noStairData.plans[0]),scope:"count"}}, {}, null).plans[0].stairs.length, 0, 'do not invent stairs without recognition or input');
const state = {...model.initState(p),scope:"count"};
state.height_mm = 3500; state.height_source = 'nhập tay';
assert.equal(model.payload(data, p, state, null).height_source, 'nhập tay');
assert.equal(model.roughRequest(data, {0: state}, {}, null).plans[0].height_source, 'nhập tay');
function remount(options={}) { cleanups.forEach(f=>f());cleanups=[];slots=[];timers.clear();adjustment=!!options.adjustment;roughOnly=!!options.roughOnly;render();return render(); }
const confirmBody = height => ({file:data.file,plan:p.plan.name,height_mm:height,groups:[],total_net_area_m2:10,warnings:[]});
const heightInput = tree => find(tree,x=>x.type==='ChangeInput'&&x.props.step===0.05);
const confirmButton = tree => find(tree,x=>x.type==='button'&&x.props.children==='Xác nhận kích thước, khối lượng');
const scopeSelect = tree => find(tree,x=>x.type==='select'&&find(x.props.children,o=>o.type==='option'&&o.props.value==='count'));
async function confirm(tree) {confirmButton(tree).props.onClick();tree=render();await find(tree,x=>x.type==='ConfirmDialog').props.send();return render();}
(async()=>{
 saved.set('optimat-project','12');saved.set('optimat-project-name','Dự án kiểm thử');saved.set('optimat-project-info',{name:'Dự án kiểm thử'});
 saved.set('optimat-confirmed',[{file:'other.dxf',plan:'Khác'}]);
 saved.set('optimat-material-draft',{file:data.file,choices:{0:{W1:'OLD'}}});saved.set('optimat-materials-ready',true);saved.set('optimat-optimization',{old:true});
 let uploadBody;
 fetchImpl=async(url,opts)=>{
  assert.equal(url,'/api/takeoff/view');uploadBody=opts.body;
  assert.ok(opts.signal instanceof AbortSignal);assert.equal(uploadBody.get('progressive'),'true');
  const bytes=new TextEncoder().encode([
   {type:'status',stage:'reading',message:'Đang đọc bản vẽ'},
   {type:'preview',preview:{origin:[0,0],size:[100,100],segments:[],total:0,shown:0}},
   {type:'recognized',data},{type:'complete',data},
  ].map(x=>JSON.stringify(x)).join('\n')+'\n');
  return new Response(new ReadableStream({start(controller){for(let i=0;i<bytes.length;i+=7)controller.enqueue(bytes.slice(i,i+7));controller.close();}}),{headers:{'content-type':'application/x-ndjson'}});
 };
 let tree=remount();
 await find(tree,x=>x.type==='input'&&x.props.type==='file').props.onChange({target:{files:[new Blob(['cad'])]}});
 assert.equal(uploadBody.get('project_id'),'12');tree=render();
 assert.equal(store.get('optimat-material-draft','missing'),null);assert.equal(store.get('optimat-materials-ready',true),false);assert.equal(store.get('optimat-optimization','missing'),null);
 scopeSelect(tree).props.onChange({target:{value:'count'}});tree=render();
 fetchImpl=async()=>response(confirmBody(3300));tree=await confirm(tree);
 assert.equal(navigations.at(-1),'/dieu-chinh');assert.equal(store.get('optimat-confirmed',[]).length,2);
 heightInput(tree).props.onCommit({value:'3.5'});tree=render();
 assert.equal(store.get('optimat-confirmed',[]).length,1,'geometry edit invalidates published confirmation');
 const stale=deferred();fetchImpl=()=>stale.promise;
 confirmButton(tree).props.onClick();tree=render();const confirming=find(tree,x=>x.type==='ConfirmDialog').props.send();
 heightInput(tree).props.onCommit({value:'3.6'});render();stale.resolve(response(confirmBody(3500)));await confirming;
 assert.equal(store.get('optimat-confirmed',[]).length,1,'stale confirm cannot restore previous geometry');
 tree=render();fetchImpl=async()=>response(confirmBody(3600));tree=await confirm(tree);
 const oldHeight=store.get('optimat-review',{}).states[0].height_mm;
 failReviewWrite=true;heightInput(tree).props.onCommit({value:'3.7'});tree=render();fetchImpl=async()=>response(confirmBody(3700));tree=await confirm(tree);
 let prevented=false;listeners.get('click')({target:new HTMLAnchorElement('/dieu-chinh'),preventDefault(){prevented=true;},stopPropagation(){}});
 assert.ok(prevented,'manual navigation must be blocked after both persistence attempts fail');
 assert.equal(store.get('optimat-review',{}).states[0].height_mm,oldHeight);
 failReviewWrite=false;tree=render();tree=await confirm(tree);
 assert.equal(store.get('optimat-review',{}).states[0].height_mm,3700);
 // Material save is a separate transaction; rough page must restore only approved choices.
 saved.set('optimat-materials-ready',true);tree=remount({roughOnly:true});
 let roughTab=find(tree,x=>x.type==='RoughTab');assert.ok(roughTab);
 const pending=deferred();fetchImpl=()=>pending.promise;
 const running=roughTab.props.onRun();tree=render();
 find(tree,x=>x.type==='RoughTab').props.onPlanParam('void_area_m2','5');render();
 pending.resolve(response({totals:['STALE']}));await running;
 assert.equal(store.get('optimat-rough','missing'),null,'old rough response rejected after parameter edit');
 fetchImpl=async()=>response({totals:['NEW'],wall_groups:[],wall_group_issues:[]});
 const recalc=[...timers.values()].pop();timers.clear();await recalc();
 assert.equal(store.get('optimat-rough',{}).result.totals[0],'NEW');
 tree=render();fetchImpl=async()=>({ok:false,json:async()=>({detail:'broken'})});
 await find(tree,x=>x.type==='RoughTab').props.onRun();assert.equal(store.get('optimat-rough','missing'),null,'failed rough must remove old procurement');
 tree=render();const oldRunResult=deferred();fetchImpl=()=>oldRunResult.promise;
 const oldRun=find(tree,x=>x.type==='RoughTab').props.onRun();
 remount();oldRunResult.resolve(response({totals:['OLD MOUNT']}));await oldRun;
 assert.equal(store.get('optimat-rough','missing'),null,'unmounted rough response cannot publish to a new geometry session');
 const legacy=clone(store.get('optimat-review',{}));delete legacy.states[0].scope;saved.set('optimat-review',legacy);saved.set('optimat-rough',{result:{totals:['OLD']}});saved.set('optimat-materials-ready',true);
 remount({roughOnly:true});assert.equal(store.get('optimat-rough','missing'),null,'legacy unclassified scope invalidates saved rough');
 tree=remount();assert.equal(scopeSelect(tree).props.value,'','legacy geometry remains editable for intentional scope decision');
 console.log('PASS current modules: explicit scope, height/multiple/missing stairs, upload project, stale confirmation, quota manual transition guard, rough restore/parameter concurrency/error/unmount, legacy snapshot migration.');
})().catch(e=>{console.error(e);process.exitCode=1;});
