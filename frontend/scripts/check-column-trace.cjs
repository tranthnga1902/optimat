// Kiểm đường truyền và phần hiển thị, không gọi API hay đọc bản vẽ thật.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const ts = require("typescript");
const react = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

function load(name) {
  const file = path.join(__dirname, "../src/app/(user)/do-boc", name);
  const loaded = new Module(file, module);
  loaded.paths = module.paths;
  loaded.require = id => id === "./paper-scale" ? load("paper-scale.ts") : Module.prototype.require.call(loaded,id);
  loaded._compile(ts.transpileModule(fs.readFileSync(file, "utf8"), {
    fileName: file, compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
  }).outputText, file);
  return loaded.exports;
}

const { roughRequest } = load("model.ts");
const { indexColumnWorks, ColumnTrace } = load("ColumnTrace.tsx");
const first = { instance_id: "seg-a", code: "C-8", grid_x: "7", grid_y: "G", floor_key: "T2",
  file: "k.dxf", sheet: "KC-8", layers: ["COLUMN"], handles: ["DA01"], evidence: ["DIM từ tờ KC-8"],
  matched_plan: "T2", matched_column_id: "local", mapping_evidence: "Hai lưới đã đối chiếu" };
const second = { ...first, instance_id: "seg-b", grid_y: "H", handles:["DB02"] };
const kt = {file_id:8, revision_id:20, role:"KT", sha256:"a".repeat(64)};
const planColumn = { id:"local", role:"ket_cau", x:0, y:0, b_mm:250, h_mm:260, keep:true, source:"signal" };
const request = roughRequest({file:"a.dxf",plans:[{plan:{name:"T2",level_m:0},source_revision:kt}]},
  {0:{scope:"count",height_mm:3000,walls:[],openings:[]}}, {0:{cols:[planColumn]}}, 8,
  {file:"k.dxf",structural_columns:[first,second]}, {});
assert.deepEqual(request.structural_columns,[first,second]);
assert.deepEqual(request.plans[0].columns,[planColumn]);
assert.equal(request.plans[0].level_m,0);
assert.deepEqual(request.plans[0].source_revision,kt);
const work = { basis:"structural_instance", code:"COT", plan:"T2", element:"C-8 [seg-a]", quantity:7,
  quantity_detail:{known_part_raw:"7.000",total_raw:null}, unit:"m³", missing:[] };
const snapshot = {request,result:{works:[work,{...work,element:"C-8 [seg-b]"},
  {...work,element:"C-8",basis:"manual"}],materials:[{name:"Bê tông từ dòng khác",material_id:"OTHER",
    unit:"m³",uses:[{work:"COT",plan:"T2",quantity:7}]}]}};
