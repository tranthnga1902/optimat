const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const ts=require(path.resolve('frontend/node_modules/typescript'));
for(const port of ['3001','3002']) {
  const folder=path.join(__dirname,port,'src/app/(user)/do-boc');
  const src=fs.readFileSync(path.join(folder,'Board.tsx'),'utf8');
  const section=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b,src.indexOf(a))).replace(/^export /,'');
  const code=section('function overviewOffset','function fallbackArc')+section('export function displayBounds','export type BoardProps');
  const {offset,bounds}=new Function(ts.transpile(code,{target:7})+';return {offset:overviewOffset,bounds:displayBounds}')();
  assert.equal(offset({origin:[140,800]},[100,900]),'translate(40 100)');
  assert.equal(offset({origin:[600,350]},[100,900]),'translate(500 550)');
  assert.equal(offset({},[100,900]),null);
  assert.deepEqual(bounds({display_bbox:[-70,-20,4,10]}),[-70,-20,4,10]);
  assert.match(src,/<details/);assert.match(src,/Hiển thị và thu phóng/);
  assert.match(src,/if \(bounds && p.fitBox\) p.fitBox/);
  assert.match(fs.readFileSync(path.join(folder,'ReadPreview.tsx'),'utf8'),/preview\.origin\[1\] - y/);
  console.log(port,'PASS origin/Y-down, negative bbox, toolbar source');
}
