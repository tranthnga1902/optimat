"use client";
import { useMemo, useState, type ReactNode } from "react";
import type { WorkReceipt, WorkSnapshot } from "@/lib/work-review";
import { adviceScope, rowName, type AdviceSelection } from "./advice-scope";
import s from "./material-sheet.module.css";

type Context = ReturnType<typeof adviceScope>;
type Props = {
  work: WorkSnapshot; receipt: WorkReceipt; version?: string; disabled: boolean;
  choices: AdviceSelection[]; catalogOptions: { id: string; name: string; raw: string; wallClasses?: string[] }[];
  onPick: (choice: AdviceSelection | null, rowIndex: number | null, lineId: string) => void;
  params: Record<string,string>; fields: { key: string; label: string; options: [string,string][] }[];
  onParam: (key: string, value: string) => void;
  assistant: (context: Context, select: (lineId: string, materialId: string) => void, open:boolean, changeOpen:(value:boolean)=>void) => ReactNode;
};
const displayNumber = new Intl.NumberFormat("vi-VN", {minimumFractionDigits:2, maximumFractionDigits:12});
const number = (value: number | null) => value == null ? "Chưa có" : displayNumber.format(value);
const fold = (text: string) => text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");

const concrete = new Set(["MONG","COT","DAM","SAN","MAI","CAU_THANG","LANH_TO","GIANG_TUONG","SE_NO"]);
function relatedField(uses: Context["materials"][number]["uses"]) {
  const codes = new Set(uses.map(u => u.work));
  if (codes.size && [...codes].every(code => concrete.has(code))) return "concrete_grade";
  if (codes.size !== 1) return null;
  const [code] = codes;
  return ({ BE_TONG_LOT:"lean_concrete_grade", TRAT:"plaster_mortar_grade", CAN_NEN:"screed_mortar_grade",
    CHONG_THAM:"waterproof_material_id", COP_PHA:"formwork_type" } as Record<string,string>)[code] || null;
}
export function AdviceSheet({ work, receipt, version, disabled, choices, catalogOptions, onPick, params, fields, onParam, assistant }: Props) {
  const [row, setRow] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  const [table, setTable] = useState<"materials" | "works">("materials");
  const [compareId, setCompareId] = useState("");
  const [copied, setCopied] = useState("");
  const [askOpen,setAskOpen]=useState(false);
  const context = useMemo(() => adviceScope(work, receipt, row, version), [work, receipt, row, version]);
  const shown = context.materials.filter(m => fold([m.material_id, m.name, ...m.uses.map(u => u.work)].join(" ")).includes(fold(filter.trim())));
  const shownWork = context.works.filter(w => fold([w.code, w.plan, work.result.works[w.rowIndex].name, w.element].join(" ")).includes(fold(filter.trim())));
  const eligible = catalogOptions.filter(o => context.materials.some(m => m.raw_class === o.raw && m.material_id && m.material_id !== o.id) &&
    (!o.wallClasses || context.works.some(w => w.checked && w.code === "XAY" && o.wallClasses!.includes(work.result.works[w.rowIndex].masonry_geometry?.wall_type || ""))));
  const suggestedIds = [...new Set(eligible.filter(o => o.wallClasses || o.raw === "chong_tham").map(o => o.id))];
  const detailText=(s:string)=>s.length>300?s.slice(0,268)+"… (xem nguyên văn trong bảng)":s;
  const reasons=(list:string[])=>list.length>12?[...list.slice(0,11).map(detailText),`Còn ${list.length-11} lý do thiếu. Xem đầy đủ trong bảng.`]:list.map(detailText);
  const questionContext = { ...context, proposedMaterialIds: compareId ? [compareId] : suggestedIds.length <= 30 ? suggestedIds : [],
    works:context.works.map(w=>({...w,missing:reasons(w.missing)})),
    materials:context.materials.map(m=>({...m,missing:reasons(m.missing),sources:m.sources.map(detailText),uses:m.uses.map(u=>({...u,via:detailText(u.via)}))})) };
  const tooLarge = context.works.length > 300 || context.materials.length > 100 || context.intermediates.length > 40 ||
    context.materials.some(m => m.uses.length > 100) ||
    new TextEncoder().encode(JSON.stringify(questionContext)).length > 60_000;
  const pick = (lineId: string, materialId: string) => {
    const line = context.materials.find(m => m.lineId === lineId);
    if (disabled || !line?.material_id || !materialId) return;
    onPick({ originalId: line.material_id, materialId, originalName: line.name, scope: context.scope, lineId, reviewId: work.reviewId,
      rowIndex: row, disposition: line.material_id === materialId ? "specified" : "proposed" }, row, lineId);
  };
  const copyTable = async () => {
    const rows = table === "materials" ? [
      ["Mã vật tư","Tên vật tư","ĐVT","Nhu cầu","Sau hao hụt","Phương án chọn"],
      ...shown.map(m => [m.material_id, m.name, m.unit, m.quantity, m.quantity_with_waste,
        choices.find(c => c.reviewId === work.reviewId && c.rowIndex === row && c.lineId === m.lineId)?.materialId || ""])
    ] : [["Tầng","Công tác","Cấu kiện","Khối lượng","ĐVT","Trạng thái"],
      ...shownWork.map(w => [w.plan,work.result.works[w.rowIndex].name,w.element,w.quantity,w.unit,w.status])];
    const cell = (v: string | number | null | undefined) => {
      if (typeof v === "number") return v.toLocaleString("vi-VN", {useGrouping:false, maximumFractionDigits:12});
      const value = (v ?? "").replace(/[\t\r\n]/g," ");
      return /^[\s]*[=+@-]/.test(value) ? "'" + value : value;
    };
    try { await navigator.clipboard.writeText(rows.map(r => r.map(cell).join("\t")).join("\r\n")); setCopied("Đã sao chép các dòng đang hiển thị. Có thể dán vào Excel."); }
    catch { setCopied("Trình duyệt chưa cho sao chép. Bạn có thể chọn các ô trực tiếp trong bảng."); }
  };
  return <section className="flex min-w-0 flex-col gap-3" aria-label="Tư vấn và chọn vật liệu phần thô">
    <label className="font-semibold">Phạm vi tư vấn <select className="field max-w-full" value={row ?? ""} onChange={e => {
      setRow(e.target.value === "" ? null : Number(e.target.value)); setFilter(""); setCompareId("");
    }}><option value="">Cả dự án · toàn bộ phần thô</option>
      {receipt.checked.toSorted((a,b) => a-b).map(i => work.result.works[i] && <option key={i} value={i}>{rowName(work.result.works[i], i)}</option>)}
    </select></label>
    {receipt.partial && <p className={s.note}>Bản kiểm một phần. Dòng thiếu dữ liệu vẫn được đánh dấu trong bảng công tác.</p>}
    <div className={s.sheet}>
      <div className={s.sheetTop}>
        <button type="button" className="btn" aria-pressed={table === "materials"} onClick={() => setTable("materials")}>Vật tư ({context.materials.length})</button>
        <button type="button" className="btn" aria-pressed={table === "works"} onClick={() => setTable("works")}>Công tác ({context.works.length})</button>
        <label>Tìm trong bảng <input type="search" className="field" placeholder="Mã hoặc tên…" value={filter} onChange={e => setFilter(e.target.value)} /></label>
        <button type="button" className="btn" onClick={copyTable}>Sao chép sang Excel</button>
        <button type="button" className="btn" aria-haspopup="dialog" disabled={disabled||tooLarge} onClick={() => setAskOpen(true)}>Hỏi trợ lý về phạm vi này</button>
      </div>
      {copied && <p className="px-3 text-sm" role="status">{copied}</p>}
      <div className={s.scroll} tabIndex={0} role="region" aria-label="Bảng dữ liệu có thể cuộn">
        {table === "materials" ? <table className={s.grid} aria-label="Bảng lựa chọn vật tư phần thô">
          <thead><tr>{["STT","Mã vật tư","Tên vật tư","ĐVT","Nhu cầu","Sau hao hụt","Phương án chọn","Nguồn và phần thiếu"].map(title => <th key={title} scope="col">{title}</th>)}</tr></thead>
          <tbody>{shown.map(line => {
            const choice = choices.find(c => c.rowIndex === row && c.lineId === line.lineId && c.originalId === line.material_id && c.reviewId === work.reviewId);
            const field = line.material_id ? undefined : fields.find(f => f.key === relatedField(line.uses));
            return <tr key={line.lineId}><th scope="row">{Number(line.lineId.slice(1))+1}</th><td>{line.material_id || "Chưa có mã"}</td><td>{line.name}</td><td>{line.unit || "—"}</td>
              <td className={s.num}>{number(line.quantity)}</td><td className={s.num}>{number(line.quantity_with_waste)}</td>
              <td>{line.material_id ? <select aria-label={`Phương án cho ${line.name} (${line.lineId})`} value={choice?.materialId || ""} disabled={disabled}
                onChange={e => { if (e.target.value) pick(line.lineId, e.target.value); else onPick(null, row, line.lineId); }}>
                <option value="">Chọn phương án…</option><option value={line.material_id}>Giữ mã {line.material_id} theo bảng</option>
                {choice && choice.materialId !== line.material_id && <option value={choice.materialId}>{choice.materialId} · chờ kiểm thiết kế</option>}
              </select> : field?.options?.length ? <label><small>{field.label} · cả dự án</small><select aria-label={`${field.label} cho ${line.name}`}
                value={params[field.key] || ""} disabled={disabled} onChange={e => onParam(field.key,e.target.value)}>
                <option value="">Chọn theo thiết kế…</option>{field.options.map(([v,label]) => <option key={v} value={v}>{label}</option>)}
              </select></label> : "Bổ sung quy cách trước khi chọn"}</td>
              <td><details><summary>{line.complete ? "Xem căn cứ" : "Cần bổ sung"}</summary>{[...line.sources,...line.missing].map((v,i) => <div key={i}>{v}</div>)}</details></td></tr>;
          })}</tbody></table> :
        <table className={s.grid} aria-label="Bảng khối lượng lắp đặt"><thead><tr>{["STT","Tầng","Công tác","Cấu kiện","Khối lượng","ĐVT","Trạng thái","Căn cứ / phần thiếu"].map(title => <th key={title} scope="col">{title}</th>)}</tr></thead>
        <tbody>{shownWork.map(w => <tr key={w.rowIndex}><th scope="row">{w.rowIndex+1}</th><td>{w.plan || "Cả công trình"}</td><td>{w.checked ?
          <button className={s.workLink} title="Xem vật tư và hỏi về công tác này" onClick={() => { setRow(w.rowIndex); setFilter(""); setCompareId(""); setTable("materials"); }}>{work.result.works[w.rowIndex].name}</button> :
          work.result.works[w.rowIndex].name}</td><td>{w.element || "—"}</td><td className={s.num}>{number(w.quantity)}</td>
          <td>{w.unit}</td><td>{w.checked ? "Đã kiểm" : "Ngoài phần đã kiểm"} · {w.status || "—"}</td><td>{w.missing.join("; ") || work.result.works[w.rowIndex].formula}</td></tr>)}</tbody></table>}
      </div>
      <p className="px-3 py-1 text-sm" role="status">{table === "materials" ? shown.length : shownWork.length} dòng trong phạm vi đang xem. {table === "materials" && !context.materials.length ? "Chưa có vật tư liên kết. Xem phần thiếu ở bảng Công tác." : ""}</p>
    </div>
    <p className={s.note}>Nhu cầu và hao hụt lấy từ bản tính. Lượng cần đặt mua còn phụ thuộc tồn kho, vật tư đã đặt và quy cách đóng gói.</p>
    {choices.length > 0 && <details><summary>Phương án đang chọn ({choices.length})</summary><ul>{choices.map(c => <li key={c.reviewId+":"+c.rowIndex+":"+c.lineId}>{c.originalName} · {c.materialId} · {c.scope}{c.reviewId !== work.reviewId ? " · thuộc bản kiểm cũ, cần chọn lại" : c.disposition === "proposed" ? " · cần duyệt thay thế" : ""}</li>)}</ul></details>}
    {eligible.length > 0 && <label>Ưu tiên mã để so sánh <select className="field" disabled={disabled} value={compareId} onChange={e => setCompareId(e.target.value)}>
      <option value="">Tự tra phương án theo bản khối lượng</option>{eligible.map(o => <option key={o.id} value={o.id}>{o.id} · {o.name}</option>)}
    </select><span className={s.note}> Mã thay thế cần kiểm lại thiết kế trước khi áp dụng.</span></label>}
    {tooLarge ? <p role="status">Phạm vi này vượt giới hạn một câu hỏi. Chọn từng công tác để hỏi. Bảng vẫn giữ đủ các dòng.</p> :
      assistant(questionContext, pick,askOpen,setAskOpen)}
  </section>;
}
