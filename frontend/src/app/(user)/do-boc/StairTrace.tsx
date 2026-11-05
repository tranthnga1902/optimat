import { useState } from "react";
import type { RoughWork } from "./model";

type Fields = Record<string, string | undefined>;
type Flight = { id:string; run_mm?:number|null; rise_mm?:number|null; width_mm?:number|null; waist_thickness_mm?:number|null; thickness_basis?:string|null; step_count?:number|null; tread_mm?:number|null; riser_mm?:number|null; field_sources?:Fields };
type Landing = { id:string; area_m2?:number|null; thickness_mm?:number|null; ownership?:"stair"|"floor"|"beam"|"unknown"; field_sources?:Fields };
export type StairScope = { id:string; from_floor?:string|null; to_floor?:string|null; scope_source?:string|null;
  waist_thickness_mm?:number|null; waist_thickness_basis?:string|null; waist_thickness_source?:string|null;
  steps_material?:"concrete"|"masonry"|"unknown"; steps_material_source?:string|null;
  flights?:Flight[]|null; landings?:Landing[]|null };
function Measure({label,value,unit,source}:{label:string;value?:number|string|null;unit?:string;source?:string|null}) {
  return <tr><th scope="row">{label}</th><td>{value == null || value === "" ? "Chưa có" : [value,unit].filter(x=>x!=null).join(" ")}</td><td>{source || "Chưa có nguồn"}</td></tr>;
}
function Scope({stair}:{stair:StairScope}) {
  return <div><h4>Thang {stair.id}</h4><div className="tw"><table><thead><tr><th>Dữ kiện</th><th>Giá trị</th><th>Căn cứ</th></tr></thead><tbody>
    <Measure label="Từ tầng" value={stair.from_floor} source={stair.scope_source}/>
    <Measure label="Đến tầng" value={stair.to_floor} source={stair.scope_source}/>
    <Measure label="Vật liệu bậc" value={({concrete:"Bê tông",masonry:"Bậc xây",unknown:"Chưa xác định"})[stair.steps_material || "unknown"]} source={stair.steps_material_source}/>
    <Measure label={stair.waist_thickness_basis==="normal"?"Dày bản thang theo phương vuông góc":"Dày bản thang"} value={stair.waist_thickness_mm} unit="mm" source={stair.waist_thickness_source}/>
    {stair.flights?.map(f=>([["run_mm","Chạy ngang","mm"],["rise_mm","Chênh cao","mm"],["width_mm","Rộng vế","mm"],["waist_thickness_mm","Dày bản riêng","mm"],["step_count","Số bậc","bậc"],["tread_mm","Mặt bậc","mm"],["riser_mm","Cao bậc","mm"]] as const).map(([k,label,u])=><Measure key={f.id+k} label={`Vế ${f.id} · ${label}`} value={f[k]} unit={u} source={f.field_sources?.[k]}/>))}
    {stair.landings?.map(l=>([["area_m2","Diện tích","m²"],["thickness_mm","Chiều dày","mm"],["ownership","Phạm vi tính",""]] as const).map(([k,label,u])=><Measure key={l.id+k} label={`Chiếu nghỉ ${l.id} · ${label}`} value={k==="ownership"?({stair:"Thang",floor:"Sàn",beam:"Dầm",unknown:"Chưa xác định"})[l.ownership || "unknown"]:l[k]} unit={u} source={l.field_sources?.[k]}/>))}
  </tbody></table></div>
  {!stair.flights?.length && <p>Chưa có dữ kiện từng vế.</p>}
  {!stair.landings && <p>Chưa xác định phạm vi chiếu nghỉ.</p>}
  {stair.steps_material==="masonry" && <p>Bậc xây được đối chiếu riêng với bê tông bản thang.</p>}
  </div>;
}

