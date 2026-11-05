"use client";

import { useState } from "react";
import { draftLabel, listProjectDrafts, type DraftEntry, type DraftOwner } from "@/lib/drawing-drafts";
import type { ProjectHistory } from "@/lib/projects";

const measure = (v:unknown) => typeof v === "number" && Number.isFinite(v) ? v.toLocaleString("vi-VN",{maximumFractionDigits:8}) : "chưa có";
export function DraftPreview({ entry }: { entry:DraftEntry }) {
  const s=entry.session;
  return <section aria-label="Chi tiết bản nháp" className="mt-3">
    <h3>{s.data.file}</h3>
    <p>{entry.source} · {draftLabel(s)} · UID nguồn {entry.sourceUid}{entry.otherSession && " · phiên cũ, chưa ghép"}</p>
    {s.data.plans.map((plan,i)=>{
      const state=s.states?.[i];
      const openings=state?.openings ?? [];
      return <div key={i}><h4>{plan.plan.name}</h4>
        {!state ? <p>Chưa có trạng thái chỉnh sửa cho mặt bằng này.</p> : !openings.length ? <p>Nháp này không chứa lỗ mở.</p> :
          <div className="overflow-auto"><table><thead><tr>
            {["ID lỗ","Tường cha","Nguồn","Giữ / bỏ","x (mm)","y (mm)","Rộng (mm)","Cao (mm)"].map(h=><th key={h}>{h}</th>)}
          </tr></thead><tbody>{openings.map((o,j)=><tr key={j}>
            <td>{o.id || "chưa có"}</td><td>{o.wall || "chưa có"}</td><td>{o.src==="manual" ? "Thêm tay" : o.src==="auto" ? "Tự động" : o.src || "chưa có"}</td>
            <td>{o.keep===true ? "Giữ" : o.keep===false ? "Bỏ" : "chưa có"}</td><td>{measure(o.x)}</td><td>{measure(o.y)}</td><td>{measure(o.w)}</td><td>{measure(o.h)}</td>
          </tr>)}</tbody></table></div>}
      </div>;
    })}
  </section>;
}
export function DrawingDraftHistory({ owner,history }: { owner:DraftOwner; history:ProjectHistory[] }) {
  const [rows,setRows]=useState<DraftEntry[]|null>(null),[selected,setSelected]=useState(""),[error,setError]=useState("");
  const read=()=>{
    try {setRows(listProjectDrafts(owner,history));setError("");setSelected("");}
    catch {setRows(null);setSelected("");setError("Không đọc được bản nháp của phiên dự án này.");}
  };
  const entry=rows?.find(r=>r.key===selected);
  return <section aria-label="Bản nháp bản vẽ" className="rounded-xl border border-rule p-4">
    <h2>Bản nháp bản vẽ</h2><p>Xem dữ liệu đã lưu trên trình duyệt của dự án đang mở.</p>
    <button className="btn" type="button" onClick={read}>{rows ? "Đọc lại danh sách" : "Xem danh sách bản nháp"}</button>
    {error && <p role="alert">{error}</p>}{rows && !rows.length && <p>Chưa tìm thấy bản nháp thuộc dự án này.</p>}
    {rows && rows.length>0 && <ul>{rows.map(r=><li key={r.key}><button className="btn" type="button" onClick={()=>setSelected(r.key)} aria-pressed={selected===r.key}>Xem nháp · {r.session.data.file}</button>
      {" · "}{r.source} · {draftLabel(r.session)}{r.otherSession && " · phiên cũ, chưa ghép · UID "+r.sourceUid}{r.time && " · "+r.time}</li>)}</ul>}
    {entry && <><DraftPreview entry={entry}/><button type="button" className="btn" onClick={()=>setSelected("")}>Đóng xem trước</button></>}
  </section>;
}