const columns = indexColumnWorks(snapshot);
assert.deepEqual(columns,[first,second,null]);
const draw = () => renderToStaticMarkup(react.createElement(ColumnTrace,{snapshot,selected:0,columns}));
const html = draw();
assert.match(html,/7\/G/); assert.match(html,/DA01/); assert.match(html,/mã phiên bản #20/);
assert.match(html,/Bê tông theo quy ước của bản tính: Chưa có/);
assert.doesNotMatch(html,/DB02|OTHER|7 m³/);
work.quantity_detail.total_raw = "0.123456";
assert.match(draw(),/0,123456 m³/);
snapshot.result.materials.push({name:"Vật tư có liên kết",material_id:"MAT",unit:"kg",
  uses:[{work:"COT",plan:"T2",rowIndex:0,quantity:0},{work:"COT",plan:"T2",rowIndex:1,quantity:12}]});
assert.match(draw(),/Lượng quy đổi: 0 kg/);
assert.doesNotMatch(draw(),/12 kg/);
work.missing = ["Thiếu cao độ riêng"];
snapshot.result.works[1].missing = ["Chỉ thiếu ở cột bên cạnh"];
snapshot.result.materials.push({name:"Vật tư chưa xác định mã",material_id:null,unit:"m³",missing:["Thiếu cao độ riêng","Chỉ thiếu ở cột bên cạnh"],
  uses:[{work:"COT",plan:"T2",rowIndex:0,quantity:null},{work:"COT",plan:"T2",rowIndex:1,quantity:99}]});
assert.match(draw(),/Vật tư chưa xác định mã/);
assert.match(draw(),/Cần bổ sung: Thiếu cao độ riêng/);
assert.doesNotMatch(draw(),/Chỉ thiếu ở cột bên cạnh|99 m³/);
assert.equal(indexColumnWorks({...snapshot,request:{...request,structural_columns:[first,{...first}]}})[0],null);
assert.deepEqual(indexColumnWorks({result:snapshot.result}),[null,null,null]);
const hash = "b".repeat(64);
first.evidence = ["Bê tông B30 theo ghi chú cấu kiện · tờ S-15, handle E7",
  "Đai Ø8 a180 theo mặt cắt X-X · tờ S-18, handle F8",
  "Hình dọc: vùng đai Ø8 a90 · tờ S-18, handle F9",
  `Tệp KC k.dxf; file_id=4; revision_id=9; sha256=${hash}`];
second.evidence = ["Cột khác dùng B45, Ø32"];
request.rebar = [
  {table:"Bảng cùng mã",row:1,element:"CỘT C8",element_code:"COT",mark:"A",dia_mm:16,revision_sha256:hash,weight_kg:999},
  {table:"Sai phiên bản",row:1,element:"C8",element_code:"COT",dia_mm:22,revision_sha256:"f".repeat(64)},
  {table:"Sai mã loại",row:1,element:"C80",element_code:"COT",dia_mm:22,revision_sha256:hash},
];
const sourced = draw();
for(const text of ["B30","tờ S-15, handle E7","Đai Ø8","tờ S-18, handle F8","Bảng cùng mã","Ø16 mm","chưa được phân bổ theo trục","Bê tông thương phẩm","trộn tại chỗ"]) assert.ok(sourced.includes(text), text);
assert.doesNotMatch(sourced,/B45|Ø32|Sai phiên bản|Sai mã loại|999/);
for (const text of ["Ø8 a180 theo mặt cắt", "vùng đai Ø8 a90", "Bước đai ghi trên mặt cắt áp dụng tại vị trí cắt", "(kg): chưa xác định"]) assert.ok(sourced.includes(text), text);
first.evidence = [];
const noEvidence = draw();
assert.doesNotMatch(noEvidence,/B30|Ø8|Ø16|Bảng cùng mã/);
console.log("PASS: giữ nguồn KT/KC, phân biệt hai cột cùng mã, giữ lượng thiếu và đúng độ chính xác từ bộ tính.");

// Đối chiếu fixture từ compute_rough của VN002 khi được truyền đường dẫn; tìm theo trục và tầng, không cố định số thứ tự dòng.
if (process.argv[2]) {
  const actual = JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
  const mapped = indexColumnWorks(actual);
  const indices = [];
  for (const axis of ["A","B"]) {
    const selected = mapped.findIndex((c,i)=>c?.grid_x==="4" && c.grid_y===axis && c.floor_key==="T2" && actual.result.works[i].code==="COT");
    assert.ok(selected>=0);
    const col = mapped[selected];
    const rows = mapped.flatMap((c,i)=>c===col?[i]:[]);
    assert.deepEqual(rows.map(i=>actual.result.works[i].code).sort(),["COP_PHA","COT"]);
    const view = renderToStaticMarkup(react.createElement(ColumnTrace,{snapshot:actual,selected,columns:mapped}));
    assert.ok(view.includes(col.instance_id));
    for (const term of ["Bê tông (chưa chọn mác)","Vật liệu cốp pha","mác bê tông","loại ván khuôn (gỗ | ván ép)","dày sàn đỉnh và căn cứ trừ sàn","Lượng quy đổi: Chưa có"]) assert.ok(view.includes(term),term);
    assert.doesNotMatch(view,/chưa nối đầy đủ đoạn cột với phạm vi tầng/);
    indices.push(rows);
  }
  assert.equal(new Set(indices.flat()).size,4);
  console.log("PASS: kết quả thật tại trục 4/A và 4/B, các nhóm dòng riêng:",JSON.stringify(indices));
}

if (process.argv[3]) {
  const reader = JSON.parse(fs.readFileSync(process.argv[3],"utf8"));
  const fromReader = {request:{structural_columns:reader.structural_columns,plans:[]},result:{works:reader.works,materials:[]}};
  const mapped = indexColumnWorks(fromReader);
  const at = mapped.findIndex((c,i)=>c?.grid_x==="4" && c.grid_y==="A" && c.floor_key==="T2" && reader.works[i].code==="COT");
  assert.ok(at>=0);
  const actual = renderToStaticMarkup(react.createElement(ColumnTrace,{snapshot:fromReader,selected:at,columns:mapped}));
  for (const term of ["0,17424 m³","120 mm","chưa dùng để khấu trừ","Bê tông theo quy ước của bản tính: Chưa có",reader.source_sha256]) assert.ok(actual.includes(term),term);
  assert.doesNotMatch(actual,/0[,.]168432/);
  console.log("PASS: reader final_v3 · C-2 4/A · gross 0,17424 m³ · sàn 120 mm chưa gắn vùng · net chưa xác định.");
}
