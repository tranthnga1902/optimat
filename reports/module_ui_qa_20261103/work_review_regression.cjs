const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "../..");
const ts = require(path.join(root, "frontend/node_modules/typescript"));
const data = new Map();
let fail;
const storage = { getItem: k => data.get(k) ?? null, removeItem: k => data.delete(k),
  setItem(k,v) { if (k === fail) { fail = null; throw new Error("quota"); } data.set(k,v); } };
const store = {get(k,d) {return data.has(k) ? JSON.parse(data.get(k)) : d;}};
function load(name) {
  const source = fs.readFileSync(path.join(root, "frontend/src/lib", name+".ts"), "utf8");
  const js = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  const sandbox = {exports:{}, require:id=>id.endsWith("work-review")?lib:id.endsWith("advice-scope")?scope:{store}, localStorage:storage, window:{dispatchEvent(){}}, CustomEvent:class{},
    DOMException, crypto:require("node:crypto").webcrypto};
  vm.runInNewContext(js,sandbox); return sandbox.exports;
}
const lib = load("work-review"), scope = load("../app/(user)/dieu-chinh/advice-scope"), session = load("review-session"), projects = load("projects");
const v = {projectUid:"A",drawingId:"D",file:"A.dxf",reviewId:"R"};
const measured = {code:"XAY",plan:"T1",element:"W1",unit:"m3",quantity:2,status:"B",missing:[],dimensions:[{label:"W1",width_m:0.2}]};
const missing = {...measured,element:"W2",quantity:null,status:"D",missing:["Chieu cao"]};
const result = {works:[measured,missing],plan_scope_confirmed:true};
const receipt = {...v,checked:[0],partial:true,confirmed:true};
const work = {...v,result,request:{plans:[]},materialRevision:"M"};
assert.equal(lib.approvedWork(work,receipt,v),true);
for(const wrong of [{...receipt,partial:false},{...receipt,checked:[]},{...receipt,confirmed:false},{...receipt,reviewId:"old"},{...receipt,projectUid:"B"},{file:"A.dxf",result}])
  assert.equal(lib.approvedWork(work,wrong,v),false);
assert.equal(lib.approvedWork(work,receipt,{...v,drawingId:"other"}),false);
const changed = { ...result,works:[{...missing,quantity:1,missing:[],status:"C"},measured] };
assert.equal(lib.geometryChanged(result,changed),true);
assert.deepEqual(Array.from(lib.unchangedCheckedRows(result,changed,receipt)),[1]);
assert.equal(lib.geometryChanged(result,{...result,works:[{...measured,formula:"new",wall_system_id:"B"},missing]}),false);
assert.equal(lib.geometryChanged(result,{...result,works:[{...measured,dimensions:[{label:"W1",width_m:0.11}]},missing]}),true);
const current = {...v,materialRevision:"M",data:{file:"A.dxf",plans:[{}]},states:{0:{scope:"count"}},confirmed:{0:{file:"A.dxf"}}};
data.set("optimat-review","old"); data.set("optimat-work-review","old");fail="optimat-rough";
assert.throws(()=>session.saveMaterialSession(current,[],{},work,receipt),/quota/);assert.deepEqual([...data],[["optimat-review","old"],["optimat-work-review","old"]]);
session.saveMaterialSession(current,[],{},work,receipt);
data.set("optimat-project-info","{}");data.set("optimat-project-uid",JSON.stringify("A"));
projects.switchProject({id:"B",name:"B",values:{"optimat-project-info":"{}"}});
assert.equal(data.has("optimat-work-review"),false);
const archive = store.get("optimat-project-history",[])[0];projects.switchProject(archive);
assert.equal(projects.projectUid(),"A");assert.equal(store.get("optimat-rough",null).reviewId,"R");assert.equal(store.get("optimat-work-review",null).checked[0],0);
const material={material_id:"XM01",name:"Xi măng",raw_class:"xi_mang",unit:"kg",quantity:null,quantity_with_waste:null,complete:false,missing:["Thiếu định mức"],uses:[]};
const proposalWork={...work,result:{...result,materials:[material]}};
data.set("optimat-rough",JSON.stringify(proposalWork));
const scoped={lineId:"m0",materialId:"XM02",originalId:"XM01",originalName:"Xi măng",scope:"Tầng 1",rowIndex:0,reviewId:"R",disposition:"proposed"};
data.set("optimat-material-selection",JSON.stringify({...v,materialRevision:"M",choices:[scoped]}));
const plan=session.saveReviewedProposal(proposalWork,[]);
assert.equal(plan.status,"conditional");assert.equal(plan.unresolved.length,1);
assert.equal(store.get("optimat-proposal-A",null).scopedChoices[0].materialId,"XM02");
assert.equal(store.get("optimat-material-selection",null).choices[0].rowIndex,0);
assert.equal(store.get("optimat-materials-ready",true),false);
assert.throws(()=>session.saveReviewedProposal(proposalWork,[{...scoped}]),/cấu kiện/);
assert.throws(()=>session.saveReviewedProposal({...proposalWork,reviewId:"old"},[]),/đổi/);
const previous=[...data];fail="optimat-proposal-A";
assert.throws(()=>session.saveReviewedProposal(proposalWork,[]),/quota/);assert.deepEqual([...data],previous);
console.log("PASS: revision, old snapshot, partial scope, numeric geometry, row identity, atomic quota and history A/B/A");
