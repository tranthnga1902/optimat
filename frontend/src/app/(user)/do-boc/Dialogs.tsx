"use client";
// Hộp thoại trong trang: gán vật liệu hàng loạt, xác nhận mặt bằng, kết quả chốt (bảng vật liệu, tối ưu nhanh), thông báo.
import Link from "next/link";
import { useState, type ReactNode } from "react";
import s from "./review.module.css";
import { useWallClasses } from "@/lib/reference";
import { ROLE, fmt, money, postJson, type Computed, type Confirmed, type Data, type Plan, type PlanState } from "./model";

export function Sheet({ onClose, children }: { onClose: () => void; children: ReactNode }) {
  return (
    <div className={s.sheet} onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={s.card} role="dialog" aria-modal="true">{children}</div>
    </div>
  );
}

/** Thông báo một nút Đóng. */
export function Msg({ title, children, primary, onClose }: { title: string; children?: ReactNode; primary?: boolean; onClose: () => void }) {
  return (
    <Sheet onClose={onClose}>
      <h2>{title}</h2>{children}
      <div className={s.actions}><button className={`${s.btn} ${primary ? s.primary : ""}`} type="button" onClick={onClose}>Đóng</button></div>
    </Sheet>
  );
}

const Warn = ({ items, style }: { items: string[]; style?: React.CSSProperties }) =>
  <ul className={s.warn} style={style}>{items.map((w, i) => <li key={i}>{w}</li>)}</ul>;

export function MaterialDialog({ data, n, onApply, onClose }: { data: Data; n: number; onApply: (mat: string, cls: string) => void; onClose: () => void }) {
  const groups = data.families.map((f) => ({ f, ms: data.materials.filter((m) => m.family === f.id) })).filter((g) => g.ms.length);
  const [mat, setMat] = useState(groups[0]?.ms[0]?.id || "");
  const [cls, setCls] = useState("");
  const classes = useWallClasses();
  return (
    <Sheet onClose={onClose}>
      <h2>Gán vật liệu cho {n} tường chưa rõ</h2><p>Dùng khi bản vẽ không ghi vật liệu nhưng thuyết minh hoặc dự toán có ghi. Có thể sửa lại từng tường sau.</p>
      <label className={s.field}>Vật liệu <select value={mat} onChange={(e) => setMat(e.target.value)}>
        {groups.map(({ f, ms }) => <optgroup key={f.id} label={f.label}>{ms.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}</optgroup>)}
      </select></label>
      <label className={s.field}>Chỉ tường loại <select value={cls} onChange={(e) => setCls(e.target.value)}><option value="">tất cả</option>{classes.map((c) => <option key={c}>{c}</option>)}</select></label>
      <div className={s.actions}><button className={s.btn} type="button" onClick={onClose}>Hủy</button>
        <button className={`${s.btn} ${s.primary}`} type="button" onClick={() => onApply(mat, cls)}>Gán</button></div>
    </Sheet>
  );
}

export function ConfirmDialog({ P, S, c, send, onClose }: { P: Plan; S: PlanState; c: Computed; send: () => Promise<void>; onClose: () => void }) {
  const [busy, setBusy] = useState(false);
  const off = S.walls.filter((w) => !w.keep).length, man = S.walls.filter((w) => w.src === "manual" && w.keep).length;
  const nomat = S.walls.filter((w) => w.keep && w.masonry && !w.mat).length;
  return (
    <Sheet onClose={onClose}>
      <h2>Xác nhận mặt bằng &quot;{P.plan.name}&quot;</h2>
      <p>Chiều cao tầng {fmt(S.height_mm / 1000)} m · {S.walls.filter((w) => w.keep).length} đoạn tường (vẽ thêm {man}, đã loại {off}) · {S.openings.filter((o) => o.keep).length} lỗ mở.</p>
      <p>Diện tích tường thực tính tạm: <b>{fmt(c.total)} m²</b>.{nomat ? ` Còn ${nomat} tường chưa có vật liệu.` : ""}</p>
      <p>Máy chủ sẽ tính lại khối lượng bằng cùng công thức và trả kết quả chốt.</p>
      <div className={s.actions}><button className={s.btn} type="button" onClick={onClose}>Quay lại sửa</button>
        <button className={`${s.btn} ${s.primary}`} type="button" disabled={busy} onClick={() => { setBusy(true); send(); }}>{busy ? "Đang gửi…" : "Xác nhận"}</button></div>
    </Sheet>
  );
}

