"use client";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { api, money, nf, post } from "@/lib/api";
import { useReference } from "@/lib/reference";
import { store, useStored, type ConfirmedPlan } from "@/lib/store";
import { currentPurchaseKey, usePurchaseSession } from "@/lib/purchase-session";
import { Card, Head, Note, Steps } from "@/components/ui";
import { Sheet } from "@/components/Sheet";
import { Proposal } from "./Proposal";

type Cons = { budget: number | null; deadline_days: number | null; max_vehicle_ton: number | null; keep_design_material: boolean; excluded_materials: string[]; site_lat?: number; site_lon?: number; province: string; procurement_mode: boolean; approved_wall_system_ids: string[] };
type Form = { budget: string; deadline: string; veh: string; keep: boolean; ex: string[]; lat: string; lon: string; province: string; approved: string[] };
type System = { wall_system_id: string; detect_class: string; data_kind: string; ready: boolean };
type Choice = {
  wall_type: string; raw_class?: string | null; wall_system_id?: string; material_id?: string; material_name: string; quantity: number; unit: string; unit_price: number; price_source: string;
  product_url?: string; supplier_name: string; distance_km: number | null; trips: number | null; vehicle_id: string;
  mortar_material_name?: string; mortar_quantity?: number; mortar_unit?: string; mortar_cost?: number; install_cost: number; transport_cost: number; transport_estimated: boolean; cost_basis: string;
};
type Sol = { total_cost: number; supply_days: number; u_value: number; choices: Choice[] };
type Result = { solutions?: Sol[]; n_evaluated?: number; notes?: string[] };

const s = (v: unknown) => (v == null ? "" : String(v));
const toForm = (c: Partial<Cons>): Form => ({ budget: s(c.budget), deadline: s(c.deadline_days), veh: s(c.max_vehicle_ton), keep: c.keep_design_material ?? true, ex: c.excluded_materials || [],
  lat: s(c.site_lat), lon: s(c.site_lon), province: c.province || "", approved: c.approved_wall_system_ids || [] });
const toCons = (f: Form): Cons => ({ budget: f.budget ? Number(f.budget) : null, deadline_days: f.deadline ? Number(f.deadline) : null,
  max_vehicle_ton: f.veh ? Number(f.veh) : null, keep_design_material: f.keep, excluded_materials: f.ex, procurement_mode: true,
  site_lat: f.lat.trim() ? Number(f.lat) : undefined, site_lon: f.lon.trim() ? Number(f.lon) : undefined, province: f.province.trim(), approved_wall_system_ids: f.keep ? [] : f.approved });
const field = "field w-full";

