"use client";
// Bảng quy tắc nhận dạng (api/admin_db.py, kind = "rule"): tên, mô tả, file nguồn, số dòng lấy từ /api/admin/db;
// cách điền từng cột lấy từ lược đồ database qua /api/admin/tables/{bảng}.
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { TableEditor } from "@/components/TableEditor";
import { Card, Loading, Note } from "@/components/ui";

type TableInfo = { name: string; rows: number | null; doc: string; title: string | null; kind: string | null; source_file: string | null };
type Db = { connected: boolean; clusters: { tables: TableInfo[] }[]; rule_views?: TableInfo[] };

export function Rules() {
  const [d, setD] = useState<Db | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<{ name: string; n: number } | null>(null);
  useEffect(() => { api<Db>("/api/admin/db").then(setD, (e) => setErr(e.message)); }, []);
  useEffect(() => {
    const sync = () => {
      if (window.location.hash === "#rule-rough_norms" &&
          (d?.rule_views ?? d?.clusters.flatMap(c => c.tables) ?? []).some(t => t.name === "rough_norms")) {
        setOpen({name: "rough_norms", n: Date.now()});
        requestAnimationFrame(() => document.getElementById("rule-editor")?.scrollIntoView());
      }
    };
    sync();
    window.addEventListener("hashchange", sync);
    const click = (event: MouseEvent) => {
      if (event.target instanceof Element && event.target.closest('a[href="#rule-rough_norms"]') && location.hash === "#rule-rough_norms") sync();
    };
    document.addEventListener("click", click);
    return () => { window.removeEventListener("hashchange", sync); document.removeEventListener("click", click); };
  }, [d]);
  if (err) return <div id="rule-rough_norms"><Note>Chưa mở được bảng định mức phần thô. {err}</Note></div>;
  if (!d) return <Loading />;
  const rules = d.rule_views ?? d.clusters.flatMap((c) => c.tables).filter((t) => t.kind === "rule");
  return (
    <>
      {!rules.some(rule => rule.name === "rough_norms") && <div id="rule-rough_norms"><Note>Danh mục máy chủ chưa cung cấp bảng định mức phần thô. Bạn vẫn có thể tra công thức ở phía trên.</Note></div>}
      {!d.connected && <Note>Chưa kết nối PostgreSQL: chỉ xem được. Sửa file trong <code>data/rules</code> bằng Excel, hoặc kết nối database (xem trang Cơ sở dữ liệu).</Note>}
      <Card>
        <div className="tw">
          <table>
            <thead><tr><th>Quy tắc</th><th>Mô tả</th><th>File nguồn</th><th className="n">Dòng</th><th /></tr></thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.name} id={`rule-${r.name}`}>
                  <td><b>{r.title || r.name}</b><div className="text-[12.5px] text-muted"><code>{r.name}</code></div></td>
                  <td className="text-[12.5px]">{r.doc}</td>
                  <td className="text-[12.5px]"><code>{r.source_file}</code></td>
                  <td className="n">{r.rows == null ? "—" : r.rows.toLocaleString("vi-VN")}</td>
                  <td className="whitespace-nowrap">
                    <button className="btn" type="button" onClick={() => setOpen((o) => ({ name: r.name, n: (o?.n || 0) + 1 }))}>{d.connected ? "Xem, ghi" : "Xem"}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {open && <div id="rule-editor"><TableEditor key={open.n} name={open.name} /></div>}
    </>
  );
}
