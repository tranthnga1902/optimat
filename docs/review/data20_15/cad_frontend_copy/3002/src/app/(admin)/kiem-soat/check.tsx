"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Head, Loading, Note, Pill, Tile, Tiles, type Level } from "@/components/ui";

type Finding = { level: "error" | "warning" | "info"; area: string; item: string; message: string };
type Summary = {
  nguon_du_lieu: string; ngay_kiem_tra: string; vat_lieu: number; vat_lieu_tuong: number; ten_goi_khac: number; phuong_an_tuong: number; phuong_an_du_so_lieu: number;
  theo_lop_tuong: Record<string, { du_so_lieu: number; phuong_an: number }>;
  nguon_cung: { vat_lieu_tuong: number; vat_lieu_tuong_co_gia: number; nha_cung_cap: number; dong_gia_dai_ly: number };
  lich_su_gia: { that: number; dong: number; nguon: string };
  dap_an_do_tay: { ban_ve: number; theo_nhom: Record<string, number> };
};
type Report = { summary: Summary; counts: { error: number; warning: number; info: number }; findings: Finding[] };

const AREA: Record<string, string> = { vat_lieu: "Vật liệu", phuong_an_tuong: "Phương án tường", ten_goi_khac: "Tên gọi khác", quy_tac: "Quy tắc bóc tách", nguon_cung: "Nguồn cung", gia: "Giá", dap_an: "Đáp án đo tay" };
const LV: Record<string, [Level, string]> = { error: ["bad", "Lỗi"], warning: ["warn", "Cảnh báo"], info: ["info", "Ghi chú"] };

export function DataCheck() {
  const [rep, setRep] = useState<Report | null>(null);
  const [err, setErr] = useState("");
  const [run, setRun] = useState(0);
  const [lv, setLv] = useState("");
  const [area, setArea] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => { api<Report>("/api/data/check").then(setRep, (e) => setErr(e.message)); }, [run]);
  const again = () => { setRep(null); setErr(""); setRun((n) => n + 1); };

  const head = (
    <Head title="Kiểm soát dữ liệu" actions={<button className="btn primary" type="button" onClick={again}>Kiểm tra lại</button>}>
      Kiểm tra danh mục vật liệu, phương án tường, quy tắc, nhà cung cấp và giá từ PostgreSQL; đáp án đo tay từ hồ sơ kiểm thử. Sửa dữ liệu trong database rồi kiểm tra lại. Cùng nội dung với <code>python scripts/check_data.py</code>.
    </Head>
  );
  if (err) return <>{head}<Note>{err}</Note></>;
  if (!rep) return <>{head}<Loading>Đang kiểm tra…</Loading></>;

  const s = rep.summary, c = rep.counts, sup = s.nguon_cung, pr = s.lich_su_gia, da = s.dap_an_do_tay;
  const areas = [...new Set(rep.findings.map((f) => f.area))].sort();
  const ql = q.trim().toLowerCase();
  const rows = rep.findings.filter((f) => (!lv || f.level === lv) && (!area || f.area === area) && (!ql || (f.item + " " + f.message).toLowerCase().includes(ql)));
  return (
    <>
      {head}
      <Tiles>
        <Tile tone={c.error ? "bad" : "ok"} k={`Kết quả (${s.nguon_du_lieu}, ${s.ngay_kiem_tra})`} v={c.error ? c.error + " lỗi" : "Đạt"} s={`${c.warning} cảnh báo · ${c.info} ghi chú`} />
        <Tile k="Vật liệu (vật liệu tường)" v={s.vat_lieu} s={`${s.vat_lieu_tuong} vật liệu tường · ${s.ten_goi_khac} tên gọi khác`} />
        <Tile tone={s.phuong_an_du_so_lieu < s.phuong_an_tuong ? "warn" : ""} k="Phương án tường đủ số liệu" v={`${s.phuong_an_du_so_lieu}/${s.phuong_an_tuong}`}
          s={Object.entries(s.theo_lop_tuong).map(([k, v]) => `${k}: ${v.du_so_lieu}/${v.phuong_an}`).join(" · ")} />
        <Tile tone={sup.vat_lieu_tuong_co_gia < sup.vat_lieu_tuong ? "warn" : ""} k="Vật liệu tường có giá" v={`${sup.vat_lieu_tuong_co_gia}/${sup.vat_lieu_tuong}`} s={`${sup.nha_cung_cap} nhà cung cấp · ${sup.dong_gia_dai_ly} dòng giá`} />
        <Tile tone={pr.that ? "" : "warn"} k="Lịch sử giá thật" v={pr.that} s={`trên ${pr.dong} dòng · ${pr.nguon}`} />
        <Tile tone={da.theo_nhom.test || 0 ? "" : "warn"} k="Bản vẽ có đáp án đo tay" v={da.ban_ve} s={`test: ${da.theo_nhom.test || 0} · build: ${da.theo_nhom.build || 0}`} />
      </Tiles>
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="m-0 mr-auto text-base font-bold">Danh sách cần xử lý</h2>
          <label className="flex items-center gap-2">Mức
            <select className="field" value={lv} onChange={(e) => setLv(e.target.value)}>
              <option value="">tất cả</option><option value="error">lỗi</option><option value="warning">cảnh báo</option><option value="info">ghi chú</option>
            </select>
          </label>
          <label className="flex items-center gap-2">Khu vực
            <select className="field" value={area} onChange={(e) => setArea(e.target.value)}>
              <option value="">tất cả</option>
              {areas.map((a) => <option key={a} value={a}>{AREA[a] || a}</option>)}
            </select>
          </label>
          <label className="flex items-center gap-2">Tìm
            <input className="field" type="search" placeholder="mã, nội dung" value={q} onChange={(e) => setQ(e.target.value)} />
          </label>
        </div>
        <div className="tw">
          <table>
            <thead><tr><th>Mức</th><th>Khu vực</th><th>Mục</th><th>Nội dung</th></tr></thead>
            <tbody>
              {rows.length ? rows.map((f, i) => (
                <tr key={i}><td><Pill level={LV[f.level][0]}>{LV[f.level][1]}</Pill></td><td>{AREA[f.area] || f.area}</td><td><b>{f.item}</b></td><td>{f.message}</td></tr>
              )) : <tr><td colSpan={4} className="text-muted">Không có mục nào.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
