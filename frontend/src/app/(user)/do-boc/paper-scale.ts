// Chỉ dùng dòng tiêu đề gắn với đúng mặt bằng. Ghi chú trong khung tên hoặc chi tiết khác không xác định được tỷ lệ của hình.
export function titleScale(name: string, texts: { t: string }[] = []) {
  const normalize = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d")
    .toLowerCase().replace(/^mb\b/, "mat bang").replace(/\s+/g, " ").trim();
  const ratio = /\b(?:tl|ti le|ty le|scale)\s*:?\s*1\s*[:/]\s*(\d+(?:[.,]\d+)?)\b/g;
  const title = normalize(name);
  if (!title || title === "toan bo ban ve") return null;
  const titleOnly = (s: string) => s.replace(ratio, "").replace(/[()\s_–-]+$/g, "").trim();
  const found = new Map<number, string>();
  for (const original of [name, ...texts.map(x => x.t)]) {
    const s = normalize(original);
    if (titleOnly(s) !== titleOnly(title)) continue;
    for (const m of s.matchAll(ratio)) {
      const n = Number(m[1].replace(",", "."));
      if (n > 0 && Number.isFinite(n)) found.set(n, original);
    }
  }
  if (found.size !== 1) return null;
  const [denominator, source] = [...found][0];
  return { denominator, source };
}
