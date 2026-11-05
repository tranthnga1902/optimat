import type { RoughResult, RoughWork } from "@/app/(user)/do-boc/model";
import type { roughRequest } from "@/app/(user)/do-boc/model";

export type DrawingVersion = { projectUid: string; drawingId: string };
export type WorkVersion = DrawingVersion & { reviewScope?: number[]; file: string; reviewId: string };
export type WorkSnapshot = WorkVersion & { at: string; request: ReturnType<typeof roughRequest>; result: RoughResult; materialRevision?: string };
export type WorkReceipt = WorkVersion & { checked: number[]; partial: boolean; confirmed: boolean };

export function sameWorkVersion(a?: Partial<WorkVersion> | null, b?: Partial<WorkVersion> | null) {
  return !!a?.projectUid && !!a.drawingId && !!a.reviewId && !!a.file && a.projectUid === b?.projectUid
    && a.drawingId === b.drawingId && a.reviewId === b.reviewId && a.file === b.file;
}
export function needsInput(w: RoughWork) {
  return w.quantity == null || w.missing.length > 0 || w.status === "D" || w.basis === "not_supported"
    || w.quantity_detail?.complete === false || !!w.dimensions?.some(d => d.missing_fields?.length);
}
export function canConfirmWork(works: RoughWork[], checked: number[], partial: boolean) {
  const indices = new Set(checked);
  const available = works.map((w, i) => w.quantity != null && w.basis !== "not_supported" ? i : -1).filter(i => i >= 0);
  return available.length > 0 && available.every(i => indices.has(i)) && (partial || !works.some(needsInput));
}
export function approvedWork(snapshot: WorkSnapshot | null, receipt: WorkReceipt | null, drawing: (Partial<DrawingVersion> & { reviewScope?: number[] }) | null) {
  return !!snapshot && !!receipt?.confirmed && Array.isArray(receipt.checked) && sameWorkVersion(snapshot, receipt)
    && snapshot.drawingId === drawing?.drawingId && snapshot.projectUid === drawing?.projectUid
    && JSON.stringify(snapshot.reviewScope ?? null) === JSON.stringify(drawing?.reviewScope ?? null)
    && !!snapshot.request && snapshot.result.plan_scope_confirmed === true && canConfirmWork(snapshot.result.works, receipt.checked, receipt.partial);
}

// Vật tư và đơn giá có thể đổi mà không làm đổi số đo đã kiểm.
function measurement(w: RoughWork) {
  return JSON.stringify([w.code, w.plan, w.element, w.unit, w.quantity, w.basis,
    w.quantity_detail && [w.quantity_detail.complete,w.quantity_detail.known_part_raw,w.quantity_detail.total_raw,
      w.quantity_detail.rows.map(r=>[r.role,r.label,r.sign,r.raw_quantity,r.unit,r.missing])],
    w.dimensions?.map(d => Object.entries(d)
      .filter(([key]) => !["note", "source", "field_sources"].includes(key)).sort(([a], [b]) => a.localeCompare(b))),
    w.masonry_geometry && [w.masonry_geometry.length_m, w.masonry_geometry.gross_area_m2,
      w.masonry_geometry.opening_area_m2, w.masonry_geometry.thickness_m]]);
}
export function geometryChanged(before: RoughResult, after: RoughResult) {
  return before.works.length !== after.works.length || after.works.some((w, i) =>
    opensNewGap(before.works[i], w) ||
    measurement(before.works[i]) !== measurement(w));
}
function opensNewGap(previous: RoughWork, next: RoughWork) {
  return (!needsInput(previous) && needsInput(next)) || next.missing.some(reason => !previous.missing.includes(reason));
}
export function unchangedCheckedRows(before: RoughResult, after: RoughResult, receipt: WorkReceipt) {
  const previous = new Map<string, number>(), next = after.works.map(measurement);
  before.works.forEach((w, i) => {
    const key = measurement(w);
    previous.set(key, previous.has(key) ? -1 : i);
  });
  const seen = new Set<string>(), ambiguous = new Set<string>();
  for (const key of next) { if (seen.has(key)) ambiguous.add(key); seen.add(key); }
  return next.flatMap((key, i) => {
    const old = previous.get(key);
    return old != null && old >= 0 && !ambiguous.has(key) && receipt.checked.includes(old) &&
      !opensNewGap(before.works[old], after.works[i]) ? [i] : [];
  });
}