export function StairTrace({ work, stair }: { work: RoughWork; stair?:StairScope|null }) {
  const detail = work.quantity_detail;
  return <section aria-label="Căn cứ khối lượng cầu thang">
    <h3>{work.element || work.name}</h3>
    <p>{work.plan || "Chưa xác định mặt bằng"}</p>
    {stair && <Scope stair={stair}/>}
    {detail ? <>
      <dl className="grid gap-2 sm:grid-cols-2">
        <div><dt>Phần đã biết</dt><dd>{detail.known_part_raw == null ? "Chưa có lượng" : detail.known_part_raw + " " + detail.unit}</dd></div>
        <div><dt>Tổng đủ căn cứ</dt><dd>{detail.complete && detail.scope_complete && detail.total_raw != null ? detail.total_raw + " " + detail.unit : "Chưa đủ căn cứ"}</dd></div>
      </dl>
      <div className="tw"><table><thead><tr><th>Phần thang</th><th>Khoản lượng</th><th>Nguồn</th><th>Còn thiếu</th></tr></thead>
        <tbody>{detail.rows.map(row => <tr key={row.row_id}><th scope="row">{row.label}</th>
          <td>{row.role === "reference" ? "Tham chiếu · " : ""}{row.raw_quantity == null ? "Chưa có lượng" : (row.sign === -1 ? "−" : "") + row.raw_quantity + " " + row.unit}</td>
          <td>{row.sources.join(" · ") || "Chưa có nguồn"}</td><td>{row.missing.join(" · ") || "—"}</td></tr>)}</tbody>
      </table></div>
    </> : <p>Chưa có bảng diễn giải khối lượng cho thang này.</p>}
    {work.missing.length > 0 && <p>Cần bổ sung: {work.missing.join(" · ")}</p>}
  </section>;
}


export type ApplyStair = (plan:string, stairId:string, parts:unknown[])=>Promise<void>;
function EvidenceInput({apply}:{apply:(parts:unknown[])=>Promise<void>}) {
  const [note,setNote]=useState("");
  const [busy,setBusy]=useState(false);
  return <details><summary>Áp dụng dữ kiện có nguồn cho thang này</summary>
    <form onSubmit={async e=>{
      e.preventDefault(); if(busy)return;
      const text=String(new FormData(e.currentTarget).get("parts") || "");
      setBusy(true);try {
        const parts:unknown=JSON.parse(text);
        if(!Array.isArray(parts)||!parts.length)throw Error("Cần ít nhất một bộ phận có nguồn.");
        await apply(parts);
      } catch(error){setNote(error instanceof Error?error.message:"Chưa áp dụng được dữ kiện.");}
      finally{setBusy(false);}
    }}><label>Dữ kiện bộ phận (JSON parts của hồ sơ thang)<textarea name="parts" className="field w-full" required /></label>
    <p>Kiểm tra phiên bản tệp và vị trí nguồn trước khi tính lại. Kết quả cần được kiểm tra lại sau khi áp dụng.</p>
    <button type="submit" className="btn" disabled={busy}>Kiểm nguồn và tính lại</button><span role="status">{note}</span></form></details>;
}
export function SelectedStairTrace({work, plans, onApply}:{
  onApply?:ApplyStair; work:RoughWork;
  plans:readonly {name:string;stairs?:readonly {id?:string}[]}[];
}) {
  const masonry = work.code === "XAY" && work.basis === "stair_steps_masonry";
  const scope = work as RoughWork & {formwork_of?:string};
  if (!(work.code === "CAU_THANG" || masonry || (work.code === "COP_PHA" && scope.formwork_of === "CAU_THANG"))) return null;
  const matches = plans.filter(plan=>plan.name===work.plan).flatMap(plan=>
    (plan.stairs || []).filter(stair=>stair.id && work.element === (masonry ? "bậc xây thang " : "thang ") + stair.id));
  const stair = matches.length===1 && matches[0].id ? {...matches[0],id:matches[0].id} : null;
  return <><StairTrace work={work} stair={stair}/>{stair && work.plan && onApply && <EvidenceInput key={work.plan+":"+stair.id} apply={parts=>onApply(work.plan!,stair.id,parts)}/>}{!stair && <p>Chưa ghép được dòng công tác với một thang duy nhất trên mặt bằng này.</p>}</>;
}