export function Optimize() {
  const { work: rough, key, reviewed, receipt, draftKey } = usePurchaseSession();
  const plans = useStored<ConfirmedPlan[]>("optimat-confirmed", []);
  const saved = useStored<Partial<Cons>>("optimat-constraints", {});
  const groups = rough?.result.wall_groups;
  const issues = reviewed?.result.wall_group_issues;
  // vật tư ngoài tường: bỏ phần đi vào khối xây (gạch, vữa xây đã nằm trong nhóm tường) để không tính hai lần
  const materials = useMemo(() => (rough?.result.materials || []).flatMap(m => {
    if (!m.material_id || !m.raw_class || m.raw_class === "gach" || m.raw_class === "khac" || !m.quantity) return [];
    const outside = m.uses?.length ? m.uses.filter(u => u.work !== "XAY").reduce((sum, u) => sum + (u.quantity || 0), 0) : m.quantity;
    const quantity = outside / m.quantity * (m.quantity_with_waste ?? m.quantity);
    return quantity > 0 ? [{ material_id: m.material_id, quantity, unit: m.unit, raw_class: m.raw_class }] : [];
  }), [rough]);
  const hasScope = !!groups?.length || materials.length > 0;
  // null: chưa sửa gì, hiển thị theo ràng buộc đã lưu
  const [edit, setEdit] = useState<{ key: string | null; form: Form } | null>(null);
  const f = edit && edit.key === key ? edit.form : toForm(saved);
  const requestRevision = useRef(0);
  const mounted = useRef(false);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const set = (next: Form) => { requestRevision.current++; setOut(null); store.set("optimat-optimization", null); setEdit({ key, form: next }); store.set("optimat-constraints", toCons(next)); };
  const [systems, setSystems] = useState<System[]>([]);
  const [systemError, setSystemError] = useState("");
  useEffect(() => {
    let live = true;
    api<{ wall_systems: System[] }>("/api/catalog/wall-materials").then(r => live && setSystems(r.wall_systems), err => live && setSystemError(err.message));
    return () => { live = false; };
  }, []);

  // họ vật liệu tường và tải trọng xe lấy từ database (material_families, vehicles)
  const { ref, error: refErr } = useReference();
  const fams = useMemo(() => (ref?.families || []).filter((x) => x.is_wall), [ref]);
  const tons = useMemo(() => [...new Set((ref?.vehicles || []).map((v) => v.payload_ton))].sort((a, b) => a - b), [ref]);
  const famName = (k: string) => fams.find((x) => x.id === k)?.name || k;

  const [msgs, setMsgs] = useState<{ me?: boolean; text: string }[]>([]);
  const [text, setText] = useState("");
  const chat = useRef<HTMLDivElement>(null);
  useEffect(() => { if (chat.current) chat.current.scrollTop = chat.current.scrollHeight; }, [msgs]);
  const say = async (e: FormEvent) => {
    e.preventDefault();
    const t = text.trim(); if (!t || !key || currentPurchaseKey() !== key) return;
    setMsgs((m) => [...m, { me: true, text: t }]); setText("");
    let reply: string;
    try {
      const p = await post("/api/constraints/parse", { message: t, use_llm: true });
      if (!mounted.current || currentPurchaseKey() !== key) return;
      const got: string[] = [], next = { ...f, ex: [...f.ex] };
      if (p.budget != null) { next.budget = String(p.budget); got.push(`ngân sách ${money(p.budget)} đồng`); }
      if (p.deadline_days != null) { next.deadline = String(p.deadline_days); got.push(`hạn ${p.deadline_days} ngày`); }
      // xe lớn nhất trong bảng vehicles không vượt giới hạn; bảng chưa có loại xe phù hợp thì giữ đúng số tấn trong câu
      if (p.max_vehicle_ton != null) { next.veh = s(tons.filter((v) => v <= p.max_vehicle_ton + 1e-9).pop() ?? p.max_vehicle_ton); got.push(`xe tối đa ${String(p.max_vehicle_ton).replace(".", ",")} tấn`); }
      const ex: string[] = p.excluded_materials || [];
      for (const k of ex) if (fams.some((x) => x.id === k) && !next.ex.includes(k)) next.ex.push(k);
      if (ex.length) got.push("loại " + ex.map(famName).join(", "));
      set(next);
      reply = `${got.length ? "Đã ghi nhận: " + got.join("; ") + "." : "Tôi chưa nhận ra ràng buộc nào trong câu này."} (bộ trích: ${p.source})`;
    } catch (err) { reply = (err as Error).message; }
    setMsgs((m) => [...m, { text: reply }]);
  };

  const savedResult = useStored<(Result & { basis?: string }) | null>("optimat-optimization", null);
  const [out, setOut] = useState<{ basis: string; busy?: boolean; r?: Result; err?: string } | null>(null);
  const basis = JSON.stringify([key, toCons(f)]);
  const visibleOut: { busy?: boolean; r?: Result; err?: string } | null =
    out?.basis === basis ? out : savedResult?.basis === basis ? { r: savedResult } : null;
  const run = async (e: FormEvent) => {
    e.preventDefault();
    if (!key || currentPurchaseKey() !== key || !hasScope || issues?.length || !f.province.trim()) return;
    const atRevision = ++requestRevision.current;
    const cons = toCons(f); store.set("optimat-constraints", cons);
    setOut({ basis, busy: true });
    try {
      const context = rough?.request.project_id && rough.result.takeoff_id
        ? { project_id: rough.request.project_id, takeoff_id: rough.result.takeoff_id } : {};
      const r = await post<Result>("/api/optimize", { groups: groups || [], materials, constraints: cons, ...context });
      if (!mounted.current || requestRevision.current !== atRevision || currentPurchaseKey() !== key) return;
      store.set("optimat-optimization", { ...r, basis }); setOut(null);
    }
    catch (err) { if (mounted.current && requestRevision.current === atRevision && currentPurchaseKey() === key) setOut({ basis, err: (err as Error).message }); }
  };

  if (!reviewed || !receipt || !draftKey) return <><Head title="Phương án vật liệu" /><Note>Hãy <Link href="/phan-tho">kiểm tra và lưu khối lượng phần thô</Link> để lập phương án cho đúng dự án.</Note></>;
  const proposal = <Proposal key={draftKey} work={reviewed} receipt={receipt} versionKey={draftKey} />;
  if (!hasScope || issues?.length) return <><Head title="Phương án vật liệu" />{proposal}
    <Note>{issues?.length ? issues.join(" · ") : "Bản tính chưa có khối xây tường hay vật tư có mã để tối ưu."}</Note></>;
  return (
    <>
      <Steps cur="/toi-uu" done={{ "/do-boc": plans.length > 0, "/phan-tho": !!rough }} />
      <Head title="Phương án vật liệu" />{proposal}
      <Head title="So sánh phương án vật liệu">So sánh chi phí, thời gian cung ứng dự kiến và hệ số truyền nhiệt U của lớp xây. Tường: chọn cấu tạo, đại lý, xe ({groups?.length || 0} nhóm).
        Vật tư khác (thép, bê tông, xi măng, cát, đá…): giữ mã thiết kế, chọn đại lý và xe ({materials.length} mã).</Head>
      <div className="flex flex-wrap items-start gap-[18px]">
        <form className="flex min-w-0 flex-[1_1_300px] flex-col gap-3 rounded-xl border border-rule bg-card p-[18px]" onSubmit={run}>
          <h2 className="m-0 text-base font-bold">Ràng buộc</h2>
          <label>Tỉnh, thành công trình (tra nhân công)<input className={field} required value={f.province} onChange={e => set({...f, province: e.target.value})} /></label>
          <label>Vĩ độ công trình<input className={field} type="number" required step="any" min="-90" max="90" value={f.lat} onChange={e => set({...f, lat: e.target.value})} /></label>
          <label>Kinh độ công trình<input className={field} type="number" required step="any" min="-180" max="180" value={f.lon} onChange={e => set({...f, lon: e.target.value})} /></label>
          <label className="flex flex-col gap-1.5 font-semibold">Ngân sách vật liệu (đồng)
            <input className={field} type="number" min="0" step="1000000" placeholder="không giới hạn" value={f.budget} onChange={(e) => set({ ...f, budget: e.target.value })} /></label>
          <label className="flex flex-col gap-1.5 font-semibold">Hạn có vật liệu (ngày)
            <input className={field} type="number" min="0" placeholder="không giới hạn" value={f.deadline} onChange={(e) => set({ ...f, deadline: e.target.value })} /></label>
          <label className="flex flex-col gap-1.5 font-semibold">Xe lớn nhất vào được
            <select className={field} value={f.veh} onChange={(e) => set({ ...f, veh: e.target.value })}>
              <option value="">không giới hạn</option>
              {[...tons, ...(f.veh && !tons.includes(Number(f.veh)) ? [Number(f.veh)] : [])].map((t) => <option key={t} value={String(t)}>{String(t).replace(".", ",")} tấn</option>)}
            </select>
            {ref && !tons.length && <span className="text-[12.5px] font-normal text-muted">Bảng <code>vehicles</code> chưa có loại xe nào.</span>}</label>
          <fieldset className="m-0 border-0 p-0"><legend className="mb-1.5 font-semibold">Loại trừ họ vật liệu</legend>
            {refErr ? <Note>{refErr}</Note> : !ref ? <span className="text-muted">Đang tải…</span> : (
              <div className="flex flex-wrap gap-x-3.5 gap-y-1">{fams.map(({ id: k, name: t }) => (
                <label key={k} className="flex min-h-8 items-center gap-2"><input type="checkbox" checked={f.ex.includes(k)}
                  onChange={(e) => set({ ...f, ex: e.target.checked ? [...f.ex, k] : f.ex.filter((x) => x !== k) })} /> {t}</label>
              ))}</div>)}</fieldset>
          <label className="flex min-h-8 items-center gap-2"><input type="checkbox" checked={f.keep} onChange={(e) => set({ ...f, keep: e.target.checked })} /> Giữ vật liệu theo thiết kế (chỉ chọn đại lý và xe)</label>
          {!f.keep && <fieldset><legend>Cấu tạo thay thế đã được duyệt cho công trình</legend>
            {systemError && <Note>{systemError}</Note>}
            {systems.filter(w => w.ready && w.data_kind === "ACTUAL" && groups?.some(g => g.wall_type === w.detect_class && g.design_wall_system_id !== w.wall_system_id)).map(w =>
              <label key={w.wall_system_id} className="flex items-center gap-2"><input type="checkbox" checked={f.approved.includes(w.wall_system_id)}
                onChange={e => set({...f, approved: e.target.checked ? [...f.approved, w.wall_system_id] : f.approved.filter(id => id !== w.wall_system_id)})}/>{w.wall_system_id} · lớp {w.detect_class}</label>)}
            <small>Để trống nếu chỉ có cấu tạo thiết kế được duyệt.</small></fieldset>}
          <button className="btn primary" type="submit" disabled={!hasScope}>Chạy tối ưu</button>
        </form>
        <Card title="Trợ lý OptiMat" className="flex-[1_1_320px]">
          <div ref={chat} className="flex max-h-[340px] flex-col gap-2.5 overflow-y-auto">
            {[{ text: 'Nêu yêu cầu bằng tiếng Việt, ví dụ: "Ngõ chỉ xe 2,5 tấn vào được, ngân sách 150 triệu, cần hàng trong 1 tuần, không dùng gạch nung". Tôi điền vào ô ràng buộc để bạn kiểm tra rồi chạy.' } as { me?: boolean; text: string }, ...msgs].map((m, i) => (
              <div key={i} className={`max-w-[90%] px-3 py-2.5 whitespace-pre-line ${m.me ? "self-end rounded-[12px_12px_2px_12px] bg-accent text-accent-ink" : "self-start rounded-[12px_12px_12px_2px] bg-bg"}`}>{m.text}</div>
            ))}
          </div>
          <form className="flex gap-2" onSubmit={say}>
            <label htmlFor="chatText" className="sr-only">Nhập yêu cầu</label>
            <input id="chatText" className="field min-w-0 flex-auto" placeholder="Nhập yêu cầu" autoComplete="off" value={text} onChange={(e) => setText(e.target.value)} />
            <button className="btn bg-ink! text-card!" type="submit">Gửi</button>
          </form>
        </Card>
      </div>
      {visibleOut?.busy ? <Card><span className="text-muted">Đang tối ưu…</span></Card>
        : visibleOut?.err ? <Card><Note>{visibleOut.err}</Note></Card>
        : visibleOut?.r && <Solutions r={visibleOut.r} />}
    </>
  );
}

