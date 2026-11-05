"use client";

import { useEffect, useRef, useState } from "react";

type Binding = { projectUid: string; drawingId: string; reviewId: string; materialRevision?: string | null };
type WorkFact = { rowIndex: number; code: string; plan?: string; element?: string; quantity: number | null; unit: string;
  status: "A" | "B" | "C" | "D" | null; checked: boolean; basis?: string | null; missing: string[] };
type MaterialFact = { lineId: string; material_id: string | null; name: string; raw_class: string; unit: string;
  quantity: number | null; quantity_with_waste: number | null; complete: boolean; missing: string[]; sources: string[];
  uses: { work: string; plan?: string; quantity: number | null; via?: string }[] };
export type MaterialAdvisorContext = { binding: Binding; partial: boolean; scope: string; works: WorkFact[];
  materials: MaterialFact[]; proposedMaterialIds: string[];
  intermediates?: { name: string; quantity: number | null; unit: string; complete: boolean }[] };
type Offer = { price: number | null; unit: string | null; price_date: string | null; source_detail: string | null;
  supplier_name: string | null; price_level: string | null; vat_included: string | null; transport_included: string | null };
type Option = { material_id: string; name: string; unit: string; data_kind: string | null; offer: Offer | null;
  needsDesignReview: boolean; needsGeometryReview: boolean; state: string; canApply: false; specification: Record<string, string | null> };
type Result = { requestId: string; contextHash: string; binding: Binding; provenance: "client_snapshot"; applied: false;
  facts: { scope: string; warnings: string[]; coverage: (WorkFact & { coverage: string; reason: string })[];
    intermediates: { name: string; quantity: number | null; unit: string; complete: boolean }[]; intermediate_note: string;
    materials: { lineId: string; raw_class: string; name: string; demand_quantity: number | null; demand_with_waste: number | null;
      demand_unit: string; purchase_quantity: null; complete: boolean; sources: string[]; options: Option[]; missing: string[] }[] };
  ai: { summary: string; advice: { lineId: string; proposed_material_ids: string[]; reason: string; checks: string[] }[] } };

