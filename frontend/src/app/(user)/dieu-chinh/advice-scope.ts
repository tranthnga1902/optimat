import type { WorkReceipt, WorkSnapshot } from "@/lib/work-review";
import type { RoughWork } from "../do-boc/model";

const workKey = (code: string, plan?: string | null) => JSON.stringify([code, plan || ""]);
export const rowName = (w: RoughWork, i: number) => `${i + 1}. ${w.plan || "Cả công trình"} · ${w.name}${w.element ? " · " + w.element : ""}`;
const distinct = (values: string[]) => [...new Set(values.filter(Boolean))];

/** Một use cũ chỉ gắn mã công tác/tầng. Không chia bình quân lượng đó cho những cấu kiện trùng mã. */
export function adviceScope(work: WorkSnapshot, receipt: WorkReceipt, selected: number | null, materialRevision?: string | null, proposedMaterialIds: string[] = []) {
  const result = work.result, checked = new Set(receipt.checked);
  if (selected != null && (!checked.has(selected) || !result.works[selected])) throw new Error("Công tác này chưa thuộc phạm vi đã kiểm.");
  const works = result.works.flatMap((w, rowIndex) => selected != null && (rowIndex !== selected || !checked.has(rowIndex)) ? [] : [{
    rowIndex, code: w.code, plan: w.plan || "", element: w.element || "", quantity: w.quantity, unit: w.unit,
    status: w.status ?? null, checked: checked.has(rowIndex), basis: w.basis ?? null, missing: w.missing,
  }]);
  const target = selected == null ? null : result.works[selected];
  const rowsByCode = new Map<string, number[]>();
  result.works.forEach((w, i) => {
    const key = workKey(w.code, w.plan);
    if (!rowsByCode.has(key)) rowsByCode.set(key, []);
    rowsByCode.get(key)!.push(i);
  });
  const materials = result.materials.flatMap((m, i) => {
    const all = m.uses || [];
    const uses = all.filter(u => selected == null || (u.rowIndex != null ? u.rowIndex === selected :
      !!target && workKey(u.work, u.plan) === workKey(target.code, target.plan)));
    if (selected != null && !uses.length) return [];
    const resolved = uses.map(u => {
      const indices = u.rowIndex == null ? rowsByCode.get(workKey(u.work, u.plan)) || [] : [u.rowIndex];
      const reviewed = indices.length > 0 && indices.every(j => {
        const row = result.works[j];
        return checked.has(j) && (selected == null || selected === j) && row?.code === u.work && (!u.plan || row.plan === u.plan);
      });
      return { use: u, reviewed };
    });
    const exact = resolved.length > 0 && resolved.every(entry => entry.reviewed);
    const whole = exact && uses.length === all.length;
    const scopedUses = resolved.map(({ use, reviewed }) => {
      const included = reviewed && (selected == null || exact);
      return { work: use.work, plan: use.plan || "", quantity: included ? use.quantity : null, via: included ? use.via || "" : "" };
    });
    let quantity = whole ? m.quantity : null;
    if (!whole) {
      const known = scopedUses.flatMap(u => u.quantity == null ? [] : [u.quantity]);
      if (known.length > 0 && (selected == null || known.length === uses.length)) {
        quantity = known.reduce((sum, value) => sum + value, 0);
      }
    }
    let missing = m.missing || [];
    if (target && selected != null) {
      // missing của vật tư là hợp các lý do từ nhiều công tác. Giữ điều kiện vật tư chung và lý do của chính dòng chọn.
      const otherWorkGaps = new Set<string>();
      for (const u of all) {
        const indices = u.rowIndex == null ? rowsByCode.get(workKey(u.work, u.plan)) || [] : [u.rowIndex];
        for (const j of indices) {
          const row = result.works[j];
          if (j !== selected && row?.code === u.work && (!u.plan || row.plan === u.plan))
            for (const gap of row.missing) otherWorkGaps.add(gap);
        }
      }
      missing = [...target.missing, ...missing.filter(gap => !otherWorkGaps.has(gap))];
    }
    return [{ lineId: "m" + i, material_id: m.material_id ?? null, name: m.name, raw_class: m.raw_class || "khac", unit: m.unit,
      quantity, quantity_with_waste: whole ? m.quantity_with_waste : null, complete: exact && m.complete,
      missing: distinct([...missing, ...(!exact ? [selected == null
        ? "Chỉ tính phần có số lượng gắn với công tác đã kiểm. Chưa đủ căn cứ cho tổng nhu cầu, hao hụt và lượng mua."
        : "Chưa tách được lượng theo từng dòng đã kiểm."] : []),
        ...(!whole && exact ? ["Chưa có lượng sau hao hụt riêng cho phạm vi này."] : [])]),
      sources: distinct(scopedUses.map(u => u.via)).slice(0, 8),
      uses: scopedUses,
    }];
  });
  return {
    binding: { projectUid: work.projectUid, drawingId: work.drawingId, reviewId: work.reviewId, materialRevision:materialRevision ?? null },
    scope: target && selected != null ? rowName(target, selected) : "Toàn bộ phần thô của dự án", partial: receipt.partial,
    works, materials, intermediates: selected == null && works.every(w => w.checked) ? (result.intermediates || []).map(
      ({ name, quantity, unit, complete }) => ({ name, quantity, unit, complete })) : [], proposedMaterialIds,
  };
}

export type AdviceSelection = {
  originalId: string | null; materialId: string; originalName: string; scope: string; lineId: string;
  reviewId: string; rowIndex: number | null; disposition: "specified" | "proposed";
};
export type SavedAdvice = {
  projectUid: string; drawingId: string; reviewId: string; materialRevision?: string; choices: AdviceSelection[];
};

// Không ghép lại theo vị trí sau khi tính: thứ tự dòng vật tư/công tác có thể đã đổi.
export function carrySelections(before: WorkSnapshot, after: WorkSnapshot, choices: AdviceSelection[]) {
  const identity = (w: RoughWork) => JSON.stringify([w.plan, w.code, w.element, w.unit]);
  return choices.map(c => {
    if (c.reviewId !== before.reviewId || !c.originalId) return c;
    const lines = after.result.materials.flatMap((m,i) => m.material_id === c.originalId ? [i] : []);
    const old = c.rowIndex == null ? null : before.result.works[c.rowIndex];
    const rows = old ? after.result.works.flatMap((w,i) => identity(w) === identity(old) ? [i] : []) : [];
    if (lines.length !== 1 || (c.rowIndex != null && (rows.length !== 1 || !old ||
      before.result.works.filter(w => identity(w) === identity(old)).length !== 1))) return c;
    const rowIndex = c.rowIndex == null ? null : rows[0];
    return { ...c, lineId: "m"+lines[0], reviewId: after.reviewId, rowIndex,
      scope: rowIndex == null ? c.scope : rowName(after.result.works[rowIndex], rowIndex) };
  });
}
