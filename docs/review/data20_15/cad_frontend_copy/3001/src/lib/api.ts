/* eslint-disable @typescript-eslint/no-explicit-any -- JSON từ API chưa có kiểu chung; từng trang tự khai báo kiểu khi gọi api<T>() */
// Gọi API FastAPI qua /api (next.config.ts chuyển tiếp). Lỗi trả về chuỗi `detail` của FastAPI.
export async function api<T = any>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(path, opts);
  let body: any = null;
  try { body = await r.json(); } catch { /* không phải JSON */ }
  if (!r.ok) throw new Error(detail(body?.detail) || `Lỗi ${r.status}`);
  return body as T;
}

// FastAPI: detail là chuỗi (HTTPException) hoặc danh sách lỗi kiểm dữ liệu [{loc, msg}] → "loc: msg; …"
const detail = (d: any): string =>
  d == null ? "" : typeof d === "string" ? d
    : Array.isArray(d) ? d.map((e) => (e?.loc ? `${e.loc.join(".")}: ${e.msg}` : JSON.stringify(e))).join("; ") : JSON.stringify(d);

export const post = <T = any>(path: string, data: unknown) =>
  api<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });

export const put = <T = any>(path: string, data: unknown) =>
  api<T>(path, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });

export const nf = (v: unknown, d = 2) =>
  v == null || isNaN(Number(v)) ? "" : Number(v).toLocaleString("vi-VN", { maximumFractionDigits: d, minimumFractionDigits: d });
export const money = (v: unknown) => (v == null || isNaN(Number(v)) ? "" : Math.round(Number(v)).toLocaleString("vi-VN"));
export const int = (v: number) => v.toLocaleString("vi-VN");

export const ROLE: Record<string, string> = { envelope: "bao che", partition: "ngăn" };
