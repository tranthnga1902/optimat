import type { Data } from "./model";
export type LinePreview = { origin: [number, number]; size: [number, number]; segments: [number, number, number, number][]; total: number; shown: number };
export type ReadEvent = { type: "status"; stage: "reading" | "recognizing" | "rendering"; message: string }
  | { type: "preview"; preview: LinePreview } | { type: "recognized" | "complete"; data: Data } | { type: "error"; message: string };
export type ReadProgress = { file: string; message: string; stage: "reading" | "recognizing" | "rendering"; preview?: LinePreview; recognized?: Data; error?: string };

/** Giữ đúng ranh giới UTF-8 và bản tin khi HTTP chia nhỏ từng khối dữ liệu. */
export async function readProgress(response: Response, onEvent: (event: ReadEvent) => void): Promise<Data> {
  if (!response.body) throw new Error("Kết nối không hỗ trợ đọc tiến trình bản vẽ.");
  const reader = response.body.getReader(), decoder = new TextDecoder();
  let pending = "", result: Data | null = null;
  const consume = (line: string) => {
    if (!line.trim()) return;
    const event = JSON.parse(line) as ReadEvent;
    if (event.type === "error") throw new Error(event.message);
    onEvent(event);
    if (event.type === "complete") result = event.data;
  };
  try {
    while (true) {
      const { done, value } = await reader.read();
      pending += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let end: number;
      while ((end = pending.indexOf("\n")) >= 0) { consume(pending.slice(0, end)); pending = pending.slice(end + 1); }
      if (done) break;
    }
    consume(pending);
    if (!result) throw new Error("Kết nối kết thúc trước khi đọc xong bản vẽ. Hãy thử lại.");
    return result;
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}
