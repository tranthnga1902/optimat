import type { WorkSnapshot } from "@/lib/work-review";
import type { StructuralColumnInstance } from "./model";
import { titleScale } from "./paper-scale";

const missing = "Chưa có";
const measure = (v: number | null | undefined, unit: string) =>
  v == null ? missing : v.toLocaleString("vi-VN", { maximumFractionDigits: 9 }) + " " + unit;

// Các nhãn này do instance_column_works phát ra với nguyên ID của đoạn, khác nhãn của bảng thống kê loại cột.
// Chỉ nối các dòng trong cùng snapshot; không ghép theo mã loại, tiết diện hoặc giá trị khối lượng.
export function indexColumnWorks(snapshot: WorkSnapshot) {
  const byKey = new Map<string, StructuralColumnInstance | null>();
  const key = (code: string, plan?: string | null, label?: string) => JSON.stringify([code, plan, label]);
  for (const col of snapshot.request?.structural_columns || []) {
    const plan = col.matched_plan || col.floor_key || col.sheet || "kết cấu chưa gắn tầng";
    const label = `${col.code} [${col.instance_id}]`;
    for (const k of [key("COT", plan, label), key("COP_PHA", plan, "cốp pha " + label)]) {
      byKey.set(k, byKey.has(k) ? null : col);
    }
  }
  return snapshot.result.works.map(w => w.basis === "structural_instance" ? byKey.get(key(w.code, w.plan, w.element)) ?? null : null);
}

export const gridLabel = (c: StructuralColumnInstance) => [c.grid_x || "?", c.grid_y || "?"].join("/");

function columnMaterialEvidence(column: StructuralColumnInstance, rebar: unknown[] = []) {
  const evidence = column.evidence || [];
  // Chỉ trích nguyên lời thuộc đoạn đang mở. Tên tệp, tiêu đề định vị và ghi chú các cột bên cạnh không phải chỉ định vật liệu.
  const notes = [...new Set(evidence.filter(s => !s.startsWith("Tệp KC ") && !/ tại \([^)]*\); layer /u.test(s)))];
  const concrete = notes.filter(s => /bê\s*tông|concrete|\b(?:B|M)\s*\d+\b/iu.test(s));
  const steel = notes.filter(s => /thép|reinforcement|stirrups?|[ØΦ∅]\s*\d|%%c\s*\d|\bCB[-\s]?\d+/iu.test(s));
  const hashes = new Set(evidence.filter(s => column.file && s.startsWith(`Tệp KC ${column.file}; `))
    .flatMap(s => s.match(/; sha256=([a-f0-9]{64})$/i)?.[1]?.toLowerCase() || []));
  const tag = (s: string) => s.normalize("NFKC").trim().toUpperCase().replace(/^CỘT\s+/, "").replace(/[-‐‑–\s]+/g, "");
  const schedule = rebar.flatMap(value => {
    if (!value || typeof value !== "object") return [];
    const row = value as Record<string, unknown>;
    if (hashes.size !== 1 || typeof row.revision_sha256 !== "string" || !hashes.has(row.revision_sha256.toLowerCase()) ||
        row.element_code !== "COT" || typeof row.element !== "string" || !tag(column.code) || tag(row.element) !== tag(column.code) ||
        typeof row.table !== "string" || !row.table.trim() || typeof row.row !== "number" ||
        typeof row.dia_mm !== "number" || !Number.isFinite(row.dia_mm) || row.dia_mm <= 0) return [];
    return [`${row.table} · dòng ${row.row} · ${row.element}${typeof row.mark === "string" && row.mark ? " · thanh " + row.mark : ""} · Ø${row.dia_mm} mm`];
  });
  return { concrete, steel, schedule };
}

