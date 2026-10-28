"use client";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { money, nf, post } from "@/lib/api";
import { useReference } from "@/lib/reference";
import { mergedGroups, store, useStored, type ConfirmedPlan } from "@/lib/store";
import { Card, Head, Note, Steps } from "@/components/ui";

type Cons = { budget: number | null; deadline_days: number | null; max_vehicle_ton: number | null; keep_design_material: boolean; excluded_materials: string[] };
type Form = { budget: string; deadline: string; veh: string; keep: boolean; ex: string[] };
type Choice = {
  wall_type: string; wall_system_id?: string; material_id?: string; material_name: string; quantity: number; unit: string; unit_price: number; price_source: string;
  product_url?: string; supplier_name: string; distance_km: number; trips: number; vehicle_id: string;
};
type Sol = { total_cost: number; supply_days: number; u_value: number; choices: Choice[] };
type Result = { solutions?: Sol[]; n_evaluated?: number; notes?: string[] };

const s = (v: unknown) => (v == null ? "" : String(v));
const toForm = (c: Partial<Cons>): Form => ({ budget: s(c.budget), deadline: s(c.deadline_days), veh: s(c.max_vehicle_ton), keep: !!c.keep_design_material, ex: c.excluded_materials || [] });
const toCons = (f: Form): Cons => ({ budget: f.budget ? Number(f.budget) : null, deadline_days: f.deadline ? Number(f.deadline) : null,
  max_vehicle_ton: f.veh ? Number(f.veh) : null, keep_design_material: f.keep, excluded_materials: f.ex });
const field = "field w-full";

export function Optimize() {
  const plans = useStored<ConfirmedPlan[]>("optimat-confirmed", []);
  const rough = useStored("optimat-rough", null);
  const saved = useStored<Partial<Cons>>("optimat-constraints", {});
  const groups = useMemo(() => mergedGroups(plans), [plans]);
  // null: chưa sửa gì, hiển thị theo ràng buộc đã lưu
  const [edit, setEdit] = useState<Form | null>(null);
  const f = edit ?? toForm(saved);
  const set = (next: Form) => { setEdit(next); store.set("optimat-constraints", toCons(next)); };

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
    const t = text.trim(); if (!t) return;
    setMsgs((m) => [...m, { me: true, text: t }]); setText("");
    let reply: string;
    try {
      const p = await post("/api/constraints/parse", { message: t, use_llm: true });
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

  const [out, setOut] = useState<{ busy?: boolean; r?: Result; err?: string } | null>(null);
  const run = async (e: FormEvent) => {
    e.preventDefault();
    const cons = toCons(f); store.set("optimat-constraints", cons);
    setOut({ busy: true });
    try { setOut({ r: await post<Result>("/api/optimize", { groups, constraints: cons }) }); }
    catch (err) { setOut({ err: (err as Error).message }); }
  };

  return (
    <>
      <Steps cur="/toi-uu" done={{ "/do-boc": plans.length > 0, "/phan-tho": !!rough }} />
      <Head title="Phương án tối ưu">Ba mục tiêu: tổng chi phí, thời gian cung ứng, hệ số truyền nhiệt U. Chỉ phương án tường đủ số liệu trong danh mục được đưa vào; phương án thiếu số liệu được liệt kê bên dưới.</Head>
      {!groups.length && <Note>Chưa có mặt bằng nào được xác nhận. Vào <Link href="/do-boc">Hồ sơ và đo bóc</Link> trước.</Note>}
      <div className="flex flex-wrap items-start gap-[18px]">
        <form className="flex min-w-0 flex-[1_1_300px] flex-col gap-3 rounded-xl border border-rule bg-card p-[18px]" onSubmit={run}>
          <h2 className="m-0 text-base font-bold">Ràng buộc</h2>
          <label className="flex flex-col gap-1.5 font-semibold">Ngân sách phần tường (đồng)
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
          <button className="btn primary" type="submit" disabled={!groups.length}>Chạy tối ưu</button>
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
      {out?.busy ? <Card><span className="text-muted">Đang tối ưu…</span></Card>
        : out?.err ? <Card><Note>{out.err}</Note></Card>
        : out?.r && <Solutions r={out.r} />}
    </>
  );
}

function Solutions({ r }: { r: Result }) {
  const sols = r.solutions || [];
  const picks: [string, Sol][] = sols.length ? [["Chi phí thấp nhất", sols[0]], ["Cung ứng nhanh nhất", [...sols].sort((a, b) => a.supply_days - b.supply_days || a.total_cost - b.total_cost)[0]],
    ["Cách nhiệt tốt nhất", [...sols].sort((a, b) => a.u_value - b.u_value || a.total_cost - b.total_cost)[0]]] : [];
  const small = "text-[12.5px] text-muted";
  return (
    <>
      {sols.length ? (<>
        <div className="flex flex-wrap items-start gap-[18px]">{picks.map(([label, x]) => (
          <Card key={label} title={label} className="flex-[1_1_280px]">
            <div className="grid grid-cols-3 gap-3.5">
              <div><div className={small}>Tổng</div><b>{money(x.total_cost)} đ</b></div>
              <div><div className={small}>Cung ứng</div><b>{x.supply_days} ngày</b></div>
              <div><div className={small}>U</div><b>{nf(x.u_value, 3)}</b></div>
            </div>
            <div className="tw"><table><tbody>{x.choices.map((c, i) => (
              <tr key={i}>
                <td>{c.wall_type}<div className={small}>{c.wall_system_id}</div></td>
                <td>{c.material_name}<div className={small}>{nf(c.quantity)} {c.unit} × {money(c.unit_price)} ({c.price_source === "model" ? "mô hình" : "danh mục"})</div></td>
                <td>{c.product_url ? <a href={c.product_url} target="_blank" rel="noopener">{c.supplier_name}</a> : c.supplier_name}
                  <div className={small}>{nf(c.distance_km, 1)} km · {c.trips} chuyến {c.vehicle_id}</div></td>
              </tr>
            ))}</tbody></table></div>
          </Card>
        ))}</div>
        <Card title={`Tập Pareto: ${sols.length} phương án không bị trội (đã xét ${r.n_evaluated} tổ hợp)`}>
          <div className="tw"><table className="nonum">
            <thead><tr><th>#</th><th className="n">Tổng đồng</th><th className="n">Ngày</th><th className="n">U</th><th>Lựa chọn</th></tr></thead>
            <tbody>{sols.map((x, i) => (
              <tr key={i}><td>{i + 1}</td><td className="n">{money(x.total_cost)}</td><td className="n">{x.supply_days}</td><td className="n">{nf(x.u_value, 3)}</td>
                <td className="text-[12.5px]">{x.choices.map((c, j) => <div key={j}>{`${c.wall_type}: ${c.wall_system_id || c.material_id} · ${c.supplier_name} · ${c.vehicle_id}`}</div>)}</td></tr>
            ))}</tbody>
          </table></div>
        </Card>
      </>) : <Card><Note>Không có phương án nào thỏa ràng buộc.</Note></Card>}
      {!!r.notes?.length && <Card title="Ghi chú của bước tối ưu"><ul className="m-0 pl-[18px] text-muted">{r.notes.map((n, i) => <li key={i}>{n}</li>)}</ul></Card>}
    </>
  );
}
