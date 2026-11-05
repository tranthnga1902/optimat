"use client";
import { useEffect, useMemo, useState } from "react";
import { canConfirmWork, needsInput, type WorkReceipt, type WorkSnapshot } from "@/lib/work-review";
import { fmt, type Confirmed, type RoughWork, type WorkDimensions } from "./model";
import { Sheet } from "@/components/Sheet";
import { SelectedStairTrace, type ApplyStair } from "./StairTrace";
import { ColumnTrace, gridLabel, indexColumnWorks } from "./ColumnTrace";
import { MaterialAdvisor, type MaterialAdvisorReceipt } from "@/components/MaterialAdvisor";
import { uncheckedRowAdvice } from "./row-advisory";
import type { AnalysisReceipt } from "./read-progress";

const fields = [["count", "Số lượng"], ["length_m", "Dài (m)"], ["width_m", "Rộng (m)"], ["height_m", "Cao/sâu (m)"],
  ["thickness_m", "Dày (m)"], ["area_m2", "Diện tích (m²)"], ["opening_area_m2", "Lỗ mở (m²)"]] as const;
const detailFields = [...fields, ["repetitions", "Số lần lặp"], ["gross_length_m", "Dài gộp (m)"], ["deducted_length_m", "Dài khấu trừ (m)"],
  ["floor_height_m", "Cao tầng (m)"], ["concrete_height_m", "Cao bê tông (m)"], ["bottom_level_m", "Cao độ đáy (m)"],
  ["top_level_m", "Cao độ đỉnh (m)"], ["slope_ratio", "Hệ số dốc"], ["faces", "Số mặt"], ["top_length_m", "Dài đỉnh (m)"],
  ["top_width_m", "Rộng đỉnh (m)"], ["slope_length_m", "Dài nghiêng (m)"], ["diameter_m", "Đường kính (m)"], ["net_area_m2", "Diện tích thực (m²)"]] as const;
type Field = typeof detailFields[number][0];
const sources = { A: "A · Đọc trực tiếp", B: "B · Suy luận", C: "C · Tạm tính", D: "D · Thiếu dữ liệu" };
function number(d: WorkDimensions, key: Field) {
  if (d[key] != null) return fmt(d[key], 3);
  if (d.not_applicable_fields?.includes(key)) return "—";
  return "Chưa có";
}
function summary(w: RoughWork, key: Field) {
  const values = [...new Set((w.dimensions || []).map(d => number(d, key)))];
  if (values.length === 0) return w.basis === "not_supported" || w.basis === "ham_luong" ? "—" : "Chưa có";
  return values.length === 1 ? values[0] : `${values.length} giá trị`;
}
function quantityText(w: RoughWork) {
  if (w.basis === "structural_instance" && w.quantity_detail)
    return w.quantity_detail.total_raw?.replace(".", ",") ?? "Chưa đủ dữ liệu";
  return w.quantity == null ? "Chưa có" : w.quantity.toLocaleString("vi-VN", { maximumFractionDigits: 12 });
}
type AdvisorySource = {
  confirmations: Confirmed[]; analysis: AnalysisReceipt | null; isCurrent: () => boolean;
};

