import type { Confirmed, Plan, PlanState } from "./model";

export type ReviewScope = number[];
type States = Record<number, PlanState>;
export type FloorGroup = { key: string; label: string; views: number[]; reasons: string[] };

const normalize = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase();
export function floorKey(title: string) {
  const s = normalize(title).replace(/\b(?:ty le|ti le|tl)\s*:?\s*1\s*[:/]\s*\d+/g, "").replace(/[±+-]?\d+[.,]\d+/g, "");
  if (/\b(?:lung|ham|ngam|dien hinh|cac tang)\b/.test(s) || /\d\s*(?:[-–—,/&+]|den|va|toi)\s*(?:(?:tang|lau)\s*)?\d/.test(s)) return null;
  const matches = [...s.matchAll(/\b(tret|san thuong|mai|(?:tang|lau)\s*\d+)\b/g)];
  const ids = new Set(matches.map(([v]) => v === "tret" ? "T1" : v === "mai" ? "MAI" : v === "san thuong" ? "ST" :
    "T" + (Number(v.match(/\d+/)![0]) + (v.startsWith("lau") ? 1 : 0))));
  return ids.size === 1 ? [...ids][0] : null;
}

function planFloor(plan: Plan) {
  const source = plan.plan.floor_key;
  return typeof source === "string" && /^(T[1-9]\d*|MAI|ST)$/.test(source) ? source : floorKey(plan.plan.name);
}
export function scopeIndices(plans: Plan[], scope?: ReviewScope) {
  return plans.flatMap((_, i) => scope === undefined || scope.includes(i) ? [i] : []);
}
export function floorGroups(plans: Plan[], states: States): FloorGroup[] {
  const groups = new Map<string, FloorGroup>();
  plans.forEach((p, i) => {
    const id = planFloor(p), key = id || "view-" + i;
    const label = id === "ST" ? "Sân thượng" : id === "MAI" ? "Mái" : id === "T1" ? "Tầng 1 / Trệt" :
      id ? "Tầng " + id.slice(1) + " / Lầu " + (Number(id.slice(1)) - 1) : p.plan.name || "Hình " + (i + 1);
    const g = groups.get(key) || { key, label, views: [], reasons: [] };
    g.views.push(i);
    const st = states[i];
    const reason = (v: string) => { if (!g.reasons.includes(v)) g.reasons.push(v); };
    if (!id) reason("Chưa rõ tầng");
    if (st?.scope !== "reference") {
      if (!((st?.height_mm ?? p.height_mm) > 0)) reason("Thiếu chiều cao");
      if ((st?.openings || p.openings).some(o => (!("keep" in o) || o.keep) && (!o.w || !o.h))) reason("Lỗ mở thiếu kích thước");
      for (const warning of p.warnings || []) if (warning.trim()) reason(warning);
    }
    groups.set(key, g);
  });
  for (const g of groups.values()) if (g.views.length > 1 && g.views.filter(i => states[i]?.scope !== "reference").length > 1)
    g.reasons.unshift("Nhiều hình cùng tầng, cần đối chiếu nguồn");
  return [...groups.values()];
}

export function scopeConflict(plans: Plan[], states: States, scope?: ReviewScope) {
  const indices = scopeIndices(plans, scope);
  const used = new Map<string, number>();
  for (const i of indices) {
    if (states[i]?.scope !== "count") continue;
    const name = plans[i].plan.name;
    const id = planFloor(plans[i]), title = normalize(name);
    const mixed = !id && (/\d\s*(?:[-–—,/&+]|den|va|toi)\s*(?:(?:tang|lau)\s*)?\d/.test(title) ||
      (title.match(/\b(?:tang\s*\d+|lau\s*\d+|tret|mai|san thuong)\b/g) || []).length > 1);
    if (mixed && indices.some(j => j !== i && states[j]?.scope === "count")) return i;
    const key = id || "name:" + title.trim();
    if (used.has(key)) return i;
    used.set(key, i);
  }
  return -1;
}
export function scopeReady(plans: Plan[], states: States, scope?: ReviewScope) {
  const indices = scopeIndices(plans, scope);
  return indices.some(i => states[i]?.scope === "count") && indices.every(i => ["count","reference"].includes(states[i]?.scope || "")) &&
    scopeConflict(plans,states,scope) < 0;
}
export function scopedBodies(plans: Plan[], states: States, confirmed: Record<number,Confirmed>, scope?: ReviewScope) {
  return Object.fromEntries(scopeIndices(plans,scope).filter(i => states[i]?.scope === "count" && confirmed[i]).map(i => [i,confirmed[i]]));
}
export function scopeLabel(plans: Plan[], states: States, scope?: ReviewScope) {
  const groups = floorGroups(plans,states);
  const selected = groups.filter(g => scope === undefined || g.views.some(i => scope.includes(i)));
  return "Phạm vi đã chọn · " + selected.length + "/" + groups.length + " tầng hoặc nhóm hình" +
    (selected.length ? " · " + selected.map(g=>g.label).join(", ") : "");
}
