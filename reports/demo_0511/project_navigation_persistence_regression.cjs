const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('frontend/src/app/(user)/do-boc/Review.tsx', 'utf8');
const persist = source.match(/const persistReview = useCallback\((\(nextConfirmed = confirmed\) => \{[\s\S]*?)\n  \}, \[data/)[1] + '\n}';
const manual = source.match(/const beforeNavigate = (\(event: globalThis.MouseEvent\) => \{[\s\S]*?)\n    \};/)[1].replace(': globalThis.MouseEvent','') + '\n}';
const auto = source.match(/if \(persistReview\(nextConfirmed\)\) router.push\("\/dieu-chinh"\);\s*else setSheet\(null\);/)[0];
let quota = false, error = '', navigations = 0;
const values = new Map([['optimat-review', 'OLD']]);
class Anchor { constructor() { this.origin = 'http://app'; this.pathname = '/dieu-chinh'; } closest() { return this; } }
const context = { data: {file:'CURRENT'}, states:{}, planP:{}, confirmed:{0:{plan:'T1'}}, nextConfirmed:{0:{plan:'T1',confirmed:true}}, pi:0, structural:null,
 localStorage:{setItem:(k,v)=>{if(quota)throw Error('quota');values.set(k,v);}}, setSaveNotice:()=>{}, setSaveError:v=>error=v,
 router:{push:()=>navigations++}, setSheet:()=>{}, Element:Anchor, HTMLAnchorElement:Anchor, location:{origin:'http://app',pathname:'/do-boc'} };
vm.createContext(context);
context.persistReview = vm.runInContext(persist, context);
context.manual = vm.runInContext(manual, context);
vm.runInContext(auto, context);
assert.equal(navigations,1);assert.equal(JSON.parse(values.get('optimat-review')).data.file,'CURRENT');
assert.equal(JSON.parse(values.get('optimat-review')).confirmed[0].confirmed,true);
quota = true;
values.set('optimat-review','OLD');
vm.runInContext(auto, context);
assert.equal(navigations,1);assert.equal(values.get('optimat-review'),'OLD');assert.ok(error);
let blocked=false,stopped=false;
context.manual({target:new Anchor(),preventDefault:()=>blocked=true,stopPropagation:()=>stopped=true});
assert.equal(blocked,true);assert.equal(stopped,true);assert.equal(values.get('optimat-review'),'OLD');
quota=false;blocked=false;stopped=false;
context.manual({target:new Anchor(),preventDefault:()=>blocked=true,stopPropagation:()=>stopped=true});
assert.equal(blocked,false);assert.equal(JSON.parse(values.get('optimat-review')).data.file,'CURRENT');assert.equal(error,'');
console.log('PASS: auto persists current confirmation before routing; quota blocks auto and manual navigation; retry persists current snapshot before manual navigation.');

const ts = require('../../frontend/node_modules/typescript');
const matchFunction = source.slice(source.indexOf('export function reviewMatchesConfirmed'), source.indexOf('type SheetState'));
const compiled = ts.transpileModule(matchFunction, {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const matcher = {exports:{}};vm.runInNewContext(compiled,matcher);
const oldPlan={file:'A',plan:'T1',height_mm:3000,total_net_area_m2:30,groups:[],confirmed_at:'old'};
const newPlan={...oldPlan,height_mm:3800,confirmed_at:'new'};
assert.equal(matcher.exports.reviewMatchesConfirmed('A',{0:oldPlan},[newPlan]),false);
assert.equal(matcher.exports.reviewMatchesConfirmed('A',{0:newPlan},[newPlan]),true);
assert.ok(source.includes('saved && (adjustment || roughOnly) && !reviewMatchesConfirmed'));
assert.ok(source.indexOf('saved && (adjustment || roughOnly) && !reviewMatchesConfirmed') < source.indexOf('setData(saved.data)'));
console.log('PASS: direct adjustment entry rejects stale snapshot before hydration, accepts matching confirmation.');

context.data={file:'LARGE',cad:'heavy-svg',plans:[{cad:'plan-svg',walls:[{id:'W1',x1:0,x2:1000}]}]};
context.localStorage.setItem=(key,value)=>{if(value.includes('heavy-svg'))throw Error('quota');values.set(key,value);};
assert.equal(context.persistReview(),true);
const compact=JSON.parse(values.get('optimat-review'));
assert.equal(compact.data.cad,undefined);assert.equal(compact.data.plans[0].cad,undefined);
assert.equal(compact.data.plans[0].walls[0].x2,1000);
assert.equal(context.data.cad,'heavy-svg');
console.log('PASS: oversized CAD fallback preserves geometry and live original while saving compact restorable snapshot.');
// Verify that only CAD backgrounds are omitted, not quantities or user decisions.
context.data={file:'LARGE',overview:{cad:'heavy-svg',size:[2000,2000],plans:[{name:'T1'},{name:'T2'}]},plans:[
 {plan:{name:'T1'},cad:'plan-svg',segs:[[0,0,1000,0]],walls:[{id:'W1',x1:0,x2:1000,mat:'G01'}],openings:[{wall:'W1',w:900,h:2100}],columns:[{id:'C1'}],stairs:[{id:'T1'}]},
 {plan:{name:'T2'},cad:'second-svg',walls:[{id:'W2',x1:0,x2:2000}]}]};
context.states={0:{height_mm:3800,walls:[{id:'W1',mat:'G02',keep:true}]},1:{height_mm:3300,walls:[{id:'W2',mat:'G03',keep:true}]}};
context.planP={0:{cols:[{id:'C1',keep:true}],is_ground:true}};
context.confirmed={0:{...newPlan,groups:[{design_material_id:'G02',net_area_m2:38}],takeoff_id:123}};
context.pi=1;context.structural={file:'KC',foundations:[{id:'F1'}]};
values.set('optimat-rough',JSON.stringify({result:{materials:[{material_id:'XM01',quantity:2}]}}));
values.set('optimat-project-history',JSON.stringify([{id:'existing'}]));
const untouchedRough=values.get('optimat-rough'),untouchedHistory=values.get('optimat-project-history');
assert.equal(context.persistReview(),true);
const restored=JSON.parse(values.get('optimat-review'));
for(const key of ['states','planP','confirmed','structural'])assert.deepEqual(restored[key],JSON.parse(JSON.stringify(context[key])));
assert.equal(restored.pi,1);assert.equal(restored.data.plans.length,2);
const withoutCad=JSON.parse(JSON.stringify(context.data,(key,value)=>key==='cad'?undefined:value));
assert.deepEqual(restored.data,withoutCad);
assert.equal(values.get('optimat-rough'),untouchedRough);assert.equal(values.get('optimat-project-history'),untouchedHistory);
const storedBeforeFailure=values.get('optimat-review'),liveBeforeFailure=JSON.stringify(context.data);
context.localStorage.setItem=()=>{throw Error('quota even compact');};
assert.equal(context.persistReview(),false);
assert.equal(values.get('optimat-review'),storedBeforeFailure);assert.equal(JSON.stringify(context.data),liveBeforeFailure);
assert.equal(values.get('optimat-project-history'),untouchedHistory);
console.log('PASS: all plans, selected plan, geometry, choices, groups, confirmation metadata, structure preserved; separate rough/history untouched; compact failure retains old snapshot and live state.');