function Solutions({ r }: { r: Result }) {
  const sols = r.solutions || [];
  const picks: [string, Sol][] = sols.length ? [["Chi phí thấp nhất", sols[0]], ["Cung ứng nhanh nhất", [...sols].sort((a, b) => a.supply_days - b.supply_days || a.total_cost - b.total_cost)[0]],
    ["Cách nhiệt tốt nhất", [...sols].sort((a, b) => a.u_value - b.u_value || a.total_cost - b.total_cost)[0]]] : [];
  const highlights = new Map<Sol, string[]>();
  for (const [label, sol] of picks) highlights.set(sol, [...(highlights.get(sol) || []), label]);
  const small = "text-[12.5px] text-muted";
  return (
    <>
      {sols.length ? (<>
        <div className="flex flex-wrap items-start gap-[18px]">{Array.from(highlights, ([x, labels]) => (
          <Card key={labels[0]} title={sols.length === 1 ? "Phương án tường duy nhất trong kết quả" : labels.join(" · ")} className="flex-[1_1_280px]">
            <div className="grid grid-cols-3 gap-3.5">
              <div><div className={small}>Tổng</div><b>{money(x.total_cost)} đ</b></div>
              <div><div className={small}>Cung ứng dự kiến</div><b>{x.supply_days ? `${x.supply_days} ngày` : "chưa có"}</b></div>
              <div><div className={small}>U</div><b>{nf(x.u_value, 3)}</b></div>
            </div>
            <div className="tw"><table><tbody>{x.choices.map((c, i) => (
              <tr key={i}>
                <td>{c.wall_type}<div className={small}>{c.wall_system_id}</div></td>
                <td>{c.material_name}<div className={small}>{nf(c.quantity)} {c.unit} × {money(c.unit_price)} đ</div>
                  {c.mortar_material_name && <div className={small}>{c.mortar_material_name} · {nf(c.mortar_quantity, 3)} {c.mortar_unit} · {money(c.mortar_cost)} đ</div>}
                  {!c.raw_class && <div className={small}>Nhân công {money(c.install_cost)} đ</div>}</td>
                <td>{c.product_url ? <a href={c.product_url} target="_blank" rel="noopener">{c.supplier_name}</a> : c.supplier_name}
                  <div className={small}>{c.vehicle_id === "CHUA_TINH" ? "Giá công bố: chưa VAT, chưa tính vận chuyển" : c.transport_estimated ? `Cước dự tính ${money(c.transport_cost)} đ` : "Giá đã gồm giao hàng"} {c.trips ? `· ${c.trips} chuyến ${c.vehicle_id}` : ""}</div><small>{c.cost_basis}</small></td>
              </tr>
            ))}</tbody></table></div>
          </Card>
        ))}</div>
        <Card title={`Tập Pareto: ${sols.length} phương án không bị trội (đã xét ${r.n_evaluated} tổ hợp)`}>
          <Sheet file="so-sanh-phuong-an.csv" rows={sols.map((solution,index)=>({
            ...solution, option:index+1, selection:solution.choices.map(c=>
              `${c.wall_type}: ${c.wall_system_id || c.material_id} · ${c.supplier_name} · ${c.vehicle_id}`).join("\n")
          }))} cols={[
            {key:"option",title:"Phương án",num:true},
            {key:"total_cost",title:"Tổng tiền (đồng)",num:true,render:r=>money(r.total_cost)},
            {key:"supply_days",title:"Ngày cung ứng",num:true},
            {key:"u_value",title:"Hệ số U",num:true,render:r=>nf(r.u_value,3)},
            {key:"selection",title:"Lựa chọn",render:r=><span className="whitespace-pre-line">{r.selection}</span>}
          ]}/>
        </Card>
      </>) : <Card><Note>Chưa có phương án đủ dữ liệu và thỏa các ràng buộc đã nhập.</Note></Card>}
      {!!r.notes?.length && <Card title="Ghi chú của bước tối ưu"><ul className="m-0 pl-[18px] text-muted">{r.notes.map((n, i) => <li key={i}>{n}</li>)}</ul></Card>}
    </>
  );
}
