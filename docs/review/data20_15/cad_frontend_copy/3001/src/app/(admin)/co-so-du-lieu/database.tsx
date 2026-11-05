"use client";
// quản trị cơ sở dữ liệu (api/admin_db.py)
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { TableEditor } from "@/components/TableEditor";
import { Card, Loading, Note, Tile, Tiles } from "@/components/ui";

type Table = { name: string; title: string | null; doc: string; rows: number | null; editable: boolean };
type Db = { connected: boolean; server?: string; url?: string; error?: string; clusters: { name: string; tables: Table[] }[] };

export function Database() {
  const [d, setD] = useState<Db | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<{ name: string; n: number } | null>(null);
  useEffect(() => { api<Db>("/api/admin/db").then(setD, (e) => setErr(e.message)); }, []);
  if (err) return <Note>{err}</Note>;
  if (!d) return <Loading />;
  const all = d.clusters.flatMap((c) => c.tables), sum = all.reduce((a, t) => a + (t.rows || 0), 0);
  return (
    <>
      {d.connected
        ? <Note tone="ok">Đã kết nối PostgreSQL {d.server || ""}: <code>{d.url}</code>. Sửa ở đây ghi thẳng vào database và nhật ký <code>audit_logs</code>.</Note>
        : <Note>
            {d.url ? <>Không kết nối được <code>{d.url}</code>: {d.error || ""}.</> : "Chưa có DATABASE_URL."}{" "}
            Đang đọc file CSV: chỉ xem được. Cách kết nối: chép <code>.env.example</code> thành <code>.env</code>, sửa mật khẩu, chạy{" "}
            <code>python scripts/init_db.py</code> (tạo bảng, nạp dữ liệu) rồi khởi động lại máy chủ.
          </Note>}
      <Tiles>
        <Tile k="Nguồn" v={d.connected ? "PostgreSQL" : "CSV"} s={d.connected ? "đọc và ghi" : "chỉ xem"} />
        <Tile k="Bảng" v={all.length} s={`${all.filter((t) => t.rows === null).length} bảng chưa có dữ liệu nguồn`} />
        <Tile k="Dòng" v={sum.toLocaleString("vi-VN")} s={`${all.filter((t) => t.editable).length} bảng sửa được`} />
      </Tiles>
      {d.clusters.map((c) => (
        <Card key={c.name} title={c.name}>
          <div className="tw">
            <table>
              <thead><tr><th>Bảng</th><th>Mô tả</th><th className="n">Dòng</th><th /></tr></thead>
              <tbody>
                {c.tables.map((t) => (
                  <tr key={t.name}>
                    <td><b>{t.title || t.name}</b><br /><code className="text-[11.5px]">{t.name}</code></td>
                    <td className="text-[12.5px]">{t.doc}</td>
                    <td className="n">{t.rows == null ? "—" : t.rows.toLocaleString("vi-VN")}</td>
                    <td className="whitespace-nowrap">
                      <button className="btn" type="button" onClick={() => setOpen((o) => ({ name: t.name, n: (o?.n || 0) + 1 }))}>{t.editable ? "Xem, sửa" : "Xem"}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ))}
      {open && <TableEditor key={open.n} name={open.name} />}
    </>
  );
}
