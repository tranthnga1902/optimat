"use client";
// Nội dung các tab bên phải: Tường, Lỗ mở, Khối lượng, Cảnh báo (tab Phần thô ở Rough.tsx).
import type { ReactNode } from "react";
import s from "./review.module.css";
import { ChangeInput } from "./ChangeInput";
import { BillTable } from "./Dialogs";
import { useWallClasses } from "@/lib/reference";
import {
  KIND, REASONS, ROLE, clsColor, convBad, famLabel, fmt, matLabel, matOf, sysOf, wallLen,
  type Computed, type Confirmed, type Data, type Plan, type PlanState, type Wall,
} from "./model";

export type Change = (id: string, f: string, v: string | boolean) => void;
const tag = (cls: string, t: ReactNode) => <span className={`${s.tag} ${cls}`}>{t}</span>;
const pickRow = (onSelect: (id: string) => void, id: string) => (e: React.MouseEvent) => {
  if ((e.target as Element).closest("select,input,button")) return;
  onSelect(id);
};

function MatSelect({ D, w, onChange }: { D: Data; w: Wall; onChange: (v: string) => void }) {
  const opt = (m: Data["materials"][number], k: string) =>
    <option key={k + m.id} value={m.id}>{m.label}{m.systems && m.systems[w.cls] ? "" : ` (chưa có phương án tường ${w.cls})`}</option>;
  const head = w.mat ? "Chưa rõ" : w.fam ? "Chưa chọn · bản vẽ ghi: " + famLabel(D, w.fam) : "Chưa rõ";
  const sugg = (w.cand || []).map((sid) => D.materials.find((m) => m.systems && m.systems[w.cls] === sid)).filter((m) => !!m);
  return (
    <select aria-label="Vật liệu" value={w.mat || ""} onChange={(e) => onChange(e.target.value)}>
      <option value="">{head}</option>
      {sugg.length > 0 && <optgroup label="Phương án hợp với ghi chú">{sugg.map((m, i) => opt(m, "s" + i))}</optgroup>}
      {D.families.map((f) => {
        const ms = D.materials.filter((m) => m.family === f.id);
        return ms.length ? <optgroup key={f.id} label={f.label}>{ms.map((m) => opt(m, f.id))}</optgroup> : null;
      })}
      {w.mat && !matOf(D, w.mat) && <option value={w.mat}>{matLabel(D, w.mat)}</option>}
    </select>
  );
}

const NAMES: Record<string, string> = { all: "Tất cả", low: "Tin cậy thấp", nomat: "Chưa có vật liệu", man: "Vẽ thêm", off: "Đã loại" };

export function WallFilters({ S, filter, onFilter, onAllMat }: { S: PlanState; filter: string; onFilter: (f: string) => void; onAllMat?: () => void }) {
  const counts: Record<string, number> = { all: S.walls.length, low: S.walls.filter((w) => w.keep && w.conf < 0.7).length,
    off: S.walls.filter((w) => !w.keep).length, man: S.walls.filter((w) => w.src === "manual").length,
    nomat: S.walls.filter((w) => w.keep && w.masonry && !w.mat).length };
  return <>
    {Object.keys(NAMES).filter((k) => onAllMat || k !== "nomat").map((k) => <button key={k} className={s.pill} type="button" aria-pressed={filter === k} onClick={() => onFilter(k)}>{NAMES[k]} {counts[k]}</button>)}
    <span className={s.grow} />{onAllMat && <button className={s.pill} type="button" onClick={onAllMat}>Gán vật liệu cho mọi tường chưa rõ…</button>}
  </>;
}

export function WallList({ materials = true, D, S, c, filter, selected, onSelect, change }: { materials?: boolean; D: Data; S: PlanState; c: Computed; filter: string; selected: string | null; onSelect: (id: string) => void; change: Change }) {
  const classes = useWallClasses();
  let items = S.walls;
  if (filter === "low") items = items.filter((w) => w.keep && w.conf < 0.7);
  if (filter === "off") items = items.filter((w) => !w.keep);
  if (filter === "man") items = items.filter((w) => w.src === "manual");
  if (filter === "nomat") items = items.filter((w) => w.keep && w.masonry && !w.mat);
  if (!items.length) return <div className={s.empty}>Không có tường nào trong mục này.</div>;
  return <>{items.map((w) => {
    const len = c.len[w.id] ?? wallLen(w), area = len * S.height_mm / 1000 - (c.openArea[w.id] || 0);
    return (
      <div key={w.id} data-id={w.id} className={`${s.row} ${w.keep ? "" : s.off} ${w.id === selected ? s.sel : ""}`} onClick={pickRow(onSelect, w.id)}>
        <input type="checkbox" checked={w.keep} onChange={(e) => change(w.id, "keep", e.target.checked)} aria-label={`Giữ tường ${w.id}`} title="Bỏ chọn để loại tường nhận nhầm" />
        <span className={s.rid}><i className={s.sw} style={{ background: w.masonry ? clsColor(w.cls) : "var(--concrete)" }} />{w.id}</span>
        <span className={s.rmain}>
          <select aria-label="Loại tường" value={w.cls} onChange={(e) => change(w.id, "cls", e.target.value)}>{(classes.includes(w.cls) ? classes : [...classes, w.cls]).map((k) => <option key={k}>{k}</option>)}</select>
          <select aria-label="Vai trò" value={w.role} onChange={(e) => change(w.id, "role", e.target.value)}><option value="envelope">bao che</option><option value="partition">ngăn</option></select>
          {materials && (w.masonry ? <MatSelect D={D} w={w} onChange={(v) => change(w.id, "mat", v)} /> : tag("", "bê tông, không tính"))}
          {w.src === "manual" ? tag(s.man, "vẽ thêm") : w.edited ? tag(s.edit, "đã sửa") : null}
          {w.src !== "manual" && w.conf < 0.7 && tag(s.low, `tin cậy ${fmt(w.conf)}`)}
          {!w.keep && w.src !== "manual" && <select aria-label="Lý do loại" value={w.reason || REASONS[0]} onChange={(e) => change(w.id, "reason", e.target.value)}>
            {REASONS.map((r) => <option key={r}>{r}</option>)}</select>}
        </span>
        <span className={s.rnum}>{fmt(len)} m<small>{!(w.keep && w.masonry) ? "—" : S.height_mm ? fmt(Math.max(0, area)) + " m²" : "chưa tính"}</small></span>
      </div>
    );
  })}</>;
}

