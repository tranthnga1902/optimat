const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const repo = path.resolve(__dirname, "../..");
const ts = require(path.join(repo,"frontend/node_modules/typescript"));
const root = process.argv[2];
const filename = path.join(root, "src/app/(user)/do-boc/model.ts");
const exportsOfModel = {};
vm.runInNewContext(ts.transpileModule(fs.readFileSync(filename,"utf8"), {compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,
  { exports:exportsOfModel, require:()=>({}) }, {filename});
const {payload, roughRequest, validationMessage} = exportsOfModel;
const plans = ["Trệt","Lầu 1"].map(name=>({plan:{name},size:[1000,1000],walls:[],openings:[],layers:[],segs:[]}));
const openings = [{id:"O7",wall:"W3",w:null,h:2100,keep:true},{id:"O8",wall:"W4",w:900,h:null,keep:true},
  {id:"O9",wall:"W4",w:null,h:null,keep:false},{id:"O10",wall:"W5",w:800,h:1800,keep:true}].map(o=>({...o,src:"auto",kind:"door"}));
const data={file:"kiem.dxf",plans};
const states={0:{walls:[],scope:"reference",openings:[]},1:{walls:[],scope:"count",height_mm:3300,openings}};
const confirm=()=>payload(data,plans[1],states[1],23);
const rough=()=>roughRequest(data,states,{1:{cols:[],is_ground:false}},23,null,{});
const pick=l=>JSON.parse(JSON.stringify(l)).map(({id,wall,w,h,keep})=>({id,wall,w,h,keep}));
if (process.argv.includes("--before")) {
  const count=confirm().openings.length;
  assert.ok([2,4].includes(count));assert.equal(rough().plans[0].openings.length,4);
  assert.equal(typeof validationMessage,"undefined");
  console.log("BEFORE: confirm gửi "+count+"/4; rough gửi 4/4; lỗi 422 chưa chỉ mặt bằng và ID.");process.exit(0);
}
assert.deepStrictEqual(pick(confirm().openings),pick(openings));assert.deepStrictEqual(pick(rough().plans[0].openings),pick(openings));
const msg=validationMessage([0,2,0].map(i=>({loc:["body","plans",0,"openings",i,"w"],msg:"Input should be a valid number"})),rough(),"Lỗi");
assert.equal(msg,"Thiếu chiều rộng (mm) — Lầu 1 · lỗ O7 · tường W3, Lầu 1 · lỗ O9 · tường W4");
assert.match(validationMessage([{loc:["body","openings",1,"h"],msg:"bad"}],confirm(),"Lỗi"),/Thiếu chiều cao.*Lầu 1.*O8.*W4/);
assert.match(validationMessage([{loc:["body","plans",0,"walls",14,"x1"],msg:"invalid"}],rough(),"Lỗi"),/plans\.0\.walls\.14\.x1/);
for(const f of [confirm,rough]) for (const field of ["w","h"]) for (const v of [NaN,Infinity,-1,0,"abc",""]) {
 const prev=openings[0][field];openings[0][field]=v;assert.throws(f,/Lầu 1.*O7.*W3.*số dương hữu hạn/);openings[0][field]=prev;
}
console.log("PASS: hai request giữ 4 ID/parent/keep/nullable/known. 24 ca sai bị chặn trước JSON, loc 422 đúng hình và lỗ kể cả sau lọc, không lặp lý do.");
