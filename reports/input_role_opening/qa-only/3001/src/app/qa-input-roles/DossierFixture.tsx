"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useRouter, projectResponse, fixtureStorage as sessionStorage } from "./fixture-api";
import { ProjectFilesPanel, type ProjectFileRevision, type FilePreview } from "@/components/ProjectFilesPanel";
import { checkedRevisions, projectPath, revisionPath, validPreview, selectedDto, type OwnedProject, type FileRole, type AnalysisContext, type ProfileRecord, type ProfileSource, type SelectedRevision } from "@/lib/project-records";
import type { ProjectInfo } from "@/lib/projects";
import { ReadPreview } from "@/app/(user)/do-boc/ReadPreview";
import type { LinePreview } from "@/app/(user)/do-boc/read-progress";

type Props={project:OwnedProject; info:ProjectInfo; form:ReactNode; editing:boolean; dirty:boolean; getUid:()=>string;profile:ProfileRecord;draft:ProjectInfo;
  sources:ProfileSource[];onSource:(s:ProfileSource)=>void;persistSelection:(r:SelectedRevision[])=>Promise<number>};
const fieldNames={location:"Địa điểm",buildingType:"Loại công trình",floors:"Số tầng",note:"Mô tả",materialNeeds:"Nhu cầu vật liệu"};
export function ProjectDossier({project,info,form,editing,dirty,getUid,profile,draft,sources,onSource,persistSelection}:Props) {
  const router=useRouter(), id=project.project_id, path=projectPath(id);
  const [files,setFiles]=useState<ProjectFileRevision[]>([]);
  const [selected,setSelected]=useState<number[]>(()=>profile.payload.selected_revisions.map(f=>f.revision_id));
  const [view,setView]=useState<number>(), [preview,setPreview]=useState<FilePreview>({status:"idle"});
  const [pending,setPending]=useState<File|null>(null);
  const [role,setRole]=useState<FileRole | "">(""),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[err,setErr]=useState("");
  const [tick,setTick]=useState(0);
  const [analysisAvailable,setAnalysisAvailable]=useState(false);
  const [replace,setReplace]=useState<number|null>(null),[sourceField,setSourceField]=useState<keyof typeof fieldNames>("note"),[position,setPosition]=useState("");
  const shown=files.find(f=>f.revision_id===view);
  const viewing=useRef<AbortController|null>(null),uploading=useRef<AbortController|null>(null);
  useEffect(()=>()=>{viewing.current?.abort();uploading.current?.abort();},[]);
  useEffect(()=>{
    const controller=new AbortController();
    projectResponse<{paths:Record<string,{post?:unknown}>}>("/openapi.json",{signal:controller.signal}).then(schema=>{
      if(!controller.signal.aborted)setAnalysisAvailable(!!schema.paths["/api/projects/{project_id}/analysis"]?.post);
    }).catch(()=>{});
    return ()=>controller.abort();
  },[]);
  useEffect(()=>{
    const abort=new AbortController();
    projectResponse<ProjectFileRevision[]>(path+"/files",{signal:abort.signal}).then(rows=>{
      if (!Array.isArray(rows) || rows.some(f=>f.project_id!==id || !Number.isSafeInteger(f.revision_id) || !Number.isSafeInteger(f.file_id))) throw Error("Danh sách phiên bản máy chủ không khớp dự án.");
      if(!abort.signal.aborted){setFiles(rows);setLoading(false);}
    }).catch(e=>{if(!abort.signal.aborted){setErr(e.message);setLoading(false);setFiles([]);}});
    return ()=>abort.abort();
  },[id,path,tick]);
  const select=(ids:number[])=>{
    try {
      const added=ids.find(n=>!selected.includes(n));
      const newFile=files.find(f=>f.revision_id===added);
      if(newFile) ids=ids.filter(n=>n===added || files.find(f=>f.revision_id===n)?.file_id!==newFile.file_id);
      const refs=ids.map(n=>files.find(f=>f.project_id===id && f.revision_id===n));
      if(refs.some(f=>!f)) throw Error("Danh sách đã đổi.");
      setSelected(ids);setErr("");
    } catch {setErr("Chưa lưu được bộ phiên bản đã chọn. Hãy tải lại danh sách hoặc kiểm tra dung lượng.");}
  };
  const viewFile=async(file:ProjectFileRevision)=>{
    if(file.project_id!==id)return;
    viewing.current?.abort();const abort=new AbortController();viewing.current=abort;
    setView(file.revision_id);setPreview({status:"loading",revision_id:file.revision_id});
    try {
      const result=await projectResponse<{revision_id?:number;sha256?:string;preview?:LinePreview;warnings?:string[];message?:string}>(revisionPath(file,"preview"),{signal:abort.signal});
      if(abort.signal.aborted)return;
      if((result.revision_id!=null && result.revision_id!==file.revision_id) || (result.sha256 && result.sha256!==file.sha256))throw Error("Bản xem trả về không khớp phiên bản đã chọn.");
      if(!validPreview(result.preview)){setPreview({status:"unsupported",revision_id:file.revision_id,message:result.message || "Không có nét xem trước cho định dạng này. Có thể tải nguyên bản để đối chiếu."});return;}
      setPreview({status:"ready",revision_id:file.revision_id,warnings:result.warnings,content:<div className="absolute inset-0 [&_svg]:h-full [&_svg]:w-full"><ReadPreview preview={result.preview} label="Các nét từ phiên bản bản vẽ gốc"/></div>});
    } catch(e) {if(!abort.signal.aborted)setPreview({status:"error",revision_id:file.revision_id,message:e instanceof Error?e.message:"Chưa mở được bản xem trước."});}
  };
  const upload=async(file?:File)=>{
    if(!file||busy||uploading.current)return;
    if (!role) {setErr("Chọn vai trò của bản vẽ trước khi tải lên.");return;}
    const abort=new AbortController();uploading.current=abort;setBusy(true);setErr("");
    try {
      const data=new FormData(); data.set("file",file); data.set("role",role);
      if(replace!=null)data.set("file_id",String(replace));
      await projectResponse(path+"/files",{method:"POST",body:data,signal:abort.signal});
      if(!abort.signal.aborted){setPending(null);setRole("");setLoading(true);setTick(t=>t+1);}
    } catch(e) {if(!abort.signal.aborted)setErr(e instanceof Error?e.message:"Chưa lưu được tệp gốc.");}
    finally {if(uploading.current===abort)uploading.current=null; if(!abort.signal.aborted)setBusy(false);}
  };
  const refList=()=>checkedRevisions(id,selected,files);
  const refsChanged=JSON.stringify([...selected].sort())!==JSON.stringify(profile.payload.selected_revisions.map(f=>f.revision_id).sort());
  const start=async()=>{
    try {
      if(dirty||busy||loading||!analysisAvailable) return;
      setBusy(true);setErr("");
      const revisions=refList();
      if(!refsChanged && revisions.some(f=>!profile.payload.selected_revisions.some(s=>s.file_id===f.file_id && s.revision_id===f.revision_id && s.sha256===f.sha256 && s.role===f.role))) throw Error("Phiên bản đã đổi. Hãy chọn lại trước khi phân tích.");
      const version=refsChanged ? await persistSelection(revisions) : profile.version;
      const token=crypto.randomUUID();
      const context:AnalysisContext={projectUid:getUid(),projectId:id,revisions,profile:{...info,profileVersion:version}};
      sessionStorage.setItem("optimat-analysis-start",JSON.stringify({token,context}));
      router.push("/do-boc?analysis="+token);
    } catch(e){setBusy(false);setErr(e instanceof Error?e.message:"Chưa chuyển được bộ hồ sơ sang bóc tách.");}
  };
  return <ProjectFilesPanel projectId={id} projectInfo={form} files={files} selectedRevisionIds={selected} viewingRevisionId={view}
    preview={preview} busy={busy} loading={loading} error={err} onView={viewFile} onDownload={()=>{}} onSelectionChange={select} onStartAnalysis={start} startBlockedReason={!analysisAvailable?"Máy chủ chưa bật phân tích từ bản gốc đã lưu.":dirty?"Lưu thay đổi thông tin trước khi bắt đầu phân tích.":undefined}
    analysisContext={<div><p>Thông tin công trình · phiên bản {profile.version}. {info.note || "Chưa có mô tả."} {info.materialNeeds && `Nhu cầu: ${info.materialNeeds}`}</p>
      {refsChanged && <button type="button" className="btn" disabled={busy||dirty} onClick={async()=>{
        setBusy(true);setErr("");try{await persistSelection(files.filter(f=>selected.includes(f.revision_id)).map(selectedDto));}
        catch(e){setErr(e instanceof Error?e.message:"Chưa lưu được lựa chọn.");}finally{setBusy(false);}
      }}>Lưu bộ tệp đã chọn</button>}</div>}
    sourceContext={<div><h3>Căn cứ của thông tin công trình</h3>
      {sources.length ? <ul>{sources.map((s,i)=><li key={i}>{fieldNames[s.field as keyof typeof fieldNames] || s.field}: {String(s.value ?? "Chưa có")} {s.unit}
        {" · "}{s.source==="document" && s.document ? <button type="button" className="btn" onClick={()=>{
          const f=files.find(x=>x.file_id===s.document!.file_id && x.revision_id===s.document!.revision_id && x.sha256===s.document!.sha256);
          if(f)void viewFile(f);else setErr("Không tìm thấy phiên bản nguồn trong dự án.");
        }}>Xem bản nguồn {files.find(f=>f.revision_id===s.document!.revision_id)?.name} · {Object.values(s.location||{}).filter(Boolean).join(" · ") || "chỉ biết tệp"}</button> : s.source==="manual"?"Người dùng nhập":"Chưa xác định nguồn"}</li>)}</ul> : <p>Chưa có nguồn tệp được liên kết.</p>}
      {editing && shown && preview.status==="ready" && preview.revision_id===shown.revision_id && <div className="flex flex-wrap gap-2">
        <label>Giá trị cần đối chiếu <select className="field" value={sourceField} onChange={e=>setSourceField(e.target.value as keyof typeof fieldNames)}>
          {Object.entries(fieldNames).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
        <label>Tầng trong bản vẽ (nếu biết) <input className="field" maxLength={120} value={position} onChange={e=>setPosition(e.target.value)}/></label>
        <button className="btn" disabled={!draft[sourceField] || busy} onClick={()=>onSource({field:sourceField,value:sourceField==="floors"?Number(draft.floors):draft[sourceField]||null,source:"document",
          unit:sourceField==="floors"?"tầng":undefined,document:selectedDto(shown),location:position.trim()?{floor:position.trim()}:undefined})}>Gắn bản đang xem làm nguồn</button>
      </div>}</div>}
    uploadControls={<div className="flex flex-wrap items-end gap-3">
      <label>Chọn bản vẽ gốc <input type="file" accept=".dwg,.dxf" disabled={busy} onChange={e=>{
        const file=e.currentTarget.files?.[0];e.currentTarget.value="";
        if (file) {setPending(file);setRole("");setErr("");}
      }}/></label>
      {pending && <strong>{pending.name}</strong>}
      <label>Vai trò của tệp <select className="field" value={role} disabled={busy || !pending} onChange={e=>setRole(e.target.value as FileRole)}>
        <option value="">Chọn vai trò bản vẽ…</option><option value="KT">Kiến trúc</option><option value="KC">Kết cấu</option><option value="THAM_KHAO">Tham khảo</option>
      </select></label>
      {!!files.length && <label>Lưu vào <select className="field" value={replace ?? ""} onChange={e=>setReplace(e.target.value?Number(e.target.value):null)}>
        <option value="">Tệp mới</option>{[...new Map(files.map(f=>[f.file_id,f])).values()].map(f=><option key={f.file_id} value={f.file_id}>Phiên bản mới · {f.name}</option>)}</select></label>}
      {pending && !role && <p>Chọn Kiến trúc cho mặt bằng nhà, Kết cấu cho móng, cột, dầm, sàn hoặc Tham khảo để lưu bản gốc.</p>}
      <button type="button" className="btn primary" disabled={busy || !pending || !role} onClick={()=>void upload(pending ?? undefined)}>Tải bản vẽ gốc</button>
      <button className="btn" type="button" disabled={busy||loading} onClick={()=>{setErr("");setLoading(true);setTick(t=>t+1);}}>Tải lại danh sách</button>
      {busy && <span role="status">Đang lưu bản gốc…</span>}
    </div>} />;
}
