const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const ts=require(path.resolve(__dirname,"../../frontend/node_modules/typescript"));
const src=fs.readFileSync(path.join(process.argv[2],"src/app/(user)/do-boc/model.ts"),"utf8"),out={};
vm.runInNewContext(ts.transpileModule(src,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,{exports:out,require:()=>({})});
const P={plan:{name:"Trệt"},walls:[],openings:[],columns:[],size:[100,100]},D={file:"qa.dxf",plans:[P]},S=out.initState(P);
Object.assign(S,{scope:"count",height_mm:3000});
const data=[{x:0,y:0},{x:31.25,y:-14.5},{},{x:null,y:0},{x:0},{x:-7,y:null}];
S.openings=data.map((pos,i)=>({id:"N"+(i+1),wall:"W3",kind:"door",w:null,h:2100,keep:i!==4,src:i===5?"auto":"manual",...pos}));
const confirmed=()=>out.payload(D,P,S,71).openings;
const rough=()=>out.roughRequest(D,{0:S},{0:{cols:[],is_ground:true}},71,null,{}).plans[0].openings;
for(const make of [confirmed,rough]){
 const result=JSON.parse(JSON.stringify(make()));assert.equal(result.length,data.length);
 result.forEach((o,i)=>{assert.deepEqual([o.x,o.y],[data[i].x??null,data[i].y??null]);assert.deepEqual([o.id,o.wall,o.keep,o.src],[S.openings[i].id,"W3",S.openings[i].keep,S.openings[i].src]);});
 for (const axis of ["x","y"]) for (const value of [NaN,Infinity,-Infinity,"0","",true]) {
   const old=S.openings[0][axis];S.openings[0][axis]=value;assert.throws(make,new RegExp("N1.*tọa độ "+axis));S.openings[0][axis]=old;
 }
}
console.log("PASS: 6 lỗ giữ hai trục độc lập (0, âm, thiếu, null), ID/parent/keep/src; 24 giá trị sai bị chặn trước JSON.");