export function OpeningList({ S, selected, onSelect, change, onDelete }: { S: PlanState; selected: string | null; onSelect: (id: string) => void; change: Change; onDelete: (id: string) => void }) {
  const byId = Object.fromEntries(S.walls.map((w) => [w.id, w]));
  if (!S.openings.length) return <div className={s.empty}>Chưa có lỗ mở. Chọn &quot;Thêm cửa&quot; rồi bấm lên tường để thêm.</div>;
  return <>{S.openings.map((o) => {
    const w = byId[o.wall], on = o.keep && w && w.keep;
    const size = (f: "w" | "h") => (el: HTMLInputElement) => { change(o.id, f, el.value); const v = Number(el.value) ? Math.max(100, Number(el.value)) : o[f]; return v == null ? "" : String(Math.round(v)); };
    return (
      <div key={o.id} data-id={o.id} className={`${s.row} ${on ? "" : s.off} ${o.id === selected ? s.sel : ""}`} onClick={pickRow(onSelect, o.id)}>
        <input type="checkbox" checked={o.keep} onChange={(e) => change(o.id, "keep", e.target.checked)} aria-label={`Giữ lỗ mở ${o.id}`} />
        <span className={s.rid}><i className={s.sw} style={{ background: "var(--open)" }} />{o.id}</span>
        <span className={s.rmain}>
          <select aria-label="Loại cửa" value={o.kind} onChange={(e) => change(o.id, "kind", e.target.value)}>{Object.keys(KIND).map((k) => <option key={k} value={k}>{KIND[k]}</option>)}</select>
          <ChangeInput type="number" value={o.w == null ? "" : String(Math.round(o.w))} placeholder="nhập rộng" step={50} min={100} aria-label="Rộng (mm)" onCommit={size("w")} /> ×
          <ChangeInput type="number" value={o.h == null ? "" : String(Math.round(o.h))} placeholder="nhập cao" step={50} min={100} aria-label="Cao (mm)" onCommit={size("h")} />
          {tag("", `tường ${o.wall}`)}
          {o.src === "manual" ? tag(s.man, "thêm tay") : o.ev ? tag("", o.ev) : null}
          {o.src === "manual" && <button className={s.x} type="button" aria-label="Xóa lỗ mở" onClick={() => onDelete(o.id)}>×</button>}
        </span>
        <span className={s.rnum}>{o.w == null || o.h == null ? "chưa trừ" : `${fmt(o.w * Math.min(o.h, S.height_mm) / 1e6)} m²`}</span>
      </div>
    );
  })}</>;
}

