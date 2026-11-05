const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ts=require('../../frontend/node_modules/typescript');
const code=ts.transpileModule(fs.readFileSync('frontend/src/app/(user)/do-boc/viewport.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
function setup(withSvg){const effects=[],events=[],removed=[];const env={exports:{},require:()=>({useRef:v=>({current:v}),useCallback:f=>f,useEffect:f=>effects.push(f)}),window:{addEventListener:n=>events.push(n),removeEventListener:n=>removed.push(n)}};vm.runInNewContext(code,env);const viewport=env.exports.useViewport();if(withSvg)viewport.svgRef.current={addEventListener:n=>events.push(n),removeEventListener:n=>removed.push(n)};const cleanups=effects.map(f=>f());return{events,removed,cleanups};}
const form=setup(false);assert.equal(form.events.length,0);assert.equal(form.cleanups[0],undefined);
const drawing=setup(true);assert.deepEqual(drawing.events,['wheel','pointermove','pointerup','resize']);drawing.cleanups.forEach(f=>f?.());assert.deepEqual(drawing.removed,drawing.events);
console.log('PASS: no viewport events without SVG; drawing viewport retains listeners and cleanup.');
