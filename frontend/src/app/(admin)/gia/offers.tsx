"use client";
import { useEffect, useState } from "react";
import { api, money } from "@/lib/api";
import { Sheet, type Col } from "@/components/Sheet";
import { TableEditor } from "@/components/TableEditor";
import { Card, Head, Loading, Note, Pill } from "@/components/ui";

type Raw = { material_id: string; material_name?: string; supplier_id: string; name?: string; province?: string; base_price: number | null;
  price_level?: string; price_date?: string; data_kind?: string; product_url?: string; maps_url?: string;
  vat_included?: string; transport_included?: string; lead_time_days?: number | null; quote_reference?: string };
const YN: Record<string, string> = { YES: "có", NO: "không" };
type Offer = Raw & { supplier: string; link: string };

const COLS: Col<Offer>[] = [
  { key: "material_id", title: "Mã vật liệu", render: (r) => <b>{r.material_id}</b> },
  { key: "material_name", title: "Tên vật liệu" },
  { key: "supplier", title: "Nhà cung cấp" },
  { key: "province", title: "Tỉnh" },
  { key: "base_price", title: "Giá", num: true, render: (r) => (r.base_price == null ? <Pill level="warn">không công khai</Pill> : money(r.base_price)) },
  { key: "price_level", title: "Mức giá" },
  { key: "price_date", title: "Ngày" },
  { key: "vat_included", title: "Gồm VAT", render: (r) => YN[r.vat_included || ""] || "chưa rõ" },
  { key: "transport_included", title: "Gồm giao", render: (r) => YN[r.transport_included || ""] || "chưa rõ" },
  { key: "lead_time_days", title: "Cung ứng (ngày)", num: true },
  { key: "quote_reference", title: "Chứng từ báo giá" },
  { key: "data_kind", title: "Loại dữ liệu", render: (r) => <Pill level={r.data_kind === "ACTUAL" ? "ok" : "info"}>{r.data_kind || "?"}</Pill> },
  { key: "link", title: "Liên kết", render: (r) => (r.link ? <a href={r.link} target="_blank" rel="noopener">mở</a> : <Pill level="warn">chưa có</Pill>) },
];

export function Offers() {
  const [rows, setRows] = useState<Offer[] | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<{ name: string; n: number } | null>(null);
  useEffect(() => {
    api<Raw[]>("/api/data/offers").then((d) => setRows(d.map((r) => ({ ...r, supplier: r.name || r.supplier_id, link: r.product_url || r.maps_url || "" }))),
      (e) => setErr(e.message));
  }, []);
  const show = (name: string) => setOpen((o) => ({ name, n: (o?.n || 0) + 1 }));

  return (
    <>
      <Head title="Giá và nhà cung cấp" actions={<>
        <button className="btn primary" type="button" onClick={() => show("suppliers")}>Quản lý đại lý</button>
        <button className="btn" type="button" onClick={() => show("supplier_materials")}>Sửa giá đại lý</button>
      </>}>
        Giá đại lý trong <code>supplier_materials</code>. Dòng MẪU (SAMPLE) hoặc MÔ PHỎNG (SYNTHETIC) không dùng để báo cáo. Đại lý thu thập thủ công theo mẫu <code>docs/du-lieu/OptiMat AI - Thu thap dai ly.xlsx</code>.
      </Head>
      {open && <TableEditor key={open.n} name={open.name} />}
      {err ? <Note>{err}</Note> : !rows ? <Loading /> : (
        <Card title={`${rows.length} dòng giá`}>
          <Sheet cols={COLS} rows={rows} file="gia_dai_ly.csv" />
        </Card>
      )}
    </>
  );
}
