"use client";
import Link from "next/link";
import { useEffect, useRef, useState, useSyncExternalStore, type FormEvent } from "react";
import { Card, Icon, type IconName } from "@/components/ui";
import { store } from "@/lib/store";
import { projectUid, switchProject, type ProjectHistory, type ProjectInfo } from "@/lib/projects";
import { saveTogether } from "@/lib/review-session";
import { emptyProfile, infoFromProfile, jsonRequest, projectPath, projectResponse, profileUpdate, profileSources,
  type OwnedProject, type ProfileRecord, type ProfileSource, type SelectedRevision } from "@/lib/project-records";
import { ProjectDossier } from "./ProjectDossier";
import { ProjectNavigator, ProjectWorkspaceLayout } from "@/components/ProjectNavigator";

const subscribe = () => () => {};
const empty: ProjectInfo = { location:"", buildingType:"", floors:"", note:"", materialNeeds:"" };
const fold = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/đ/g,"d");
type FormValues = { name:string; info:ProjectInfo };
const active = ():FormValues => ({ name:store.get("optimat-project-name",""), info:store.get("optimat-project-info",null) || empty });
function historyInfo(item:ProjectHistory) { try {return JSON.parse(item.values["optimat-project-info"] || "{}") as ProjectInfo;} catch {return empty;} }
function projectTarget(title:string,info:ProjectInfo,id?:number):ProjectHistory {
  return {id:crypto.randomUUID(),name:title,at:new Date().toISOString(),values:{
    "optimat-project-name":JSON.stringify(title), "optimat-project-info":JSON.stringify(info),
    ...(id ? {"optimat-project":JSON.stringify(id)} : {})
  }};
}
function ProjectScreen() {
  const [saved,setSaved]=useState(active);
  const [form,setForm]=useState(saved);
  const [creating,setCreating]=useState(false), [editing,setEditing]=useState(false);
  const [showDetails,setShowDetails]=useState(()=>new URLSearchParams(location.search).has("ho-so"));
  const [history]=useState(()=>store.get<ProjectHistory[]>("optimat-project-history",[]));
  const [query,setQuery]=useState("");
  const [busy,setBusy]=useState(false), [error,setError]=useState(""), [notice,setNotice]=useState("");
  const [owned,setOwned]=useState<OwnedProject[]|null>(null), [serverError,setServerError]=useState("");
  const [linkedId]=useState(()=>Number(store.get("optimat-project","")) || null);
  const [profile,setProfile]=useState<ProfileRecord|null>(null), [created,setCreated]=useState<OwnedProject|null>(null);
  const [newProfile,setNewProfile]=useState<ProfileRecord>(emptyProfile);
  const [sources,setSources]=useState<ProfileSource[]>([]);
  const nameInput=useRef<HTMLInputElement>(null);
  const [sessionUid]=useState(projectUid);
  const [stale,setStale]=useState(false);
  const ensureActive=()=>{if(store.get("optimat-project-uid","")!==sessionUid)throw Error("Dự án đang mở đã đổi. Tải lại trang để tiếp tục.");};
  useEffect(()=>{
    const changed=(e:StorageEvent)=>{if(!e.key || ["optimat-project-uid","optimat-project","optimat-project-info"].includes(e.key))setStale(true);};
    window.addEventListener("storage",changed);
    return ()=>window.removeEventListener("storage",changed);
  },[]);
  const verified=owned?.find(p=>p.project_id===linkedId);
  const dirty=JSON.stringify(form)!==JSON.stringify(saved) || !!sources.length;
  const openDetails=()=>{setShowDetails(true);const url=new URL(location.href);url.searchParams.set("ho-so","1");window.history.replaceState(null,"",url);};
  useEffect(()=>{
    const controller=new AbortController();
    projectResponse<OwnedProject[]>("/api/projects",{signal:controller.signal}).then(list=>{
      if (!Array.isArray(list) || list.some(p=>!Number.isSafeInteger(p.project_id) || typeof p.name !== "string")) throw Error("Danh sách dự án máy chủ chưa đúng định dạng.");
      setOwned(list);
      const p=list.find(p=>p.project_id===linkedId);
      if(p) return projectResponse<ProfileRecord>(projectPath(p.project_id)+"/profile",{signal:controller.signal}).then(record=>{
        if(controller.signal.aborted || store.get("optimat-project-uid","")!==sessionUid)return;
        const values={name:p.name,info:infoFromProfile(p,record)};
        setSaved(values);setForm(values);setCreating(false);setProfile(record);
        saveTogether({"optimat-project-name":JSON.stringify(p.name),"optimat-project-info":JSON.stringify(values.info)});
      });
    }).catch(e=>{if (!controller.signal.aborted) setServerError(e instanceof Error?e.message:"Không tải được dự án trên máy chủ.");});
    return ()=>controller.abort();
  },[linkedId,sessionUid]);
  const reopen=(target:ProjectHistory)=>{
    if (busy || dirty) return;
    try { ensureActive(); switchProject(target); openDetails();location.reload(); } catch(e) {setError(e instanceof Error?e.message:"Chưa chuyển được dự án. Kiểm tra dung lượng trình duyệt rồi thử lại.");}
  };
  const create=()=>{openDetails();setCreating(true);setEditing(false);setCreated(null);setNewProfile(emptyProfile());setSources([]);setForm({name:"",info:{...empty}});setError("");setNotice(""); };
  const cancel=()=>{setForm(saved);setCreating(false);setEditing(false);setSources([]);setCreated(null);setError("");setNotice("");};
  const set=(key:keyof ProjectInfo,value:string)=>{setForm(old=>({...old,info:{...old.info,[key]:value}}));setNotice("");};
  const save=async(e:FormEvent)=>{
    e.preventDefault();if(busy)return;
    const title=form.name.trim(), note=form.info.note.trim();
    if(!title||!note){setError("Hãy nhập tên và mô tả để nhận diện dự án.");return;}
    const info={...form.info,note,updatedAt:new Date().toISOString()};
    setBusy(true);setError("");setNotice("");
    try {
      ensureActive();
      if(creating && owned===null && !serverError) throw Error("Đang xác minh dịch vụ dự án, hãy thử lại sau.");
      if(creating && !owned) {
        switchProject(projectTarget(title,info));
        location.reload();return;
      }
      if(creating || verified) {
        const p=creating ? created || await projectResponse<OwnedProject>("/api/projects",jsonRequest("POST",{name:title,address:info.location})) : verified!;
        if(creating)setCreated(p);
        if(!creating && !profile)throw Error("Chưa tải được phiên bản hồ sơ. Tải lại trước khi lưu.");
        const prev=creating ? newProfile : profile!;
        const record=await projectResponse<ProfileRecord>(projectPath(p.project_id)+"/profile",jsonRequest("PATCH",profileUpdate(prev,info,prev.payload.selected_revisions,sources)));
        if(creating)setNewProfile(record);else setProfile(record);
        setSources([]);info.profileVersion=record.version;
        if(p.name!==title || (p.address||"")!==info.location) {
          await projectResponse(projectPath(p.project_id),jsonRequest("PATCH",{name:title,address:info.location}));
        }
        setOwned(old=>(old||[]).map(x=>x.project_id===p.project_id?{...x,name:title,address:info.location}:x));
        ensureActive();
        if(creating){switchProject(projectTarget(title,info,p.project_id)); location.reload();return;}
      }
      saveTogether({"optimat-project-name":JSON.stringify(title),"optimat-project-info":JSON.stringify(info)});
      const current={name:title,info};setSaved(current);setForm(current);setEditing(false);setNotice(verified?`Đã lưu hồ sơ phiên bản ${info.profileVersion} trên máy chủ.`:"Đã lưu thông tin trên trình duyệt.");
    } catch (e) {setError(e instanceof Error?e.message:"Chưa lưu được thông tin. Giữ trang này mở rồi thử lại.");}
    finally {setBusy(false);}
  };
  const projectForm=<form onSubmit={save} aria-label="Thông tin công trình"><fieldset disabled={busy} className="grid gap-3 sm:grid-cols-2">
    <label className="grid gap-1">Tên dự án *<input ref={nameInput} className="field" required maxLength={160} value={form.name} onChange={e=>{setForm({...form,name:e.target.value});setNotice("");}} /></label>
    <label className="grid gap-1">Địa điểm<input className="field" maxLength={250} value={form.info.location || ""} onChange={e=>set("location",e.target.value)} /></label>
    <label className="grid gap-1">Loại công trình<input className="field" maxLength={120} value={form.info.buildingType || ""} onChange={e=>set("buildingType",e.target.value)} /></label>
    <label className="grid gap-1">Số tầng (tầng)<input className="field" type="number" min="1" step="1" value={form.info.floors || ""} onChange={e=>set("floors",e.target.value)} /></label>
    <label className="grid gap-1 sm:col-span-2">Mô tả *<textarea className="field" required rows={2} maxLength={500} value={form.info.note} onChange={e=>set("note",e.target.value)} /></label>
    <label className="grid gap-1 sm:col-span-2">Nhu cầu vật liệu (tùy chọn)<textarea className="field" rows={2} maxLength={1200} placeholder="Ví dụ: ưu tiên vật tư có sẵn ở địa phương" value={form.info.materialNeeds || ""} onChange={e=>set("materialNeeds",e.target.value)} /></label>
    <p className="m-0 text-sm text-muted sm:col-span-2">Ô bỏ trống là chưa có thông tin. Giá trị tự nhập có nguồn “Người dùng nhập”. {saved.info.updatedAt && !creating && `Lần lưu gần nhất: ${new Date(saved.info.updatedAt).toLocaleString("vi-VN")}.`}</p>
    <div className="flex flex-wrap items-center gap-2 sm:col-span-2"><button className="btn primary" disabled={busy} type="submit">{creating?"Tạo và mở dự án":"Lưu thông tin"}</button>
      <button type="button" className="btn" onClick={cancel}>Hủy</button>
      <span role="status">{notice || (dirty ? "Có thay đổi chưa lưu" : !creating ? verified ? `Hồ sơ máy chủ · phiên bản ${profile?.version ?? "…"}` : "Đã lưu trên trình duyệt" : "")}</span></div>
  </fieldset></form>;
  const details=editing || creating ? projectForm : <section aria-label="Thông tin công trình">
    <dl className="m-0 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{([
      ["Tên công trình", saved.name, "folder"], ["Địa điểm", saved.info.location, "pin"],
      ["Loại công trình", saved.info.buildingType, "building"], ["Số tầng", saved.info.floors && saved.info.floors+" tầng", "stack"],
      ["Nhu cầu vật liệu", saved.info.materialNeeds, "layers"], ["Nơi lưu", linkedId ? "Tài khoản" : "Trình duyệt", "db"],
      ["Mô tả", saved.info.note, "text"]
    ] as [string, string | undefined, IconName][]).map(([label,value,icon]) => <div key={label} className={`flex min-w-0 items-start gap-3 rounded-xl border border-rule2 bg-bg/60 p-3.5 ${label==="Mô tả" ? "col-span-full" : ""}`}>
      <span className="grid size-9 shrink-0 place-items-center rounded-lg border border-rule bg-card text-muted"><Icon name={icon} /></span>
      <div className="min-w-0"><dt className="text-xs font-medium text-muted">{label}</dt>
        <dd className={`m-0 mt-0.5 whitespace-pre-wrap break-words text-sm ${value ? "font-semibold" : "text-muted"}`}>{value || "Chưa cập nhật"}</dd></div>
    </div>)}</dl>
    {notice && <p role="status">{notice}</p>}</section>;
  if(stale)return <div role="status">Dữ liệu dự án đã đổi ở tab khác. <button className="btn" onClick={()=>location.reload()}>Tải lại dự án</button></div>;
  type ListRow={key:string;name:string;location:string;note:string;source:string;current?:boolean;open:()=>void};
  const rows:ListRow[]=[];
  const dbIds=new Set<number>();
  if(saved.name && (!linkedId || verified)){
    if(linkedId)dbIds.add(linkedId);
    rows.push({key:"active",...saved.info,name:saved.name,source:linkedId?"Tài khoản":"Trình duyệt",current:true,open:()=>{cancel();openDetails();}});
  }
  for(const item of history){
    const id=Number(item.values["optimat-project"]?.replaceAll('"',""));
    if(id && (dbIds.has(id)||!owned?.some(p=>p.project_id===id)))continue;
    if(id)dbIds.add(id);
    const p=owned?.find(p=>p.project_id===id), meta=historyInfo(item);
    rows.push({key:item.id,name:p?.name || item.name,location:p?.address || meta.location,note:meta.note,source:p?"Tài khoản":"Trình duyệt",open:()=>reopen(item)});
  }
  for(const item of owned||[])if(!dbIds.has(item.project_id))rows.push({key:"db-"+item.project_id,name:item.name,location:item.address||"",note:"",source:"Tài khoản",open:()=>reopen(projectTarget(item.name,{...empty},item.project_id))});
  const visible=rows.filter(row=>fold([row.name,row.location,row.note].join(" ")).includes(fold(query.trim())));
  const canEdit = !!saved.name && !creating && !editing && (!linkedId || !!(verified && profile));
  const startEdit = () => {setEditing(true);setNotice("");requestAnimationFrame(()=>nameInput.current?.focus());};
  const backToList = () => {
    setShowDetails(false);
    const url = new URL(location.href);
    url.searchParams.delete("ho-so");
    window.history.replaceState(null, "", url);
  };
  return <ProjectWorkspaceLayout detailOpen={showDetails} onBack={backToList} backDisabled={dirty || busy} navigator={
    <ProjectNavigator projects={visible.map(row => ({...row, current: row.current && !creating}))}
      totalCount={rows.length} query={query} onQueryChange={setQuery}
      onCreate={create} disabled={busy || dirty} createDisabled={creating} error={error} />
  }>
    <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-rule bg-card p-5">
      <div className="min-w-0"><div className="flex flex-wrap items-center gap-3"><h1 className="m-0 text-xl font-bold break-words">{creating ? "Tạo dự án" : saved.name && (!linkedId || verified) ? saved.name : "Dự án của tôi"}</h1>{saved.name && !creating && (!linkedId || verified) && <span className="pill ok">Đang mở</span>}</div>
        <p className="m-0 mt-1 text-sm text-muted">Thông tin dự án và hồ sơ nguồn</p></div>
      {canEdit && <button type="button" className="btn min-h-10 rounded-xl border-rule" onClick={startEdit}><Icon name="edit" size={16} className="text-muted" />Chỉnh sửa thông tin</button>}
    </header>
    {!creating&&!saved.name ? <p>Chọn một công trình để xem thông tin và bản vẽ kèm theo.</p> : !creating && linkedId && !verified ? <p role="status">{serverError || (owned?"Tài khoản hiện tại không có dự án máy chủ này. Chọn một dự án thuộc tài khoản.":"Đang kiểm tra quyền truy cập dự án…")}</p> : creating || !verified ? <>
      <Card title={creating?"Tạo dự án mới":"Thông tin công trình"}>{details}</Card>
      {creating && !owned && serverError && <p role="status">{serverError} Dự án mới hiện chỉ lưu được trên trình duyệt này.</p>}
      {!creating && <Card title="Hồ sơ gốc và căn cứ">
        <p>{serverError || (owned ? "Chọn dự án thuộc tài khoản để quản lý phiên bản tệp gốc." : "Đang tải hồ sơ dự án trên máy chủ…")}</p>
        {owned && <button className="btn" onClick={()=>{setCreating(true);setCreated(null);setNewProfile(emptyProfile());setNotice("Lưu để tạo dự án mới trên tài khoản bằng thông tin đang hiển thị.");}}>Tạo hồ sơ máy chủ từ thông tin này</button>}
        {!!store.get("optimat-review",null) && <Link className="btn" href="/do-boc">Mở bản bóc tách đã lưu</Link>}
      </Card>}
    </> : !profile ? <p role="status">{serverError || "Đang mở phiên bản thông tin công trình…"}</p> :
      <ProjectDossier key={verified.project_id} project={verified} info={saved.info} form={details} editing={editing} dirty={dirty||busy} getUid={()=>{ensureActive();return sessionUid;}}
        profile={profile} draft={form.info} sources={[...profileSources(profile),...sources]} onSource={s=>{
          setEditing(true);setForm(old=>({...old,info:{...old.info,[s.field]:String(s.value??"")}}));
          setSources(old=>[...old,s]);setNotice("Đã đưa dữ kiện vào bản nháp. Kiểm tra trước khi lưu.");
        }}
        persistSelection={async(refs:SelectedRevision[])=>{
          ensureActive();
          const rec=await projectResponse<ProfileRecord>(projectPath(verified.project_id)+"/profile",jsonRequest("PATCH",profileUpdate(profile,saved.info,refs)));
          ensureActive();const updated={...saved,info:{...saved.info,profileVersion:rec.version}};
          const cadKey=(list:SelectedRevision[])=>JSON.stringify(list.filter(f=>f.role!=="THAM_KHAO").map(f=>[f.file_id,f.revision_id,f.role,f.sha256]).sort());
          const changed=cadKey(profile.payload.selected_revisions)!==cadKey(rec.payload.selected_revisions);
          saveTogether({"optimat-project-info":JSON.stringify(updated.info),"optimat-project-files-selected":JSON.stringify(rec.payload.selected_revisions),
            ...(changed?{"optimat-work-review":"null","optimat-materials-ready":"false","optimat-optimization":"null","optimat-material-selection":"null"}:{})});
          setProfile(rec);setSaved(updated);setForm(updated);return rec.version;
        }}/>}
    {canEdit && <div className="flex flex-wrap items-center gap-2">
      <button type="button" className="btn" disabled aria-describedby="delete-status">Xóa</button>
      <small id="delete-status">Chức năng xóa công trình chưa được bật.</small></div>}
  </ProjectWorkspaceLayout>;
}
export function ProjectWorkspace() {
  const hydrated=useSyncExternalStore(subscribe,()=>true,()=>false);
  return hydrated ? <ProjectScreen/> : <p role="status">Đang mở dự án…</p>;
}
