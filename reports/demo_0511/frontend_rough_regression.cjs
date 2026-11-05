const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../frontend');
const ts = require(path.join(root, 'node_modules/typescript'));
const jsx = (type, props) => ({ type, props });
const components = new Proxy({}, {get: (_, k) => k});
function load(file, require) {
  const exports = {};
  const code = ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {compilerOptions: {module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true}}).outputText;
  vm.runInNewContext(code, {exports, require, console, localStorage: {getItem: () => null}});
  return exports;
}
const api = load('src/lib/api.ts', () => components);
const model = load('src/app/(user)/do-boc/model.ts', () => components);
const sessionLib = load('src/lib/review-session.ts', () => components);
let saved;
const deps = name => {
  if (name === 'react/jsx-runtime') return {jsx, jsxs: jsx, Fragment: 'Fragment'};
  if (name === '@/lib/api') return api;
  if (name === './model') return model;
  if (name === '@/lib/review-session') return sessionLib;
  if (name === '@/lib/reference') return {useReference: () => ({ref: {concrete_grades: ['M250'], mortar_grades: ['M75'], plaster_thicknesses: ['15'], screed_thicknesses: ['20']}, error: null})};
  if (name === '@/lib/store') return {useStored: (key, fallback) => key === 'optimat-rough' ? saved : fallback};
  if (name.endsWith('.css')) return {};
  return components;
};
const tab = load('src/app/(user)/do-boc/Rough.tsx', deps);
const page = load('src/app/(user)/phan-tho/rough.tsx', deps);
function find(tree, test) {
  if (!tree || typeof tree !== 'object') return;
  if (Array.isArray(tree)) { for (const child of tree) {const match = find(child, test); if (match) return match;} return; }
  if (test(tree)) return tree;
  return find(tree.props?.children, test);
}
function text(tree) {
  if (tree == null || typeof tree === 'boolean') return '';
  if (Array.isArray(tree)) return tree.map(text).join(' ');
  if (typeof tree !== 'object') return String(tree);
  if (typeof tree.type === 'function') return text(tree.type(tree.props));
  return text(tree.props?.children);
}
const changes = [];
const tree = tab.RoughTab({P: {plan: {name: 'T1'}}, pp: {cols: [], is_ground: false}, values: {natural_ground_level_mm: '-100', slab_thickness_mm: '120'}, rough: null, busy: false,
  onParam: (k,v) => changes.push([k,v]), onPlanParam() {}, onRun() {}, structural: null, onStructural() {}});
const ground = find(tree, x => x.type === 'ChangeInput' && x.props.value === '-100');
const slab = find(tree, x => x.type === 'ChangeInput' && x.props.value === '120');
assert.equal(changes.length, 0, 'rendering catalog suggestions must not auto-select a material value');
const concreteSuggestion = find(tree, x => x.type === 'select' && x.props['aria-label'] === 'Đề xuất mác bê tông');
assert.equal(concreteSuggestion, undefined, 'material selection lives in its own module, not rough calculations');
assert.equal(ground.props.min, undefined);
assert.equal(slab.props.min, 0);
ground.props.onCommit({value: '-200'});
assert.deepEqual(changes.pop(), ['natural_ground_level_mm', '-200']);
assert.equal(slab.props.onCommit({value: '-200'}), '120');
assert.equal(changes.length, 0);
slab.props.onCommit({value: ''});
assert.deepEqual(changes.pop(), ['slab_thickness_mm', '']);
slab.props.onCommit({value: '150'});
assert.deepEqual(changes.pop(), ['slab_thickness_mm', '150']);
saved = {file: 'demo.dxf', at: '2026-11-03', result: {
  works: [{code: 'SAN', plan: 'T1', missing: ['thiếu tầng']}], totals: [{code: 'SAN', name: 'Sàn', quantity: 7, unit: 'm3', complete: false, status: 'D'}],
  formwork: [{name: 'Cốp pha sàn', quantity: 30, complete: false, status: 'C'}],
  materials: [{material_id: 'XM01', name: 'Xi măng', quantity: 2, quantity_with_waste: 3, unit: 'kg', complete: false, status: 'D', missing: ['thiếu định mức'], best_price: 5, est_cost: 123456, price_source: 'BULLETIN, Sở XD, 2026-10-01, ACTUAL'},
    {material_id: 'TH01', name: 'Thép', quantity: null, quantity_with_waste: null, unit: 'kg', complete: false, status: 'D', missing: ['thiếu đường kính'], best_price: null, est_cost: null}], warnings: []}};
const displayed = text(page.Rough());
assert.ok(displayed.includes('123.456,00'), 'display API est_cost verbatim; do not calculate 3*5');
assert.ok(displayed.includes('BULLETIN, Sở XD, 2026-10-01, ACTUAL'), 'preserve price source/date/labels');
assert.ok(displayed.includes('giá công bố (BULLETIN) không phải báo giá mua đã xác nhận'));
assert.ok(displayed.includes('D thiếu'));
assert.ok(displayed.includes('C tạm tính'));
assert.ok(displayed.includes('một phần'));
assert.ok(displayed.includes('thiếu đường kính'));
assert.ok(displayed.includes('chưa có giá'));
console.log('PASS: signed ground only; reject negative dimensions; display API price/cost/source/date/status/missing/partial without recalculation.');
