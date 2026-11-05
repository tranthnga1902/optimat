const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),req=require('module').createRequire(path.resolve('package.json')),ts=req('typescript'),R=req('react'),ssr=req('react-dom/server');
for(const port of ['3001','3002']){
 const file=path.join(__dirname,port,'src/app/(user)/do-boc/Board.tsx'),m={exports:{}};
 new Function('module','exports','require',ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{jsx:4,module:1,target:7}}).outputText)(m,m.exports,n=>n==='./model'?{ROLE:{},clsColor:()=>'',band:()=>'',fmt:String,wallLen:()=>1}:n.endsWith('.css')?{default:{}}:n==='@/lib/reference'?{useWallClasses:()=>[]}:req(n));
 for(const [x,y,visible,...width] of [[0,0,true],[-20,-20,true],[null,1,false],[1,null,false],[null,null,false],[undefined,1,false],[1,undefined,false],[NaN,0,false],[0,Infinity,false],[0,0,false,null],[5,4,false,undefined]]){
 const openings=[{id:'O',wall:'W',x,y,...(width.length?(width[0]===undefined?{}:{w:width[0]}):{w:10}),keep:true}],P={segs:[],layers:[],size:[100,100]},S={walls:[{id:'W',x1:-50,y1:-50,x2:50,y2:50,keep:true}],openings};
 const html=ssr.renderToStaticMarkup(R.createElement(m.exports.Board,{P,S,pi:0,data:{plans:[P]},bg:'lines',mode:'select',showRec:true,cols:[],unit:1,movedRef:{current:false}}));
 assert.equal(html.includes('stroke-linecap="butt"'),visible);assert.equal(openings.length,1)
 }console.log(port,'PASS actual Board SSR: zero, negative, null, absent, NaN, Infinity, null/missing width')
}
