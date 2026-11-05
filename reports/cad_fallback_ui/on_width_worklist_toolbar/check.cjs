const fs=require("fs"),assert=require("node:assert/strict"),path=require("path");
const req=require("module").createRequire(path.resolve("package.json")),ts=req("typescript");
for(const port of ["3001","3002"]){
 const dir=path.join(__dirname,port,"src/app/(user)/do-boc");
 const src=fs.readFileSync(path.join(dir,"Board.tsx"),"utf8");
 const section=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b,src.indexOf(a))).replace(/^export /,"");
 const code=section("function overviewOffset","function fallbackArc")+section("export function displayBounds","export type BoardProps");
 const {offset,bounds}=new Function(ts.transpile(code,{target:7})+";return {offset:overviewOffset,bounds:displayBounds}")();
 assert.equal(offset({origin:[140,800]},[100,900]),"translate(40 100)");
 assert.equal(offset({origin:[600,350]},[100,900]),"translate(500 550)");
 assert.equal(offset({},[100,900]),null);
 for(const box of [[-70,-20,4,10],[1,2,1,2]])assert.deepEqual(bounds({display_bbox:box}),box);
 for(const box of [undefined,[0,0,Infinity,1],[1,0,0,3],[NaN,1,2,3]])assert.equal(bounds({display_bbox:box}),null);
 const diff=fs.readFileSync(path.join(__dirname,port+".patch"),"utf8");
 assert.equal((diff.match(/^\+\+\+ /gm)||[]).length,2);
 assert(!diff.split("\n").filter(x=>/^[-+][^-+]/.test(x)).some(x=>/onConfirm|quantity|roughRequest|onToggleCol|S\.openings|S\.walls/.test(x)));
 console.log(port,"PASS bbox/origin; no quantity or selection hunk")
}
