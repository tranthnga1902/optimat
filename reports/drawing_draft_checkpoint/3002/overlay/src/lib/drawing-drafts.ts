import { saveTogether, type ReviewSession } from "./review-session";
import type { AnalysisContext } from "./project-records";
import type { ProjectHistory } from "./projects";

export const DRAFTS_KEY = "optimat-drawing-drafts";
export type DraftOwner = { projectUid:string; projectId:number|null };
export type DraftSource = { kind:"file"; sha256:string } | {
  kind:"revisions"; profileVersion:number; files:{file_id:number;revision_id:number;sha256:string;role:string}[];
};
type Bundle = { review:string; values:Record<string,string> };
type SavedDraft = Bundle & { id:string; at:string };
type Archive = DraftOwner & { version:1; items:SavedDraft[] };
export type DraftEntry = { key:string; source:string; sourceUid:string; otherSession:boolean; time?:string; session:ReviewSession };
const defaults:Record<string,string> = {
  "optimat-rough-params":"{}","optimat-confirmed":"[]","optimat-analysis-context":"null","optimat-rough":"null","optimat-work-review":"null",
  "optimat-material-draft":"null","optimat-material-selection":"null","optimat-materials-ready":"false","optimat-optimization":"null",
};
const mismatched = () => new Error("Phiên dự án hoặc bản vẽ đã thay đổi. Hãy mở lại trang hiện tại.");
function parse<T>(raw:string | null | undefined):T | null { return raw ? JSON.parse(raw) as T : null; }
function projectId(raw:string|null|undefined) {
  const value = parse<number|string>(raw);
  if (value == null || value === "") return null;
  const n = Number(value);
  if (!Number.isSafeInteger(n) || n < 1) throw mismatched();
  return n;
}
export function sameOwner(a:DraftOwner,b:DraftOwner) {
  return !!a.projectUid && a.projectUid === b.projectUid && a.projectId === b.projectId;
}
function checkCurrent(owner:DraftOwner,expected:string|null) {
  const actual = {projectUid:parse<string>(localStorage.getItem("optimat-project-uid")) || "",projectId:projectId(localStorage.getItem("optimat-project"))};
  if (!sameOwner(actual,owner) || localStorage.getItem("optimat-review") !== expected) throw mismatched();
}
function empty(owner:DraftOwner):Archive { return {...owner,version:1,items:[]}; }
function archiveOf(raw:string|null|undefined,owner:DraftOwner):Archive {
  const archive=parse<Archive>(raw);
  if (!archive) return empty(owner);
  if (archive.version !== 1 || !sameOwner(archive,owner) || !Array.isArray(archive.items)) throw mismatched();
  return archive;
}
function reviewOf(raw:string,owner:DraftOwner,legacy=false) {
  const s=parse<ReviewSession>(raw);
  if (!s || !Array.isArray(s.data?.plans) || !s.states || typeof s.data.file !== "string" ||
    (!s.projectUid && !owner.projectUid && !(legacy && s.projectId!=null && s.projectId===owner.projectId)) ||
    (s.projectUid !== owner.projectUid && !(legacy && !s.projectUid && s.projectId === owner.projectId && owner.projectId !== null)) ||
    (s.projectId !== undefined && s.projectId !== owner.projectId)) throw mismatched();
  return s;
}
function compact(raw:string) {
  const s=JSON.parse(raw) as ReviewSession;
  for (const plan of s.data.plans) delete plan.cad;
  if (s.data.overview) delete s.data.overview.cad;
  return JSON.stringify(s);
}
function related() {
  return Object.fromEntries(Object.keys(defaults).map(key=>[key,localStorage.getItem(key) ?? defaults[key]]));
}
// Serialize cooperating tabs, and check the active project/snapshot again inside the lock.
export function withDraftLock<T>(owner:DraftOwner,action:()=>T):Promise<T> {
  return typeof navigator !== "undefined" && navigator.locks
    ? navigator.locks.request("optimat-drafts:"+owner.projectUid,action)
    : Promise.resolve().then(action);
}
function revisionSource(context:AnalysisContext):DraftSource {
  const files = context.revisions.filter(f=>f.role !== "THAM_KHAO").map(({file_id,revision_id,sha256,role})=>{
    if (!Number.isSafeInteger(file_id) || !Number.isSafeInteger(revision_id) || !sha256 || !/^[a-f0-9]{64}$/i.test(sha256) || !role) throw mismatched();
    return {file_id,revision_id,sha256,role};
  });
  const version=context.profile.profileVersion;
  if (!files.length || version == null || !Number.isSafeInteger(version) || version < 1) throw mismatched();
  return {kind:"revisions",profileVersion:version,files};
}
export async function sourceFor(context?:AnalysisContext,file?:File):Promise<DraftSource> {
  if (context) return revisionSource(context);
  if (!file) throw new Error("Không xác định được nguồn bản vẽ.");
  const digest=await crypto.subtle.digest("SHA-256",await file.arrayBuffer());
  return {kind:"file",sha256:Array.from(new Uint8Array(digest),n=>n.toString(16).padStart(2,"0")).join("")};
}
// Call under withDraftLock. Leave the active drawing untouched on every failed checkpoint.
export function checkpointDraft(owner:DraftOwner,raw:string|null) {
  checkCurrent(owner,raw);
  if (!raw) return;
  const s=reviewOf(raw,owner);
  if (!s.draftId) throw new Error("Thiếu mã nháp. Hãy giữ bản vẽ đang mở.");
  const archive=archiveOf(localStorage.getItem(DRAFTS_KEY),owner);
  const rest=archive.items.filter(item=>item.id!==s.draftId);
  const entry:SavedDraft={id:s.draftId,at:s.savedAt || new Date().toISOString(),review:raw,values:related()};
  const save=(row:SavedDraft)=>localStorage.setItem(DRAFTS_KEY,JSON.stringify({...archive,items:[row,...rest]}));
  try {save(entry);} catch {
    try {save({...entry,review:compact(raw)});} catch {throw Error("Bộ nhớ chưa lưu được nháp. Bản đang mở và nháp trước đó vẫn được giữ.");}
  }
}
export function draftOptions(owner:DraftOwner) {
  return archiveOf(localStorage.getItem(DRAFTS_KEY),owner).items.map(row=>({
    id:row.id,at:row.at,raw:row.review,session:reviewOf(row.review,owner)
  }));
}
export function draftLabel(s:ReviewSession) {
  if (s.draftSource?.kind==="file") return "Tệp cục bộ · SHA-256 "+s.draftSource.sha256;
  if (s.draftSource?.kind==="revisions") return "Hồ sơ v"+s.draftSource.profileVersion+" · "+s.draftSource.files.map(f=>"tệp "+f.file_id+" / revision "+f.revision_id+" ("+f.role+")").join(", ");
  return "Bản cũ · chưa xác định phiên bản nguồn";
}
export function newDrawingBundle(session:ReviewSession,context?:AnalysisContext):Bundle {
  return {review:JSON.stringify(session),values:{...defaults,"optimat-rough-params":localStorage.getItem("optimat-rough-params") || "{}","optimat-analysis-context":JSON.stringify(context || null)}};
}
export function storedDrawingBundle(owner:DraftOwner,id:string,expectedRaw:string):Bundle {
  const row=archiveOf(localStorage.getItem(DRAFTS_KEY),owner).items.find(r=>r.id===id && r.review===expectedRaw);
  if (!row || reviewOf(row.review,owner).draftId!==id) throw mismatched();
  const s=reviewOf(row.review,owner), values={...row.values};
  const source=s.draftSource;
  if (!source) {
    // Không gắn biên nhận hay tọa độ từ bản máy chủ khác vào nháp cũ chưa rõ nguồn.
    return {review:JSON.stringify({...s,confirmed:{},materialRevision:undefined}),values:{...defaults,"optimat-rough-params":values["optimat-rough-params"] || "{}"}};
  }
  if (source.kind==="revisions") {
    const context=parse<AnalysisContext>(values["optimat-analysis-context"]);
    if (!context || context.projectUid!==owner.projectUid || context.projectId!==owner.projectId ||
      JSON.stringify(revisionSource(context))!==JSON.stringify(source)) throw mismatched();
  } else if (source.kind!=="file" || !/^[a-f0-9]{64}$/i.test(source.sha256)) throw mismatched();
  const rough=parse<{projectUid?:string;drawingId?:string;file?:string;reviewId?:string}>(values["optimat-rough"]);
  const receipt=parse<{projectUid?:string;drawingId?:string;file?:string;reviewId?:string}>(values["optimat-work-review"]);
  if (!rough || rough.projectUid!==s.projectUid || rough.drawingId!==s.drawingId || rough.file!==s.data.file || !rough.reviewId) {
    for (const key of ["optimat-rough","optimat-work-review","optimat-material-draft","optimat-material-selection","optimat-materials-ready","optimat-optimization"]) values[key]=defaults[key];
  } else if (!receipt || receipt.projectUid!==rough.projectUid || receipt.drawingId!==rough.drawingId || receipt.file!==rough.file || receipt.reviewId!==rough.reviewId) {
    for (const key of ["optimat-work-review","optimat-materials-ready","optimat-optimization","optimat-material-selection"]) values[key]=defaults[key];
  }
  return {review:row.review,values};
}
// Commit all active per-drawing keys before changing React state. Never touch the archive here.
export function installDrawing(owner:DraftOwner,expected:string|null,next:Bundle) {
  checkCurrent(owner,expected);reviewOf(next.review,owner);
  const values=Object.fromEntries(Object.keys(defaults).map(k=>[k,next.values[k] ?? defaults[k]]));
  const install=(review:string)=>{saveTogether({...values,"optimat-review":review});return review;};
  try {return install(next.review);} catch {
    try {return install(compact(next.review));} catch {throw Error("Chưa lưu được phiên mới. Bản vẽ hiện tại chưa chuyển.");}
  }
}
export function listProjectDrafts(owner:DraftOwner,history:ProjectHistory[]):DraftEntry[] {
  const result:DraftEntry[]=[];
  const add=(raw:string|undefined,key:string,source:string,bound:DraftOwner,time?:string)=>{
    if (!raw) return;
    try {const session=reviewOf(raw,bound,true);result.push({key,source,sourceUid:session.projectUid || bound.projectUid || "chưa có",otherSession:bound.projectUid!==owner.projectUid,time:session.savedAt || time,session});} catch { /* Foreign or unreadable legacy entry. */ }
  };
  const current=localStorage.getItem("optimat-review");checkCurrent(owner,current);
  add(current || undefined,"current","Đang mở",owner);
  for (const item of archiveOf(localStorage.getItem(DRAFTS_KEY),owner).items) add(item.review,"draft:"+item.id,"Đã lưu trước khi đổi bản vẽ",owner,item.at);
  for (const h of history) {
    try {
      const id=projectId(h.values["optimat-project"]);
      if (id !== owner.projectId) continue;
      const inner=parse<ReviewSession>(h.values["optimat-review"]);
      const uid=parse<string>(h.values["optimat-project-uid"]) || (id!==null && inner?.projectId===id ? inner.projectUid : undefined) || "";
      if (id===null && (!uid || uid!==owner.projectUid)) continue;
      const bound={projectUid:uid,projectId:id};
      add(h.values["optimat-review"],"history:"+h.id,"Lịch sử dự án trên trình duyệt",bound,h.at);
      for (const row of archiveOf(h.values[DRAFTS_KEY],bound).items) add(row.review,"history:"+h.id+":"+row.id,"Nháp trong lịch sử dự án",bound,row.at);
    } catch { /* Do not expose another project's or an invalid container's geometry. */ }
  }
  return result;
}
