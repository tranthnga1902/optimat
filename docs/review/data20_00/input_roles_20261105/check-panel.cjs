// Chạy tại frontend của candidate: node <đường dẫn tới check-panel.cjs>
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const requireFrontend = require("node:module").createRequire(path.resolve("package.json"));
const ts = requireFrontend("typescript");
const React = requireFrontend("react");
const { renderToStaticMarkup } = requireFrontend("react-dom/server");

// Chỉ thay các wrapper hiển thị. Logic chọn hồ sơ và nút Start lấy từ component candidate.
const wrapper = ({ children }) => React.createElement("section", {}, children);
function load(name) {
  if (name === "@/components/ui") return { Card: wrapper, Empty: wrapper, Note: wrapper };
  if (name === "@/components/Sheet") return { Sheet: () => null };
  if (name.endsWith(".css")) return { default: {} };
  return requireFrontend(name);
}
const source = fs.readFileSync("src/components/ProjectFilesPanel.tsx", "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } });
const panel = {};
new Function("exports", "require", compiled.outputText)(panel, load);
const file = (id, role, file_id = id) => ({
  project_id: 1, file_id, revision_id: id, version: 1, sha256: "a".repeat(64),
  original_format: "dwg", role, name: role + "-sample.dwg",
});
const render = files => renderToStaticMarkup(React.createElement(panel.ProjectFilesPanel, {
  projectId: 1, files, selectedRevisionIds: files.map(f => f.revision_id), preview: { status: "idle" },
}));
const blocked = html => /<button[^>]*disabled[^>]*>Bắt đầu phân tích/.test(html);
assert(blocked(render([])));
assert(blocked(render([file(1, "KC")])));
assert(blocked(render([file(1, "KT"), file(2, "KT", 1)])));
const kt = render([file(1, "KT")]);
assert(!blocked(kt) && kt.includes("Chưa chọn bản kết cấu riêng"));
const pair = render([file(1, "KT"), file(2, "KC")]);
assert(!blocked(pair) && pair.includes("Bản kết cấu được đọc riêng"));
console.log("PASS: 5 trạng thái chọn phiên bản (React SSR, không gửi tệp).");
