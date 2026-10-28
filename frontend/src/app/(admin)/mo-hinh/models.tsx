"use client";
import { useEffect, useState } from "react";
import { api, nf } from "@/lib/api";
import { Card, Empty, Loading, Note, Pill } from "@/components/ui";

type ModelInfo = {
  loaded: boolean; metrics?: { metrics_on_test?: Record<string, Record<string, unknown>>; contains_synthetic?: boolean };
  nsga: { pop_size: number; generations: number }; llm_provider: string; llm_model: string; llm_available: boolean;
};
type Health = { catalog_source: string; dwg_converter_available: boolean };

export function Models() {
  const [d, setD] = useState<{ m: ModelInfo; h: Health } | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    Promise.all([api<ModelInfo>("/api/models"), api<Health>("/api/health")]).then(([m, h]) => setD({ m, h }), (e) => setErr(e.message));
  }, []);
  if (err) return <Note>{err}</Note>;
  if (!d) return <Loading />;
  const { m, h } = d;
  const met = m.metrics?.metrics_on_test ? Object.entries(m.metrics.metrics_on_test) : [];
  const keys = met.length ? Object.keys(met[0][1]) : [];
  return (
    <div className="flex flex-wrap gap-[18px]">
      <Card style={{ flex: "2 1 460px" }} title={<>Mô hình dự đoán giá {m.loaded ? <Pill level="ok">đã nạp</Pill> : <Pill level="warn">chưa huấn luyện</Pill>}</>}>
        {met.length ? <>
          <div className="tw">
            <table>
              <thead><tr><th>Mô hình</th>{keys.map((k) => <th key={k} className="n">{k}</th>)}</tr></thead>
              <tbody>
                {met.map(([name, v]) => (
                  <tr key={name}><td><b>{name}</b></td>{keys.map((k) => <td key={k} className="n">{typeof v[k] === "number" ? nf(v[k], 4) : String(v[k] ?? "")}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          {m.metrics?.contains_synthetic && <Note>Mô hình học trên dữ liệu có dòng MÔ PHỎNG: không dùng các chỉ số này để báo cáo.</Note>}
        </> : <Empty>Chưa có <code>models/material_price_metrics.json</code>. Chạy huấn luyện để có bảng chỉ số.</Empty>}
      </Card>
      <Card style={{ flex: "1 1 280px" }} title="Cấu hình đang chạy">
        <table>
          <tbody>
            <tr><td>Nguồn danh mục</td><td>{h.catalog_source}</td></tr>
            <tr><td>NSGA-II</td><td>quần thể {m.nsga.pop_size}, {m.nsga.generations} thế hệ</td></tr>
            <tr><td>Mô hình ngôn ngữ</td><td>{m.llm_provider} · {m.llm_model} {m.llm_available ? <Pill level="ok">sẵn sàng</Pill> : <Pill level="warn">chưa có khóa, chạy luồng cố định</Pill>}</td></tr>
            <tr><td>Chuyển DWG (ODA)</td><td>{h.dwg_converter_available ? <Pill level="ok">có</Pill> : <Pill level="warn">chưa cài</Pill>}</td></tr>
          </tbody>
        </table>
        <p className="m-0 text-[12.5px] text-muted">Sửa cấu hình trong <code>src/optimat/config.py</code> và biến môi trường.</p>
      </Card>
    </div>
  );
}
