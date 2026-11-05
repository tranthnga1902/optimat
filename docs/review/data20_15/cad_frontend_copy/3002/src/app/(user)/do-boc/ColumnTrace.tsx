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

export function ColumnTrace({ snapshot, selected, columns }: { snapshot: WorkSnapshot; selected: number; columns: (StructuralColumnInstance | null)[] }) {
  const works = snapshot.result.works;
  const work = works[selected];
  if (work?.basis !== "structural_instance") return work?.code === "COT"
    ? <p>Chưa có liên kết từ dòng cột này đến một vị trí trục và đoạn cao độ riêng trong hồ sơ kết cấu.</p> : null;
  const col = columns[selected];
  if (!col) return <p>Chưa nối được dòng này với một đoạn cột duy nhất trong hồ sơ nguồn.</p>;
  const scale = titleScale(col.sheet || "", (col.evidence || []).map(t => ({ t })));
  const architectural = col.mapping_evidence && col.matched_column_id
    ? snapshot.request.plans.find(p => p.name === col.matched_plan && p.columns.some(c => c.id === col.matched_column_id)) : undefined;
  const related = works.flatMap((row, index) => columns[index] === col ? [{ row, index }] : []);
  const concrete = related.find(r => r.row.code === "COT");
  const formwork = related.find(r => r.row.code === "COP_PHA");
  const materialLines = snapshot.result.materials.flatMap(m => {
    const uses = (m.uses || []).filter(use => related.some(({ row, index }) => {
      if (use.work !== row.code) return false;
      if (use.rowIndex != null) return use.rowIndex === index && (!use.plan || use.plan === row.plan);
      return use.plan === row.plan && works.filter(w => w.code === row.code && w.plan === row.plan).length === 1;
    }));
    if (!uses.length) return [];
    const amount = uses.every(u => u.quantity != null) ? uses.reduce((n, u) => n + (u.quantity ?? 0), 0) : null;
    return [{ m, amount }];
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
    <h4>Khối lượng và vật tư của đoạn cột</h4>
    <p>Bê tông theo quy ước của bản tính: {concrete?.row.quantity_detail?.total_raw != null
      ? concrete.row.quantity_detail.total_raw.replace(".", ",") + " m³" : missing}. Cần kiểm phân bổ phần giao với dầm và sàn trước khi chốt.</p>
    <p>Cốp pha: {measure(formwork?.row.quantity, "m²")}{formwork?.row.missing.length ? " · " + formwork.row.missing.join("; ") : ""}.</p>
    <p>Cốt thép: chưa có khối lượng thép gắn riêng với đoạn cột này.</p>
    {materialLines.length ? <ul>{materialLines.map(({m,amount},i) => <li key={i}>
      {m.material_id ? `${m.material_id} · ${m.name}` : "Chưa có mã vật tư tương ứng trong danh mục"} · Lượng quy đổi: {measure(amount,m.unit)}
      {m.material_id && m.best_price != null && m.price_source ? ` · Đơn giá theo nguồn ${m.best_price.toLocaleString("vi-VN")} đ/${m.unit} (${m.price_source})` : " · Chưa có đơn giá có nguồn"}.
    </li>)}</ul> : <p>Chưa có mã vật tư và đơn giá truy được riêng về đoạn cột.</p>}
  </section>;
}
