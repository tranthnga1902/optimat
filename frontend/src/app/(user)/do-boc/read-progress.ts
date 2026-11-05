import type { Data } from "./model";
import type { SelectedRevision } from "@/lib/project-records";
export type AnalysisReceipt = { receipt_version: number; analysis_id: string; client_analysis_id: string | null;
  project_id: number; profile_version: number; files: SelectedRevision[]; started_at: string; completed_at: string;
  request_sha256: string; response_sha256: string; request_hash_scope: string; response_hash_scope: string };
export async function sha256(text: string): Promise<string> {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, "0")).join("");
}
export async function verifyAnalysisReceipt(receipt: AnalysisReceipt | undefined, projectId: number,
  profileVersion: number | undefined, files: SelectedRevision[], clientId: string | undefined, requestBody: BodyInit | null | undefined) {
  if (!receipt || receipt.receipt_version !== 1 || !/^[0-9a-f-]{36}$/i.test(receipt.analysis_id) ||
      receipt.client_analysis_id !== clientId || receipt.project_id !== projectId || receipt.profile_version !== profileVersion ||
      receipt.request_hash_scope !== "utf8_http_request_body" || typeof requestBody !== "string" ||
      receipt.request_sha256 !== await sha256(requestBody) || !Array.isArray(receipt.files) || receipt.files.length !== files.length ||
      !files.every(f => receipt.files.some(p => p.file_id === f.file_id && p.revision_id === f.revision_id && p.role === f.role && p.sha256 === f.sha256)))
    throw Error("Receipt không khớp yêu cầu, dự án hoặc phiên bản tệp.");
}
export type LinePreview = { origin: [number, number]; size: [number, number]; segments: [number, number, number, number][]; total: number; shown: number };
export type ReadEvent = { type: "status"; stage: "reading" | "recognizing" | "rendering"; message: string }
  | { type: "preview"; preview: LinePreview } | { type: "recognized" | "complete"; data: Data } | { type: "error"; message: string }
  | { type: "receipt"; receipt: AnalysisReceipt };
export type ReadProgress = { file: string; message: string; stage: "reading" | "recognizing" | "rendering"; preview?: LinePreview; recognized?: Data; error?: string };

/** Giữ đúng ranh giới UTF-8 và bản tin khi HTTP chia nhỏ từng khối dữ liệu. */
export async function readProgress(response: Response, onEvent: (event: ReadEvent) => void, requireReceipt = false): Promise<Data> {
  if (!response.body) throw new Error("Kết nối không hỗ trợ đọc tiến trình bản vẽ.");
  const reader = response.body.getReader(), decoder = new TextDecoder();
  const fragments: string[] = [];
  let result: Data | null = null, completeLine = "";
  const received: { receipt: AnalysisReceipt | null } = { receipt: null };
  const consume = (line: string) => {
    if (!line.trim()) return;
    const event = JSON.parse(line) as ReadEvent;
    if (event.type === "error") throw new Error(event.message);
    onEvent(event);
    if (event.type === "complete") { if (result) throw new Error("Kết quả phân tích bị lặp."); result = event.data; if (requireReceipt) completeLine = line; }
    if (event.type === "receipt") { if (received.receipt || !result) throw new Error("Receipt phân tích không đúng thứ tự."); received.receipt = event.receipt; }
  };
  try {
    while (true) {
      const { done, value } = await reader.read();
      const chunk = done ? decoder.decode() : decoder.decode(value, { stream: true });
      let start = 0;
      for (let end = chunk.indexOf("\n"); end >= 0; end = chunk.indexOf("\n", start)) {
        fragments.push(chunk.slice(start, end));
        consume(fragments.join(""));
        fragments.length = 0;
        start = end + 1;
      }
      if (start < chunk.length) fragments.push(chunk.slice(start));
      if (done) break;
    }
    if (fragments.length) consume(fragments.join(""));
    if (!result) throw new Error("Kết nối kết thúc trước khi đọc xong bản vẽ. Hãy thử lại.");
    if (requireReceipt) {
      const receipt = received.receipt;
      if (!receipt || receipt.response_hash_scope !== "utf8_ndjson_complete_line_without_newline" || await sha256(completeLine) !== receipt.response_sha256)
        throw new Error("Receipt thiếu hoặc hash kết quả không khớp.");
      return Object.assign(result, { analysis_receipt: receipt });
    }
    return result;
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}
