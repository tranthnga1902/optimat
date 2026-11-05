"use client";
// Tab Phần thô: form thông số công trình và mặt bằng, kết quả máy chủ tính (công tác, cốp pha, vật liệu, chi tiết theo tầng).
import s from "./review.module.css";
import { ChangeInput } from "./ChangeInput";
import { MATERIAL_PARAMS } from "@/lib/review-session";
import { useReference } from "@/lib/reference";
import { PP, fmt, roughFields, type Plan, type PlanParams, type Rough, type RoughResult, type Status, type Structural } from "./model";

const missTip = (list?: string[]) => (list || []).join("; ");
// trạng thái dữ liệu (đặc tả 30/10 mục 3): C luôn ghi "tạm tính", D không ra số
const ST: Record<string, string> = { A: "A đọc", B: "B suy", C: "C tạm tính", D: "D thiếu" };
const Badge = ({ st, tip }: { st?: Status; tip?: string }) => st ? <span className={`${s.tag} ${st === "C" || st === "D" ? s.low : ""}`} title={tip}>{ST[st]}</span> : null;

function RoughResultView({ R }: { R: Rough }) {
  if (!R) return <p style={{ color: "var(--muted)", margin: 0 }}>Bổ sung thông số hình học và bấm Tính khối lượng; chưa cần chọn vật liệu. Các công tác chưa đủ dữ liệu sẽ ghi rõ thông tin cần bổ sung.</p>;
  if ("error" in R) return <ul className={s.warn}><li>{R.error}</li></ul>;
  const r: RoughResult = R;
  const why = (code: string) => r.works.filter((w) => w.code === code && w.missing.length).flatMap((w) => w.missing.map((m) => (w.plan ? w.plan + ": " : "") + m));
  const low = (t: string, title?: string) => <span className={`${s.tag} ${s.low}`} title={title}>{t}</span>;
  const plans = [...new Set(r.works.map((w) => w.plan || "Cả công trình"))];
  return <>
    <p className={s.label}>Khối lượng công tác (cộng các tầng) <Badge st={r.status} tip="Trạng thái xấu nhất của toàn bảng" /></p>
    <div style={{ overflowX: "auto" }}><table><thead><tr><th>Công tác</th><th className={s.num}>Khối lượng</th><th>ĐVT</th><th>Trạng thái</th><th></th></tr></thead><tbody>
      {r.totals.map((t, i) => <tr key={i}><td>{t.name}</td><td className={s.num}>{t.quantity == null ? "" : fmt(t.quantity)}</td><td>{t.unit}</td><td><Badge st={t.status} /></td>
        <td>{t.complete ? "" : low("còn thiếu", missTip([...new Set(why(t.code))]))}</td></tr>)}
    </tbody></table></div>
    {(r.formwork || []).length > 0 && <>
      <p className={s.label}>Cốp pha theo cấu kiện</p>
      <div style={{ overflowX: "auto" }}><table><tbody>{r.formwork!.map((f, i) => <tr key={i}><td>{f.name}</td><td className={s.num}>{f.quantity == null ? "" : fmt(f.quantity)}</td><td>m²</td><td><Badge st={f.status} /></td><td>{f.complete ? "" : low("còn thiếu")}</td></tr>)}</tbody></table></div>
    </>}
    <p className={s.label}>Chi tiết theo tầng</p>
    {plans.map((pl) => <details key={pl}><summary>{pl}</summary><div style={{ overflowX: "auto" }}><table><tbody>
      {r.works.filter((w) => (w.plan || "Cả công trình") === pl).map((w, i) => <tr key={i}><td>{w.name}<br /><small style={{ color: "var(--muted)" }}>{w.element || ""}</small></td>
        <td><small>{w.formula}</small>{w.missing.length > 0 && <><br />{low("thiếu: " + w.missing.join(", "))}</>}</td>
        <td className={s.num}>{w.quantity == null ? "" : fmt(w.quantity, 3)} {w.unit}</td><td><Badge st={w.status} tip={(w.inputs || []).join("; ")} /></td></tr>)}
    </tbody></table></div></details>)}
    {r.warnings.length > 0 && <><p className={s.label}>Cảnh báo</p><ul className={s.warn} style={{ padding: 0 }}>{r.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></>}
    {r.takeoff_id ? <p>Đã lưu vào dự án (mã kết quả {r.takeoff_id}).</p> : null}
  </>;
}

export function RoughTab({ P, pp, values, rough, busy, onParam, onPlanParam, onRun, structural, onStructural }: {
  P: Plan; pp: PlanParams; values: Record<string, string>; rough: Rough; busy: boolean;
  onParam: (k: string, v: string) => void; onPlanParam: (k: string, v: string | boolean) => void; onRun: () => void;
  structural: Structural | { error: string } | { busy: string } | null; onStructural: (f: File | undefined) => void;
}) {
  const cols = pp.cols;
  const { ref, error } = useReference();
  const suggestions: Record<string, string[]> = {
    concrete_grade: ref?.concrete_grades || [], lean_concrete_grade: ref?.concrete_grades || [],
    masonry_mortar_grade: ref?.mortar_grades || [], plaster_mortar_grade: ref?.mortar_grades || [],
    screed_mortar_grade: ref?.mortar_grades || [], plaster_thickness_mm: ref?.plaster_thicknesses || [],
    screed_thickness_mm: ref?.screed_thicknesses || [],
  };
  return (
    <div className={s.qty}>
      <p className={s.label}>Bản vẽ kết cấu</p>
      <div className={s.actions} style={{ justifyContent: "flex-start", alignItems: "center" }}>
        <label className={s.btn}>{structural && "file" in structural ? "Đổi bản vẽ kết cấu…" : "Mở bản vẽ kết cấu…"}
          <input type="file" accept=".dxf,.dwg" hidden onChange={(e) => { onStructural(e.target.files?.[0]); e.target.value = ""; }} /></label>
        <span style={{ color: "var(--muted)", fontSize: 12.5 }}>
          {!structural ? "Chưa có: dầm suy từ tường và cột, móng chưa tính. Mở file kết cấu (móng, dầm, cột, bảng thép) nếu tách riêng."
            : "busy" in structural ? structural.busy
            : "error" in structural ? <span className={`${s.tag} ${s.low}`}>{structural.error}</span>
            : `${structural.file}: ${Object.keys(structural.structural_beams || {}).length} mặt bằng dầm, ${structural.foundations.length} loại móng.`}
        </span>
      </div>
      {structural && "notes" in structural && structural.notes.length > 0 &&
        <details><summary>Ghi chú đọc kết cấu ({structural.notes.length})</summary><ul className={s.warn} style={{ padding: 0 }}>{structural.notes.map((n, i) => <li key={i}>{n}</li>)}</ul></details>}
      <p className={s.label}>Thông số tính phần thô</p>
      <p style={{ margin: 0, color: "var(--muted)" }}>Chọn vật liệu ở bước tiếp theo. Thông số kết cấu được bổ sung từ bản vẽ khi có dữ liệu; các giá trị còn thiếu có thể nhập tại đây.</p>
      {error && <p role="alert" className={s.warn}>Chưa tải được danh mục đề xuất: {error}. Bạn có thể nhập thông số riêng hoặc tải lại trang.</p>}
      {!ref && !error && <p role="status">Đang tải thông số tham khảo…</p>}
      {/* gợi ý mác bê tông: biến thể BE_TONG_TRON trong rough_norms */}
      <datalist id="concrete-grades">{(ref?.concrete_grades || []).map((g) => <option key={g} value={g} />)}</datalist>
      {roughFields(ref).map(([title, fields]) => [title, fields.filter(([key]) => !MATERIAL_PARAMS.has(key))] as const).filter(([, fields]) => fields.length > 0).map(([title, fields]) => (
        <fieldset key={title} className={s.rfs}><legend>{title}</legend>
          {fields.map(([k, label, type, ph]) => (
            <label key={k} className={s.rf}><span>{label}</span>
              {suggestions[k]?.length > 0 && <>
                <select aria-label={`Đề xuất ${label.toLowerCase()}`} value={suggestions[k].includes(values[k] || "") ? values[k] : ""}
                  onChange={(e) => onParam(k, e.target.value)}>
                  <option value="">{values[k] ? "Thông số riêng" : "Chọn phương án đề xuất…"}</option>
                  {suggestions[k].map((v) => <option key={v} value={v}>{v}{k.endsWith("_mm") ? " mm" : ""}</option>)}
                </select>
                <small>Đề xuất từ dữ liệu · có thể sửa bên dưới</small>
              </> }
              {Array.isArray(type)
                ? <select value={String(values[k] || "")} onChange={(e) => onParam(k, e.target.value)}>{type.map(([val, txt]) => <option key={val} value={val}>{txt}</option>)}</select>
                : <ChangeInput {...(type === "num" ? { type: "number", min: k === "natural_ground_level_mm" ? undefined : 0, step: "any" } : { type: "text" })} list={type === "grade" ? "concrete-grades" : undefined}
                  value={values[k] ?? ""} placeholder={ph || (suggestions[k] ? "Hoặc nhập thông số riêng" : "Bổ sung nếu bản vẽ chưa có")}
                  onCommit={(el) => {
                    if (type === "num" && el.value !== "" && (!Number.isFinite(Number(el.value)) || (k !== "natural_ground_level_mm" && Number(el.value) < 0))) return values[k] ?? "";
                    onParam(k, el.value);
                  }} />}
            </label>
          ))}
        </fieldset>
      ))}
      <p className={s.label}>Mặt bằng &quot;{P.plan.name}&quot;</p>
      <fieldset className={s.rfs}>
        <label className={`${s.rf} ${s.rfc}`}><input type="checkbox" checked={pp.is_ground} onChange={(e) => onPlanParam("is_ground", e.target.checked)} /> <span>Tầng trệt (tính nền, không tính sàn)</span></label>
        {PP.map(([k, label]) => (
          <label key={k} className={s.rf}><span>{label}</span>
            <ChangeInput type="number" min={0} step="any" value={String(pp[k] ?? "")} onCommit={(el) => onPlanParam(k, el.value)} /></label>
        ))}
      </fieldset>
      <p style={{ margin: 0, color: "var(--muted)", fontSize: 12.5 }}>Cột nhận được: {cols.filter((c) => c.keep).length}/{cols.length} (theo nhận dạng đã lưu). {structural && "file" in structural ? "Dầm, móng lấy từ bản vẽ kết cấu." : "Dầm chưa có bản vẽ kết cấu thì suy từ tường và cột."}</p>
      <div className={s.actions} style={{ justifyContent: "flex-start" }}>
        <button className={`${s.btn} ${s.primary}`} type="button" disabled={busy} onClick={onRun}>{busy ? "Đang tính…" : "Tính khối lượng"}</button>
      </div>
      <div className={s.qty} style={{ padding: 0 }}><RoughResultView R={rough} /></div>
    </div>
  );
}
