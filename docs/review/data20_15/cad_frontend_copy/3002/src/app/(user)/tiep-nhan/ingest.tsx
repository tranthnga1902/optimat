"use client";
import { useState, type FormEvent, type ReactNode } from "react";
import { api } from "@/lib/api";
import { Card, Pill } from "@/components/ui";

// Kết quả /api/ingest (chỉ đọc các trường trang hiển thị).
type Inv = {
  file: { name: string; size?: number; version?: number; duplicate?: boolean; sha256?: string; dwg_version?: string };
  status: string; takeoff_allowed: boolean; warnings: { code: string; message: string }[];
  acad_release?: string; conversion?: { ok: boolean; converter_version?: string; target_version: string; seconds?: number };
  units?: { name: string; insunits: number; scale_to_mm: number }; bbox_mm?: { size: [number, number] };
  entity_counts: Record<string, number>; entity_total: number; entities: unknown[];
  layers: { name: string; entities: number; off: boolean; frozen: boolean; in_table: boolean }[];
  blocks: { name: string; inserts: number; entities: number; is_xref: boolean; xref_path?: string }[];
  layouts: { name: string; entities: number }[];
  fonts: { style: string; font: string; encoding: string }[];
};

function Table<R>({ cols, rows }: { cols: [string, (r: R) => ReactNode][]; rows: R[] }) {
  return (
    <div className="tw max-h-80 overflow-y-auto">
      <table>
        <thead><tr>{cols.map(([t]) => <th key={t}>{t}</th>)}</tr></thead>
        <tbody>{rows.map((r, i) => <tr key={i}>{cols.map(([t, f]) => { const v = f(r); return <td key={t} className={typeof v === "number" ? "n" : ""}>{v}</td>; })}</tr>)}</tbody>
      </table>
    </div>
  );
}

const More = ({ title, n, children }: { title: string; n: number; children: ReactNode }) =>
  n ? <details><summary className="cursor-pointer text-accent">{title} ({n})</summary>{children}</details> : null;

function download(r: Inv) {
  const a = Object.assign(document.createElement("a"), { download: r.file.name + ".inventory.json",
    href: URL.createObjectURL(new Blob([JSON.stringify(r, null, 1)], { type: "application/json" })) });
  a.click(); URL.revokeObjectURL(a.href);
}

function InvCard({ r }: { r: Inv }) {
  const { file: f, bbox_mm: b, units: u, conversion: c } = r;
  const counts = Object.entries(r.entity_counts).sort((x, y) => y[1] - x[1]);
  const yes = (v: boolean) => (v ? "có" : "");
  return (
    <Card>
      <div className="flex flex-wrap items-center gap-2.5">
        <strong>{f.name}</strong><Pill level={r.status === "ok" ? "ok" : "bad"}>{r.status}</Pill>
        {!r.takeoff_allowed && <Pill level="bad">không được bóc tách</Pill>}
      </div>
      {r.warnings.map((w, i) => (
        <div key={i} className="rounded-md bg-warn-bg px-2.5 py-1.5 text-warn-ink"><b className="mr-1.5 font-mono text-xs">{w.code}</b>{w.message}</div>
      ))}
      <dl className="m-0 grid grid-cols-[max-content_1fr] gap-x-3.5 gap-y-0.5 [&_dd]:m-0 [&_dt]:text-muted">
        <dt>Dung lượng</dt><dd>{f.size != null ? (f.size / 1024).toFixed(1) + " KB" : "-"}{f.version ? ` · phiên bản ${f.version}${f.duplicate ? " (trùng nội dung đã lưu)" : ""}` : ""}</dd>
        <dt>SHA-256</dt><dd className="break-all text-muted">{f.sha256 || "-"}</dd>
        <dt>Định dạng</dt><dd>{f.dwg_version ? "DWG " + f.dwg_version : ""} {r.acad_release ? "DXF " + r.acad_release : ""}</dd>
        {c && <><dt>Chuyển DWG</dt><dd>{c.ok ? "thành công" : "thất bại"} · {c.converter_version || "Bộ chuyển đổi CAD"} → {c.target_version} · {c.seconds ?? "?"} s</dd></>}
        <dt>Đơn vị</dt><dd>{u ? `${u.name} ($INSUNITS = ${u.insunits}) · ×${u.scale_to_mm} → mm` : "-"}</dd>
        <dt>Khung bao (mm)</dt><dd>{b ? `${b.size[0].toLocaleString("vi")} × ${b.size[1].toLocaleString("vi")}` : "-"}</dd>
        <dt>Entity modelspace</dt><dd>{r.entity_total.toLocaleString("vi")} · {r.layers.length} layer · {r.blocks.length} block · {r.layouts.length} layout</dd>
      </dl>
      {counts.length > 0 && <Table rows={counts} cols={[["Loại", (x) => x[0]], ["Số lượng", (x) => x[1]]]} />}
      <More title="Layer" n={r.layers.length}>
        <Table rows={r.layers} cols={[["Layer", (x) => x.name], ["Entity", (x) => x.entities], ["Tắt", (x) => yes(x.off)], ["Đóng băng", (x) => yes(x.frozen)], ["Trong bảng layer", (x) => (x.in_table ? "có" : "không")]]} />
      </More>
      <More title="Block" n={r.blocks.length}>
        <Table rows={[...r.blocks].sort((x, y) => y.inserts - x.inserts)} cols={[["Block", (x) => x.name], ["Lần chèn", (x) => x.inserts], ["Entity", (x) => x.entities], ["XREF", (x) => (x.is_xref ? x.xref_path : "")]]} />
      </More>
      <More title="Layout" n={r.layouts.length}><Table rows={r.layouts} cols={[["Layout", (x) => x.name], ["Entity", (x) => x.entities]]} /></More>
      <More title="Kiểu chữ" n={r.fonts.length}><Table rows={r.fonts} cols={[["Kiểu", (x) => x.style], ["Font", (x) => x.font], ["Bảng mã", (x) => x.encoding]]} /></More>
      <div><button className="btn" type="button" onClick={() => download(r)}>Tải JSON kiểm kê ({r.entities.length} entity kèm nguồn)</button></div>
    </Card>
  );
}

export function Ingest() {
  const [res, setRes] = useState<Inv[]>([]);
  const [state, setState] = useState("");

  async function submit(ev: FormEvent<HTMLFormElement>) {
    ev.preventDefault();
    const form = ev.currentTarget, fd = new FormData();
    for (const file of (form.elements.namedItem("files") as HTMLInputElement).files ?? []) fd.append("files", file);
    fd.append("store", String((form.elements.namedItem("store") as HTMLInputElement).checked));
    setState("Đang đọc bản vẽ…");
    try {
      const out = await api<Inv[]>("/api/ingest", { method: "POST", body: fd });
      setRes(out);
      setState(`${out.length} file, ${out.filter((r) => r.status !== "ok").length} lỗi`);
    } catch (e) { setState("Lỗi: " + (e as Error).message); }
  }

  return (
    <>
      <Card>
        <form className="flex flex-wrap items-center gap-2.5" onSubmit={submit}>
          <input type="file" name="files" accept=".dxf,.dwg" multiple required aria-label="Chọn file DXF hoặc DWG" />
          <label className="flex items-center gap-1.5"><input type="checkbox" name="store" defaultChecked /> Lưu bản gốc (theo hash, có phiên bản)</label>
          <button className="btn primary" type="submit">Kiểm tra</button>
          <span className="text-muted" role="status">{state}</span>
        </form>
      </Card>
      {res.map((r, i) => <InvCard key={i} r={r} />)}
    </>
  );
}
