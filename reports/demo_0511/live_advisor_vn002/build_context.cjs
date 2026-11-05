// Build the diagnostic input with the same material scope function as the app.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const vm = require("node:vm");
const repo = path.resolve(__dirname, "../../..");
const relative = "data/ground_truth/du_toan/normalized_20261103/nha_sang_hai_duong_4x15.comparison.json";
const digest = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const raw = fs.readFileSync(path.join(repo, relative));
const report = JSON.parse(raw.toString("utf8").replace(/^\uFEFF/, ""));
const drawings = report.source_drawings.map(source => {
  const base = path.win32.basename(source.path);
  const observed = digest(fs.readFileSync(path.join(repo, "data/drawings/build", base)));
  if (observed !== source.sha256.toLowerCase()) throw Error("Drawing hash mismatch");
  return { file: base, sha256: observed };
});
if (drawings.length !== 2 || report.verification_status !== "chua_kiem") throw Error("Check project provenance");
const scopeFile = path.join(repo, "frontend/src/app/(user)/dieu-chinh/advice-scope.ts");
const ts = require(path.join(repo, "frontend/node_modules/typescript"));
const js = ts.transpileModule(fs.readFileSync(scopeFile, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 }
}).outputText;
const sandbox = { exports: {} };
vm.runInNewContext(js, sandbox);
const tag = digest(raw).slice(0, 18);
const snapshot = { projectUid: "qa-isolated", drawingId: "draw-" + tag, reviewId: "unreviewed-" + tag, result: report.cad_result };
const context = sandbox.exports.adviceScope(snapshot, { checked: [], confirmed: false, partial: true }, null, "no-material-approval", []);
if (context.works.some(x => x.checked) || context.materials.some(x => x.complete)) throw Error("Unexpected approval");
fs.writeFileSync(path.join(__dirname, "context.local.json"), JSON.stringify(context), "utf8");
fs.writeFileSync(path.join(__dirname, "provenance.json"), JSON.stringify({
  case: "VN002", real_input: true, mode: "LIVE_STAGING", data_kind: "ACTUAL", input_origin: "existing_cad_takeoff",
  human_approval: false, persisted_project: false, comparison: relative, comparison_sha256: digest(raw), drawings,
  checked_work_count: 0, work_count: context.works.length, material_count: context.materials.length,
  deduction_rows: context.works.filter(w => w.quantity < 0).map(w => ({rowIndex:w.rowIndex, code:w.code, quantity:w.quantity, unit:w.unit})),
  material_ids: context.materials.map(m => m.material_id), scope_builder_sha256: digest(fs.readFileSync(scopeFile))
}, null, 2), "utf8");
console.log(JSON.stringify({drawings:drawings.length, works:context.works.length, materials:context.materials.length, checked:0}));
