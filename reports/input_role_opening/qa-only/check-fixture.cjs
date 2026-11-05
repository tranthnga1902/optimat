const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");
const deps=path.resolve(__dirname,"../../../frontend/node_modules"),req=n=>require(path.join(deps,n));
const React=req("react"),ts=req("typescript"),ssr=req("react-dom/server");
const directory=process.argv[2], dir="src/app/qa-input-roles/";
const wrappers=({children})=>React.createElement("div",null,children);
const capture=[], native={FormData,File,CustomEvent,window:{dispatchEvent:e=>capture.push(e.detail)}};
let mode=0,modeHook=true;
const modules={react:{...React,useState:init=>{
 if(modeHook){modeHook=false;return [mode,()=>{}];}
 return [typeof init==="function"?init():init,()=>{}];},useEffect(){}},
 "react/jsx-runtime":req("react/jsx-runtime"),"@/components/Sheet":{Sheet:()=>null},"@/components/ui":{Card:wrappers,Note:wrappers,Empty:wrappers},
 "./ProjectFilesPanel.module.css":{default:{}},
 "@/lib/project-records":{emptyProfile:()=>({version:0,payload:{selected_revisions:[]}})}};
function load(file){
 const src=fs.readFileSync(path.join(directory,file),"utf8"),exports={};
 vm.runInNewContext(ts.transpileModule(src,{compilerOptions:{jsx:ts.JsxEmit.ReactJSX,module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,
  {...native,exports,require:n=>{if(!(n in modules))throw Error(n);return modules[n];}});
 return exports;
}
const api=load(dir+"fixture-api.ts");
modules["@/components/ProjectFilesPanel"]=load("src/components/ProjectFilesPanel.tsx");
modules["./DossierFixture"]={ProjectDossier:()=>"Mẫu Dossier"};
const page=load(dir+"page.tsx").default;
const render=m=>{mode=m;modeHook=true;return ssr.renderToStaticMarkup(React.createElement(page));};
const blocked=html=>/<button[^>]*disabled[^>]*>Bắt đầu phân tích/.test(html);
(async()=>{
 for(const [m,disabled,note] of [[0,true,"Chọn phiên bản cần phân tích"],[1,false,"Chưa chọn bản kết cấu riêng"],[2,true,"cần một bản CAD kiến trúc"],
  [3,false,"Bản kết cấu được đọc riêng"],[4,true,"Chỉ chọn một phiên bản"],[5,true,"mã kiểm tra"],[6,true,"Chỉ chọn tệp CAD"]]){
   const html=render(m);assert.equal(blocked(html),disabled);assert.ok(html.includes(note),note);
 }
 assert.ok(render(7).includes("Mẫu Dossier"));
 const body=new FormData();body.set("file",new File(["x"],"mau.dxf"));body.set("role","KC");
 assert.deepEqual(Array.from(await api.projectResponse("/api/projects/701/files")),[]);
 await api.projectResponse("/api/projects/701/files",{method:"POST",body});assert.equal(JSON.stringify(capture),JSON.stringify([{name:"mau.dxf",role:"KC"}]));
 await assert.rejects(()=>api.projectResponse("/api/real"));assert.throws(()=>api.fixtureStorage.setItem("x","y"));assert.throws(()=>api.useRouter().push("/do-boc"));
 console.log("PASS: route QA render 7 ca panel thật, chuyển mẫu Dossier, shim chỉ ghi tên/vai trò vào RAM và chặn API ngoài, storage, điều hướng.");
})().catch(e=>{console.error(e);process.exitCode=1});
