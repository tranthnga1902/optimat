"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { MaterialAdvisor } from "@/components/MaterialAdvisor";
import { Card, Note } from "@/components/ui";
import { nf } from "@/lib/api";
import { currentDraftKey } from "@/lib/purchase-session";
import { saveReviewedProposal } from "@/lib/review-session";
import { store, useStored } from "@/lib/store";
import type { WorkReceipt, WorkSnapshot } from "@/lib/work-review";
import { adviceScope, type SavedAdvice } from "../dieu-chinh/advice-scope";

type Choice = { lineId: string; materialId: string; originalId: string | null; needsDesignReview: boolean; needsGeometryReview: boolean };
type Accepted = { key: string; choices: Choice[] };

export function Proposal({ work, receipt, versionKey }: { work: WorkSnapshot; receipt: WorkReceipt; versionKey: string }) {
  const context = useMemo(() => adviceScope(work, receipt, null, work.materialRevision), [work, receipt]);
  const storageKey = "optimat-proposal-" + work.projectUid;
  const [edits, setEdits] = useState<Record<string, Choice>>({});
  const [accepted, setAccepted] = useState<Accepted | null>(() => store.get<Accepted | null>(storageKey, null));
  const [error, setError] = useState("");
  const saved = accepted?.key === versionKey && Array.isArray(accepted.choices) ? accepted : null;
  const prior = useStored<SavedAdvice | null>("optimat-material-selection", null);
  const overrides = prior?.projectUid === work.projectUid && prior.drawingId === work.drawingId &&
    prior.reviewId === work.reviewId && prior.materialRevision === work.materialRevision ? prior.choices : [];
  const scoped = overrides.filter(c => c.rowIndex !== null);
  const choices: Choice[] = [];
  for (const line of context.materials) {
    if (scoped.some(c => c.lineId === line.lineId)) continue;
    const previous = edits[line.lineId] || saved?.choices.find(c => c.lineId === line.lineId);
    const specified = overrides.find(c => c.lineId === line.lineId && c.rowIndex === null);
    if (previous) choices.push(previous);
    else if (specified) choices.push({lineId: line.lineId, materialId: specified.materialId, originalId: specified.originalId,
      needsDesignReview: specified.disposition === "proposed", needsGeometryReview: specified.disposition === "proposed"});
    else if (line.material_id && line.complete && line.sources.length && line.quantity_with_waste != null) {
      choices.push({ lineId: line.lineId, materialId: line.material_id, originalId: line.material_id,
        needsDesignReview: false, needsGeometryReview: false });
    }
  }
  const confirm = () => {
    if (currentDraftKey() !== versionKey) { setError("Bản kiểm đã đổi. Hãy mở lại phương án hiện tại."); return; }
    try {
      setAccepted(saveReviewedProposal(work, choices)); setEdits({}); setError("");
    } catch (err) {
      setError(err instanceof Error && !(err instanceof DOMException) ? err.message : "Chưa lưu được phương án đã chọn. Hãy giữ trang này mở và thử lại.");
    }
  };
  return <>
    <Card title="Phương án nháp cho toàn bộ phần thô">
      <p>Hệ thống lấy mã vật tư và lượng có nguồn từ bản khối lượng đã kiểm. Những dòng thiếu quy cách hoặc căn cứ tính được giữ lại để tư vấn có điều kiện.</p>
      {receipt.partial && <Note>Bản kiểm chỉ xác nhận một phần công trình.</Note>}
      {context.materials.length ? <div className="tw"><table><thead><tr><th>Vật tư</th><th>Mã trong phương án</th><th>Nhu cầu theo định mức</th><th>Căn cứ và phần thiếu</th></tr></thead>
        <tbody>{context.materials.map((line, index) => {
          const choice = choices.find(c => c.lineId === line.lineId);
          const byElement = scoped.filter(c => c.lineId === line.lineId);
          const source = work.result.materials[index];
          const sameMaterial = !!line.material_id && source?.material_id === line.material_id &&
            (!choice || choice.materialId === line.material_id) && byElement.every(c => c.materialId === line.material_id);
          return <tr key={line.lineId}><td>{line.name}</td><td>{byElement.length ? byElement.map(c =>
            <div key={c.rowIndex}>{c.materialId} · {c.scope}{c.disposition === "proposed" && " · cần duyệt"}</div>) :
            choice?.materialId || (line.material_id ? `${line.material_id} · mã tham chiếu` : "Chờ xác định")}
            {choice?.needsDesignReview && <div>Cần kiểm thiết kế</div>}</td>
            <td>{line.quantity_with_waste != null ? `${nf(line.quantity_with_waste, 3)} ${line.unit}` :
              line.quantity != null ? `${nf(line.quantity, 3)} ${line.unit} · phần đã tính` : "Chưa đủ dữ liệu"}</td>
            <td>{line.missing.join(" · ")}{line.sources.length > 0 && <details><summary>Xem căn cứ</summary>{line.sources.join(" · ")}</details>}
              <p>{!line.material_id && !choice && !byElement.length ? "Cần xác định mã và quy cách trước khi lấy báo giá." :
                sameMaterial && source?.best_price != null && source.price_source ?
                  <>Đơn giá ghi trong bản tính: {nf(source.best_price)} đ/{source.unit}. {source.price_source}. Cần đối chiếu báo giá cho lượng đặt và nơi giao của dự án.</> :
                  "Cần bổ sung báo giá cho mã và quy cách đang xét, ghi rõ đơn vị bán, lượng áp dụng, nơi giao, VAT, cước và hiệu lực."}</p>
            </td></tr>;
        })}</tbody></table></div> : <Note>Bản tính chưa có dòng vật tư cho phạm vi này.</Note>}
      <p><Link href="/dieu-chinh">Điều chỉnh quy cách nếu cần</Link> · <Link href="/phan-tho">Xem lại công tác và nguồn khối lượng</Link></p>
    </Card>
    <MaterialAdvisor context={context} initialQuestion="Đề xuất cho toàn bộ phần thô theo thiết kế. Giải thích vì sao từng dòng chỉ có một lựa chọn nếu gặp. Giữ các vật tư thiếu giá và ghi rõ cần bổ sung gì để lấy báo giá." onPropose={selection => {
      if (currentDraftKey() !== versionKey || selection.binding.reviewId !== work.reviewId) return;
      const line = context.materials.find(m => m.lineId === selection.lineId);
      if (!line) return;
      if (scoped.some(c => c.lineId === line.lineId)) { setError("Dòng này có lựa chọn riêng theo cấu kiện. Hãy kiểm phạm vi trước khi thay mã."); return; }
      setEdits(Object.fromEntries([...choices.filter(c => c.lineId !== selection.lineId), {
        lineId: line.lineId, originalId: line.material_id, materialId: selection.materialId,
        needsDesignReview: selection.needsDesignReview, needsGeometryReview: selection.needsGeometryReview
      }].map(c => [c.lineId, c])));
      setError("");
    }} />
    <Card title="Xác nhận cả phương án">
      <p>{new Set([...choices, ...scoped].map(c => c.lineId)).size}/{context.materials.length} dòng có mã được đưa vào phương án. Các dòng còn thiếu tiếp tục chờ bổ sung.</p>
      <button className="btn primary" disabled={!context.materials.length} onClick={confirm}>Lưu phương án đã chọn</button>
      {saved && !Object.keys(edits).length && <Note>Đã lưu lựa chọn cho bản kiểm này.
        {choices.some(c => c.needsGeometryReview || c.needsDesignReview) && <> Có đề xuất thay thế cần <Link href="/dieu-chinh">kiểm tra cấu tạo</Link> và kiểm lại khối lượng bị ảnh hưởng trước khi áp.</>}</Note>}
      {error && <p role="alert">{error}</p>}
    </Card>
  </>;
}
