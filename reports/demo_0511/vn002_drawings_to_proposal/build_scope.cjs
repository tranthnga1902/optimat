// Lấy đúng phạm vi mà giao diện gửi, không tạo phiếu xác nhận cho hồ sơ đang kiểm.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../../..');
const ts = require(path.join(root, 'frontend/node_modules/typescript'));
const file = path.join(root, 'frontend/src/app/(user)/dieu-chinh/advice-scope.ts');
const js = ts.transpileModule(fs.readFileSync(file, 'utf8'), {compilerOptions: {
  module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020,
}}).outputText;
const moduleScope = {exports: {}};
vm.runInNewContext(js, moduleScope);
const current = process.argv[2] !== '--saved-request';
const resultPath = current ? 'rough.local.json' : 'rough.from_saved_request.json';
const result = JSON.parse(fs.readFileSync(path.join(__dirname, resultPath), 'utf8'));
const snapshot = {projectUid: 'local-audit', drawingId: 'cad-source-pair', reviewId: 'unreviewed', result};
const context = moduleScope.exports.adviceScope(snapshot, {checked: [], partial: true, confirmed: false}, null);
if (context.works.length !== result.works.length || context.materials.length !== result.materials.length) {
  throw Error('Phạm vi tư vấn khác với bản bóc DXF.');
}
const contextPath = current ? 'context.local.json' : 'context.from_saved_request.json';
fs.writeFileSync(path.join(__dirname, contextPath), JSON.stringify(context), 'utf8');