export function QtyTab({ materials = true, D, S, c, confirmed }: { materials?: boolean; D: Data; S: PlanState; c: Computed; confirmed?: Confirmed }) {
  const edits = S.walls.filter((w) => w.edited || w.src === "manual" || !w.keep).length + S.openings.filter((o) => o.src === "manual" || o.edited || !o.keep).length;
  return (
    <div className={s.qty}>
      <p className={s.label}>Khối lượng theo loại tường · chiều cao {fmt(S.height_mm / 1000)} m</p>
      <div style={{ overflowX: "auto" }}><table><thead><tr><th>Loại</th><th>Vai trò</th><th className={s.num}>Dài m</th><th className={s.num}>Gộp m²</th><th className={s.num}>Lỗ mở m²</th><th className={s.num}>Thực m²</th></tr></thead>
        <tbody>{c.groups.length ? c.groups.map((g, i) => <tr key={i}><td><i className={s.sw} style={{ background: clsColor(g.cls) }} /> {g.cls}</td><td>{ROLE[g.role]}</td>
          <td className={s.num}>{fmt(g.L)}</td><td className={s.num}>{fmt(g.gross)}</td><td className={s.num}>{fmt(g.open)}</td><td className={s.num}><b>{fmt(g.net)}</b></td></tr>)
          : <tr><td colSpan={6}>Chưa có tường nào được giữ.</td></tr>}</tbody>
        <tfoot><tr><td colSpan={5}>Tổng</td><td className={s.num}>{fmt(c.total)}</td></tr></tfoot></table></div>
      {materials && <><p className={s.label}>Vật liệu theo thiết kế</p>
      <div style={{ overflowX: "auto" }}><table><tbody>{c.groups.map((g, i) => {
        const sys = g.mat && sysOf(D, g.mat, g.cls);
        return <tr key={i}><td>{g.cls} {ROLE[g.role]}</td><td>{g.mat ? <>{matLabel(D, g.mat)} {tag("", `${Math.round(g.share * 100)}% chiều dài`)}{" "}
          {sys ? tag("", sys) : tag(s.low, `chưa có phương án tường ${g.cls}`)}</> : tag(s.low, "chưa rõ")}</td></tr>;
      })}</tbody></table></div>
      </>}
      <p style={{ color: "var(--muted)", margin: 0 }}>{edits ? `Đã chỉnh tay ${edits} mục so với kết quả tự động.` : "Chưa chỉnh mục nào."} Số trên trang là tính tạm; bấm &quot;Xác nhận bản vẽ&quot; để chốt kích thước và khối lượng.</p>
      {materials && confirmed && confirmed.bill && <BillTable r={confirmed} />}
    </div>
  );
}

function Conventions({ D }: { D: Data }) {
  const C = D.conventions;
  if (!C) return null;
  if (C.error) return <ul className={s.warn}><li>{C.error}</li></ul>;
  const n = (st: string) => C.checks.filter((c) => c.trang_thai === st).length;
  const verdict = C.trong_quy_uoc == null ? "Không áp dụng: file không có mặt bằng kiến trúc."
    : C.trong_quy_uoc ? "Trong quy ước: không vi phạm điều khoản bắt buộc (B)."
    : "Ngoài quy ước: có vi phạm điều khoản bắt buộc (B). Vẫn bóc tách, nhưng không tính vào số liệu cam kết sai số.";
  const bad = convBad(D);
  return <>
    <p className={s.label} style={{ margin: 12 }}>Quy ước bản vẽ v1.0 (cả file)</p><p style={{ margin: "0 12px" }}>{verdict}</p>
    {bad.length > 0 && <ul className={s.warn}>{bad.map((c, i) => <li key={i}><b>{c.ma}</b> {tag(c.muc === "B" ? s.low : "", c.muc === "B" ? "bắt buộc" : "khuyến nghị")} {c.ket_qua}
      {c.bang_chung.length > 0 && <details><summary>{c.bang_chung.length} bằng chứng</summary>{c.bang_chung.map((b, j) => <span key={j}>{j ? <br /> : null}{b}</span>)}</details>}</li>)}</ul>}
    <p style={{ color: "var(--muted)", margin: "0 12px 12px", fontSize: 12 }}>{n("dat")} đạt · {n("chua_kiem")} chưa kiểm · {n("khong_ap_dung")} không áp dụng. Định nghĩa và bằng chứng từng điều khoản: <code>python scripts/concept_report.py &lt;bản vẽ&gt;</code></p>
  </>;
}

export function WarnTab({ D, P }: { D: Data; P: Plan }) {
  const w = P.warnings || [];
  return <>
    <Conventions D={D} />
    {w.length ? <><p className={s.label} style={{ margin: 12 }}>Mặt bằng này</p><ul className={s.warn}>{w.map((x, i) => <li key={i}>{x}</li>)}</ul></>
      : <div className={s.empty}>Không có cảnh báo.</div>}
  </>;
}

// Toàn bộ bản vẽ: mở cả file như phần mềm xem bản vẽ, khung các mặt bằng đã tách; bấm khung để kiểm tra mặt bằng đó.
export function OverviewList({ D, indices, onOpen }: { D: Data; indices: number[]; onOpen: (i: number) => void }) {
  const O = D.overview!;
  return <>
    {!D.plans.length && <div className={s.empty}>Không tìm thấy mặt bằng kiến trúc để đo tường (bản vẽ chỉ có mặt bằng kết cấu, móng hoặc điện nước).</div>}
    <div className={s.empty} style={{ textAlign: "left" }}>Toàn bộ bản vẽ, vẽ như phần mềm CAD. Khung xanh là các mặt bằng tầng hệ thống đã tách ({O.plans.length}).
      Bấm vào khung hoặc chọn bên dưới để kiểm tra từng mặt bằng.</div>
    {O.plans.map((b, i) => indices.includes(i) && (
      <div key={i} className={s.overviewRow}><b style={{ flex: 1 }}>{i + 1}. {b.name}</b><button className={s.btn} type="button" onClick={() => onOpen(i)}>Kiểm tra</button></div>
    ))}
  </>;
}
