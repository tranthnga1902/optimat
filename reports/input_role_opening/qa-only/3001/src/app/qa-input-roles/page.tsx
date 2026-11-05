"use client";

import { useEffect, useState } from "react";
import { ProjectFilesPanel, type ProjectFileRevision } from "@/components/ProjectFilesPanel";
import { emptyProfile } from "@/lib/project-records";
import { ProjectDossier } from "./DossierFixture";

const project = { project_id: 701, name: "Dự án kiểm thử" };
const info = { location:"", buildingType:"", floors:"", note:"", materialNeeds:"" };
function file(id: number, role: ProjectFileRevision["role"], changes: Partial<ProjectFileRevision> = {}): ProjectFileRevision {
  return { project_id:project.project_id,file_id:id,revision_id:id,version:1,sha256:"a".repeat(64),name:"Mẫu-"+id+".dwg",
    original_format:"dwg",size_bytes:2000,role,uploaded_at:null,...changes };
}
const kt = file(11,"KT",{name:"Mặt bằng mẫu.dwg"}), kc = file(21,"KC",{name:"Kết cấu mẫu.dxf",original_format:"dxf"});
const prior = file(12,"KT",{file_id:kt.file_id,version:2,name:kt.name});
const note = file(31,"THAM_KHAO",{name:"Ghi chú mẫu.pdf",original_format:"pdf"});
const cases = [
  { label:"Chưa chọn",files:[kt,kc],selected:[] },
  { label:"Chỉ kiến trúc",files:[kt,kc],selected:[11] },
  { label:"Chỉ kết cấu",files:[kt,kc],selected:[21] },
  { label:"Kiến trúc và kết cấu",files:[kt,kc],selected:[11,21] },
  { label:"Hai phiên bản của một tệp",files:[kt,prior],selected:[11,12] },
  { label:"Mã kiểm tra không hợp lệ",files:[{...kt,sha256:"sai"}],selected:[11] },
  { label:"Tài liệu ngoài CAD trong bộ đã lưu",files:[kt,note],selected:[11,31] },
];
function Panel({ scenario }: { scenario: typeof cases[number] }) {
  const [selected,setSelected] = useState<number[]>(scenario.selected);
  const [message,setMessage] = useState("");
  return <>
    <p aria-live="polite">Phiên bản đang chọn: {selected.join(", ") || "chưa chọn"}. {message}</p>
    <ProjectFilesPanel projectId={project.project_id} projectInfo={project.name}
      files={scenario.files} selectedRevisionIds={selected} preview={{status:"idle"}}
      onSelectionChange={ids=>{setSelected(ids);setMessage("");}}
      onStartAnalysis={()=>setMessage("Đã bấm Bắt đầu phân tích trong mẫu kiểm thử.")}
      onView={f=>setMessage("Đã chọn xem "+f.name)} onDownload={f=>setMessage("Đã bấm tải "+f.name+" trong mẫu kiểm thử.")} />
  </>;
}
export default function InputRolesFixture() {
  const [mode,setMode]=useState(0);
  const [sent,setSent]=useState<string[]>([]);
  useEffect(()=>{
    const capture=(event:Event)=>{
      const {name,role}=(event as CustomEvent<{name:string;role:string}>).detail;
      setSent(items=>[...items,name+" · "+role]);
    };
    window.addEventListener("qa-input-upload",capture);
    return ()=>window.removeEventListener("qa-input-upload",capture);
  },[]);
  return <main className="p-5"><h1>Kiểm thử vai trò bản vẽ</h1>
    <p>Mẫu tổng hợp, thao tác chỉ có hiệu lực trong trang này.</p>
    <label>Ca kiểm thử <select value={mode} onChange={e=>{setSent([]);setMode(Number(e.target.value));}}>
      {cases.map((c,i)=><option key={c.label} value={i}>{c.label}</option>)}
      <option value={cases.length}>Chọn vai trò trước khi tải</option>
    </select></label>
    {mode===cases.length
      ? <><p role="status">Mô phỏng tải trong bộ nhớ · {sent.length} tệp. {sent.join(", ")}</p>
          <ProjectDossier project={project} info={info} draft={info} form={project.name} profile={emptyProfile()} editing={false}
            dirty={false} getUid={()=>"fixture"} sources={[]} onSource={()=>{}} persistSelection={async()=>1} /></>
      : <Panel key={mode} scenario={cases[mode]} />}
  </main>;
}