async function send<T>(url: string, body: unknown, signal: AbortSignal): Promise<T> {
  const response = await fetch(url, { method: "POST", credentials: "same-origin", signal,
    headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Chưa gửi được yêu cầu trợ lý.");
  return data as T;
}

function sameBinding(a: Binding, b: Binding) {
  return a.projectUid === b.projectUid && a.drawingId === b.drawingId && a.reviewId === b.reviewId && (a.materialRevision ?? null) === (b.materialRevision ?? null);
}

export function MaterialAdvisor({ context, onPropose }: { context: MaterialAdvisorContext;
  onPropose?: (selection: { binding: Binding; contextHash: string; lineId: string; materialId: string;
    needsDesignReview: boolean; needsGeometryReview: boolean }) => void }) {
  const contextJson = JSON.stringify(context);
  const latestContext = useRef(contextJson);
  const sequence = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const [question, setQuestion] = useState("");
  const [busyContext, setBusyContext] = useState<string | null>(null);
  const pending = busyContext === contextJson;
  const [error, setError] = useState("");
  const [answer, setAnswer] = useState<{ contextJson: string; value: Result } | null>(null);
  const [selection, setSelection] = useState("");
  useEffect(() => {
    latestContext.current = contextJson;
    sequence.current += 1;
    controller.current?.abort();
    return () => { sequence.current += 1; controller.current?.abort(); };
  }, [contextJson]);
  // Không hiển thị trả lời cũ ngay cả trước khi effect đổi snapshot chạy.
  const result = answer?.contextJson === contextJson ? answer.value : null;
  const cancel = () => { sequence.current += 1; controller.current?.abort(); setBusyContext(null); };
  const ask = async () => {
    controller.current?.abort();
    const abort = new AbortController(); controller.current = abort;
    const turn = ++sequence.current;
    const snapshot = contextJson;
    setBusyContext(snapshot); setError(""); setAnswer(null); setSelection("");
    try {
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(snapshot));
      const contextHash = Array.from(new Uint8Array(digest), x => x.toString(16).padStart(2, "0")).join("");
      if (turn !== sequence.current || latestContext.current !== snapshot) return;
      const requestId = crypto.randomUUID();
      const body = { question: question.trim(), contextJson: snapshot, contextHash, requestId };
      const bound = await send<{ contextHash: string; binding: Binding }>("/api/assistant/material-session", body, abort.signal);
      if (turn !== sequence.current || latestContext.current !== snapshot) return;
      if (bound.contextHash !== contextHash || !sameBinding(bound.binding, context.binding)) throw new Error("Phiên tư vấn không khớp bản đang xem.");
      const value = await send<Result>("/api/assistant/materials", body, abort.signal);
      if (turn !== sequence.current || latestContext.current !== snapshot) return;
      if (value.requestId !== requestId || value.contextHash !== contextHash || !sameBinding(value.binding, context.binding)) throw new Error("Phản hồi thuộc bản dữ liệu khác.");
      setAnswer({ contextJson: snapshot, value });
    } catch (err) {
      if (turn === sequence.current && latestContext.current === snapshot && !abort.signal.aborted)
        setError(err instanceof Error ? err.message : "Chưa nhận được phản hồi trợ lý.");
    } finally { if (turn === sequence.current) setBusyContext(null); }
  };
  const fmt = (v: number | null) => v == null ? "Chưa có" : v.toLocaleString("vi-VN");
  return <section className="min-w-0 rounded border border-rule p-3" aria-label="AI hỗ trợ chọn vật liệu phần thô">
    <h2>AI hỗ trợ chọn vật liệu phần thô</h2>
    <p>Phạm vi: {context.scope}. Trợ lý dùng bản dữ liệu do trình duyệt cung cấp, chưa đối chiếu độc lập với bản vẽ.</p>
    <p>Đề xuất cần được bạn kiểm tra. Giữ nguyên bảng công tác và vật tư gốc để đối chiếu. Không nhập thông tin nhạy cảm vào câu hỏi.</p>
    <label>Yêu cầu của bạn<textarea className="field w-full" maxLength={1500} rows={3} value={question}
      onChange={e => setQuestion(e.target.value)} placeholder="Tôi cần kiểm quy cách bê tông, thép và vật tư chống thấm; ưu tiên dễ cung ứng." /></label>
    <div className="flex gap-2"><button className="btn" disabled={pending || !question.trim()} onClick={ask}>Tư vấn chọn vật liệu</button>
      {pending && <button className="btn" onClick={cancel}>Hủy chờ</button>}</div>
    {pending && <p role="status">Đang tra danh mục và chuẩn bị tư vấn…</p>}
    {error && <p role="alert">{error}</p>}
    {result && <div>
      <h3>Căn cứ từ bảng hiện có</h3>
      <p>{result.facts.scope}</p>
      <ul>{result.facts.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
      <details><summary>Đối chiếu công tác và vật tư ({result.facts.coverage.length} dòng)</summary>
        <ul>{result.facts.coverage.map(w => <li key={w.rowIndex}>{w.plan} · {w.code} · {w.element}: {w.reason}</li>)}</ul></details>
      {!!result.facts.intermediates.length && <details><summary>Vữa/bê tông trung gian</summary><p>{result.facts.intermediate_note}</p>
        <ul>{result.facts.intermediates.map((i, k) => <li key={k}>{i.name}: {fmt(i.quantity)} {i.unit} · {i.complete ? "Đủ số" : "Còn thiếu"}</li>)}</ul></details>}
      {result.facts.materials.map(line => <article className="my-3 rounded border border-rule p-2" key={line.lineId}>
        <h4>{line.name}</h4>
        <p>Nhu cầu đã tính: {fmt(line.demand_quantity)} {line.demand_unit} · Theo hao hụt: {fmt(line.demand_with_waste)} {line.demand_unit}.</p>
        <p>Lượng mua: chưa xác định. {line.complete ? "" : "Dòng còn thiếu, số hiện có chỉ là phần đã tính."}</p>
        <p>Nguồn bảng: {line.sources.join("; ") || "Chưa có"}</p>
        <ul>{line.missing.map((s, i) => <li key={i}>{s}</li>)}</ul>
        {line.options.length === 0 && <p>Chưa có phương án để so sánh.</p>}
        {line.options.map(option => <div key={option.material_id}>
          <p><strong>{option.material_id} · {option.name}</strong> · {option.data_kind} · {option.needsDesignReview ? "Đề xuất cần kiểm thiết kế/cấu tạo" : "Vật tư hiện có trong bảng"}</p>
          <p>{option.offer ? `Đơn giá nguồn: ${fmt(option.offer.price)} / ${option.offer.unit || "chưa rõ đơn vị"} · ${option.offer.price_level || ""} · ${option.offer.price_date || ""}` : "Chưa có giá hợp lệ; chưa thể kết luận rẻ nhất."}</p>
          {option.offer && <p>Nguồn: {option.offer.source_detail || "Chưa có mô tả chứng từ"} · VAT: {option.offer.vat_included || "chưa rõ"} · Giao hàng: {option.offer.transport_included || "chưa rõ"}.</p>}
          {onPropose && <button className="btn" onClick={() => setSelection(`${line.lineId}|${option.material_id}`)}>Chọn để kiểm tiếp</button>}
          {onPropose && selection === `${line.lineId}|${option.material_id}` && <div><p>Lựa chọn này chưa được phê duyệt hoặc áp dụng. Cần kiểm lại cấu tạo và tính lại phần bị ảnh hưởng trước khi mua.</p>
            <button className="btn" onClick={() => { onPropose({ binding: result.binding, contextHash: result.contextHash,
              lineId: line.lineId, materialId: option.material_id, needsDesignReview: option.needsDesignReview,
              needsGeometryReview: option.needsGeometryReview }); setSelection(""); }}>Xác nhận chuyển sang bước kiểm lựa chọn</button></div>}
        </div>)}
      </article>)}
      <h3>Hướng dẫn và gợi ý của AI</h3><p>{result.ai.summary}</p>
      {result.ai.advice.map(a => <div key={a.lineId}><p>{result.facts.materials.find(m => m.lineId === a.lineId)?.name}: {a.reason}</p>
        <p>Vật tư được gợi ý kiểm: {a.proposed_material_ids.join(", ") || "Chưa có"}</p><ul>{a.checks.map((s, i) => <li key={i}>{s}</li>)}</ul></div>)}
    </div>}
  </section>;
}
