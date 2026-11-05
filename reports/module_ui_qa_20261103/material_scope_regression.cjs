const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const ts=require("../../frontend/node_modules/typescript");
const code=ts.transpileModule(fs.readFileSync("frontend/src/app/(user)/dieu-chinh/advice-scope.ts","utf8"),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const box={exports:{}};vm.runInNewContext(code,box);const {adviceScope,carrySelections}=box.exports;
const cols=(element,q)=>({code:"COT",plan:"T1",element,name:"Cột",quantity:q,unit:"m³",status:"B",missing:[]});
const result={works:[cols("C1",2),cols("C2",3),{...cols("Đáy sàn",-2.25),code:"COP_PHA",unit:"m²"}],
  materials:[{material_id:"M1",name:"Cấp phối",unit:"m³",raw_class:"vua_be_tong",complete:true,quantity:5,quantity_with_waste:5.1,
    uses:[{work:"COT",plan:"T1",quantity:2,via:"Cấp phối C1"},{work:"COT",plan:"T1",quantity:3,via:"Cấp phối C2"}]}],intermediates:[]};
const work={reviewId:"r1",projectUid:"p",drawingId:"d",result}, receipt={checked:[0,1,2],partial:true};
const whole=adviceScope(work,receipt,null,"m");assert.equal(whole.works[2].quantity,-2.25);assert.equal(whole.materials[0].quantity,5);
const one=adviceScope(work,receipt,1,"m");assert.equal(one.works.length,1);assert.equal(one.materials[0].quantity,null);assert.equal(one.materials[0].quantity_with_waste,null);assert.equal(one.materials[0].complete,false);assert.equal(one.materials[0].sources.length,0);
assert.equal(adviceScope(work,{checked:[0]},null,"m").materials[0].quantity,null);
const selection={originalId:"M1",materialId:"M2",reviewId:"r1",lineId:"m0",rowIndex:0,scope:"C1",disposition:"proposed"};
const next={...work,reviewId:"r2",result:{...result,works:[result.works[1],result.works[0]],materials:[{material_id:"X"},result.materials[0]]}};
const [mapped]=carrySelections(work,next,[selection]);assert.equal(mapped.rowIndex,1);assert.equal(mapped.reviewId,"r2");assert.equal(mapped.lineId,"m1");assert.equal(mapped.disposition,"proposed");
console.log("PASS: phạm vi đã kiểm, không chia lượng gộp/hao hụt, giữ khoản trừ có dấu, giữ lựa chọn khi đổi thứ tự.");
