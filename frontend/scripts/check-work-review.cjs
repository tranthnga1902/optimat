const fs = require('node:fs');
const ts = require('typescript');
const Module = require('node:module');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const assert = require('node:assert/strict');
const path = require('node:path').resolve(__dirname, '../src/app/(user)/do-boc/WorkReview.tsx');
const source = ts.transpileModule(fs.readFileSync(path, 'utf8'), {
  compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS },
}).outputText;
const loaded = new Module(path, module);
loaded.filename = path;
loaded.paths = module.paths;
loaded.require = name => name === './model' ? { fmt: n => String(n) } : require(name);
loaded._compile(source, path);
const html = renderToStaticMarkup(React.createElement(loaded.exports.WorkReview, {
  result: { works: [{ name: 'Bê tông sàn', code: 'SAN', plan: 'Tầng 1', formula: '60 × dày sàn',
    missing: ['chiều dày sàn'], quantity: null, unit: 'm³', status: 'D' }] },
  onConfirm() { throw new Error('Không được tự xác nhận khi render'); },
}));
assert(html.includes('Chưa có'));
assert(html.includes('chiều dày sàn'));
assert(html.includes('khối lượng một phần'));
assert(html.includes('disabled=""'));
assert(!html.includes('Vật liệu mua về'));
console.log('PASS: giữ dữ liệu thiếu và chặn tiếp trước khi kiểm.');
