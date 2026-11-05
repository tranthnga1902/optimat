"use client";
// Tải dự toán (bảng công tác, bảng vật tư) lên /api/estimate/check; khối lượng hệ thống lấy từ kết quả phần thô gần nhất ("optimat-rough").
import Link from "next/link";
import { useState, type FormEvent, type ReactNode } from "react";
import { api, money, nf } from "@/lib/api";
import { useStored } from "@/lib/store";
import { Card, Field, Head, Note, Pill, Tile, Tiles } from "@/components/ui";

type Row = Record<string, unknown> & { ket_luan?: string; lech_pct?: number | null };
type Result = { nguong_pct: number; khoi_luong: Row[]; dinh_muc: Row[]; don_gia: Row[]; so_hoc: Row[]; ghi_chu: string[];
  tom_tat: { khoi_luong_lech: number; dinh_muc_lech: number; don_gia_lech: number; so_hoc_loi: number; cong_tac: number; vat_tu: number } };
type Saved = { file?: string; at?: string; request?: { params?: unknown }; result?: { works?: unknown[] } };

const verdict = (r: Row) => {
  const k = r.ket_luan;
  return <Pill level={k === "lệch" ? "bad" : k === "khớp" ? "ok" : "warn"}>{k}</Pill>;
};
const pct = (v: unknown) => (v == null ? "" : `${Number(v) > 0 ? "+" : ""}${nf(v, 1)} %`);

function Table({ cols, rows, empty }: { cols: [string, (r: Row) => ReactNode, boolean?][]; rows: Row[]; empty: string }) {
  if (!rows.length) return <p className="m-0 text-muted">{empty}</p>;
  return (
    <div className="tw max-h-[420px] overflow-y-auto"><table>
      <thead><tr>{cols.map(([t, , n]) => <th key={t} className={n ? "n" : ""}>{t}</th>)}</tr></thead>
      <tbody>{rows.map((r, i) => <tr key={i}>{cols.map(([t, f, n]) => <td key={t} className={n ? "n" : ""}>{f(r)}</td>)}</tr>)}</tbody>
    </table></div>
  );
}

