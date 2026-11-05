const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,"../.."), ts=require(path.join(root,"frontend/node_modules/typescript"));
for(const port of ["3001","3002"]){
 const filename=path.join(root,"reports/opening_parent_on_cad",port,"overlay/src/app/(user)/do-boc/model.ts");
 const compiled=ts.transpileModule(fs.readFileSync(filename,"utf8"),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}});
 const api={};vm.runInNewContext(compiled.outputText,{exports:api,require:()=>({})});
 const plan={plan:{name:"Mặt bằng mẫu"},walls:[],openings:[],size:[3000,2000],columns:[]};
 const data={file:"tong-hop-qa.dxf",plans:[plan]},state={...api.initState(plan),scope:"count",height_mm:3300};
 state.openings.push({id:"N5",wall:"W3",kind:"door",src:"manual",w:900,h:2100,x:0,y:-245.5,keep:true});
 const snapshot=JSON.parse(JSON.stringify({states:{0:state}}));
 const confirm=api.payload(data,plan,state,701).openings[0];
 const rough=api.roughRequest(data,{0:state},{0:{cols:[],is_ground:true}},701,null,{}).plans[0].openings[0];
 assert.deepEqual([snapshot.states[0].openings[0].x,snapshot.states[0].openings[0].y],[0,-245.5]);
 for(const dto of [confirm,rough]){
  assert.equal(dto.id,"N5"); assert.equal(dto.wall,"W3");
  assert.equal(Object.hasOwn(dto,"x"),false);assert.equal(Object.hasOwn(dto,"y"),false);
 }
 console.log(port+" · Dữ liệu tổng hợp: state JSON giữ (0,-245.5); cả confirm và rough chưa gửi x/y.");
}
