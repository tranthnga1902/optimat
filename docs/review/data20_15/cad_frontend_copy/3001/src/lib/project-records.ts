import type { ProjectFileRevision } from "@/components/ProjectFilesPanel";
import type { ProjectInfo } from "./projects";
import type { LinePreview } from "@/app/(user)/do-boc/read-progress";

export type OwnedProject = { project_id: number; name: string; address?: string };
export type FileRole = NonNullable<ProjectFileRevision["role"]>;
export type RevisionRef = Pick<ProjectFileRevision,"project_id"|"file_id"|"revision_id"|"version"|"sha256"|"role"|"name">;
export class ProjectApiError extends Error {
  constructor(readonly status: number, message: string) { super(message); }
}
export async function projectResponse<T>(path: string, options: RequestInit = {}): Promise<T> {
  const r = await fetch(path, {credentials:"same-origin", cache:"no-store", ...options});
  const body = await r.json().catch(() => null);
  if (!r.ok) {
    const fallback = r.status === 403 || r.status === 401 ? "Phiên hiện tại không có quyền mở hồ sơ này."
      : r.status === 404 ? "Máy chủ chưa cung cấp hồ sơ hoặc chức năng này." : "Yêu cầu hồ sơ không thành công.";
    throw new ProjectApiError(r.status, typeof body?.detail === "string" && body.detail !== "Not Found" ? body.detail : fallback);
  }
  return body as T;
}
export const projectPath = (id: number) => {
  if (!Number.isSafeInteger(id) || id <= 0) throw new Error("Cần mở một dự án thuộc tài khoản trên máy chủ.");
  return "/api/projects/" + id;
};
export const revisionPath = (file: RevisionRef, kind: "original" | "preview") =>
  projectPath(file.project_id) + "/files/" + file.file_id + "/revisions/" + file.revision_id + "/" + kind;
export function revisionRef(f: ProjectFileRevision): RevisionRef {
  const {project_id,file_id,revision_id,version,sha256,role,name}=f;
  return {project_id,file_id,revision_id,version,sha256,role,name};
}
export function checkedRevisions(projectId: number, ids: number[], files: ProjectFileRevision[]) {
  if (!ids.length || new Set(ids).size !== ids.length) throw new Error("Chọn lại bộ phiên bản cần phân tích.");
  const refs=ids.map(id => {
    const f=files.find(x=>x.project_id===projectId && x.revision_id===id);
    if (!f || !f.version || !f.role || !/^[a-f\d]{64}$/i.test(f.sha256 || "")) throw new Error("Phiên bản tệp đã thay đổi hoặc thiếu thông tin. Hãy tải lại danh sách.");
    return revisionRef(f);
  });
  if (new Set(refs.map(f=>f.file_id)).size !== refs.length) throw new Error("Chỉ chọn một phiên bản cho mỗi tệp.");
  if (!refs.some(f=>f.role === "KT")) throw new Error("Cần một bản kiến trúc để bắt đầu phân tích.");
  return refs;
}
export function validPreview(v: LinePreview | undefined): v is LinePreview {
  return !!v && Array.isArray(v.size) && v.size.length === 2 && v.size.every(n=>Number.isFinite(n) && n>0) &&
    Array.isArray(v.segments) && v.segments.every(s=>Array.isArray(s) && s.length === 4 && s.every(Number.isFinite));
}
export type AnalysisContext = { projectUid: string; projectId: number; profile: ProjectInfo; revisions: RevisionRef[] };
export type SelectedRevision = Pick<RevisionRef,"file_id"|"revision_id"|"sha256"|"role">;
export type SourceLocation = {page?:number|null;floor?:string|null;table?:string|null;cell?:string|null;cad_handle?:string|null};
type SourceValue = {value:string|number|boolean|null;source:"manual"|"document"|"unknown";unit?:string|null;document?:SelectedRevision|null;location?:SourceLocation|null};
export type ProfileSource = SourceValue & {field:string};
export type ProfileRecord = {version:number;payload:{design_facts:Record<string,string>;material_preferences:Record<string,string>;
  source_values:Record<string,SourceValue>;effective_values:Record<string,string>;selected_revisions:SelectedRevision[]}};
export const emptyProfile=():ProfileRecord=>({version:0,payload:{design_facts:{},material_preferences:{},source_values:{},effective_values:{},selected_revisions:[]}});
export const selectedDto=({file_id,revision_id,sha256,role}:SelectedRevision)=>({file_id,revision_id,sha256,role});
export function infoFromProfile(_project:OwnedProject,profile:ProfileRecord):ProjectInfo {
  const str=(k:string)=>String(profile.payload.source_values[profile.payload.effective_values[k]]?.value ?? "");
  return {location:str("location"),buildingType:str("buildingType"),floors:str("floors"),note:str("note"),materialNeeds:str("materialNeeds"),profileVersion:profile.version};
}
export function profileSources(profile:ProfileRecord):ProfileSource[] {
  const fields={...profile.payload.design_facts,...profile.payload.material_preferences,...profile.payload.effective_values};
  return Object.entries(profile.payload.source_values).map(([key,v])=>({...v,field:Object.keys(fields).find(k=>fields[k]===key) || key.split("@")[0]}));
}
export function profileUpdate(prev:ProfileRecord,info:ProjectInfo,selected:SelectedRevision[]=prev.payload.selected_revisions,extra:ProfileSource[]=[]){
  const payload={design_facts:{...prev.payload.design_facts},material_preferences:{...prev.payload.material_preferences},
    effective_values:{...prev.payload.effective_values},source_values:{...prev.payload.source_values},selected_revisions:selected.map(selectedDto)};
  const record=({field,...v}:ProfileSource)=>{
    const key=field+"@"+crypto.randomUUID();
    payload.source_values[key]=v;
    (field==="materialNeeds"?payload.material_preferences:payload.design_facts)[field]=key;
    payload.effective_values[field]=key;
  };
  for(const source of extra)record(source);
  for(const field of ["location","buildingType","floors","note","materialNeeds"] as const){
    const raw=info[field]?.trim() || "";
    const old=payload.source_values[payload.effective_values[field]];
    if(old && String(old.value??"")===raw || !old && !raw)continue;
    record({field,source:raw?"manual":"unknown",value:raw?(field==="floors"?Number(raw):raw):null,unit:field==="floors"?"tầng":undefined});
  }
  return {expected_version:prev.version,payload};
}
export const jsonRequest=(method:string,value:unknown):RequestInit=>({method,headers:{"Content-Type":"application/json"},body:JSON.stringify(value)});
