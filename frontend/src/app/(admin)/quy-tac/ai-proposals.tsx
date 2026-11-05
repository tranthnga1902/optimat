"use client";
// KD06: hàng chờ duyệt đề xuất AI (api/ai_review.py). Duyệt = thêm một dòng quy tắc CSV; lần sau quy tắc khớp, không gọi AI.
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, Loading, Note } from "@/components/ui";

type Item = { id: string; task: string; label: string; excerpt: string; text: string; pattern: string; source_file: string; seen: number };
type Data = { items: Item[]; targets: Record<string, string>; notice: string };

const TASK: Record<string, string> = {
  thong_so: "Thông số trong ghi chú", tieu_de_bang: "Tiêu đề cột bảng thép", loai_ban_ve: "Loại tờ / mặt bằng",
  ky_hieu: "Ký hiệu cấu kiện", du_toan: "Mã công tác dự toán",
};

export function AiProposals() {
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState("");
  const load = () => api<Data>("/api/admin/ai-proposals").then(setD, (e) => setErr(e.message));
  useEffect(() => { void load(); }, []);
  const decide = async (id: string, approve: boolean) => {
    setBusy(id); setErr("");
    try {
      await api(`/api/admin/ai-proposals/${id}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ approve }) });
      await load();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(""); }
  };
  return (
    <Card title="Đề xuất AI chờ duyệt">
      {err && <Note>{err}</Note>}
      {!d ? (!err && <Loading />) : <>
        <p className="mb-2 text-sm">{d.notice}</p>
        {!d.items.length ? <p className="text-sm text-muted">Chưa có đề xuất nào. Đề xuất xuất hiện khi phân tích hồ sơ có bật AI.</p> :
          <div className="tw"><table>
            <thead><tr><th>Loại</th><th>Nhãn</th><th>Trích đoạn gốc</th><th>Mẫu quy tắc sẽ thêm</th><th>Tệp quy tắc</th><th className="n">Gặp</th><th></th></tr></thead>
            <tbody>{d.items.map((i) => (
              <tr key={i.id}>
                <td>{TASK[i.task] || i.task}</td><td>{i.label}</td>
                <td title={`${i.source_file}: ${i.text}`}>{i.excerpt}</td>
                <td><code className="break-all text-[12px]">{i.pattern}</code></td>
                <td className="text-[12.5px] text-muted">{d.targets[i.task]}</td><td className="n">{i.seen}</td>
                <td className="whitespace-nowrap">
                  <button className="btn primary" type="button" disabled={!!busy} onClick={() => decide(i.id, true)}>Duyệt</button>{" "}
                  <button className="btn" type="button" disabled={!!busy} onClick={() => decide(i.id, false)}>Từ chối</button>
                </td>
              </tr>))}</tbody>
          </table></div>}
      </>}
    </Card>
  );
}
