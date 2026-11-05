// Kiểm tra phạm vi tư vấn trên hai dòng xây tường cùng mã và tầng.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { createRequire, Module } = require("node:module");
const frontend = path.resolve(__dirname, "../../frontend");
const ts = createRequire(path.join(frontend, "package.json"))("typescript");
const file = path.join(frontend, "src/app/(user)/do-boc/row-advisory.ts");
const compiled = new Module(file, module);
compiled._compile(ts.transpileModule(fs.readFileSync(file, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, file);
const { uncheckedRowAdvice } = compiled.exports;

const partition = { code: "XAY", name: "Xây tường", plan: "Tầng 1", element: "tường 110 ngăn",
  dimensions: [{ label: "W5" }], wall_system_id: "W-AAC01-100", masonry_geometry: { wall_type: "110", role: "partition" },
  unit: "m³", missing: [], quantity: 1.505, status: "C" };
const facade = { ...partition, element: "tường bao", wall_system_id: "W-GN", masonry_geometry: { wall_type: "220", role: "envelope" } };
const legacy = { work: "XAY", plan: "Tầng 1", quantity: 11, via: "cả nhóm" };
const line = (id, uses) => ({ material_id: id, name: id, unit: "m³", raw_class: "gach", uses, quantity: 100, complete: true });
const snapshot = { projectUid: "p", drawingId: "d", reviewId: "r", file: "sample.dxf", request: { project_id: 23 },
  result: { works: [partition, facade], materials: [line("AAC01",[legacy]), line("GN01",[legacy]),
    line("VU04",[{ ...legacy, rowIndex: 0, quantity: 0 }]), line("WRONG",[{ ...legacy, rowIndex: 0, work: "TRAT" }])] } };
const confirmed = [{ file: snapshot.file, plan: partition.plan, takeoff_id: 26, bill: [
  { material_id: "AAC01", wall_type: "110", role: "partition", wall_system_id: "W-AAC01-100" },
  { material_id: "GN01", wall_type: "220", role: "envelope", wall_system_id: "W-GN" }] }];
const before = JSON.stringify([snapshot, confirmed]);
const answer = uncheckedRowAdvice(snapshot, 0, confirmed);
assert.deepEqual(answer.components, ["W5"]);
assert.deepEqual([answer.projectId, answer.confirmedId, answer.context.partial], [23, 26, true]);
assert.deepEqual(answer.context.works.map(w => [w.rowIndex,w.checked,w.quantity,w.status]), [[0,false,1.505,"C"]]);
assert.deepEqual(answer.context.materials.map(m => [m.material_id,m.quantity,m.quantity_with_waste,m.complete]),
  [["AAC01",null,null,false], ["VU04",0,null,false]]);
assert.deepEqual(answer.context.materials[0].uses, []);
assert.equal(JSON.stringify([snapshot, confirmed]), before);
assert.deepEqual(uncheckedRowAdvice(snapshot, 0, [{...confirmed[0],file:"other.dxf"}]).context.materials.map(m=>m.material_id), ["VU04"]);
assert.deepEqual(uncheckedRowAdvice(snapshot, 0, [...confirmed,...confirmed]).context.materials.map(m=>m.material_id), ["VU04"]);
assert.equal(uncheckedRowAdvice(snapshot, 999, confirmed), null);
console.log("PASS: một dòng chưa kiểm; phân biệt hai tường cùng mã; giữ 0, loại nguồn khác; không ghi dữ liệu.");
