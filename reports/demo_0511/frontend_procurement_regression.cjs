const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'../../frontend'),ts=require(path.join(root,'node_modules/typescript'));
let slots=[],cursor=0,effects=[],calls=[],values=new Map();
const react={useState:init=>{const i=cursor++;if(!(i in slots))slots[i]=typeof init==='function'?init():init;return[slots[i],v=>slots[i]=typeof v==='function'?v(slots[i]):v]},useRef:init=>{const i=cursor++;return slots[i]??={current:init}},useMemo:f=>f(),useEffect:(f,deps)=>{const i=cursor++,prev=slots[i];if(!deps||!prev||deps.some((v,j)=>!Object.is(v,prev[j]))){slots[i]=deps;effects.push(f)}}};
const jsx=(type,props)=>({type,props}),components=new Proxy({},{get:(_,k)=>k});
const selectedQuote = {price:7,supplier_name:'BEST_ACTUAL',price_date:'2026-11-03',unit:'viên',is_reference:false,vat_included:'YES',transport_included:'NO'};
const pricedRow = {wall_type:'110',role:'partition',material_id:'GN01',quantity:30,unit:'viên',missing:[],offers:[{price:1,supplier_name:'WRONG_FIRST'}],best_offer:selectedQuote,est_cost:210};
let billRows = [pricedRow];
const api={nf:(n,d=2)=>n==null?'':Number(n).toLocaleString('vi-VN',{minimumFractionDigits:d,maximumFractionDigits:d}),money:n=>n==null?'':Math.round(n).toLocaleString('vi-VN'),ROLE:{partition:'ngăn'},api:async()=>({wall_systems:[]}),post:async(url,body)=>{calls.push({url,body});return url==='/api/price/bill'?billRows:{solutions:[],notes:[]}}};
function load(relative){const exports={};vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(root,relative),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2017,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText,{exports,window:{dispatchEvent(){}},CustomEvent:class {},DOMException,localStorage:{getItem:k=>values.has(k)?JSON.stringify(values.get(k)):null,setItem:(k,v)=>values.set(k,JSON.parse(v)),removeItem:k=>values.delete(k)},require:name=>name==='@/lib/review-session'?producer:name==='@/app/(user)/dieu-chinh/advice-scope'?scopeBuilder:name==='./Proposal'?{Proposal}:name==='../dieu-chinh/advice-scope'?scopeBuilder:name==='@/lib/purchase-session'?purchase:name==='./work-review'?workReview:name==='react'?react:name==='react/jsx-runtime'?{jsx,jsxs:jsx,Fragment:'Fragment'}:name==='@/lib/api'?api:(name==='@/lib/store'||name==='./store')?{store:{get:(k,d)=>values.get(k)??d,set:(k,v)=>values.set(k,v)},useStored:(k,d)=>values.get(k)??d}:name==='@/lib/reference'?{useReference:()=>({ref:{families:[],vehicles:[]}})}:components});return exports;}
const workReview=load('src/lib/work-review.ts'),purchase=load('src/lib/purchase-session.ts');
const scopeBuilder=load('src/app/(user)/dieu-chinh/advice-scope.ts');
const producer=load('src/lib/review-session.ts');
const Proposal=load('src/app/(user)/toi-uu/Proposal.tsx').Proposal;
const Bill=load('src/app/(user)/vat-lieu/bill.tsx').Bill,Optimize=load('src/app/(user)/toi-uu/optimize.tsx').Optimize;
function render(Component){cursor=0;effects=[];const tree=Component();effects.forEach(f=>f());return tree;}
function reset() {
 slots=[];calls=[];
 values=new Map([['optimat-project-uid','P1'],['optimat-review',{projectUid:'P1',drawingId:'D1',data:{file:'plan.dxf'},materialRevision:'M1'}],
   ['optimat-work-review',{projectUid:'P1',drawingId:'D1',file:'plan.dxf',reviewId:'R1',confirmed:true,checked:[0],partial:false}],
   ['optimat-materials-ready',true],['optimat-confirmed',[{groups:[{net_area_m2:33}]}]]]);
}
function find(tree,p){if(!tree||typeof tree!=='object')return;if(Array.isArray(tree)){for(const child of tree){const found=find(child,p);if(found)return found;}return;}if(p(tree))return tree;return find(tree.props?.children,p);}
function text(tree){if(tree==null||typeof tree==='boolean')return'';if(Array.isArray(tree))return tree.map(text).join(' ');if(typeof tree!=='object')return String(tree);return typeof tree.type==='function'?text(tree.type(tree.props)):text(tree.props?.children);}
const groups=[{wall_type:'110',role:'partition',net_area_m2:30,design_wall_system_id:'W-GN01-110'}];
const rough=(extra={})=>({projectUid:'P1',drawingId:'D1',reviewId:'R1',file:'plan.dxf',materialRevision:'M1',request:{file:'plan.dxf'},
 result:{plan_scope_confirmed:true,works:[{code:'XAY',quantity:3.15,status:'C',missing:[]}],wall_groups:groups,wall_group_issues:[],materials:[],...extra}});