export function EstimateCheck() {
  const saved = useStored<Saved | null>("optimat-rough", null);
  const works = saved?.result?.works;
  const [files, setFiles] = useState<File[]>([]);
  const [threshold, setThreshold] = useState("10");
  const [res, setRes] = useState<Result | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const form = (excel: boolean) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    if (works) fd.append("works", JSON.stringify(works));
    if (saved?.request?.params) fd.append("params", JSON.stringify(saved.request.params));
    fd.append("nguong_pct", threshold || "10");
    if (excel) fd.append("excel", "true");
    return fd;
  };
  const run = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { setRes(await api<Result>("/api/estimate/check", { method: "POST", body: form(false) })); }
    catch (x) { setErr((x as Error).message); setRes(null); }
    finally { setBusy(false); }
  };
  const excel = async () => {
    const r = await fetch("/api/estimate/check", { method: "POST", body: form(true) });
    if (!r.ok) { setErr(`Lỗi ${r.status} khi xuất Excel`); return; }
    const a = Object.assign(document.createElement("a"), { download: "kiem_tra_sai_lech.xlsx", href: URL.createObjectURL(await r.blob()) });
    a.click(); URL.revokeObjectURL(a.href);
  };
  const t = res?.tom_tat;

  return (
    <>
      <Head title="Kiểm tra sai lệch dự toán" actions={res && <button type="button" className="btn" onClick={excel}>Tải Excel</button>}>
        So dự toán với hệ thống: khối lượng công tác so với kết quả phần thô, đơn giá vật tư so với giá danh mục, vật tư so với
        định mức, và lỗi số học (khối lượng × đơn giá ≠ thành tiền). Dòng vượt ngưỡng được đánh dấu &quot;lệch&quot;.
      </Head>
      <Card title="Hồ sơ dự toán">
        <form onSubmit={run} className="flex flex-col gap-3">
          <Field label="File dự toán (XLS, XLSX) hoặc bảng chuẩn (CSV, XLSX)"
            hint="File dự toán xuất từ phần mềm dự toán: hệ thống tự tìm sheet bảng khối lượng và tổng hợp vật tư (cột tên, đơn vị, khối lượng, số thứ tự; chữ VNI/TCVN3 tự đổi). Bảng chuẩn: dòng đầu là tiêu đề ten_cong_tac / ten_vat_tu, don_vi, khoi_luong, tùy chọn don_gia, thanh_tien, ma_cong_tac, material_id.">
            <input type="file" multiple accept=".csv,.xlsx,.xls" onChange={(e) => setFiles(Array.from(e.target.files || []))} />
          </Field>
          <Field label="Ngưỡng lệch (%)">
            <input type="number" min={1} max={100} step={1} value={threshold} onChange={(e) => setThreshold(e.target.value)} className="w-24" />
          </Field>
          {works
            ? <Note tone="ok">So khối lượng với kết quả phần thô {saved?.file ? `của ${saved.file} ` : ""}tính lúc {(saved?.at || "").replace("T", " ").slice(0, 16)}.</Note>
            : <Note>Chưa có kết quả phần thô: chỉ kiểm đơn giá, định mức và số học. Muốn so khối lượng, tính ở <Link href="/phan-tho">Kiểm tra công tác và khối lượng</Link> trước.</Note>}
          <div><button className="btn primary" disabled={!files.length || busy}>{busy ? "Đang kiểm tra…" : "Kiểm tra"}</button></div>
          {err && <Note>{err}</Note>}
        </form>
      </Card>
      {res && t && (<>
        <Tiles>
          <Tile tone={t.khoi_luong_lech ? "bad" : "ok"} k="Khối lượng lệch" v={`${t.khoi_luong_lech}/${res.khoi_luong.length}`} s={`${t.cong_tac} dòng công tác`} />
          <Tile tone={t.dinh_muc_lech ? "bad" : "ok"} k="Vật tư lệch định mức" v={`${t.dinh_muc_lech}/${res.dinh_muc.length}`} />
          <Tile tone={t.don_gia_lech ? "bad" : "ok"} k="Đơn giá lệch" v={`${t.don_gia_lech}/${res.don_gia.length}`} s={`${t.vat_tu} dòng vật tư`} />
          <Tile tone={t.so_hoc_loi ? "bad" : "ok"} k="Lỗi số học" v={t.so_hoc_loi} />
        </Tiles>
        <Card title="Khối lượng: dự toán so với hệ thống">
          <Table empty="Không so được (thiếu bảng công tác hoặc kết quả phần thô)." rows={res.khoi_luong} cols={[
            ["Công tác", (r) => <>{String(r.ten)}{r.cau_kien ? ` (${r.cau_kien})` : ""}{r.tu_gan ? <> <Pill level="info">tự gắn</Pill></> : null}</>],
            ["ĐVT", (r) => String(r.don_vi)], ["Dự toán", (r) => nf(r.du_toan, 3), true], ["Hệ thống", (r) => nf(r.he_thong, 3), true],
            ["Lệch", (r) => pct(r.lech_pct), true], ["Hệ thống tính", (r) => String(r.trang_thai_he_thong)], ["Kết luận", verdict]]} />
        </Card>
        <Card title="Vật tư: định mức so với dự toán">
          <Table empty="Không có vật tư tính được theo định mức." rows={res.dinh_muc} cols={[
            ["Mã", (r) => String(r.material_id)], ["Vật tư", (r) => String(r.ten)], ["ĐVT", (r) => String(r.don_vi)],
            ["Theo định mức", (r) => nf(r.dinh_muc, 3), true], ["Dự toán", (r) => nf(r.du_toan, 3), true], ["Lệch", (r) => pct(r.lech_pct), true],
            ["Kết luận", verdict], ["Còn thiếu", (r) => <span className="text-[12.5px] text-muted">{(r.thieu as string[]).join("; ")}</span>]]} />
        </Card>
        <Card title="Đơn giá: dự toán so với giá tham chiếu">
          <Table empty="Không có bảng vật tư hoặc cột đơn giá." rows={res.don_gia} cols={[
            ["Mã", (r) => <>{String(r.material_id)}{r.tu_gan ? <> <Pill level="info">tự gắn</Pill></> : null}</>], ["Vật tư", (r) => String(r.ten_vat_tu)],
            ["Đơn giá dự toán", (r) => `${money(r.don_gia_du_toan)} /${r.don_vi_du_toan}`, true], ["Quy đổi", (r) => r.don_gia_quy_doi == null ? "" : `${money(r.don_gia_quy_doi)} /${r.don_vi}`, true],
            ["Tham chiếu (trung vị)", (r) => money(r.gia_tham_chieu), true], ["Khoảng giá", (r) => r.gia_min == null ? "" : `${money(r.gia_min)} – ${money(r.gia_max)}`, true],
            ["Nguồn", (r) => <span className="text-[12.5px] text-muted">{r.so_nguon ? `${r.so_nguon} · ${(r.loai_nguon as string[]).join(", ")}` : ""}</span>],
            ["Lệch", (r) => pct(r.lech_pct), true], ["Kết luận", verdict]]} />
          <p className="m-0 text-[12.5px] text-muted">Giá tham chiếu là trung vị các giá hợp lệ trong danh mục (đại lý, báo giá, công bố giá). Giá công bố (BULLETIN) chỉ để tham khảo; nên so cùng thời điểm lập dự toán.</p>
        </Card>
        <Card title="Lỗi số học">
          <Table empty="Không có dòng sai (hoặc file không có cột thành tiền)." rows={res.so_hoc} cols={[
            ["Bảng", (r) => (r.bang === "cong_tac" ? "công tác" : "vật tư")], ["Dòng", (r) => String(r.dong), true], ["Tên", (r) => String(r.ten)],
            ["Khối lượng", (r) => nf(r.khoi_luong, 3), true], ["Đơn giá", (r) => money(r.don_gia), true], ["Thành tiền ghi", (r) => money(r.thanh_tien), true],
            ["Tính lại", (r) => money(r.tinh_lai), true], ["Chênh", (r) => money(r.chenh), true]]} />
        </Card>
        {res.ghi_chu.length > 0 && <Card title="Ghi chú"><ul className="m-0 pl-[18px] text-muted">{res.ghi_chu.map((g, i) => <li key={i}>{g}</li>)}</ul></Card>}
      </>)}
    </>
  );
}