export function ColumnTrace({ snapshot, selected, columns }: { snapshot: WorkSnapshot; selected: number; columns: (StructuralColumnInstance | null)[] }) {
  const works = snapshot.result.works;
  const work = works[selected];
  if (work?.basis !== "structural_instance") return work?.code === "COT"
    ? <p>Chưa có liên kết từ dòng cột này đến một vị trí trục và đoạn cao độ riêng trong hồ sơ kết cấu.</p> : null;
  const col = columns[selected];
  if (!col) return <p>Chưa nối được dòng này với một đoạn cột duy nhất trong hồ sơ nguồn.</p>;
  const specs = columnMaterialEvidence(col, snapshot.request.rebar);
  const scale = titleScale(col.sheet || "", (col.evidence || []).map(t => ({ t })));
  const architectural = col.mapping_evidence && col.matched_column_id
    ? snapshot.request.plans.find(p => p.name === col.matched_plan && p.columns.some(c => c.id === col.matched_column_id)) : undefined;
  const related = works.flatMap((row, index) => columns[index] === col ? [{ row, index }] : []);
  const concrete = related.find(r => r.row.code === "COT");
  const formwork = related.find(r => r.row.code === "COP_PHA");
  const materialLines = snapshot.result.materials.flatMap(m => {
    const uses = (m.uses || []).flatMap(use => {
      const source = related.find(({ row, index }) => {
        if (use.work !== row.code) return false;
        if (use.rowIndex != null) return use.rowIndex === index && (!use.plan || use.plan === row.plan);
        return use.plan === row.plan && works.filter(w => w.code === row.code && w.plan === row.plan).length === 1;
      });
      return source ? [{ use, source: source.row }] : [];
    });
    if (!uses.length) return [];
    const amount = uses.every(({use}) => use.quantity != null) ? uses.reduce((n, {use}) => n + (use.quantity ?? 0), 0) : null;
    const reasons = new Set(uses.flatMap(({source}) => source.missing || []));
    // missing ở cấp vật tư gộp cả dự án. Chỉ hiện lý do chắc chắn thuộc các đóng góp đang mở.
    for (const reason of m.missing || []) {
      const sharedConcreteGrade = reason === "mác bê tông" && uses.every(({source}) => source.code === "COT")
        && !snapshot.request.params?.concrete_grade;
      const sharedFormworkType = reason === "loại ván khuôn (gỗ | ván ép)" && uses.every(({source}) => source.code === "COP_PHA")
        && !snapshot.request.params?.formwork_type;
      if (uses.length === m.uses?.length || sharedConcreteGrade || sharedFormworkType) reasons.add(reason);
    }
    return [{ m, amount, reasons: [...reasons] }];
  });
  return <section aria-label="Truy vết đoạn cột" className="my-3 min-w-0 break-words rounded border border-rule p-3">
    <h4>{col.code} · trục {gridLabel(col)} · {col.floor_key || "Chưa rõ tầng"}</h4>
    <p>Đoạn cột {col.instance_id}</p>
    <dl>
      <dt>Nguồn kết cấu</dt><dd>{col.file || "Chưa rõ tệp"} · {col.sheet || "Chưa rõ tờ"}</dd>
      <dt>Đối chiếu kiến trúc</dt><dd>{architectural ? <>
        {architectural.name} · {col.matched_column_id} · {col.mapping_evidence}
        {architectural.source_revision && <> · Tệp #{architectural.source_revision.file_id}, mã phiên bản #{architectural.source_revision.revision_id}</>}
      </> : "Chưa có liên kết với cột trên mặt bằng kiến trúc."}</dd>
      <dt>Layer CAD</dt><dd>{col.layers?.join(", ") || missing}</dd>
      <dt>Mã thực thể CAD (handle)</dt><dd>{col.handles?.join(", ") || missing}</dd>
      <dt>Tỷ lệ in của hình kết cấu</dt><dd>{scale ? `1:${scale.denominator} · ${scale.source}` : "Chưa xác định từ tiêu đề hình"}</dd>
      <dt>Tiết diện</dt><dd>{measure(col.b_mm, "mm")} × {measure(col.h_mm, "mm")}</dd>
      <dt>Cao độ dưới → trên</dt><dd>{measure(col.z_from_mm == null ? null : col.z_from_mm / 1000, "m")} → {measure(col.z_to_mm == null ? null : col.z_to_mm / 1000, "m")}</dd>
      <dt>Sàn đỉnh</dt><dd>{measure(col.top_slab_thickness_mm, "mm")} · {col.top_slab_source || "Chưa có nguồn chiều dày sàn"}</dd>
    </dl>
    <details><summary>Căn cứ nhận diện và đo</summary>
      {col.evidence?.length ? <ul>{col.evidence.map((item,i) => <li key={i}>{item}</li>)}</ul> : <p>Chưa có bằng chứng nhận diện.</p>}
    </details>
    <h4>Phương án vật liệu cho đoạn cột · {col.code} · {gridLabel(col)}</h4>
    <p>Bê tông theo quy ước của bản tính: {concrete?.row.quantity_detail?.total_raw != null
      ? concrete.row.quantity_detail.total_raw.replace(".", ",") + " m³" : missing}. Cần kiểm phân bổ phần giao với dầm và sàn trước khi chốt.</p>
    {specs.concrete.length ? <><p>Ghi chú bê tông được gắn với đoạn cột:</p><ul>{specs.concrete.map(s => <li key={s}>{s}</li>)}</ul></>
      : <p>Chưa có ghi chú cấp bê tông gắn với đoạn cột trong kết quả đọc.</p>}
    <p><b>Bê tông thương phẩm.</b> Đối chiếu cấp bê tông trong ghi chú thiết kế với quy cách nhà cung cấp; cần báo giá giao theo đợt đổ và lượng tối thiểu.</p>
    <p><b>Bê tông trộn tại chỗ.</b> Cần cấp phối đã duyệt cho đúng cấp bê tông trước khi tính xi măng, cát, đá và nước. Đây là phương án thay thế cho thương phẩm.</p>
    <p><b>Cốt thép.</b> {specs.steel.length ? "Ghi chú thép được gắn với đoạn cột:" : "Chưa có ghi chú đường kính, mác hoặc bước đai gắn với riêng đoạn này."}</p>
    {!!specs.steel.length && <ul>{specs.steel.map(s => <li key={s}>{s}</li>)}</ul>}
    {!!specs.schedule.length && <details><summary>Bảng thép cùng loại cột, cùng bản KC ({specs.schedule.length} dòng)</summary>
      <ul>{specs.schedule.map((s,i) => <li key={i}>{s}</li>)}</ul><p>Các dòng này chưa được phân bổ theo trục và đoạn cao độ.</p></details>}
    <p>Khối lượng thép riêng của đoạn (kg): chưa xác định. Bước đai ghi trên mặt cắt áp dụng tại vị trí cắt.
      {" "}Cần đối chiếu từng vùng bước đai trên hình dọc, số thanh, chiều dài cắt uốn và neo nối của đoạn để tính kg.</p>
    <p><b>Cốp pha.</b> Diện tích: {measure(formwork?.row.quantity, "m²")}{formwork?.row.missing.length ? " · " + formwork.row.missing.join("; ") : ""}.
      {" "}Để tính số tấm cần có quy cách tấm, cách ghép và số lần luân chuyển.</p>
    {materialLines.length ? <ul>{materialLines.map(({m,amount,reasons},i) => <li key={i}>
      <strong>{m.name}</strong> · {m.material_id || "Chưa có mã vật tư tương ứng trong danh mục"} · Lượng quy đổi: {measure(amount,m.unit)}
      {m.material_id && m.best_price != null && m.price_source ? ` · Đơn giá theo nguồn ${m.best_price.toLocaleString("vi-VN")} đ/${m.unit} (${m.price_source})` : " · Chưa có đơn giá có nguồn"}.
      {!!reasons.length && <p>Cần bổ sung: {reasons.join("; ")}.</p>}
    </li>)}</ul> : <p>Chưa truy được dòng vật tư riêng cho đoạn cột.</p>}
  </section>;
}
