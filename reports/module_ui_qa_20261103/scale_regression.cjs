const vm = require("node:vm"), fs = require("node:fs"), assert = require("node:assert/strict");
const ts = require("../../frontend/node_modules/typescript");
const effects = [], handlers = {}, node = () => ({value:""});
const dom = {addEventListener(k,f){handlers[k]=f}, removeEventListener(){}};
const react = {useCallback:f=>f,useRef:current=>({current}),useEffect:f=>effects.push(f)};
function load(file) {
  const env = {exports:{},require:()=>react,window:dom,setTimeout};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync("frontend/src/app/(user)/do-boc/"+file,"utf8"), {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,env);return env.exports;
}
const {titleScale} = load("paper-scale.ts");
assert.equal(titleScale("MB trệt",[{t:"Mặt bằng trệt (TL 1:100)"},{t:"MB tầng 2 TL 1:50"}]).denominator,100);
assert.equal(titleScale("MB tầng 2 TL 1/50").denominator,50);
assert.equal(titleScale("MB tầng 2",[{t:"Khung tên TL 1:100"},{t:"TL 1:50"}]),null);
assert.equal(titleScale("MB tầng 2",[{t:"MB tầng 2 TL 1:50"},{t:"MB tầng 2 TL 1:100"}]),null);
const vp = load("viewport.ts").useViewport(), box={width:800,height:400,left:25,top:25};
vp.svgRef.current={...dom,getBoundingClientRect:()=>box,setAttribute(){}};
vp.zoomLabel.current=node();vp.zoomRef.current=node();vp.scaleRef.current=node();effects.forEach(f=>f());
vp.fitSize([12000,5000]);const fit={...vp.vbRef.current}, ruler=vp.scaleRef.current.textContent;
vp.zoomTo(200);assert.equal(vp.vbRef.current.w,fit.w/2);assert.equal(vp.zoomLabel.current.value,"200%");assert.notEqual(vp.scaleRef.current.textContent,ruler);
handlers.wheel({preventDefault(){},deltaY:-50,clientX:300,clientY:200});assert.equal(Number(vp.zoomRef.current.value),230);
const before={...vp.vbRef.current};vp.onPointerDown({clientX:100,clientY:100});handlers.pointermove({clientX:180,clientY:140});assert.equal(vp.vbRef.current.w,before.w);assert.notEqual(vp.vbRef.current.x,before.x);
vp.fitSize([12000,5000]);assert.equal(vp.zoomLabel.current.value,"100%");assert.equal(vp.scaleRef.current.textContent,ruler);
console.log("PASS: per-plan print scale, unmatched/conflicting sources, wheel, slider, fit, pan, ruler");
