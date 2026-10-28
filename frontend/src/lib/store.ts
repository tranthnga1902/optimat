"use client";
// Lưu trên trình duyệt (tiện cho một người dùng); kết quả chốt chính thức nằm trong database.
// Khóa giữ nguyên như app.html cũ: optimat-role, optimat-project, optimat-confirmed, optimat-rough.
import { useEffect, useState } from "react";

export const store = {
  get<T>(k: string, d: T): T {
    try { const v = localStorage.getItem(k); return v ? (JSON.parse(v) as T) : d; } catch { return d; }
  },
  set(k: string, v: unknown) {
    try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* chế độ riêng tư */ }
    window.dispatchEvent(new CustomEvent("optimat-store", { detail: k }));
  },
};

/** Đọc một khóa và tự cập nhật khi trang khác (hoặc tab khác) ghi vào. Lần render đầu trả `d` để khớp với HTML máy chủ. */
export function useStored<T>(k: string, d: T): T {
  const [v, setV] = useState<T>(d);
  useEffect(() => {
    const read = () => setV(store.get(k, d));
    read();
    const onStore = (e: Event) => { if (!(e instanceof CustomEvent) || e.detail === k) read(); };
    window.addEventListener("optimat-store", onStore);
    window.addEventListener("storage", read);
    return () => { window.removeEventListener("optimat-store", onStore); window.removeEventListener("storage", read); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [k]);
  return v;
}

export type WallGroup = {
  wall_type: string; role: string; design_wall_system_id?: string; design_material_id?: string;
  length_m: number; gross_area_m2: number; opening_area_m2: number; net_area_m2: number; [k: string]: unknown;
};
export type ConfirmedPlan = { groups?: WallGroup[]; [k: string]: unknown };

/** Gộp các mặt bằng đã chốt theo loại tường + vai trò + phương án tường để tra giá và tối ưu. */
export function mergedGroups(plans: ConfirmedPlan[]): WallGroup[] {
  const by: Record<string, WallGroup> = {};
  for (const p of plans) for (const g of p.groups || []) {
    const k = [g.wall_type, g.role, g.design_wall_system_id || g.design_material_id || ""].join("|");
    const t = (by[k] = by[k] || { ...g, length_m: 0, gross_area_m2: 0, opening_area_m2: 0, net_area_m2: 0 });
    for (const f of ["length_m", "gross_area_m2", "opening_area_m2", "net_area_m2"] as const) t[f] = Math.round((t[f] + g[f]) * 100) / 100;
  }
  return Object.values(by).sort((a, b) => (a.wall_type + a.role).localeCompare(b.wall_type + b.role));
}
