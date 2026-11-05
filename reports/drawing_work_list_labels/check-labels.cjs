const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const deps = path.resolve(__dirname, "../../frontend/node_modules");
const ts = require(path.join(deps, "typescript"));
const React = require(path.join(deps, "react"));
const { renderToStaticMarkup } = require(path.join(deps, "react-dom/server"));
const source = fs.readFileSync(path.join(process.argv[2], "src/app/(user)/do-boc/DrawingWorkList.tsx"), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
});
const loaded = {};
vm.runInNewContext(compiled.outputText, { exports: loaded, require: name => require(path.join(deps, name)) });
const local = { plan:{name:"Lầu 1"}, walls:[], stairs:[{}], found:{SLAB:["KT-SÀN"]} };
const data = { file:"mẫu", plans:[local], drawing_work_signals:{REBAR:["KC-THÉP"]} };
const render = (drawing, index) => renderToStaticMarkup(React.createElement(loaded.DrawingWorkList, {
  data:drawing, index, params:{0:{stairDrafts:[]}},
}));
const selected = render(data, 0);
const heading = "Dấu hiệu toàn hồ sơ · chưa gán cho mặt bằng đang mở";
assert.ok(selected.includes(heading), "Thiếu nhãn phạm vi toàn hồ sơ khi mở một mặt bằng");
const [before, after] = selected.split(heading);
assert.match(before, /KT-SÀN/);
assert.doesNotMatch(before, /KC-THÉP/);
assert.match(after, /KC-THÉP/);
assert.match(before, /1 cầu thang từ nhận diện ban đầu/);
assert.match(render(data,-1), /Dấu hiệu toàn hồ sơ/);
assert.doesNotMatch(render(data,-1), /mặt bằng đang mở/);
assert.doesNotMatch(render({...data,drawing_work_signals:{}},0), /Dấu hiệu toàn hồ sơ/);
const structuralOnly = render({...data,plans:[]},-1);
assert.match(structuralOnly, /Dấu hiệu toàn hồ sơ/);
assert.match(structuralOnly, /KC-THÉP/);
console.log("PASS: nhãn đúng phạm vi ở mặt bằng, tổng quan, hồ sơ chỉ có KC và không có dấu hiệu; thang mang nguồn nhận diện ban đầu.");
