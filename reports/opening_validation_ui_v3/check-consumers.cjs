const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");
const ts=require(path.resolve(__dirname,"../../frontend/node_modules/typescript"));
const source=process.argv[2],mod={},postCalls=[],effects=[];
const jsx=(type,props)=>({type,props}), refs={};
const state={req:{plans:[{name:"Lầu 2",walls:[{id:"W1",masonry:true,keep:true}],openings:[{id:"N1",wall:"W1",w:null,h:1900,keep:true}]}]}};
const groups=[{wall_type:"110",net_area_m2:12.34}];
const work={file:"sample",request:state.req,materialRevision:"M",result:{wall_groups:groups,wall_group_issues:[],plan_scope_confirmed:true,materials:[]}};
const known={file:"sample",plan:"Lầu 2",complete:false,groups};
Object.assign(mod,{react:{useState:init=>[typeof init==="function"?init():init,()=>{}],useRef:v=>({current:v}),useMemo:f=>f(),useEffect:f=>effects.push(f)},
 "react/jsx-runtime":{jsx,jsxs:jsx,Fragment:"Fragment"},"next/link":"Link","@/components/ui":new Proxy({},{get:(_,k)=>k}),
 "@/lib/api":{post:async(p)=>{postCalls.push(p);return []},api:async()=>({wall_systems:[]}),nf:Number,money:String},
 "@/lib/reference":{useReference:()=>({ref:null})},"@/lib/store":{useStored:(k,d)=>k==="optimat-confirmed"?[known]:d,store:{get:(_,d)=>d,set(){}}},
 "@/lib/purchase-session":{usePurchaseSession:()=>({work,reviewed:work,receipt:{},ready:true,draftKey:"x",key:"x"}),currentPurchaseKey:()=>"x"},"./Proposal":{Proposal:"Proposal"}});
function load(k){const src=fs.readFileSync(path.join(source,"src/app/(user)",k),"utf8"),exports={};const js=ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;vm.runInNewContext(js,{require:n=>mod[n]||{},exports});return exports}
mod["../do-boc/model"]=load("do-boc/model.ts");mod["../do-boc/KnownWallQuantities"]=load("do-boc/KnownWallQuantities.tsx");
function collect(t){if(t==null||typeof t==="boolean")return "";if(Array.isArray(t))return t.map(collect).join(" ");if(typeof t!=="object")return String(t);if(typeof t.type==="function")return collect(t.type(t.props));return collect(t.props?.children);}
const bill=load("vat-lieu/bill.tsx").Bill, optimize=load("toi-uu/optimize.tsx").Optimize;
const price=collect(bill());for(const effect of effects.splice(0))effect();
assert.match(price,/Lầu 2/);assert.match(price,/12,34/);assert.match(price,/toàn mặt bằng chưa đủ/);assert.deepEqual(postCalls,[]);
const result=collect(optimize());assert.match(result,/Lầu 2/);assert.match(result,/12,34/);assert.match(result,/Chưa thể tối ưu/);assert.doesNotMatch(result,/Chạy tối ưu/);assert.deepEqual(postCalls,[]);
state.req.plans[0].openings[0].w=800;known.complete=true;
bill();for(const effect of effects.splice(0))effect();assert.ok(postCalls.includes("/api/price/bill"));
console.log("PASS: giá và tối ưu hiện nhóm đủ 12,34 m² riêng, chặn gửi nhóm như toàn công trình; đường tra giá mở lại sau khi đủ dữ liệu.");
