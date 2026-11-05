// Chạy các handler thật của Review với nhiều mặt bằng, API hoãn phản hồi và bộ nhớ có thể đầy.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require(path.resolve(__dirname,"../../frontend/node_modules/typescript"));
const frontend = process.env.CONFIRM_TEST_FRONTEND || path.resolve(__dirname, "..");
const dependencies = process.env.CONFIRM_TEST_BASE || frontend;
const folder = "src/app/(user)/do-boc/";

function session(scopes, heights, active = 0, savedValues, boxes = []) {
  const fits=[];
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
    "./viewport":{useViewport:()=>({svgRef:{},scaleRef:{},vbRef:{current:{w:1}},movedRef:{},fitBox:(...args)=>fits.push(["box",...args]),fitSize:value=>fits.push(["size",...value])})}};
  function load(file) {
    const edited=path.join(frontend,file);
    const text=fs.readFileSync(fs.existsSync(edited)?edited:path.join(dependencies,file),"utf8");
    const js=ts.transpileModule(text,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;
    const exports={}; vm.runInNewContext(js,{...globals,exports,require:n=>modules[n]||placeholder},{filename:file}); return exports;
  }
  const model=modules["./model"]=load(folder+"model.ts");
  modules["./paper-scale"]=load(folder+"paper-scale.ts");
  modules["@/lib/review-session"]=load("src/lib/review-session.ts");
  modules["./Board"]=load(folder+"Board.tsx");
  const component=load(folder+"Review.tsx").Review;
  const plans=scopes.map((s,i)=>({plan:{name:"Tầng "+(i+1)},display_bbox:boxes[i],height_mm:heights[i],walls:[],openings:[],size:[100,100],layers:[],segs:[]}));
  const data={file:"kiem-tra.dxf",plans,overview:{cad:"test",size:[501,601],display_bbox:boxes[2]},materials:[],families:[]};
  const states=Object.fromEntries(plans.map((p,i)=>[i,{...model.initState(p),scope:scopes[i]}]));
  store.set("optimat-project-uid","qa");store.set("optimat-project","25");store.set("optimat-project-name","Kiểm thử");
  store.set("optimat-project-info",{name:"Kiểm thử"});
  store.set("optimat-review",{projectUid:"qa",drawingId:"drawing",data,states,confirmed:{},planP:{},pi:active});
  if (savedValues) for (const [key,value] of savedValues) values.set(key,value);
  function render(){cursor=0;effects=[];tree=component({});for(const fn of effects)fn();}
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
  return {fits,render,find,button,calls,store,respond,navigations,listeners,values,publications:()=>publications,
    fail:v=>{failLocal=v;}, dialog:()=>find(n=>n.type==="ConfirmDialog"),
    open:()=>{button("Xác nhận kích thước, khối lượng").props.onClick();render();return find(n=>n.type==="ConfirmDialog").props.send();}};
}


const boxes=[[-30,25,70,125],[20,-80,40,40],[-32,-98,100,173]];
const s=session(["count","count"],[3000,3400],0,undefined,boxes);
assert.deepEqual(s.fits.at(-1),["box",...boxes[0],0.03,true]);
const choose=(t,from,to)=>{t.find(n=>n.type==="select"&&n.props.value===String(from)).props.onChange({target:{value:String(to)}});t.render()};
choose(s,0,1);assert.deepEqual(s.fits.at(-1),["box",...boxes[1],0.03,true]);
choose(s,1,-1);assert.deepEqual(s.fits.at(-1),["box",...boxes[2],0.03,true]);
const fallback=session(["count"],[3300],0,undefined,[]);assert.deepEqual(fallback.fits.at(-1),["size",100,100]);
choose(fallback,0,-1);assert.deepEqual(fallback.fits.at(-1),["size",501,601]);
console.log("PASS: khôi phục, mở mặt bằng và tổng quan dùng fitBox theo display_bbox; dữ liệu cũ dùng fitSize.");
