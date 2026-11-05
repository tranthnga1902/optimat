"use client";
// Hộp thoại trong trang: gán vật liệu hàng loạt, xác nhận mặt bằng, kết quả chốt (bảng vật liệu, tối ưu nhanh), thông báo.
import { useState, type ReactNode } from "react";
import s from "./review.module.css";
import { useWallClasses } from "@/lib/reference";
import { ROLE, fmt, money, type Computed, type Confirmed, type Data, type Plan, type PlanState } from "./model";

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

export function ConfirmDialog({ P, S, c, send, busy, onClose }: { P: Plan; S: PlanState; c: Computed; send: () => Promise<void>; busy: boolean; onClose: () => void }) {
  const off = S.walls.filter((w) => !w.keep).length, man = S.walls.filter((w) => w.src === "manual" && w.keep).length;
  return (
    <Sheet onClose={onClose}>
      <h2>Xác nhận mặt bằng &quot;{P.plan.name}&quot;</h2>
      <p>Chiều cao tầng {fmt(S.height_mm / 1000)} m · {S.walls.filter((w) => w.keep).length} đoạn tường (vẽ thêm {man}, đã loại {off}) · {S.openings.filter((o) => o.keep).length} lỗ mở.</p>
      <p>Diện tích tường thực tính tạm: <b>{fmt(c.total)} m²</b>. Vật liệu được lựa chọn ở bước tiếp theo.</p>
      <p>Máy chủ sẽ tính lại khối lượng bằng cùng công thức và trả kết quả chốt.</p>
      <div className={s.actions}><button className={s.btn} type="button" disabled={busy} onClick={onClose}>Quay lại sửa</button>
        <button className={`${s.btn} ${s.primary}`} type="button" disabled={busy} onClick={send}>{busy ? "Đang gửi…" : "Xác nhận"}</button></div>
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

/** Xác nhận chỉ hiển thị khối lượng; vật liệu và tối ưu nằm ở bước sau. */
export function ConfirmedDialog({ body, total, onClose, onNext }: { body: Confirmed; total: number; onClose: () => void; onNext: () => void }) {
  return <Sheet onClose={onClose}>
    <h2>Đã xác nhận khối lượng mặt bằng</h2>
    <p>Diện tích tường thực: <b>{fmt(body.total_net_area_m2)} m²</b> (trang tính {fmt(total)} m²).</p>
    <p>Tiếp tục xác nhận các mặt bằng cần tính. Khi hoàn tất, hệ thống mở bước Kiểm tra công tác và khối lượng.</p>
    {body.warnings.length > 0 && <Warn items={body.warnings} />}
    <button className={s.btn} type="button" onClick={onNext}>Kiểm tra mặt bằng tiếp theo</button>
  </Sheet>;
}
