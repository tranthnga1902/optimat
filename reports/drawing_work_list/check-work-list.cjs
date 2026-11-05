const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const pkg=path.resolve(__dirname,"../../frontend/node_modules"),ts=require(path.join(pkg,"typescript")),react=require(path.join(pkg,"react")),ssr=require(path.join(pkg,"react-dom/server"));
const dir=path.join(process.argv[2],"src/app/(user)/do-boc");
const source=fs.readFileSync(path.join(dir,"DrawingWorkList.tsx"),"utf8");
const out={};vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText,
  {exports:out,require:k=>k==="react"?react:require(path.join(pkg,k))});
const plans=[{plan:{name:"Trệt"},walls:[{masonry:true}],columns:[{}],stairs:[],found:{}},
 {plan:{name:"Lầu 1"},walls:[{masonry:true},{masonry:true}],stairs:[{}],found:{STAIR:["A"],SLAB:["SLAB-L1"]}}];
const render=props=>ssr.renderToStaticMarkup(react.createElement(out.DrawingWorkList,props));
const data={file:"fixture.dxf",plans};
const recognized=render({data,index:-1});assert.match(recognized,/Trệt/);assert.match(recognized,/Lầu 1/);assert.match(recognized,/2 đoạn tường/);
const single=render({data,index:1,states:{1:{scope:"reference",walls:[{masonry:true,keep:false},{masonry:true,keep:true}]}},structural:{file:"ket-cau.dxf",foundations:[{}]}});
assert.ok(!single.includes("Trệt"));assert.match(single,/1 đoạn tường/);assert.match(single,/Mặt bằng tham khảo/);assert.match(single,/Bê tông móng/);assert.match(single,/cầu thang/);assert.match(single,/SLAB-L1/);
assert.match(render({data:{file:"rỗng",plans:[],drawing_work_signals:{REBAR:["BH-01"]}},index:-1}),/BH-01/);
assert.match(render({data:{file:"rỗng",plans:[]},index:-1}),/Chưa có mặt bằng/);
const parent=fs.readFileSync(path.join(dir,"Review.tsx"),"utf8");
assert.ok(parent.indexOf("<Board ")<parent.indexOf("<DrawingWorkList "));
assert.match(parent,/!reading\.error && reading\.recognized && <DrawingWorkList data=\{reading\.recognized\} index=\{-1\}/);
assert.match(parent,/<DrawingWorkList data=\{data\} index=\{pi\} states=\{states\} params=\{planP\}/);
console.log("PASS: dưới Board, preview nhận diện, đúng mặt bằng và bản tham khảo, tường đã loại, nguồn KT/KC, hồ sơ không có mặt bằng.");
