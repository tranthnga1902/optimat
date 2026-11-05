import type { MaterialAdvisorContext } from "@/components/MaterialAdvisor";
import type { WorkSnapshot } from "@/lib/work-review";
import type { Confirmed, RoughWork } from "./model";

// Các trường tùy chọn có trong kết quả máy chủ. Bản lưu cũ vẫn mở được khi thiếu chúng.
type MasonryRow = RoughWork & { wall_system_id?: string; masonry_geometry?: {
  role?: string; issues?: string[];
} | null };
type BillLine = NonNullable<Confirmed["bill"]>[number] & { wall_system_id?: string };

export function uncheckedRowAdvice(snapshot: WorkSnapshot, index: number, confirmations: Confirmed[]) {
  const work: MasonryRow | undefined = snapshot.result.works[index];
  if (!work) return null;
  const matching = confirmations.filter(p => p.file === snapshot.file && p.plan === work.plan);
  const plan = matching.length === 1 ? matching[0] : undefined;
  const geometry = work.masonry_geometry;
  const bill: BillLine[] = plan?.bill || [];
  const designIds = new Set(bill.filter(line => work.code === "XAY" && work.wall_system_id &&
    line.wall_system_id === work.wall_system_id && line.wall_type === geometry?.wall_type &&
    line.role === geometry?.role).map(line => line.material_id).filter(Boolean));
  const sameGroup = snapshot.result.works.filter(w => w.code === work.code && w.plan === work.plan);
  const materials = snapshot.result.materials.flatMap((line, i) => {
    const exact = (line.uses || []).filter(u => u.work === work.code &&
      (u.rowIndex != null ? u.rowIndex === index && (!u.plan || u.plan === work.plan)
        : (u.plan || "") === (work.plan || "") && sameGroup.length === 1));
    const inDesign = !!line.material_id && designIds.has(line.material_id);
    if (!exact.length && !inDesign) return [];
    const quantity = exact.length && exact.every(u => u.quantity != null)
      ? exact.reduce((sum, u) => sum + (u.quantity ?? 0), 0) : null;
    return [{ lineId: "m" + i, material_id: line.material_id ?? null, name: line.name,
      raw_class: line.raw_class || "khac", unit: line.unit, quantity, quantity_with_waste: null,
      complete: false, missing: [...new Set(["Công tác chưa kiểm; chưa xác định hao hụt và lượng mua.",
        ...(exact.length && exact.length === line.uses?.length ? line.missing || [] : []),
        ...(quantity == null ? ["Chưa tách được lượng vật tư cho riêng dòng này."] : [])])],
      sources: [...new Set([...(inDesign ? ["Cấu tạo " + work.wall_system_id + " của mặt bằng đã xác nhận"] : []),
        ...exact.flatMap(u => u.via ? [u.via] : [])])],
      uses: exact.map(u => ({ work: u.work, plan: u.plan || "", quantity: u.quantity, via: u.via || "" })) }];
  });
  const components = [...new Set((work.dimensions || []).map(d => d.label).filter(Boolean))];
  const projectId = snapshot.request.project_id;
  const scope = [projectId != null && "Dự án " + projectId, plan?.takeoff_id && "bản xác nhận " + plan.takeoff_id,
    snapshot.result.takeoff_id && "bảng phần thô " + snapshot.result.takeoff_id,
    work.plan, work.element || work.name, components.slice(0, 3).join(", "), "chưa kiểm"].filter(Boolean).join(" · ").slice(0, 300);
  const context: MaterialAdvisorContext = {
    binding: { projectUid: snapshot.projectUid, drawingId: snapshot.drawingId, reviewId: snapshot.reviewId,
      materialRevision: snapshot.materialRevision ?? null },
    scope, partial: true, works: [{ rowIndex: index, code: work.code, plan: work.plan || "", element: work.element || "",
      quantity: work.quantity, unit: work.unit, status: work.status ?? null, basis: work.basis, checked: false,
      missing: [...new Set([...work.missing, ...(geometry?.issues || [])])] }],
    materials, proposedMaterialIds: [],
  };
  const question = [`Tư vấn vật liệu có điều kiện cho ${work.name} · ${work.element || work.plan || ""} (${components.join(", ")}).`,
    work.formula, ...(work.inputs || []), ...(work.dimensions?.[0]?.note ? [work.dimensions[0].note] : []),
    "Cần đối chiếu quy cách, vật tư đi kèm và nguồn giá nào trước khi chọn? Dòng này chưa kiểm."].filter(Boolean).join(" ").slice(0, 1500);
  return { context, question, projectId, confirmedId: plan?.takeoff_id ?? null, components };
}
