"use client";
// Quản lý dự án (AD01-05): /api/admin/projects (danh sách) và /api/admin/projects/{id} (chi tiết, hồ sơ liên quan).
import { useCallback, useEffect, useState } from "react";
import { api, int, nf } from "@/lib/api";
import { Card, Empty, Field, Loading, Note, Pager, Pill } from "@/components/ui";
import { when } from "../tong-quan/dashboard";

type Row = { project_id: number; name: string; address: string; email: string; files: number; takeoffs: number; runs: number;
  created_at: string; updated_at: string };
type Page = { total: number; page: number; size: number; rows: Row[] };
type Detail = {
  project: Record<string, unknown> & { name: string; email: string };
  files: { file_id: number; filename: string; file_type: string; uploaded_at: string }[];
  takeoffs: { takeoff_id: number; file_id: number | null; kind: string; confirmed_at: string | null; created_at: string }[];
  runs: { run_id: number; method: string; model_version: string | null; llm_model: string | null; chosen_index: number | null; solutions: number; created_at: string }[];
};
const SIZE = 50;
// thông số dự án hiển thị ở chi tiết (đơn vị theo bảng projects)
const PARAMS: [string, string][] = [["address", "Địa chỉ"], ["floor_height_mm", "Chiều cao tầng (mm)"], ["door_width_mm", "Cửa đi rộng (mm)"],
  ["door_height_mm", "Cửa đi cao (mm)"], ["window_width_mm", "Cửa sổ rộng (mm)"], ["window_height_mm", "Cửa sổ cao (mm)"],
  ["budget", "Ngân sách (đồng)"], ["deadline_days", "Hạn cung ứng (ngày)"], ["max_vehicle_ton", "Xe tối đa (tấn)"]];

