const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const deps = path.resolve(__dirname, "../../frontend/node_modules");
const ts = require(path.join(deps,"typescript"));
const dir = process.argv[2], port = process.argv[3];
const calls = [], hooks = [];
let cursor = 0, tag = 0;
const react = {
  useState(initial) {
    const at = cursor++;
    if (!(at in hooks)) hooks[at] = typeof initial === "function" ? initial() : initial;
    return [hooks[at],next=>{ hooks[at] = typeof next === "function" ? next(hooks[at]) : next; }];
  },
  useRef(value) { return react.useState(()=>({current:value}))[0]; }, useEffect() {},
};
const jsx = (type,props)=>({type,props});
const modules = {react,"react/jsx-runtime":{jsx,jsxs:jsx},"next/navigation":{useRouter:()=>({})},
  "@/components/ProjectFilesPanel":{ProjectFilesPanel:"Panel"},"@/lib/project-records":{projectPath:()=>"/test",projectResponse:async(url,options)=>{
    const b=options.body; calls.push([b.get("file").name,b.get("role")]);await Promise.resolve();
  }}};
const source=fs.readFileSync(path.join(dir,"src/app/(user)/du-an-cua-toi/ProjectDossier.tsx"),"utf8");
const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;
const entry={};vm.runInNewContext(code,{require:name=>modules[name]||{},exports:entry,FormData,AbortController,crypto:{randomUUID:()=>"item-"+(++tag)}});
const props={project:{project_id:1},draft:{},profile:{version:1,payload:{selected_revisions:[]}},info:{},sources:[],getUid:()=>"test"};
let tree;
const render=()=>{cursor=0;tree=entry.ProjectDossier(props).props.uploadControls;};
function all(test,n=tree){
 if(Array.isArray(n))return n.flatMap(x=>all(test,x));
 if(!n?.props)return [];
 return [...(test(n)?[n]:[]),...all(test,n.props.children ?? null)];
}
const upload=()=>all(n=>n.type==="button" && ["Tải bản vẽ gốc","Tải các tệp đang chờ"].includes(n.props.children))[0];
const role=(filename)=>all(n=>n.type==="select"&&(port==="3002"?n.props["aria-label"]==="Vai trò của "+filename:all(j=>j.type==="option"&&j.props.value==="KC",n).length>0))[0];
const file=(name)=>new File(["fixture"],name);
function selectFiles(names){all(n=>n.type==="input"&&n.props.type==="file")[0].props.onChange({currentTarget:{files:names.map(file),value:"fixture"}});render();}
function setRole(name,value){role(name).props.onChange({target:{value}});render();}
(async()=>{
 render();selectFiles(["ket-cau.DWG",...(port==="3002"?["mat-bang.dxf"]:[])]);
 assert.equal(role("ket-cau.DWG").props.value,"");assert.equal(upload().props.disabled,true);assert.deepEqual(calls,[]);
 assert.deepEqual(all(n=>n.type==="option",role("ket-cau.DWG")).map(n=>n.props.value),["","KT","KC","THAM_KHAO"]);
 upload().props.onClick();render();assert.deepEqual(calls,[]);
 setRole("ket-cau.DWG","KC");
 if(port==="3002"){
   assert.equal(role("mat-bang.dxf").props.value,"");assert.equal(upload().props.disabled,true);
   setRole("mat-bang.dxf","KT");
 }
 assert.equal(upload().props.disabled,false);upload().props.onClick();await new Promise(setImmediate);render();
 assert.deepEqual(calls,port==="3002"?[["ket-cau.DWG","KC"],["mat-bang.dxf","KT"]]:[["ket-cau.DWG","KC"]]);
 selectFiles(["tham-khao.dxf"]);assert.equal(role("tham-khao.dxf").props.value,"");assert.equal(upload().props.disabled,true);
 setRole("tham-khao.dxf","THAM_KHAO");upload().props.onClick();await new Promise(setImmediate);
 assert.deepEqual(calls.at(-1),["tham-khao.dxf","THAM_KHAO"]);
 if(port==="3002"){selectFiles(["khoi-luong.xlsx","ghi-chu.pdf"]);assert.equal(role("khoi-luong.xlsx").props.value,"TIEN_LUONG");assert.equal(role("ghi-chu.pdf").props.value,"HO_SO");}
 console.log("PASS: CAD mới chưa có vai trò, chọn tệp chưa POST, cả UI và handler chặn vai trò trống, POST giữ đúng vai trò từng tệp, tệp tiếp theo chờ chọn lại.");
})().catch(e=>{console.error(e);process.exitCode=1;});
