import type { ConfirmedPlan } from "@/lib/store";

export function KnownWallQuantities({ plans }: { plans: ConfirmedPlan[] }) {
  const rows = plans.flatMap(p => (p.groups || []).filter(g => Number.isFinite(g.net_area_m2)).map(g => ({
    name:String(p.plan || ""), wall:g.wall_type, area:g.net_area_m2
  })));
  if (!rows.length) return null;
  return <details><summary>Xem {rows.length} nhóm tường đủ dữ liệu</summary>
    <table><thead><tr><th>Mặt bằng</th><th>Loại tường</th><th>Diện tích thực (m²)</th></tr></thead>
    <tbody>{rows.map((r,i) => <tr key={i}><td>{r.name}</td><td>{r.wall}</td><td>{r.area.toLocaleString("vi-VN",{maximumFractionDigits:2})}</td></tr>)}</tbody></table>
  </details>;
}