export function Projects() {
  const [q, setQ] = useState({ q: "", sort: "updated_at", order: "desc", page: 1 });
  const [d, setD] = useState<Page | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<Detail | null>(null);
  const [openErr, setOpenErr] = useState("");

  const load = useCallback(() => {
    const p = new URLSearchParams({ ...q, page: String(q.page), size: String(SIZE) });
    api<Page>(`/api/admin/projects?${p}`).then((r) => { setD(r); setErr(""); }, (e) => setErr(e.message));
  }, [q]);
  useEffect(load, [load]);
  const show = (id: number) => { setOpenErr(""); api<Detail>(`/api/admin/projects/${id}`).then(setOpen, (e) => setOpenErr(e.message)); };

  return (
    <>
      <Card>
        <div className="flex flex-wrap items-end gap-2">
          <Field label="Tìm"><input className="field" placeholder="Tên dự án, địa chỉ, email chủ dự án" value={q.q}
            onChange={(e) => setQ((o) => ({ ...o, q: e.target.value, page: 1 }))} /></Field>
          <Field label="Sắp xếp">
            <select className="field" value={`${q.sort}:${q.order}`} onChange={(e) => { const [sort, order] = e.target.value.split(":"); setQ((o) => ({ ...o, sort, order })); }}>
              <option value="updated_at:desc">Cập nhật gần nhất</option><option value="created_at:desc">Mới tạo</option>
              <option value="name:asc">Tên A→Z</option><option value="email:asc">Chủ dự án A→Z</option>
            </select>
          </Field>
        </div>
        {err ? <Note>{err}</Note> : !d ? <Loading /> : !d.rows.length ? <Empty>Chưa có dự án nào{q.q ? " khớp" : ""}.</Empty> : <>
          <div className="tw max-h-[55vh] overflow-y-auto">
            <table className="nonum">
              <thead className="sticky top-0 bg-card"><tr><th>Dự án</th><th>Chủ dự án</th><th className="n">Hồ sơ CAD</th><th className="n">Bóc tách</th>
                <th className="n">Tối ưu</th><th>Cập nhật</th><th /></tr></thead>
              <tbody>
                {d.rows.map((r) => (
                  <tr key={r.project_id}>
                    <td><b>{r.name}</b>{r.address && <div className="text-[12.5px] text-muted">{r.address}</div>}</td>
                    <td>{r.email}</td><td className="n">{int(r.files)}</td><td className="n">{int(r.takeoffs)}</td><td className="n">{int(r.runs)}</td>
                    <td className="whitespace-nowrap">{when(r.updated_at)}</td>
                    <td><button className="btn" type="button" onClick={() => show(r.project_id)}>Chi tiết</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={d.page} size={d.size} total={d.total} onPage={(page) => setQ((o) => ({ ...o, page }))} />
        </>}
      </Card>
      {openErr && <Note>{openErr}</Note>}
      {open && <ProjectDetail d={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function ProjectDetail({ d, onClose }: { d: Detail; onClose: () => void }) {
  const p = d.project;
  return (
    <Card title={<span className="flex flex-wrap items-center gap-2">{p.name}<span className="text-[13px] font-normal text-muted">#{String(p.project_id)} · {p.email}</span>
      <button className="btn ml-auto" type="button" onClick={onClose}>Đóng</button></span>}>
      <dl className="m-0 grid gap-x-6 gap-y-1 [grid-template-columns:repeat(auto-fit,minmax(220px,1fr))]">
        {PARAMS.map(([k, t]) => (
          <div key={k} className="flex justify-between gap-2 border-b border-rule py-1.5">
            <dt className="text-muted">{t}</dt>
            <dd className="m-0 text-right">{p[k] == null || p[k] === "" ? <span className="text-muted">chưa nhập</span>
              : typeof p[k] === "number" ? nf(p[k], 0) : String(p[k])}</dd>
          </div>
        ))}
      </dl>
      <h3 className="m-0 text-[15px] font-bold">Hồ sơ CAD ({d.files.length})</h3>
      {d.files.length ? <div className="tw"><table className="nonum"><thead><tr><th>File</th><th>Loại</th><th>Tải lên</th></tr></thead><tbody>
        {d.files.map((f) => <tr key={f.file_id}><td>{f.filename}</td><td>{f.file_type.toUpperCase()}</td><td>{when(f.uploaded_at)}</td></tr>)}
      </tbody></table></div> : <Empty>Chưa có file nào.</Empty>}
      <h3 className="m-0 text-[15px] font-bold">Kết quả bóc tách ({d.takeoffs.length})</h3>
      {d.takeoffs.length ? <div className="tw"><table className="nonum"><thead><tr><th>Mã</th><th>Loại</th><th>File</th><th>Trạng thái</th><th>Tạo lúc</th></tr></thead><tbody>
        {d.takeoffs.map((t) => <tr key={t.takeoff_id}><td>#{t.takeoff_id}</td><td>{t.kind === "rough" ? "Phần thô" : "Tường"}</td>
          <td>{d.files.find((f) => f.file_id === t.file_id)?.filename || "—"}</td>
          <td>{t.confirmed_at ? <Pill level="ok">Đã xác nhận {when(t.confirmed_at)}</Pill> : <Pill level="warn">Chưa xác nhận</Pill>}</td>
          <td>{when(t.created_at)}</td></tr>)}
      </tbody></table></div> : <Empty>Chưa có lần bóc tách nào.</Empty>}
      <h3 className="m-0 text-[15px] font-bold">Lần tối ưu ({d.runs.length})</h3>
      {d.runs.length ? <div className="tw"><table className="nonum"><thead><tr><th>Mã</th><th>Phương pháp</th><th className="n">Phương án</th><th>Đã chọn</th><th>Mô hình giá</th><th>LLM</th><th>Lúc</th></tr></thead><tbody>
        {d.runs.map((r) => <tr key={r.run_id}><td>#{r.run_id}</td><td>{r.method}</td><td className="n">{r.solutions}</td>
          <td>{r.chosen_index == null ? "—" : `phương án ${r.chosen_index + 1}`}</td><td>{r.model_version || "—"}</td>
          <td>{r.llm_model || "luồng cố định"}</td><td>{when(r.created_at)}</td></tr>)}
      </tbody></table></div> : <Empty>Chưa có lần tối ưu nào.</Empty>}
    </Card>
  );
}
