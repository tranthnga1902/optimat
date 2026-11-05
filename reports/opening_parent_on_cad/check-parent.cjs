const assert=require("node:assert/strict"), fs=require("node:fs"), path=require("node:path"), vm=require("node:vm");
const pkg=path.resolve(__dirname,"../../frontend/node_modules"),ts=require(path.join(pkg,"typescript"));
const file=path.join(process.argv[2],"src/app/(user)/do-boc/model.ts"),exportsOfModel={};
vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,"utf8"),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,{exports:exportsOfModel,require:()=>({})});
const {compute,missingWallOpenings,roughRequest,payload}=exportsOfModel;
const wall=(id,cls,masonry=true,keep=true)=>({id,cls,masonry,keep,role:"partition",x1:0,y1:0,x2:2000,y2:0});
const walls=[wall("W1","110"),wall("W2","220"),wall("C1","220",false),wall("C-off","220",false,false),wall("W-off","220",true,false)];
const opening=(id,parent,w,h,keep=true)=>({id,wall:parent,w,h,keep,kind:"door",src:"auto"});
const retained=[opening("A","C1",900,1800),opening("B","C1",null,1800),opening("C","C1",900,null),opening("D","C1",null,null)];
const states=o=>({height_mm:3000,scope:"count",length_rule:"tim",walls,openings:o});
const oneGroupWithGap=opening("M1","W1",null,1700),complete=opening("M2","W2",1000,1000);
const clean=compute(states([...retained,complete]));
assert.equal(clean.total,11,"Lỗ của tường ngoài khối xây không được khóa tổng khối xây");
assert.deepEqual(Array.from(clean.pending),[]);assert.deepEqual(Array.from(clean.pendingWalls),[]);
const first=states([...retained,oneGroupWithGap,complete]),second=states([complete]);
const a=compute(first);assert.equal(a.total,null);assert.equal(a.known,5);assert.equal(a.groups.find(g=>g.cls==="110").net,null);assert.equal(a.groups.find(g=>g.cls==="220").net,5);
assert.deepEqual(Array.from(a.pending,o=>o.id),["M1"]);assert.deepEqual(Array.from(a.pendingWalls),["W1"]);
const data={file:"fixture.dxf",plans:["Tầng 1","Tầng 2"].map(name=>({plan:{name},walls,openings:[],size:[2000,1000]})),materials:[],families:[]};
const plans={0:{cols:[],is_ground:true},1:{cols:[],is_ground:false}};
const request=roughRequest(data,{0:first,1:second},plans,23,null,{});
const trace=o=>({id:o.id,wall:o.wall,w:o.w,h:o.h,keep:o.keep});
for(const body of [request.plans[0],payload(data,data.plans[0],first,23)]){
  assert.deepEqual(Array.from(body.openings,trace),first.openings.map(trace));
}
assert.deepEqual(Array.from(missingWallOpenings(request)),["Tầng 1 · M1"]);
for(const parent of ["không có","C-off","W-off"]){
  const s=states([...retained,opening("X",parent,950,1800)]),c=compute(s);
  assert.equal(c.total,null);assert.equal(c.known,0);assert.ok(c.groups.every(g=>g.net===null));assert.equal(compute(second).total,11);
  const r=roughRequest(data,{0:s,1:second},plans,null,null,{});
  assert.deepEqual(Array.from(missingWallOpenings(r)),["Tầng 1 · X"]);
}
const ignored=states([opening("bỏ","C-off",null,null,false),complete]);assert.equal(compute(ignored).total,11);
console.log("PASS: cha xây, cha ngoài khối xây đang giữ (đủ/thiếu rộng/cao), cha mất/đã bỏ, lỗ bỏ, hai tầng độc lập. Confirm và rough giữ nguyên ID/cha/kích thước/keep.");