// bảng vật liệu cần mua và giá đang có (máy chủ tra theo mã vật liệu trong danh mục)
export function BillTable({ r }: { r: Confirmed }) {
  if (!r.bill || !r.bill.length) return null;
  const low = (t: string) => <span className={`${s.tag} ${s.low}`}>{t}</span>;
  return <>
    <p className={s.label}>Vật liệu cần mua và giá trong danh mục</p>
    <div style={{ overflowX: "auto" }}><table><thead><tr><th>Nhóm tường</th><th>Vật liệu</th><th className={s.num}>Khối lượng</th><th className={s.num}>Giá thấp nhất</th><th>Nguồn giá</th><th className={s.num}>Thành tiền</th></tr></thead>
      <tbody>{r.bill.map((b, i) => {
        const best = b.offers.find((o) => o.price != null), who = best && (best.supplier_name || best.supplier_id || "");
        return (
          <tr key={i}><td>{b.wall_type} {ROLE[b.role] || b.role}</td><td>{b.kind === "mortar" ? "Vữa " : ""}{b.material_id ? b.material_id + " · " + (b.material_name || "") : low("chưa chọn")}</td>
            <td className={s.num}>{b.quantity == null ? low("thiếu") : fmt(b.quantity) + " " + (b.unit || "")}</td>
            <td className={s.num}>{best ? money(best.price) : low("chưa có giá")}</td>
            <td>{best && <>{best.url ? <a href={best.url} target="_blank" rel="noopener">{who}</a> : who || best.price_level || ""}
              {best.data_kind && best.data_kind !== "ACTUAL" && <> <span className={`${s.tag} ${s.low}`}>{best.data_kind}</span></>}</>}</td>
            <td className={s.num}>{money(b.est_cost)}</td></tr>
        );
      })}</tbody><tfoot><tr><td colSpan={5}>Tổng tiền vật liệu</td><td className={s.num}>{r.bill_total == null ? "chưa đủ giá" : money(r.bill_total)}</td></tr></tfoot></table></div>
    {(r.bill_missing || []).length > 0 && <Warn items={r.bill_missing!} />}
  </>;
}

type Choice = { wall_type: string; wall_system_id?: string; material_id?: string; product_url?: string; supplier_name: string };
type Solution = { total_cost: number; supply_days: number; u_value: number; choices: Choice[] };

/** Kết quả chốt của máy chủ; tối ưu nhanh riêng mặt bằng này với các nhóm tường đã chốt (cùng mã vật liệu, phương án tường). */
export function ConfirmedDialog({ body, total, onClose }: { body: Confirmed; total: number; onClose: () => void }) {
  const [keepDesign, setKeepDesign] = useState(false);
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<{ sols: Solution[]; notes: string[] } | { error: string } | null>(null);
  const run = async () => {
    setBusy(true);
    try {
      const r = await postJson<{ solutions?: Solution[]; notes?: string[] }>("/api/optimize", { groups: body.groups, constraints: { keep_design_material: keepDesign } }, "Không tối ưu được.");
      setOut({ sols: r.solutions || [], notes: r.notes || [] });
    } catch (err) { setOut({ error: (err as Error).message }); }
    setBusy(false);
  };
  let result: ReactNode = null;
  if (out && "error" in out) result = <Warn items={[out.error]} />;
  else if (out) {
    const sols = out.sols;
    const pick: [string, Solution][] = sols.length ? [["Chi phí thấp nhất", sols[0]],
      ["Cung ứng nhanh nhất", [...sols].sort((a, b) => a.supply_days - b.supply_days || a.total_cost - b.total_cost)[0]],
      ["Cách nhiệt tốt nhất", [...sols].sort((a, b) => a.u_value - b.u_value || a.total_cost - b.total_cost)[0]]] : [];
    result = <>
      {sols.length ? <div style={{ overflowX: "auto" }}><table><thead><tr><th>Phương án</th><th>Tường</th><th>Vật liệu</th><th>Nhà cung cấp</th><th className={s.num}>Tổng đồng</th><th className={s.num}>Ngày</th><th className={s.num}>U</th></tr></thead><tbody>
        {pick.flatMap(([label, sol], k) => sol.choices.map((c, i) => (
          <tr key={k + ":" + i}><td>{i ? "" : label}</td><td>{c.wall_type}</td><td>{c.wall_system_id || c.material_id}</td>
            <td>{c.product_url ? <a href={c.product_url} target="_blank" rel="noopener">{c.supplier_name}</a> : c.supplier_name}</td>
            <td className={s.num}>{i ? "" : money(sol.total_cost)}</td><td className={s.num}>{i ? "" : sol.supply_days}</td><td className={s.num}>{i ? "" : sol.u_value}</td></tr>
        )))}
      </tbody></table></div> : <p>Không có phương án nào.</p>}
      {out.notes.length > 0 && <Warn items={out.notes} />}
    </>;
  }
  return (
    <Sheet onClose={onClose}>
      <h2>Đã xác nhận</h2><p>Máy chủ tính được <b>{fmt(body.total_net_area_m2)} m²</b> tường thực (trang tính tạm {fmt(total)} m²).</p>
      {body.takeoff_id ? <p>Đã lưu vào dự án (mã kết quả {body.takeoff_id}).</p> : null}
      <BillTable r={body} />
      {body.warnings.length > 0 && <Warn items={body.warnings} />}
      <p>Đã ghi mặt bằng này cho giao diện chung: <Link href="/vat-lieu">Vật liệu và giá (gộp các tầng)</Link> · <Link href="/toi-uu">Phương án tối ưu</Link>.</p>
      <p className={s.label}>Hoặc tối ưu nhanh riêng mặt bằng này</p>
      <label className={s.field}><input type="checkbox" checked={keepDesign} onChange={(e) => setKeepDesign(e.target.checked)} /> Giữ vật liệu theo thiết kế (chỉ chọn nhà cung cấp và xe)</label>
      <div>{result}</div>
      <div className={s.actions}><button className={s.btn} type="button" onClick={onClose}>Đóng</button>
        <button className={`${s.btn} ${s.primary}`} type="button" disabled={busy} onClick={run}>{busy ? "Đang tối ưu…" : "Tối ưu"}</button></div>
    </Sheet>
  );
}
