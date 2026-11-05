import { memo } from "react";
import type { Data, PlanParams, PlanState, Structural } from "./model";

const titles: Record<string, string> = {
  BEAM: "Bê tông dầm", SLAB: "Bê tông sàn", STAIR: "Bê tông cầu thang",
  LINTEL: "Lanh tô", FOUNDATION: "Bê tông móng", COLUMN: "Bê tông cột", REBAR: "Cốt thép",
};

export const DrawingWorkList = memo(function DrawingWorkList({ data, index, states, params, structural }: {
  data: Data; index: number; states?: Record<number, PlanState>; params?: Record<number, PlanParams>; structural?: Structural | null;
}) {
  const plans = data.plans.flatMap((p, i) => {
    if (index >= 0 && i !== index) return [];
    const state = states?.[i];
    const walls = state ? state.walls.filter(w => w.keep && w.masonry).length : p.walls.filter(w => w.masonry).length;
    const columns = params?.[i]?.cols?.filter(c => c.keep).length ?? p.columns?.length ?? 0;
    const rows: [string, string][] = [];
    if (walls) rows.push(["Xây tường", `${walls} đoạn tường · cần kiểm chiều cao và lỗ mở`]);
    if (columns) rows.push(["Bê tông cột", `${columns} vị trí cột · cần đối chiếu mặt cắt và cao độ`]);
    if (p.stairs?.length) rows.push([titles.STAIR, `${p.stairs.length} cầu thang nhận diện · cần kiểm bản thang và chiếu nghỉ`]);
    for (const [role, sources] of Object.entries(p.found || {})) {
      if (titles[role] && Array.isArray(sources) && sources.length && !(role === "STAIR" && p.stairs?.length))
        rows.push([titles[role], `Dấu hiệu từ ${sources.join(", ")} · cần đối chiếu cấu kiện`]);
    }
    return [<div key={i} className="mb-2"><strong>{p.plan.name}</strong>
      {state?.scope === "reference" && <span> · Mặt bằng tham khảo</span>}
      {rows.length ? <ul className="list-disc pl-5">{rows.map(([name, basis]) =>
        <li key={name}><b>{name}</b> · {basis}</li>)}</ul> : <p>Chưa nhận diện được công tác trên mặt bằng này.</p>}
    </div>];
  });
  const structuralRows: string[] = [];
  if (structural?.foundations?.length) structuralRows.push("Bê tông móng");
  if (Object.values(structural?.structural_beams || {}).some(b => Array.isArray(b) && b.length)) structuralRows.push("Bê tông dầm");
  if (structural?.structural_columns?.length || structural?.column_schedule?.length) structuralRows.push("Bê tông cột");
  if (structural?.rebar?.length) structuralRows.push("Cốt thép theo bảng thống kê");
  const signals = Object.entries(data.drawing_work_signals || {}).filter(([key, sources]) => titles[key] && sources.length);
  return <section aria-label="Danh sách công tác sau bóc tách" className="max-h-56 overflow-auto border-t border-rule bg-card px-5 py-3">
    <h2 className="font-bold">Danh sách công tác sau bóc tách</h2>
    <p className="mb-2 text-muted">Theo bản vẽ {data.file}. Xác nhận phạm vi mặt bằng để kiểm tra khối lượng ở bước 3.</p>
    {plans}
    {signals.length > 0 && <ul className="list-disc pl-5">{signals.map(([key, sources]) =>
      <li key={key}><b>{titles[key]}</b> · {sources.join(", ")} · chờ kiểm vị trí và kích thước</li>)}</ul>}
    {structuralRows.length > 0 && <p><b>Hồ sơ kết cấu · {structural?.file}</b> · {structuralRows.join(", ")}. Cần đối chiếu vị trí trước khi gán cho tầng.</p>}
    {!plans.length && !signals.length && !structuralRows.length && <p>Chưa có mặt bằng hoặc cấu kiện đủ căn cứ để lập danh sách.</p>}
  </section>;
});
