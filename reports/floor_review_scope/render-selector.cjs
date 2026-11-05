const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const r=__dirname, libs=path.resolve(r,"../../frontend/node_modules");
const ts=require(path.join(libs,"typescript")),React=require(path.join(libs,"react")),server=require(path.join(libs,"react-dom/server")),jsx=require(path.join(libs,"react/jsx-runtime"));
const dir=path.join(r,"3002/overlay/src/app/(user)/do-boc");
function load(file,modules) {
  const source=fs.readFileSync(path.join(dir,file),"utf8"), exports={};
  const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;
  vm.runInNewContext(js,{require:k=>modules[k],exports});return exports;
}
const {FloorSelector}=load("FloorSelector.tsx",{react:React,"react/jsx-runtime":jsx,"./floor-review":load("floor-review.ts",{})});
const plans=["Mặt bằng trệt","Tầng 1 (hình đối chiếu)","Mặt bằng lầu 1","Mặt bằng lầu 2"].map((name,i)=>({plan:{name},warnings:i===2?["D1 chưa có kích thước"]:[],openings:[],height_mm:3350}));
const html=server.renderToStaticMarkup(React.createElement(FloorSelector,{plans,states:{},selected:[0,1,2],disabled:false,onChange(){},onOpen(){}}));
const base=JSON.parse(fs.readFileSync(path.join(r,"base.json")))[3002].base,chunks=path.join(base,".next/static/chunks");
const css=fs.readdirSync(chunks).filter(f=>f.endsWith(".css")).map(f=>fs.readFileSync(path.join(chunks,f),"utf8")).join("\n");
fs.writeFileSync(path.join(r,"chon-tang-960.html"),'<!doctype html><html lang="vi"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\';style-src \'unsafe-inline\';img-src data:"><style>'+css+'</style><main class="p-5"><p class="text-muted">Mẫu kiểm thử giao diện · 960 px</p><h1>Kiểm tra công tác và khối lượng</h1>'+html+'</main></html>');