(async()=>{
 reset();const reviewedOnly=rough({wall_groups:[],materials:[{material_id:"M",name:"Vật tư từ bản kiểm",raw_class:"khac",unit:"kg",quantity:10,quantity_with_waste:11,complete:true,missing:[],uses:[{work:"XAY",plan:"",quantity:10,via:"Định mức đã kiểm"}]}]});
 delete reviewedOnly.materialRevision;delete values.get('optimat-review').materialRevision;
 values.set('optimat-rough',reviewedOnly);values.set('optimat-materials-ready',false);
 const draftTree=render(Optimize),draft=find(draftTree,x=>x.type===Proposal);
 assert.ok(draft && draft.props.work===reviewedOnly,'Approved quantities can go directly to whole-project advice without manual materials or walls');
 assert.equal(purchase.currentPurchaseKey(),null,'An advisory draft is not a purchase approval');
 assert.ok(text(draftTree).includes('Vật tư từ bản kiểm'));assert.equal(calls.length,0);
 assert.match(text(draftTree),/Cần bổ sung báo giá.*đơn vị bán.*nơi giao.*hiệu lực/);
 reviewedOnly.result.wall_group_issues=['Cần đối chiếu mác vữa của hệ tường thử'];
 assert.ok(text(render(Optimize)).includes('Cần đối chiếu mác vữa của hệ tường thử'));
 slots=[];let plan=render(()=>Proposal(draft.props));
 assert.match(find(plan,x=>x.type==='MaterialAdvisor').props.initialQuestion,/toàn bộ phần thô/);
 find(plan,x=>x.type==='button'&&text(x).includes('Lưu phương án')).props.onClick();
 let accepted=values.get('optimat-proposal-P1');
 assert.equal(accepted.choices.length,1);assert.equal(accepted.choices[0].materialId,'M');
 assert.equal(accepted.status,'selected');assert.equal(values.get('optimat-materials-ready'),false);
 values.set('optimat-material-selection',{projectUid:'P1',drawingId:'D1',reviewId:'R1',choices:[
   {rowIndex:0,lineId:'m0',scope:'Cấu kiện A',originalId:'M',materialId:'USER',disposition:'proposed'}]});
 slots=[];plan=render(()=>Proposal(draft.props));
 reviewedOnly.result.materials[0].best_price=100;
 reviewedOnly.result.materials[0].price_source='Nguồn của mã ban đầu';
 slots=[];plan=render(()=>Proposal(draft.props));
 assert.ok(text(plan).includes('USER'));assert.ok(!text(plan).includes('Nguồn của mã ban đầu'));
 find(plan,x=>x.type==='button'&&text(x).includes('Lưu phương án')).props.onClick();
 accepted=values.get('optimat-proposal-P1');assert.equal(accepted.choices.length,0);
 assert.equal(accepted.scopedChoices[0].materialId,'USER');assert.equal(accepted.status,'conditional');
 values.delete('optimat-material-selection');values.delete('optimat-proposal-P1');slots=[];
 reviewedOnly.result.materials[0].complete=false;reviewedOnly.result.materials[0].quantity_with_waste=null;
 reviewedOnly.result.materials[0].missing=['Thiếu quy cách đóng gói'];
 plan=render(()=>Proposal(draft.props));find(plan,x=>x.type==='button'&&text(x).includes('Lưu phương án')).props.onClick();
 accepted=values.get('optimat-proposal-P1');assert.equal(accepted.choices.length,0);assert.equal(accepted.status,'conditional');
 assert.equal(accepted.unresolved[0].lineId,'m0');assert.equal(purchase.currentPurchaseKey(),null);
 for (const Component of [Bill,Optimize]) {
   for (const invalidate of [
     () => values.delete('optimat-work-review'),
     () => values.set('optimat-project-uid','P2'),
     () => { values.get('optimat-work-review').reviewId='R2'; },
     () => { values.get('optimat-work-review').checked=[]; },
     () => { values.get('optimat-review').drawingId='D2'; },
     () => { values.get('optimat-review').materialRevision='M2'; },
     () => { values.get('optimat-review').data.file='other.dxf'; },
     () => { delete values.get('optimat-rough').request; },
   ]) {
     reset();values.set('optimat-rough',rough());invalidate();render(Component);await Promise.resolve();
     assert.equal(calls.length,0,'An old or mismatched approval must not authorize a request');
     assert.equal(purchase.currentPurchaseKey(),null);
   }
 }
 for(const Component of [Bill,Optimize])for(const state of [null,rough({plan_scope_confirmed:undefined}),rough({wall_group_issues:['thiếu khối lượng']})]){
   reset();values.set('optimat-rough',state);const tree=render(Component);await Promise.resolve();assert.equal(calls.length,0);
   if(Component===Optimize && state?.result.wall_group_issues.length)assert.ok(find(tree,x=>x.type===Proposal));
   else assert.ok(text(tree).includes('phần thô'));
 }
 reset();values.set('optimat-rough',rough());let tree=render(Bill);await Promise.resolve();tree=render(Bill);
 assert.equal(calls.length,1);assert.equal(calls[0].body.actual_only,true);assert.equal(calls[0].body.groups[0].net_area_m2,30);
 assert.ok(text(tree).includes('BEST_ACTUAL'));assert.ok(!text(tree).includes('WRONG_FIRST'));assert.ok(text(tree).includes('2026-11-03'));
 assert.match(text(tree), /đã gồm VAT/); assert.match(text(tree), /chưa gồm cước giao hàng/);
 assert.match(text(tree), /Ngày giá 2026-11-03 · chưa rõ hiệu lực/);
 billRows = [pricedRow, {...pricedRow, best_offer:{...selectedQuote,transport_included:'YES',valid_until:'2026-11-15',source_detail:'Phiếu BG-B'}, est_cost:350},
   {...pricedRow, best_offer:null, est_cost:null, missing:['giá'], offers:[{...selectedQuote,supplier_name:'Báo giá gốc',valid_until:'2026-11-01',vat_included:'UNKNOWN',rejection_reasons:['Chưa rõ VAT']}]}];
 reset();values.set('optimat-rough',rough());tree=render(Bill);await Promise.resolve();tree=render(Bill);
 const mixed=text(tree); assert.equal(mixed.split('Tạm tính 1/3 dòng').length-1,2);
 assert.ok(!mixed.includes('560'));assert.ok(mixed.includes('Báo giá gốc') && mixed.includes('Chưa rõ VAT'));
 assert.ok(mixed.includes('Phiếu BG-B') && mixed.includes('hạn theo nguồn 2026-11-15') && mixed.includes('hạn theo nguồn 2026-11-01'));
 reset();values.set('optimat-rough',rough());tree=render(Optimize);await Promise.resolve();tree=render(Optimize);
 const form=find(tree,x=>x.type==='form'&&find(x.props.children,y=>y.type==='h2'));
 assert.ok(form);assert.equal(find(tree,x=>x.type==='input'&&x.props.type==='checkbox').props.checked,true,'default keeps design');
 const lat=find(tree,x=>x.type==='input'&&x.props.min==='-90'),lon=find(tree,x=>x.type==='input'&&x.props.min==='-180');
 assert.equal(lat.props.required,true);assert.equal(lon.props.required,true);
 await form.props.onSubmit({preventDefault(){}});assert.equal(calls.length,0,'blank province blocks submission');
 values.set('optimat-constraints',{province:'Hà Nội',site_lat:21.02,site_lon:105.83});tree=render(Optimize);
 await find(tree,x=>x.type==='form'&&find(x.props.children,y=>y.type==='h2')).props.onSubmit({preventDefault(){}});
 assert.equal(calls.length,1);assert.equal(calls[0].url,'/api/optimize');assert.equal(calls[0].body.constraints.procurement_mode,true);assert.equal(calls[0].body.constraints.keep_design_material,true);assert.equal(calls[0].body.groups[0].net_area_m2,30);assert.equal(calls[0].body.constraints.province,'Hà Nội');
 const storedResult=values.get('optimat-optimization');
 values.set('optimat-optimization',{...storedResult,solutions:[{total_cost:100,supply_days:2,u_value:1,choices:[]}]});
 tree=render(Optimize);
 const resultElement=find(tree,x=>typeof x.type==='function' && x.type.name==='Solutions');
 const resultsTree=resultElement.type(resultElement.props);
 assert.ok(find(resultsTree,x=>x.props.title==='Phương án tường duy nhất trong kết quả'));
 assert.ok(!find(resultsTree,x=>x.props.title==='Chi phí thấp nhất'),'A single solution is not displayed as three alternatives');
 const delayedPost=api.post;
 let release;
 api.post=(url,body)=>url==='/api/optimize'?new Promise(resolve=>{release=resolve}):delayedPost(url,body);
 const stale=find(tree,x=>x.type==='form'&&find(x.props.children,y=>y.type==='h2')).props.onSubmit({preventDefault(){}});
 values.set('optimat-optimization',null);
 values.get('optimat-rough').materialRevision='M2';values.get('optimat-review').materialRevision='M2';
 release({solutions:[],notes:['OLD_RESULT']});await stale;
 assert.equal(values.get('optimat-optimization'),null,'Old response cannot write into another material revision');
 console.log('PASS Bill/Optimize and producer approval contract: stale project/drawing/review/material/request rejected, late response discarded, final wall quantity and quote conditions verified.');
})().catch(error=>{console.error(error);process.exitCode=1});
