"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { ProjectFilesPanel, type ProjectFileRevision, type FilePreview } from "@/components/ProjectFilesPanel";
import { checkedRevisions, projectPath, projectResponse, revisionPath, validPreview, selectedDto, type OwnedProject, type FileRole, type AnalysisContext, type ProfileRecord, type ProfileSource, type SelectedRevision } from "@/lib/project-records";
import type { ProjectInfo } from "@/lib/projects";
import { SheetFacts, type SheetData } from "./SheetFacts";
import { ReadPreview } from "../do-boc/ReadPreview";
import type { LinePreview } from "../do-boc/read-progress";

type Props={project:OwnedProject; info:ProjectInfo; form:ReactNode; editing:boolean; dirty:boolean; getUid:()=>string;profile:ProfileRecord;draft:ProjectInfo;
  sources:ProfileSource[];onSource:(s:ProfileSource)=>void;persistSelection:(r:SelectedRevision[])=>Promise<number>};
type UploadItem = { key: string; file: File; role: FileRole | ""; target: string; status: "ready" | "sending" | "saved" | "failed"; message?: string };
const roleLabels = { KT:"Kiến trúc", KC:"Kết cấu", HO_SO:"Hồ sơ", TIEN_LUONG:"Tiên lượng", THAM_KHAO:"Tham khảo" };
const fieldNames={location:"Địa điểm",buildingType:"Loại công trình",floors:"Số tầng",note:"Mô tả",materialNeeds:"Nhu cầu vật liệu"};
export function ProjectDossier({project,info,form,editing,dirty,getUid,profile,draft,sources,onSource,persistSelection}:Props) {
  const router=useRouter(), id=project.project_id, path=projectPath(id);
  const [files,setFiles]=useState<ProjectFileRevision[]>([]);
  const [selected,setSelected]=useState<number[]>(()=>profile.payload.selected_revisions.map(f=>f.revision_id));
  const [sheetData,setSheetData]=useState<SheetData|null>(null);
  const [view,setView]=useState<number>(), [preview,setPreview]=useState<FilePreview>({status:"idle"});
  const [queue,setQueue]=useState<UploadItem[]>([]),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true),[err,setErr]=useState("");
  const [tick,setTick]=useState(0);
  const [analysisAvailable,setAnalysisAvailable]=useState(false);
  const [allowAi,setAllowAi]=useState(false);
  const [sourceField,setSourceField]=useState<keyof typeof fieldNames>("note"),[position,setPosition]=useState("");
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
  const viewFile=async(file:ProjectFileRevision,sheet=1)=>{
    if(file.project_id!==id)return;
    viewing.current?.abort();const abort=new AbortController();viewing.current=abort;
    setSheetData(null);setView(file.revision_id);setPreview({status:"loading",revision_id:file.revision_id});
    try {
      const result=await projectResponse<{table?:SheetData;paragraphs?:{id:string;text:string}[];truncated?:boolean;revision_id?:number;sha256?:string;preview?:LinePreview;warnings?:string[];message?:string}>(revisionPath(file,"preview")+"?sheet="+sheet,{signal:abort.signal});
      if(abort.signal.aborted)return;
      if((result.revision_id!=null && result.revision_id!==file.revision_id) || (result.sha256 && result.sha256!==file.sha256))throw Error("Bản xem trả về không khớp phiên bản đã chọn.");
      if(result.table && result.revision_id===file.revision_id && result.sha256===file.sha256){
        setSheetData(result.table);
        setPreview({status:"unsupported",revision_id:file.revision_id,message:"Đối chiếu dữ kiện bảng tính trong mục hồ sơ gốc."});return;
      }
      if(result.paragraphs && result.revision_id===file.revision_id && result.sha256===file.sha256){
        const paragraphs=result.paragraphs;
        setPreview({status:"ready",revision_id:file.revision_id,warnings:result.truncated?["Chỉ hiện 2.000 đoạn đầu."]:[],
          content:<div className="absolute inset-0 overflow-auto p-3 text-[13px]">{paragraphs.length?<ol className="m-0 pl-[22px]">{paragraphs.map(p=><li key={p.id} title={p.id}>{p.text}</li>)}</ol>:<p className="text-muted">Tệp DOCX không có đoạn văn.</p>}</div>});
        return;
      }
      if(!validPreview(result.preview)){setPreview({status:"unsupported",revision_id:file.revision_id,message:result.message || "Không có nét xem trước cho định dạng này. Có thể tải nguyên bản để đối chiếu."});return;}
      setPreview({status:"ready",revision_id:file.revision_id,warnings:result.warnings,content:<div className="absolute inset-0 [&_svg]:h-full [&_svg]:w-full"><ReadPreview preview={result.preview} label="Các nét từ phiên bản bản vẽ gốc"/></div>});
    } catch(e) {if(!abort.signal.aborted)setPreview({status:"error",revision_id:file.revision_id,message:e instanceof Error?e.message:"Chưa mở được bản xem trước."});}
  };
  const updateItem=(key:string, change:Partial<UploadItem>) =>
    setQueue(items => items.map(item => item.key === key ? {...item,...change} : item));
  const upload=async(items:UploadItem[])=>{
    if (!items.length || busy || uploading.current) return;
    if (items.some(item => !item.role)) { setErr("Chọn vai trò cho từng bản vẽ CAD đang chờ tải."); return; }
    const abort=new AbortController();
    uploading.current=abort;
    setBusy(true);
    let savedAny=false;
    try {
      for (const item of items) {
        if (abort.signal.aborted) break;
        updateItem(item.key,{status:"sending",message:undefined});
        try {
          getUid();
          const data=new FormData();
          data.set("file",item.file);
          data.set("role",item.role);
          if (item.target) data.set("file_id",item.target);
          await projectResponse(path+"/files",{method:"POST",body:data,signal:abort.signal});
          if (!abort.signal.aborted) {
            updateItem(item.key,{status:"saved"});
            savedAny=true;
          }
        } catch(e) {
          if (!abort.signal.aborted) updateItem(item.key,{status:"failed",message:e instanceof Error ? e.message : "Chưa lưu được tệp."});
        }
      }
    } finally {
      uploading.current=null;
      if (!abort.signal.aborted) {
        setBusy(false);
        if(savedAny){setLoading(true);setTick(t=>t+1);}
      }
    }
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
      const context:AnalysisContext={projectUid:getUid(),projectId:id,revisions,profile:{...info,profileVersion:version},allowAi};
      sessionStorage.setItem("optimat-analysis-start",JSON.stringify({token,context}));
      router.push("/do-boc?analysis="+token);
    } catch(e){setBusy(false);setErr(e instanceof Error?e.message:"Chưa chuyển được bộ hồ sơ sang bóc tách.");}
  };
  return <ProjectFilesPanel projectId={id} projectInfo={form} files={files} selectedRevisionIds={selected} viewingRevisionId={view}
    preview={preview} busy={busy} loading={loading} error={err} onView={viewFile} onDownload={f=>{
      if(f.project_id===id){const a=document.createElement("a");a.href=revisionPath(f,"original");a.download=f.name;a.click();}
    }} onSelectionChange={select} onStartAnalysis={start} startBlockedReason={!analysisAvailable?"Máy chủ chưa bật phân tích từ bản gốc đã lưu.":dirty?"Lưu thay đổi thông tin trước khi bắt đầu phân tích.":undefined}
    analysisContext={<div><p>Thông tin công trình · phiên bản {profile.version}. {info.note || "Chưa có mô tả."} {info.materialNeeds && `Nhu cầu: ${info.materialNeeds}`}</p>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={allowAi} onChange={e=>setAllowAi(e.target.checked)}/>Cho phép AI (OpenAI) đọc chữ ghi chú, tiêu đề của hồ sơ để gợi ý thông số. Không bật với hồ sơ không được gửi ra ngoài.</label>
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
      {shown && sheetData && <SheetFacts table={sheetData} draft={draft} changeSheet={n=>void viewFile(shown,n)} apply={(field,value,cell)=>onSource({field,value,source:"document",document:selectedDto(shown),unit:field==="floors"?"tầng":undefined,location:{table:sheetData.sheet_name,cell}})} />}
      <label>Chọn tệp hồ sơ <input type="file" multiple aria-describedby="project-file-formats" accept=".dwg,.dxf,.docx,.xls,.xlsx" disabled={busy} onChange={e=>{
        const added=Array.from(e.currentTarget.files || [],(file):UploadItem=>({
          key:crypto.randomUUID(),file,target:"",status:"ready",
          role:/\.(dwg|dxf)$/i.test(file.name) ? "" : /\.xlsx?$/i.test(file.name) ? "TIEN_LUONG" : "HO_SO"
        }));
        setQueue(items=>[...items,...added]);e.currentTarget.value="";
      }}/></label>
      <small id="project-file-formats">Bắt buộc bản vẽ DWG hoặc DXF. Tùy chọn: dự toán XLS, XLSX và thuyết minh DOCX. Không nhận PDF, ảnh; tệp Word .doc cũ hãy lưu thành .docx.</small>
      {!!queue.length && <div className="w-full space-y-2">
        {queue.map(item=><div key={item.key} className="flex flex-wrap items-center gap-2 rounded border border-slate-200 p-3">
          <strong className="break-all">{item.file.name}</strong>
          <label>Vai trò <select className="field" aria-label={`Vai trò của ${item.file.name}`} disabled={busy||item.status==="saved"} value={item.role} onChange={e=>updateItem(item.key,{role:e.target.value as FileRole})}>
            {!item.role && <option value="">Chọn vai trò bản vẽ…</option>}
            {Object.entries(roleLabels).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
          <label>Lưu vào <select className="field" disabled={busy||item.status==="saved"} value={item.target} onChange={e=>updateItem(item.key,{target:e.target.value})}>
            <option value="">Tệp mới</option>{[...new Map(files.map(f=>[f.file_id,f])).values()].map(f=><option key={f.file_id} value={f.file_id}>Phiên bản mới · {f.name}</option>)}</select></label>
          <span role="status">{{ready:"Chờ tải",sending:"Đang tải…",saved:"Đã lưu",failed:item.message}[item.status]}</span>
          {item.status==="failed" && <button type="button" className="btn" disabled={busy} onClick={()=>void upload([item])}>Thử lại</button>}
          {item.status!=="saved" && <button type="button" className="btn" disabled={busy} onClick={()=>setQueue(items=>items.filter(row=>row.key!==item.key))}>Bỏ khỏi danh sách</button>}
        </div>)}
        {queue.some(i=>i.status==="ready" && !i.role) && <p>Chọn Kiến trúc cho mặt bằng nhà, Kết cấu cho bản vẽ móng, cột, dầm, sàn hoặc Tham khảo nếu chỉ cần lưu bản gốc.</p>}
        <button type="button" className="btn primary" disabled={busy||!queue.some(i=>i.status==="ready")||queue.some(i=>i.status==="ready" && !i.role)} onClick={()=>void upload(queue.filter(i=>i.status==="ready"))}>Tải các tệp đang chờ</button>
      </div>}
      <button className="btn" type="button" disabled={busy||loading} onClick={()=>{setErr("");setLoading(true);setTick(t=>t+1);}}>Tải lại danh sách</button>
      {busy && <span role="status">Đang lưu bản gốc…</span>}
    </div>} />;
}
