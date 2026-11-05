// Chạy các handler thật của Review với nhiều mặt bằng, API hoãn phản hồi và bộ nhớ có thể đầy.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require(path.resolve(__dirname,"../../frontend/node_modules/typescript"));
const frontend = process.env.CONFIRM_TEST_FRONTEND;
const dependencies = process.env.CONFIRM_TEST_BASE || frontend;
const folder = "src/app/(user)/do-boc/";

function session(scopes, heights, active = 0, savedValues, mode = {}, names = [], warnings = []) {
  const hooks = [], values = new Map(), listeners = {}, calls = [], navigations = [];
  let publications = 0;
  let cursor = 0, effects = [], tree, failLocal = false;
  const state = initial => {
    const i = cursor++;
    if (!(i in hooks)) hooks[i] = typeof initial === "function" ? initial() : initial;
    return [hooks[i], next => { hooks[i] = typeof next === "function" ? next(hooks[i]) : next; }];
  };
  const memo = (fn, deps) => {
    const i = cursor++, prev = hooks[i];
    if (!prev || !deps || deps.some((v,j) => !Object.is(v,prev.deps[j]))) hooks[i] = { deps, value:fn() };
    return hooks[i].value;
  };
  const effect = (fn, deps) => memo(() => { effects.push(fn); }, deps);
  const react = { useState:state, useRef:v=>state(()=>({current:v}))[0], useEffect:effect, useLayoutEffect:effect,
    useMemo:memo, useCallback:(fn,deps)=>memo(()=>fn,deps) };
  const jsx = (type, props) => ({type,props});
  const localStorage = { getItem:k=>values.get(k)??null, removeItem:k=>values.delete(k), setItem:(k,v)=>{
    if (failLocal && k === "optimat-confirmed") throw Error("QuotaExceededError");
    if (k === "optimat-confirmed") publications++;
    values.set(k,v);
  }};
  const store={get:(k,d)=>values.has(k)?JSON.parse(values.get(k)):d,set:(k,v)=>{
    try { localStorage.setItem(k,JSON.stringify(v)); } catch { /* store.set của ứng dụng cũng bỏ qua lỗi quota; saveTogether phải báo lỗi. */ }
  }};
  const win={addEventListener:(k,f)=>{listeners[k]=f;},removeEventListener(){},dispatchEvent(){},setTimeout,clearTimeout};
  const globals={ structuredClone, window:win, localStorage, crypto:globalThis.crypto, URLSearchParams, location:{search:""},
    document:{addEventListener(){},removeEventListener(){}}, CustomEvent:class{}, AbortController, setTimeout, clearTimeout,
    fetch:(url,init)=>new Promise(resolve=>calls.push({url,signal:init.signal,body:JSON.parse(init.body),resolve})) };
  const placeholder=new Proxy({},{get:(_,k)=>k});
  const modules={react,"react/jsx-runtime":{jsx,jsxs:jsx,Fragment:"Fragment"},"next/link":"Link",
    "next/navigation":{useRouter:()=>({push:u=>navigations.push(u)})},
    "@/lib/store":{store,useStored:store.get},"@/lib/projects":{projectUid:()=>store.get("optimat-project-uid","")},
    "./viewport":{useViewport:()=>({svgRef:{},scaleRef:{},vbRef:{current:{w:1}},movedRef:{},fitSize(){}})}};
  function load(file) {
    const edited=path.join(frontend,file);
    const text=fs.readFileSync(fs.existsSync(edited)?edited:path.join(dependencies,file),"utf8");
    const js=ts.transpileModule(text,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;
    const exports={}; vm.runInNewContext(js,{...globals,exports,require:n=>modules[n]||placeholder},{filename:file}); return exports;
  }
  const floors=modules["./floor-review"]=modules["@/app/(user)/do-boc/floor-review"]=load(folder+"floor-review.ts");
  const model=modules["./model"]=load(folder+"model.ts");
  modules["./paper-scale"]=load(folder+"paper-scale.ts");
  modules["@/lib/review-session"]=load("src/lib/review-session.ts");
  modules["@/lib/work-review"]=load("src/lib/work-review.ts");
  modules["./scope-workspace"]=load(folder+"scope-workspace.ts");
  const selector=load(folder+"FloorSelector.tsx").FloorSelector;
  const component=load(folder+"Review.tsx").Review;
  const plans=scopes.map((s,i)=>({plan:{name:names[i] || "Tầng "+(i+1)},height_mm:heights[i],warnings:warnings[i]||[],walls:[],openings:[],size:[100,100],layers:[],segs:[]}));
  const data={file:"kiem-tra.dxf",plans,materials:[],families:[]};
  const states=Object.fromEntries(plans.map((p,i)=>[i,{...model.initState(p),scope:scopes[i]}]));
  store.set("optimat-project-uid","qa");store.set("optimat-project","25");store.set("optimat-project-name","Kiểm thử");
  store.set("optimat-project-info",{name:"Kiểm thử"});
  store.set("optimat-review",{projectUid:"qa",drawingId:"drawing",data,states,confirmed:{},planP:{},pi:active});
  if (savedValues) for (const [key,value] of savedValues) values.set(key,value);
  function render(){cursor=0;effects=[];tree=component(mode);for(const fn of effects)fn();}
  function find(pred,node=tree) {
    if (Array.isArray(node)) return node.map(n=>find(pred,n)).find(Boolean);
    if (!node||typeof node!=="object") return undefined;
    if (pred(node)) return node;
    return node.props && node.props.children!==undefined ? find(pred,node.props.children) : undefined;
  }
  const textOf=t=>Array.isArray(t)?t.map(textOf).join(""):!t?"":typeof t==="object"?textOf(t.props?.children):String(t);
  const button=label=>find(n=>n.type==="button"&&textOf(n.props.children).includes(label));
  function respond(n,id,ok=true) {
    const req=calls[n];req.resolve({ok,status:ok?200:422,json:async()=>ok?{
      file:req.body.file,plan:req.body.plan,height_mm:req.body.height_mm,groups:[],warnings:[],total_net_area_m2:0,takeoff_id:id
    }:{detail:"Dữ liệu chưa hợp lệ."}});
  }
  render();render();
  const picker=()=>find(n=>n.type==="FloorSelector").props;
  return {render,find,button,calls,store,respond,navigations,listeners,values,model,floors,data,states,picker,
    choose:ids=>{picker().onChange(ids);render();}, apply:()=>{picker().onOpen();render();},
    controls:()=>selector(picker()),publications:()=>publications,
    fail:v=>{failLocal=v;}, dialog:()=>find(n=>n.type==="ConfirmDialog"),
    open:()=>{button("Xác nhận kích thước, khối lượng").props.onClick();render();return find(n=>n.type==="ConfirmDialog").props.send();}};
}

(async()=>{
  if (process.env.CONFIRM_REPRO_BEFORE === "1") {
    const old=session([null,"count","reference"],[3300,3600,0]);
    await old.open();old.render();
    assert.ok(old.dialog());assert.equal(old.calls.length,0);assert.deepEqual(old.navigations,[]);
    console.log("REPRO: hộp thoại của bản cũ vẫn mở sau Xác nhận khi phạm vi thiếu; không POST, không chuyển trang.");
    return;
  }
  const q=session(["count",null,"reference"],[3300,0,0]);
  q.button("Phân loại hình 2/3").props.onClick();q.render();
  assert.equal(q.store.get("optimat-review").pi,1);
  assert.equal(q.dialog(),undefined);assert.equal(q.calls.length,0);
  assert.equal(q.store.get("optimat-review").states[1].height_mm,0);
  const scope=q.find(n=>n.type==="select" && n.props.value==="" && n.props.onChange);
  scope.props.onChange({target:{value:"count"}});q.render();
  assert.ok(q.button("Nhập chiều cao tầng"));assert.equal(q.dialog(),undefined);assert.equal(q.calls.length,0);
  q.find(n=>n.type==="ChangeInput"&&n.props.step===0.05).props.onCommit({value:"3.6"});q.render();
  const first=q.open();const duplicate=q.dialog().props.send();q.render();
  assert.equal(q.dialog().props.busy,true);assert.equal(q.calls.length,1);assert.equal(q.calls[0].body.plan,"Tầng 2");
  q.respond(0,71);await Promise.all([first,duplicate]);q.render();
  q.find(n=>n.type==="ConfirmedDialog").props.onNext();q.render();assert.equal(q.store.get("optimat-review").pi,0);
  const last=q.open();q.fail(true);q.respond(1,72);await last;q.render();
  assert.ok(q.button("Thử lưu phiên và tiếp tục"));assert.deepEqual(q.navigations,[]);
  assert.equal(q.store.get("optimat-review").confirmed[0],undefined);
  assert.deepEqual(q.store.get("optimat-confirmed").map(p=>p.takeoff_id),[71]);
  q.fail(false);q.button("Thử lưu phiên và tiếp tục").props.onClick();q.render();
  assert.equal(q.calls.length,2);assert.deepEqual(q.navigations,["/phan-tho"]);
  assert.deepEqual(q.store.get("optimat-confirmed").map(p=>p.takeoff_id).sort(),[71,72]);
  assert.equal(q.store.get("optimat-review").states[2].scope,"reference");
  const stale=session(["count"],[3300]);const waiting=stale.open();
  stale.listeners.storage({key:"optimat-project-uid"});assert.ok(stale.calls[0].signal.aborted);
  stale.respond(0,99);await waiting;stale.render();assert.deepEqual(stale.navigations,[]);assert.equal(stale.store.get("optimat-confirmed",[]).length,0);
  const error=session(["count"],[3300]);const rejected=error.open();error.respond(0,0,false);await rejected;error.render();
  assert.ok(error.find(n=>n.type==="Msg"&&n.props.title.includes("Chưa nhận")));assert.equal(error.dialog(),undefined);
  const simple=session(["count","reference"],[3300,0]);const success=simple.open();simple.respond(0,73);await success;simple.render();
  assert.deepEqual(simple.navigations,["/phan-tho"]);assert.equal(simple.calls.length,1);
  // Cùng tab: thay context không phát StorageEvent. Body đã được server lưu nhưng chưa ghi vào trình duyệt.
  for (const [change,from] of [["id","retry"],["uid","header"],["drawing","header"],["sameDrawingEdit","retry"],["edit","retry"],["plan","retry"]]) {
    const tab=session(["count","reference"],[3300,0]); const wait=tab.open();tab.fail(true);tab.respond(0,95);await wait;tab.render();
    const retry=tab.button(from==="header"?"Tiếp tục từ bản đã xác nhận":"Thử lưu phiên và tiếp tục").props.onClick;
    if (change==="id") tab.store.set("optimat-project","75");
    if (change==="uid") tab.store.set("optimat-project-uid","uid-khac");
    if (change==="drawing" || change==="sameDrawingEdit") {
      const snap=tab.store.get("optimat-review");
      if (change==="drawing") snap.drawingId="new-drawing"; else snap.states[0].height_mm=4200;
      tab.store.set("optimat-review",snap);
    }
    if (change==="edit") tab.find(n=>n.type==="ChangeInput"&&n.props.step===0.05).props.onCommit({value:"4.2"});
    if (change==="plan") tab.find(n=>n.type==="select"&&n.props.value==="0").props.onChange({target:{value:"1"}});
    tab.fail(false);tab.render();
    const before=JSON.stringify(tab.store.get("optimat-review"));retry();tab.render();
    assert.equal(tab.calls.length,1,change+": không POST lại");
    assert.equal(tab.navigations.length,0,change+": không chuyển trang bằng bản cũ");
    assert.ok(!tab.store.get("optimat-confirmed",[]).some(p=>p.takeoff_id===95),change+": không xuất bản thu cũ");
    assert.equal(JSON.stringify(tab.store.get("optimat-review")),before,change+": không ghi đè phiên hiện tại");
  }
  const multi=session(["count","count"],[3300,3600]);
  const firstFloor=multi.open();multi.respond(0,101);await firstFloor;multi.render();
  multi.find(n=>n.type==="ConfirmedDialog").props.onNext();multi.render();
  multi.find(n=>n.type==="ChangeInput"&&n.props.step===0.05).props.onCommit({value:"4.2"});multi.render();
  multi.find(n=>n.type==="select"&&n.props.value==="1").props.onChange({target:{value:"0"}});multi.render();
  const writes=multi.publications();
  multi.button("Tiếp tục từ bản đã xác nhận").props.onClick();multi.render();
  assert.ok(multi.find(n=>n.type==="ConfirmedDialog"));assert.equal(multi.publications(),writes);assert.equal(multi.calls.length,1);
  multi.find(n=>n.type==="ConfirmedDialog").props.onNext();multi.render();
  const resumed=session(["count","count"],[3300,3600],0,multi.values);
  const secondFloor=resumed.open();assert.equal(resumed.calls[0].body.height_mm,4200);
  resumed.respond(0,102);await secondFloor;resumed.render();
  assert.deepEqual(resumed.navigations,["/phan-tho"]);assert.equal(resumed.calls.length,1);
  assert.deepEqual(resumed.store.get("optimat-confirmed").map(p=>p.takeoff_id).sort(),[101,102]);

  const named=["Mặt bằng trệt","Tầng 1 - bản đối chiếu","Lầu 1","Tầng 3"];
  const t=session(["count","reference","count",null],[3350,3350,3300,3200],0,undefined,{roughOnly:true},named,[[],[],["Chưa rõ cửa D1"],[]]);
  const {floors,model}=t;
  const flagged=session(["count",null,"count",null],[3350,3350,3300,3200],0,undefined,{roughOnly:true},named,[[],[],["Chưa rõ cửa D1"],[]]);
  const command=flagged.find(n=>n.type==="button"&&n.props.children==="Chỉ tầng cần kiểm tra",flagged.controls());
  command.props.onClick();flagged.render();assert.deepEqual(Array.from(flagged.picker().selected),[0,1,2]);
  const labels=flagged.controls();
  assert.equal(flagged.find(n=>n.type==="button"&&Array.isArray(n.props.children)&&n.props.children.includes(" tầng đã chọn"),labels).props.children[1],2);
  const absent=session([null,null,null],[3000,3100,3200],0,undefined,{roughOnly:true});
  assert.equal(absent.floors.floorGroups(absent.data.plans,absent.states).filter(g=>g.reasons.length).length,0);
  flagged.fail(true);flagged.apply();flagged.render();
  assert.equal(flagged.store.get("optimat-review").reviewScope,undefined);assert.equal(flagged.navigations.length,0);
  flagged.fail(false);flagged.apply();assert.deepEqual(flagged.store.get("optimat-review").reviewScope,[0,1,2]);
  assert.equal(floors.floorKey("Lầu 1"),floors.floorKey("Tầng 2"));assert.equal(floors.floorKey("Tầng 2–3"),null);
  assert.equal(floors.floorKey("Tầng trệt và lầu 1"),null);
  const bad={...t.states,1:{...t.states[1],scope:"count"}};
  assert.equal(floors.scopeConflict(t.data.plans,bad,[0,1]),1);
  assert.throws(()=>model.roughRequest(t.data,bad,{},25,null,{},[0,1]),/mỗi tầng/);
  assert.deepEqual(Array.from(floors.floorGroups(t.data.plans,bad)).filter(g=>g.reasons.length).map(g=>g.key),["T1","T2"]);
  // Các hình khác dù chưa phân loại không chặn tập con. Checkbox chỉ chọn để kiểm.
  t.choose([]); assert.equal(t.find(n=>n.type==="button" && n.props.disabled===true,t.controls()).props.disabled,true);
  t.apply();assert.equal(t.navigations.length,0);
  t.choose([0,1,2]);t.apply();assert.deepEqual(t.navigations,["/do-boc"]);assert.deepEqual(t.store.get("optimat-review").reviewScope,[0,1,2]);
  const v=session(["count","reference","count",null],[3350,3350,3300,3200],0,t.values,{},named);
  const g=v.open();v.respond(0,101);await g;v.render();v.find(n=>n.type==="ConfirmedDialog").props.onNext();v.render();
  assert.equal(v.store.get("optimat-review").pi,2);const g2=v.open();v.respond(1,102);await g2;v.render();
  assert.deepEqual(v.navigations,["/phan-tho"]);const saved=v.store.get("optimat-review");assert.equal(saved.states[3].scope,null);assert.equal(saved.confirmed[3],undefined);
  const req=model.roughRequest(t.data,t.states,{},25,{foundations:[{x:1}],structural_beams:{outside:[]}}, {},[0,1,2]);
  assert.deepEqual(Array.from(req.plans,p=>p.name),[named[0],named[2]]);assert.equal(req.structural_beams,undefined);assert.equal(req.params.foundations,undefined);
  const rough=session(["count","reference","count",null],[3350,3350,3300,3200],2,v.values,{roughOnly:true},named);
  const prior={file:saved.data.file,projectUid:saved.projectUid,drawingId:saved.drawingId,reviewId:"prior",reviewScope:[0,1,2],result:{works:[]}};
  rough.store.set("optimat-rough",prior);rough.store.set("optimat-work-review",{reviewId:"prior",checked:[0]});
  rough.choose([2]);rough.apply();assert.equal(rough.store.get("optimat-rough"),null);assert.equal(rough.store.get("optimat-review").confirmed[0].takeoff_id,101);
  rough.choose([0,1,2]);rough.apply();assert.equal(rough.store.get("optimat-rough").reviewId,"prior");assert.deepEqual(rough.store.get("optimat-work-review").checked,[0]);
  console.log("PASS phạm vi: nhóm trệt/tầng 1, lọc cảnh báo 2/3, 0 tầng, kiểm 2 tầng tại bước 3, giữ tầng ngoài, loại bản sao, khôi phục kết quả/biên nhận sau đổi nhóm.");

  console.log("PASS: xác nhận tuần tự, quota/retry, HTTP lỗi, không POST/ghi lại; chặn 6 ca đổi ngữ cảnh cùng tab; sửa tầng khác, mở lại và hoàn tất.");
})().catch(e=>{console.error(e);process.exitCode=1;});
