// Dùng nguyên bộ chọn dòng của UI trên snapshot mới và bản JSON thiếu index kiểu cũ.
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../../../..'), ts = require(path.join(root, 'frontend/node_modules/typescript'));
const read = name => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
const source = fs.readFileSync(path.join(root, 'frontend/src/app/(user)/do-boc/row-advisory.ts'), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } });
const run = {exports:{}}; vm.runInNewContext(compiled.outputText, run);
const snapshot = read('ui_input.json'), receipt = read('production.json');
const old = structuredClone(snapshot);
for (const m of old.result.materials) for (const u of m.uses) delete u.rowIndex;
const checked = [];
for (const col of receipt.column_segments) for (const work of col.works) {
  const get = data => run.exports.uncheckedRowAdvice(data, work.rowIndex, []).context;
  const former = get(old), current = get(snapshot);
  const got = current.materials.flatMap(m => m.uses);
  assert.equal(former.materials.length, 0);
  assert.equal(got.length, work.contributions.length);
  assert.equal(current.works[0].element, work.element);
  assert.ok(current.materials.every(m => m.quantity === null && m.quantity_with_waste === null && !m.complete));
  assert.ok(current.works.every(w => !w.checked));
  checked.push({axis:col.axis, work_key:work.work_key, before_rows:former.materials.length,
                after_rows:current.materials.length, quantity:current.materials[0].quantity, checked:false});
}
fs.writeFileSync(path.join(__dirname, 'consumer.json'), JSON.stringify({actual_ui_helper:true,browser_run:false,checked},null,2));
console.log('UI helper distinguishes 4/A and 4/B; nullable contributions retained; ambiguous legacy rows withheld.');