function RowAdvice({ snapshot, index, source }: { snapshot: WorkSnapshot; index: number; source: AdvisorySource }) {
  const [open, setOpen] = useState(false);
  const [receipt, setReceipt] = useState<MaterialAdvisorReceipt | null>(null);
  const [error, setError] = useState("");
  const advice = uncheckedRowAdvice(snapshot, index, source.confirmations);
  if (!advice) return null;
  const { context } = advice;
  const contextJson = JSON.stringify(context);
  const tooLarge = context.works.some(w => w.missing.length > 12 || w.missing.some(s => s.length > 300)) ||
    context.materials.length > 100 || context.materials.some(m => m.uses.length > 100 || m.sources.length > 8 ||
      m.missing.length > 300 || [...m.missing, ...m.sources].some(s => s.length > 300)) ||
    new TextEncoder().encode(contextJson).length > 60000;
  function isCurrent() {
    if (source.isCurrent()) return true;
    setOpen(false); setReceipt(null); setError("Bản khối lượng đã đổi. Hãy mở lại chi tiết công tác.");
    return false;
  }
  const download = () => {
    if (!receipt || receipt.contextJson !== contextJson || !isCurrent()) return;
    const row = snapshot.result.works[index];
    const blob = new Blob([JSON.stringify({ provenance: "client_snapshot", ...receipt,
      source: { project_id: advice.projectId, file: snapshot.file, confirmed_takeoff_id: advice.confirmedId,
        rough_takeoff_id: snapshot.result.takeoff_id ?? null, row_index: index, components: advice.components,
        formula: row.formula, dimensions: row.dimensions || [], input_sources: row.inputs || [],
        analysis_receipt: source.analysis, evidence: row.evidence || [],
        analysis_source_note: source.analysis ? "Biên nhận phân tích đã lưu trong phiên bản vẽ." : "Chưa có biên nhận phân tích gắn với phiên bản vẽ này." },
    }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a"); link.href = url; link.download = `tu-van-cong-tac-${receipt.requestId}.json`;
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <section aria-label="Tư vấn công tác chưa kiểm" className="mt-3">
    <p>{context.scope}</p>
    <p>Mã vật tư đối chiếu được: {context.materials.map(m => m.material_id).filter(Boolean).join(", ") || "Chưa xác định"}.
      {" "}Khối lượng và quy cách vẫn cần kiểm trước khi mua.</p>
    <button className="btn" type="button" aria-haspopup="dialog" disabled={tooLarge}
      onClick={() => { if (isCurrent()) setOpen(true); }}>Hỏi AI về công tác này</button>
    {tooLarge && <p>Dòng này vượt giới hạn dữ liệu của trợ lý.</p>}
    {error && <p role="alert">{error}</p>}
    <MaterialAdvisor context={context} open={open} onOpenChange={setOpen} initialQuestion={advice.question}
      onResult={value => { if (isCurrent() && value.contextJson === contextJson) setReceipt(value); }} />
    {receipt?.contextJson === contextJson && <button type="button" className="btn" onClick={download}>Tải biên nhận tư vấn (JSON)</button>}
  </section>;
}

export function WorkReview({ snapshot, initial, onApplyStair, onSave, advisory }: {
  onApplyStair?:ApplyStair; snapshot: WorkSnapshot; initial: WorkReceipt | null; onSave: (receipt: WorkReceipt, destination?: "/dieu-chinh" | "/toi-uu") => void;
  advisory: AdvisorySource;
}) {
  const [floor, setFloor] = useState("");
  const [code, setCode] = useState("");
  const [source, setSource] = useState("");
  const [filter, setFilter] = useState("");
  const [checked, setChecked] = useState<number[]>(initial?.checked || []);
  const [selected, setSelected] = useState<number | null>(null);
  const [partial, setPartial] = useState(!!initial?.partial);
  const [error, setError] = useState("");
  const rows = snapshot.result.works;
  const columns = useMemo(() => indexColumnWorks(snapshot), [snapshot]);
  const missing = rows.filter(needsInput);
  const unsupported = rows.filter(w => w.basis === "not_supported");
  const current = selected == null ? null : rows[selected];
  const level = (w: RoughWork) => w.plan || "Cả công trình";
  const save = (indices: number[], acceptPartial: boolean, destination?: "/dieu-chinh" | "/toi-uu") => {
    const { file, projectUid, drawingId, reviewId } = snapshot;
    try {
      onSave({ file, projectUid, drawingId, reviewId, checked: indices, partial: acceptPartial, confirmed: !!destination }, destination);
      setError("");
    } catch {
      setError("Chưa lưu được bản kiểm. Hãy giữ trang mở, kiểm tra dung lượng hoặc phiên dự án rồi thử lại.");
    }
  };
  useEffect(() => {
    if (!error) return;
    const block = (e: MouseEvent) => { if (e.target instanceof Element && e.target.closest("a[href]")) { e.preventDefault(); e.stopPropagation(); } };
    const unload = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = ""; };
    document.addEventListener("click", block, true); window.addEventListener("beforeunload", unload);
    return () => { document.removeEventListener("click", block, true); window.removeEventListener("beforeunload", unload); };
  }, [error]);
  const visible = rows.map((w, i) => ({ w, i })).filter(({ w, i }) =>
    (!floor || level(w) === floor) && (!code || w.code === code) && (!source || w.status === source) &&
    (!filter || (filter === "missing" && needsInput(w)) || (filter === "unchecked" && !checked.includes(i)) || (filter === "unsupported" && w.basis === "not_supported")));
  return <section className="flex min-w-0 flex-col gap-3">
    <h2>Công tác theo mặt bằng</h2>
    <p>{snapshot.file} · Tính lúc {new Date(snapshot.at).toLocaleString("vi-VN")}. Đây là khối lượng theo kích thước và cấu tạo hiện tại.</p>
    <p>Đủ dữ liệu: {rows.length - missing.length} · Cần bổ sung: {missing.length - unsupported.length} · Chưa hỗ trợ: {unsupported.length} · Chưa kiểm: {rows.length - checked.length}</p>
    <div className="flex flex-wrap gap-3">
      <label>Tầng <select className="field" value={floor} onChange={e => setFloor(e.target.value)}><option value="">Tất cả tầng</option>{[...new Set(rows.map(level))].map(p => <option key={p}>{p}</option>)}</select></label>
      <label>Công tác <select className="field" value={code} onChange={e => setCode(e.target.value)}><option value="">Tất cả công tác</option>{[...new Map(rows.map(w => [w.code, w.name]))].map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label>
      <label>Nguồn <select className="field" value={source} onChange={e => setSource(e.target.value)}><option value="">Mọi nguồn</option>{Object.entries(sources).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
      <label>Trạng thái <select className="field" value={filter} onChange={e => setFilter(e.target.value)}><option value="">Tất cả</option><option value="unchecked">Chưa kiểm</option><option value="missing">Còn thiếu</option><option value="unsupported">Chưa hỗ trợ</option></select></label>
      {/* Chỉ tác động các dòng đang hiện theo bộ lọc */}
      <label><input type="checkbox" disabled={!visible.length} checked={!!visible.length && visible.every(({ i }) => checked.includes(i))} onChange={e => {
        const ids = visible.map(({ i }) => i);
        const next = e.target.checked ? [...new Set([...checked, ...ids])] : checked.filter(j => !ids.includes(j));
        setChecked(next); save(next, partial);
      }} /> Đánh dấu đã kiểm tất cả ({visible.length} dòng đang hiện)</label>
    </div>
    <div className={current ? "grid min-w-0 grid-cols-[minmax(0,1fr)] gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,32%)]" : "min-w-0"}>
      <Sheet rows={visible} file="kiem-tra-cong-tac.csv" cols={[
        { key:"checked", title:"Đã kiểm", text:({i}) => checked.includes(i) ? "Đã kiểm" : "Chưa kiểm",
          render:({w,i}) => <input type="checkbox" aria-label={`Đã kiểm ${level(w)} · ${w.name} · ${i + 1}`} checked={checked.includes(i)} onChange={e => {
            const next = e.target.checked ? [...checked, i] : checked.filter(j => j !== i); setChecked(next); save(next, partial);
          }} /> },
        { key:"plan", title:"Tầng", text:({w}) => level(w) },
        { key:"work", title:"Công tác / cấu kiện", text:({w,i}) => [w.name,w.element,columns[i] && gridLabel(columns[i])].filter(Boolean).join(" · "),
          render:({w,i}) => <button className="btn" onClick={() => setSelected(i)}>{w.name} {columns[i] ? `${columns[i].code} · trục ${gridLabel(columns[i])}` : w.element}</button> },
        ...fields.map(([k,title]) => ({ key:k, title, num:true, text:({w}:{w:RoughWork}) => summary(w,k) })),
        { key:"quantity",title:"Khối lượng",num:true,text:({w}) => w.basis === "structural_instance" ? quantityText(w) : w.quantity == null ? "Chưa có" : String(w.quantity),
          render:({w}) => quantityText(w) },
        { key:"unit",title:"ĐVT",text:({w}) => w.unit }, { key:"source",title:"Nguồn",text:({w}) => w.status ? sources[w.status] : "Chưa phân loại" },
        { key:"missing",title:"Thông tin thiếu",text:({w}) => (w.basis === "not_supported" ? "Chưa hỗ trợ. " : "") + (w.missing.join("; ") || "—") },
      ]} />
      {current && <aside className="min-w-0 rounded border border-rule p-3" aria-label="Chi tiết công tác">
        <h3>{level(current)} · {current.element || current.name}</h3>
        {selected != null && <ColumnTrace snapshot={snapshot} selected={selected} columns={columns} />}
        {selected != null && <SelectedStairTrace onApply={onApplyStair} work={snapshot.result.works[selected]} plans={snapshot.request?.plans ?? []} />}
        <p>{current.formula || "Chưa có công thức"} · {quantityText(current)} {current.unit}</p>
        {current.quantity_detail ? <section aria-label="Diễn giải khối lượng">
          <h4>Diễn giải khối lượng ({current.quantity_detail.unit})</h4>
          <p>Phần đã tính <b>{current.quantity_detail.known_part_raw ?? "Chưa có"}</b> · {current.basis === "structural_instance" ? "Tổng theo quy ước của đoạn cột" : "Tổng đủ phạm vi"} <b>{current.quantity_detail.total_raw ?? "Chưa đủ dữ liệu"}</b></p>
          <p>Lượng trong kết quả tổng hợp {current.quantity_detail.legacy_quantity ?? "Chưa có"} · Chênh với phần đã tính {current.quantity_detail.legacy_delta ?? "Chưa xác định"}</p>
          <div className="tw"><table><thead><tr><th>Cấu kiện</th><th>Kích thước và hệ số</th><th>Lượng gốc</th><th>Nguồn và phần thiếu</th></tr></thead>
            <tbody>{current.quantity_detail.rows.map(r=><tr key={r.row_id}>
              <td>{r.group} {r.label}{r.role==="reference"&&<small> · Tham khảo</small>}</td>
              <td>{r.dimensions && detailFields.filter(([k])=>r.dimensions?.[k]!=null).map(([k,label])=><div key={k}>{label} · {r.dimensions![k]} {r.dimensions?.field_sources?.[k] && <small>({r.dimensions.field_sources[k]})</small>}</div>)}
                {r.factors.map((f,i)=><div key={i}>{f.meaning || f.name} × {f.value} {f.unit} · {f.source}</div>)}
                {r.conversion && <div>{r.conversion.from_unit} → {r.conversion.to_unit} × {r.conversion.factor} · {r.conversion.source}</div>}
                {r.expression}</td>
              <td>{r.raw_quantity==null?"Chưa có":(r.sign===-1?"−":"")+r.raw_quantity+" "+r.unit}</td>
              <td>{r.sources.join(" · ")}{r.missing.length>0 && <p>Cần bổ sung {r.missing.join(", ")}</p>}</td></tr>)}</tbody></table></div>
        </section>:<p>Chưa có diễn giải khối lượng theo cấu kiện cho dòng này.</p>}
        {(current.dimensions || []).map((d, i) => <section key={i}><strong>{d.label}</strong>
          {d.basis && <p>{{input: "Kích thước đầu vào", reference: "Kích thước tham khảo", union: "Phần hợp sau giao", deduction: "Khoản khấu trừ"}[d.basis]}</p>}
          <dl className="grid grid-cols-2 gap-x-3">{detailFields.filter(([k]) => !d.not_applicable_fields?.includes(k)).map(([k,title]) =>
            <div key={k}><dt>{title}</dt><dd>{number(d, k)} {d.field_sources?.[k] && <small>({d.field_sources[k]})</small>}</dd></div>)}</dl><p>{d.source} {d.note}</p></section>)}
        {!current.dimensions?.length && <p>Chưa có bảng kích thước riêng cho dòng này.</p>}
        <p>Nguồn đầu vào: {current.inputs?.join("; ") || "Chưa có"}.</p><p>Bằng chứng: {current.evidence?.join("; ") || "Chưa có vị trí liên kết trên bản vẽ"}.</p>
        <p>Cần bổ sung: {current.missing.join("; ") || "Không"}.</p>
        {selected != null && !checked.includes(selected) && <RowAdvice key={selected} snapshot={snapshot} index={selected} source={advisory} />}
      </aside>}
    </div>
    {!!missing.length && <details><summary>Phạm vi còn thiếu ({missing.length} dòng)</summary><ul>{missing.map((w, i) => <li key={i}>{level(w)} · {w.name} {w.element}: {w.missing.join("; ") || "Chưa đủ dữ liệu"}</li>)}</ul></details>}
    {!!missing.length && <label><input type="checkbox" checked={partial} onChange={e => { setPartial(e.target.checked); save(checked, e.target.checked); }} /> Tôi đã xem danh sách còn thiếu và đồng ý tiếp tục với phần khối lượng đã tính.</label>}
    <p>Lựa chọn từng dòng được lưu trong dự án. Kiểm đủ các dòng có khối lượng trước khi chuyển bước.</p>
    {error && <p role="alert">{error}</p>}
    <div className="flex gap-2"><button className="btn" onClick={() => save(checked, partial)}>Lưu kiểm tra</button>
      <button className="btn" disabled={!canConfirmWork(rows, checked, partial)} onClick={() => save(checked, partial, "/dieu-chinh")}>Xác nhận và chọn vật liệu</button>
      <button className="btn primary" disabled={!canConfirmWork(rows, checked, partial)} onClick={() => save(checked, partial, "/toi-uu")}>Xác nhận và xem phương án tối ưu</button></div>
    {!canConfirmWork(rows, checked, partial) && (() => {
      const unchecked = rows.filter((w, i) => w.quantity != null && w.basis !== "not_supported" && !checked.includes(i)).length;
      const available = rows.filter(w => w.quantity != null && w.basis !== "not_supported").length;
      return <p className="text-sm">Chưa xác nhận được vì: {!available ? "chưa có dòng nào có khối lượng." :
        unchecked ? `còn ${unchecked}/${available} dòng có khối lượng chưa đánh dấu đã kiểm (tích ô ở từng dòng trong bảng).` :
        "còn dòng thiếu dữ liệu; tích ô “đồng ý tiếp tục với phần khối lượng đã tính” ở trên."}</p>;
    })()}
  </section>;
}
