// Dữ liệu và công thức của trang Kiểm tra bóc tách (công thức tính tạm; số chốt do review.py trả).
import type { Reference } from "@/lib/reference";
import type { SelectedRevision } from "@/lib/project-records";

export type Material = { id: string; name?: string; label: string; family: string; systems?: Record<string, string>; ready?: Record<string, boolean> };
export type Family = { id: string; label: string };
export type RawWall = { id: string; cls: string; role?: string; x1: number; y1: number; x2: number; y2: number; mat?: string | null; fam?: string | null;
  cand?: string[]; masonry: boolean; conf: number; layer?: string; src?: string; rule?: string | null };
export type RawOpening = { name?: string; x: number; y: number; w: number; h: number | null; wall?: string | null; kind?: string; ev?: string | null };
export type Column = { id: string; x: number; y: number; b_mm: number; h_mm: number; source?: string; role?: "ket_cau" | "kien_truc" | null };
export type Plan = {
  texts?: { t: string; x: number; y: number }[];
  source_revision?: SelectedRevision;
  plan: { name: string; level_m?: number | null; height_source?: string | null; is_ground?: boolean };
  height_mm: number; length_rule?: string; size: [number, number]; origin?: [number, number];
  layers: { name: string; role: string }[]; segs: [number, number, number, number, number, number][];
  walls: RawWall[]; openings: RawOpening[]; rejected?: { reason: string; cls: string; x1: number; y1: number; x2: number; y2: number }[];
  wall_layers?: string[]; warnings?: string[]; unmatched?: Record<string, unknown>; cad?: string;
  columns?: Column[]; found?: Record<string, unknown>; labels?: unknown[];
  stairs?: { id?: string; steps: number | null; flight_width_mm: number | null; tread_mm: number | null; landing_area_m2: number }[];   // thang tự nhận (B)
};
export type Check = { ma: string; muc: string; trang_thai: string; ket_qua: string; bang_chung: string[] };
export type Data = {
  file: string; plans: Plan[]; materials: Material[]; families: Family[];
  overview?: { cad?: string; size: [number, number]; plans: { name: string; x: number; y: number; w: number; h: number }[] };
  conventions?: { error?: string; trong_quy_uoc?: boolean | null; checks: Check[] };
};

export type Wall = { id: string; cls: string; role: string; x1: number; y1: number; x2: number; y2: number; reason: string | null; mat: string | null;
  fam: string | null; cand: string[]; masonry: boolean; conf: number; layer?: string; msrc?: string; rule?: string | null;
  keep: boolean; src: string; edited: boolean };
export type Opening = { id: string; wall: string; kind: string; w: number; h: number | null; ev?: string | null; x: number; y: number; keep: boolean; src: string;
  edited?: boolean; reason?: string | null };
export type PlanState = { paperScale?: number; scope?: "count" | "reference" | null; height_mm: number; height_source?: string | null; length_rule: string; walls: Wall[]; openings: Opening[]; seq: number };
export type PlanCol = Column & { keep: boolean; source: string };
export type PlanParams = { is_ground: boolean; cols: PlanCol[]; [k: string]: unknown };

// màu theo lớp tường; lớp chưa có màu riêng (--cXXX trong review.module.css) dùng màu lớp 110
export const clsColor = (c: string) => `var(--c${c}, var(--c110))`;
export const ROLE: Record<string, string> = { envelope: "bao che", partition: "ngăn" };
// lý do loại một tường nhận nhầm: dùng để thống kê lỗi nhận diện khi lưu làm đáp án
export const REASONS = ["chưa ghi lý do", "cầu thang", "lan can", "khung cửa, kính", "nội thất, thiết bị", "bồn hoa, bậc", "cột, vách bê tông", "trùng tường khác", "ký hiệu, chi tiết", "khác"];
export const KIND: Record<string, string> = { door: "Cửa đi", window: "Cửa sổ", block: "Block cửa" };
export const fmt = (v: unknown, d = 2) => Number(v).toLocaleString("vi-VN", { minimumFractionDigits: d, maximumFractionDigits: d });
export const money = (v: number | null | undefined) => (v == null ? "" : Math.round(v).toLocaleString("vi-VN"));

export function initState(p: Plan): PlanState {
  return {
    scope: null,
    height_mm: p.height_mm,
    height_source: p.plan.height_source || null,
    length_rule: p.length_rule || "tim",
    walls: p.walls.map((w) => ({ id: w.id, cls: w.cls, role: w.role || "partition", x1: w.x1, y1: w.y1, x2: w.x2, y2: w.y2,
      reason: null, mat: w.mat || null, fam: w.fam || null, cand: w.cand || [], masonry: w.masonry, conf: w.conf, layer: w.layer, msrc: w.src, rule: w.rule,
      keep: true, src: "auto", edited: false })),
    openings: p.openings.map((o, i) => ({ id: "O" + (i + 1), wall: o.wall ?? "", kind: o.kind || "block",
      w: o.w, h: o.h, ev: o.ev, x: o.x, y: o.y, keep: true, src: "auto" })),
    seq: 0,
  };
}

type Seg = { id: string; cls: string; x1: number; y1: number; x2: number; y2: number };
export const wallLen = (w: Seg) => Math.hypot(w.x2 - w.x1, w.y2 - w.y1) / 1000;
// chép từ walls.net_lengths (công thức chốt ở máy chủ): mỗi đầu nằm trong thân tường không song song thì bớt tới mặt tường đó
export function netLengths(walls: Seg[]) {
  const out: Record<string, number> = {};
  for (const w of walls) {
    const L = Math.hypot(w.x2 - w.x1, w.y2 - w.y1);
    let cut = 0;
    for (const [ex, ey] of [[w.x1, w.y1], [w.x2, w.y2]]) {
      let best = 0;
      for (const o of walls) {
        const lo = Math.hypot(o.x2 - o.x1, o.y2 - o.y1), t = Number(o.cls);
        if (o.id === w.id || !lo || !L) continue;
        const ux = (o.x2 - o.x1) / lo, uy = (o.y2 - o.y1) / lo;
        if (Math.abs(ux * (w.x2 - w.x1) / L + uy * (w.y2 - w.y1) / L) > 0.9) continue;
        const along = (ex - o.x1) * ux + (ey - o.y1) * uy, off = Math.abs((ex - o.x1) * -uy + (ey - o.y1) * ux);
        if (along >= -t / 2 - 1 && along <= lo + t / 2 + 1 && off < t / 2 - 1)
          best = Math.max(best, (t / 2 - off) / Math.abs(ux * (w.y2 - w.y1) / L - uy * (w.x2 - w.x1) / L));
      }
      cut += best;
    }
    out[w.id] = Math.max(0, L - cut) / 1000;
  }
  return out;
}

export type Group = { cls: string; role: string; L: number; open: number; mats: Record<string, number>; gross: number; net: number | null; mat: string | null; share: number };
export function compute(S: PlanState) {
  const H = S.height_mm;
  const kept = S.walls.filter((w) => w.keep && w.masonry), ids = new Set(kept.map((w) => w.id));
  const len = S.length_rule === "thong_thuy" ? netLengths(S.walls.filter((w) => w.keep))
    : Object.fromEntries(S.walls.map((w) => [w.id, wallLen(w)]));
  const pending = S.openings.filter(o => o.keep && (o.w == null || o.h == null || !ids.has(o.wall)));
  // Khi chưa biết tường cha, chưa thể loại trừ ảnh hưởng đến bất kỳ nhóm nào của mặt bằng này.
  const unassigned = pending.some(o => !ids.has(o.wall));
  const pendingWalls = unassigned ? ids : new Set(pending.map(o => o.wall));
  const pendingGroups = new Set(kept.filter(w => pendingWalls.has(w.id)).map(w => w.cls + "|" + w.role + "|" + (w.mat || "")));
  const openArea: Record<string, number> = {};
  for (const o of S.openings) if (o.keep && ids.has(o.wall) && o.w != null && o.h != null) openArea[o.wall] = (openArea[o.wall] || 0) + o.w * Math.min(o.h, H) / 1e6;
  // lỗ mở một tường không vượt diện tích tường (như review.py)
  for (const id in openArea) openArea[id] = Math.min(openArea[id], len[id] * H / 1000);
  const groups: Record<string, Omit<Group, "gross" | "net" | "mat" | "share">> = {};
  for (const w of kept) {
    // mỗi vật liệu một nhóm, như máy chủ: bảng vật liệu áp đúng định mức từng phương án
    const k = w.cls + "|" + w.role + "|" + (w.mat || ""), g = (groups[k] = groups[k] || { cls: w.cls, role: w.role, L: 0, open: 0, mats: {} });
    g.L += len[w.id]; g.open += openArea[w.id] || 0;
    if (w.mat) g.mats[w.mat] = (g.mats[w.mat] || 0) + len[w.id];
  }
  const list: Group[] = Object.values(groups).sort((a, b) => (a.cls + a.role).localeCompare(b.cls + b.role)).map((g) => {
    const gross = g.L * H / 1000, mat = Object.keys(g.mats).sort((a, b) => g.mats[b] - g.mats[a])[0] || null;
    return { ...g, gross, net: pendingGroups.has(g.cls + "|" + g.role + "|" + (mat || "")) ? null : Math.max(0, gross - g.open), mat, share: mat ? g.mats[mat] / g.L : 0 };
  });
  const known = list.reduce((sum,g) => sum + (g.net ?? 0),0);
  return { groups:list, openArea, len, pendingWalls, pending, known, total:pending.length ? null : known };
}
export type Computed = ReturnType<typeof compute>;

export function band(w: Seg) {
  const dx = w.x2 - w.x1, dy = w.y2 - w.y1, L = Math.hypot(dx, dy) || 1, t = Number(w.cls) / 2;
  const nx = (-dy / L) * t, ny = (dx / L) * t;
  return [[w.x1 + nx, w.y1 + ny], [w.x2 + nx, w.y2 + ny], [w.x2 - nx, w.y2 - ny], [w.x1 - nx, w.y1 - ny]].map((p) => p.join(",")).join(" ");
}

export function nearestWall(S: PlanState, x: number, y: number) {
  let best: Wall | null = null, bd = 600;
  for (const w of S.walls) {
    if (!w.keep) continue;
    const L2 = (w.x2 - w.x1) ** 2 + (w.y2 - w.y1) ** 2 || 1;
    const t = Math.max(0, Math.min(1, ((x - w.x1) * (w.x2 - w.x1) + (y - w.y1) * (w.y2 - w.y1)) / L2));
    const d = Math.hypot(x - (w.x1 + t * (w.x2 - w.x1)), y - (w.y1 + t * (w.y2 - w.y1)));
    if (d < bd) { bd = d; best = w; }
  }
  return best;
}

// vật liệu = mã trong danh mục (GN01, AAC01...): cùng mã dùng để tra giá. Phương án tường suy theo mã + loại tường.
export const matOf = (D: Data, id: string) => D.materials.find((m) => m.id === id);
export const matLabel = (D: Data, id: string | null) => { if (!id) return "Chưa rõ"; const m = matOf(D, id); return m ? m.label : id + " (không có trong danh mục)"; };
export const sysOf = (D: Data, id: string, cls: string) => { const m = matOf(D, id); return m && m.systems ? m.systems[cls] || null : null; };
export const famLabel = (D: Data, f: string | null) => (f || "").split("|").map((x) => (D.families.find((k) => k.id === x) || { label: x }).label).join(" hoặc ");

// đối chiếu Quy ước bản vẽ v1.0 (cả file, máy chủ tính khi mở bản vẽ: convention_check.py)
export const convBad = (D: Data | null) => ((D && D.conventions && D.conventions.checks) || []).filter((c) => c.trang_thai === "vi_pham")
  .sort((a, b) => (a.muc === b.muc ? 0 : a.muc === "B" ? -1 : 1));

// JSON.stringify biến NaN/Infinity thành null. Chặn dữ liệu sai trước khi tuần tự hóa.
function openingDimensions(plan: string, opening: Opening) {
  const { w, h } = opening;
  for (const [label, value] of [["chiều rộng", w], ["chiều cao", h]] as const) {
    if (value != null && (typeof value !== "number" || !Number.isFinite(value) || value <= 0))
      throw new Error(`${plan} · lỗ ${opening.id} · tường ${opening.wall}: ${label} phải là số dương hữu hạn (mm).`);
  }
  return { w: w ?? null, h: h ?? null };
}

export function payload(D: Data, P: Plan, S: PlanState, project: number | null) {
  // rule, msrc, ev, height_source, unmatched: căn cứ nhận dạng, lưu cùng bản chốt để truy vết
  return { project_id: project, file: D.file, plan: P.plan.name, height_mm: S.height_mm, length_rule: S.length_rule || "tim",
    height_source: S.height_source || P.plan.height_source || null, unmatched: P.unmatched || {},
    walls: S.walls.map(({ id, cls, role, x1, y1, x2, y2, mat, masonry, keep, src, edited, rule, msrc }) => ({ id, cls, role, x1, y1, x2, y2, mat, masonry, keep, src, edited, rule: rule || null, msrc: msrc || null })),
    openings: S.openings.map(o => ({ id: o.id, wall: o.wall, kind: o.kind, ...openingDimensions(P.plan.name, o), keep: o.keep, src: o.src, ev: o.ev || null })) };
}

// Mặt bằng đã sửa cho đúng = đáp án. Tọa độ lưu theo hệ của bản vẽ (mm) để so với lần nhận diện sau dù khung cắt thay đổi.
export function groundTruth(D: Data, P: Plan, S: PlanState) {
  const [ox, oy] = P.origin || [0, 0], ab = (x: number, y: number) => [Math.round((x + ox) * 10) / 10, Math.round((oy - y) * 10) / 10];
  const wall = (w: Wall) => { const [x1, y1] = ab(w.x1, w.y1), [x2, y2] = ab(w.x2, w.y2); return { id: w.id, cls: w.cls, role: w.role, x1, y1, x2, y2, src: w.src, edited: !!w.edited }; };
  return { version: 1, file: D.file, plan: P.plan.name, height_mm: S.height_mm, saved_at: new Date().toISOString(),
    walls: S.walls.filter((w) => w.keep && w.masonry).map(wall),
    removed: S.walls.filter((w) => !w.keep && w.src !== "manual").map((w) => ({ ...wall(w), reason: w.reason || REASONS[0] })),
    openings: S.openings.filter((o) => o.keep).map((o) => ({ id: o.id, wall: o.wall, kind: o.kind, w: o.w, h: o.h, src: o.src })) };
}

export const base = (D: Data, P: Plan) => (D.file || "ban_ve").replace(/\.[^.]+$/, "") + "_" + (P.plan.name || "mat_bang").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/gi, "d").replace(/[^\w]+/g, "_");

export function csvText(D: Data, S: PlanState) {
  const c = compute(S), rows: (string | number)[][] = [["muc", "id", "loai", "vai_tro", "dai_m", "dien_tich_thuc_m2", "vat_lieu", "phuong_an_tuong", "nguon", "giu"]];
  for (const w of S.walls) rows.push(["tuong", w.id, w.cls, w.role, (c.len[w.id] ?? wallLen(w)).toFixed(3), w.keep && w.masonry && !c.pendingWalls.has(w.id) ? Math.max(0, (c.len[w.id] ?? wallLen(w)) * S.height_mm / 1000 - (c.openArea[w.id] || 0)).toFixed(2) : "", w.mat || "", (w.mat && sysOf(D, w.mat, w.cls)) || "", w.src, w.keep ? 1 : 0]);
  for (const o of S.openings) rows.push(["lo_mo", o.id, o.kind, o.wall, o.w == null ? "" : (o.w / 1000).toFixed(3), o.w == null || o.h == null ? "" : (o.w * Math.min(o.h, S.height_mm) / 1e6).toFixed(2), "", "", o.src, o.keep ? 1 : 0]);
  for (const g of c.groups) rows.push(["tong_hop", "", g.cls, g.role, g.L.toFixed(3), g.net?.toFixed(2) ?? "", g.mat || "", (g.mat && sysOf(D, g.mat, g.cls)) || "", "", 1]);
  return "﻿" + rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
}

// ---------------------------------------------------------------- phần thô
// Thông số công trình (Quy ước B1) nhập một lần cho cả bản vẽ, nhớ trên trình duyệt; thông số từng mặt bằng nhập theo tầng.
// Trang không tự tính phần thô: gửi mọi mặt bằng (đã sửa) lên /api/takeoff/rough, máy chủ là công thức chốt duy nhất.
// "grade": mác, ô chữ có gợi ý từ database (biến thể BE_TONG_TRON trong rough_norms)
export type RField = [string, string, "num" | "text" | "grade" | [string, string][], string?];
/** Thông số công trình. Vật liệu chống thấm, mác bê tông, cấu kiện thép lấy từ database (/api/catalog/reference). */
export function roughFields(ref: Reference | null): [string, RField[]][] {
  return [
    ["Bê tông", [["concrete_supply", "Cấp bê tông", [["", "chưa chọn"], ["ready_mix", "thương phẩm"], ["site_mix", "trộn tại chỗ"]]],
      ["concrete_grade", "Mác bê tông", "grade"], ["lean_concrete_grade", "Mác bê tông lót", "grade"]]],
    ["Vữa", [["masonry_mortar_grade", "Mác vữa xây", "text"], ["plaster_mortar_grade", "Mác vữa trát", "text"],
      ["screed_mortar_grade", "Mác vữa cán", "text"], ["plaster_thickness_mm", "Dày trát (mm)", "num"], ["screed_thickness_mm", "Dày cán nền (mm)", "num"]]],
    ["Kết cấu", [["slab_thickness_mm", "Dày sàn (mm)", "num"], ["beam_width_mm", "Rộng dầm (mm)", "num"], ["beam_depth_mm", "Cao dầm (mm)", "num"],
      ["lintel_height_mm", "Cao lanh tô (mm)", "num"], ["lintel_bearing_mm", "Gối lanh tô (mm)", "num"], ["stair_slab_thickness_mm", "Dày bản thang (mm)", "num"],
      ["formwork_type", "Loại ván khuôn", [["", "chưa chọn"], ["go", "gỗ (định mức AF.81)"], ["van_ep", "ván ép phủ phim (chưa có định mức)"]]]]],
    ["Móng, đào đất", [["natural_ground_level_mm", "Cốt đất tự nhiên (mm, so với ±0.000)", "num", "âm: dưới ±0.000"],
      ["excavation_margin_mm", "Mở rộng đáy hố đào mỗi bên (mm)", "num"], ["excavation_slope", "Hệ số mái taluy m", "num", "0 = vách đứng"]]],
    ["Nền, chống thấm", [["ground_sand_mm", "Đệm cát nền (mm)", "num"], ["ground_lean_mm", "Bê tông lót nền (mm)", "num"],
      ["waterproof_upturn_mm", "Cổ tường chống thấm (mm)", "num"],
      ["waterproof_material_id", "Vật liệu chống thấm", [["", "chưa chọn"], ...(ref?.waterproof_materials || []).map((m): [string, string] => [m.id, `${m.id} ${m.name}`])]]]],
    ["Kiểm tra, hướng nhà", [["building_area_m2", "Diện tích xây dựng (m²)", "num"], ["north_deg", "Hướng bắc (độ, từ trục +x)", "num"],
      ["min_opening_m2", "Không trừ lỗ nhỏ hơn (m²)", "num", "0 = trừ mọi lỗ"]]],
    ["Hàm lượng thép (kg/m³)",(ref?.steel_elements || []).map((e): RField => [`steel_${e.code}`, e.name.charAt(0).toUpperCase() + e.name.slice(1), "num"])],
  ];
}
export const PP: [string, string][] = [["void_area_m2", "Ô trống trên sàn (m²)"], ["balcony_area_m2", "Ban công cần chống thấm (m²)"],
  ["outline_area_m2", "Nhập tay: trong tim tường bao (m²)"], ["usable_area_m2", "Nhập tay: diện tích sử dụng (m²)"],
  ["stair_steps", "Thang: số bậc"], ["stair_width", "Thang: rộng vế (mm)"], ["stair_tread", "Thang: rộng bậc (mm)"], ["stair_landing", "Thang: chiếu nghỉ (m²)"]];
export const RP_KEY = "optimat-rough-params";
export const numOr = (v: unknown) => (v === "" || v == null || isNaN(Number(v)) ? null : Number(v));
export function roughValues(): Record<string, string> { try { return JSON.parse(localStorage.getItem(RP_KEY) || "{}"); } catch { return {}; } }
const st0 = (p: Plan) => (p.stairs || [])[0];
// ô thang điền sẵn theo thang máy chủ tự nhận trên nét mũi bậc (người dùng sửa được)
export const initPlanParams = (p: Plan): PlanParams => ({ is_ground: !!(p.plan && p.plan.is_ground),
  cols: (p.columns || []).map((c) => ({ ...c, keep: true, source: c.source || "hatch" })),
  ...(st0(p) ? { stair_steps: String(st0(p).steps ?? ""), stair_width: String(st0(p).flight_width_mm ?? ""), stair_tread: String(st0(p).tread_mm ?? ""),
    stair_landing: String(st0(p).landing_area_m2 || "") } : {}) });

const TEXT_PARAMS = ["concrete_supply", "waterproof_material_id", "formwork_type"];
// chỉ gửi thông số có trên biểu mẫu (trình duyệt có thể còn khóa cũ)
const KNOWN = new Set(roughFields(null).flatMap(([, f]) => f.map(([k]) => k)));
function projectParams(v: Record<string, string>) {
  const out: Record<string, unknown> & { steel_kg_per_m3: Record<string, number>; ground_layers: { kind: string; thickness_mm: number }[] } = { steel_kg_per_m3: {}, ground_layers: [] };
  for (const [k, raw] of Object.entries(v)) {
    if (k === "material_classes") { if (raw) out.material_classes = String(raw).split(",").filter(Boolean); continue; }   // loại vật liệu cần bóc
    if (raw === undefined || raw === "" || !(k.startsWith("steel_") || KNOWN.has(k))) continue;
    const n = numOr(raw);
    if (k.startsWith("steel_")) { if (n != null) out.steel_kg_per_m3[k.slice(6)] = n; }
    else if (k === "ground_sand_mm") { if (n) out.ground_layers.push({ kind: "NEN_DEM_CAT", thickness_mm: n }); }
    else if (k === "ground_lean_mm") { if (n) out.ground_layers.push({ kind: "BE_TONG_LOT", thickness_mm: n }); }
    else out[k] = k.endsWith("_grade") ? String(raw).trim().toUpperCase() : TEXT_PARAMS.includes(k) ? raw : n;   // mác: M250
  }
  return out;
}

/** Một đoạn cột tại một vị trí. Nhiều đoạn có thể dùng cùng mã chi tiết cột. */
export type StructuralColumnInstance = {
  instance_id: string; code: string; grid_x?: string | null; grid_y?: string | null; floor_key?: string | null;
  z_from_mm?: number | null; z_to_mm?: number | null; b_mm?: number | null; h_mm?: number | null;
  deduct_top_slab?: boolean; top_slab_thickness_mm?: number | null; top_slab_source?: string | null;
  file?: string; source_sha256?: string | null; sheet?: string; layers?: string[]; handles?: string[]; evidence?: string[];
  missing?: string[];
  top_slab_candidates?: { thickness_mm: number; level_mm: number; floor_key: string; handles: string[]; evidence: string[]; region_confirmed: false }[];
  matched_plan?: string | null; matched_column_id?: string | null; mapping_evidence?: string | null;
};

/** Phần đọc từ bản vẽ kết cấu tách file (/api/takeoff/structural): dầm, cột, móng, bảng thép, cấu kiện phụ. */
export type Structural = { file: string; foundations: unknown[]; lintel_height_mm: number | null; notes: string[];
  structural_columns?: StructuralColumnInstance[];
  structural_beams: Record<string, unknown>; sheets: unknown[]; structural_floors: unknown; column_sections: unknown;
  column_schedule: unknown[]; rebar: unknown[]; members: unknown[] };

// thang giữ đúng số tự nhận thì là suy luận (B), người dùng đã sửa thì là nhập tay (C)
const stairSource = (p: Plan, pp: PlanParams) => {
  const a = st0(p);
  return a && numOr(pp.stair_steps) === a.steps && numOr(pp.stair_width) === a.flight_width_mm && numOr(pp.stair_tread) === a.tread_mm
    && (numOr(pp.stair_landing) || 0) === (a.landing_area_m2 || 0) ? "auto" : "manual";
};

export function roughRequest(D: Data, states: Record<number, PlanState>, planP: Record<number, PlanParams>, project: number | null,
  structural?: Structural | null, values = roughValues()) {
  if (D.plans.some((_, i) => !states[i]?.scope)) throw new Error("Chọn tính khối lượng hoặc tham khảo cho từng hình mặt bằng trước khi tính.");
  if (!D.plans.some((_, i) => states[i]?.scope === "count")) throw new Error("Cần ít nhất một mặt bằng được tính khối lượng.");
  const params = projectParams(values);
  // móng, cao lanh tô đọc từ bản vẽ kết cấu chỉ bổ sung khi người dùng chưa nhập
  const { foundations, lintel_height_mm, ...parts } = structural || ({} as Partial<Structural>);
  if (structural) {
    if (foundations?.length) params.foundations = foundations;
    if (params.lintel_height_mm == null && lintel_height_mm != null) params.lintel_height_mm = lintel_height_mm;
  }
  return { ...parts, plan_scope_confirmed: true, project_id: project, file: D.file, params, plans: D.plans.flatMap((p, i) => {
    if (states[i]?.scope !== "count") return [];
    const st = states[i] || initState(p), pp = planP[i] || initPlanParams(p);
    const steps = numOr(pp.stair_steps);
    const hasStair = !!st0(p) || [pp.stair_steps, pp.stair_width, pp.stair_tread, pp.stair_landing].some((v) => numOr(v) != null);
    const stair = hasStair ? [{ ...st0(p), id: st0(p)?.id || "T1", steps: steps == null ? null : Math.round(steps), flight_width_mm: numOr(pp.stair_width),
      tread_mm: numOr(pp.stair_tread), landing_area_m2: numOr(pp.stair_landing) || 0, source: stairSource(p, pp) }] : [];
    // Biểu mẫu hiện sửa thang đầu tiên; các thang còn lại phải giữ nguyên dữ liệu máy chủ.
    const stairs = [...stair, ...(p.stairs || []).slice(1)];
    return [{ name: p.plan.name, source_revision: p.source_revision, level_m: p.plan.level_m,
      is_ground: pp.is_ground, height_mm: st.height_mm, height_source: st.height_source || p.plan.height_source || null,
      void_area_m2: numOr(pp.void_area_m2), balcony_area_m2: numOr(pp.balcony_area_m2),
      outline_area_m2: numOr(pp.outline_area_m2), usable_area_m2: numOr(pp.usable_area_m2),
      walls: st.walls.map(({ id, cls, role, x1, y1, x2, y2, mat, masonry, keep, src, edited }) => ({ id, cls, role, x1, y1, x2, y2, mat, masonry, keep, src, edited })),
      openings: st.openings.map(o => ({ id: o.id, wall: o.wall, kind: o.kind, ...openingDimensions(p.plan.name, o), keep: o.keep, src: o.src })),
      columns: pp.cols.map(col => ({ ...col })),
      stairs, labels: p.labels || [], found: p.found || {} }];
  }) };
}

export type Status = "A" | "B" | "C" | "D" | null;
export type WorkDimensions = { label: string; count?: number | null; length_m?: number | null; width_m?: number | null;
  height_m?: number | null; thickness_m?: number | null; area_m2?: number | null; opening_area_m2?: number | null;
  basis?: "input" | "reference" | "union" | "deduction"; repetitions?: number;
  gross_length_m?: number | null; deducted_length_m?: number | null; floor_height_m?: number | null;
  bottom_level_m?: number | null; top_level_m?: number | null; slope_ratio?: number | null; faces?: number | null;
  concrete_height_m?: number | null; top_length_m?: number | null; top_width_m?: number | null;
  slope_length_m?: number | null; diameter_m?: number | null; net_area_m2?: number | null;
  source: string; note?: string; missing_fields?: string[]; not_applicable_fields?: string[]; field_sources?: Record<string, string> };
export type WorkQuantityDetail = {unit:string;complete:boolean;scope_complete:boolean;known_part_raw:string|null;total_raw:string|null;
  legacy_quantity:string|null;legacy_delta:string|null;rows:{row_id:string;label:string;group:string;role:"contribution"|"reference";
    sign:1|-1;unit:string;raw_quantity:string|null;dimensions?:WorkDimensions|null;expression:string;sources:string[];missing:string[];
    factors:{name:string;value:string;unit:string;meaning:string;source:string}[];
    conversion?:{from_unit:string;to_unit:string;factor:string;source:string}|null}[]};
export type RoughWork = { quantity_detail?:WorkQuantityDetail|null; dimensions?: WorkDimensions[]; evidence?: string[]; basis?: string | null; masonry_geometry?: { wall_type?: string; length_m: number; gross_area_m2: number; opening_area_m2: number; thickness_m: number } | null; code: string; name: string; plan?: string | null; element?: string; formula: string; missing: string[]; quantity: number | null; unit: string;
  status?: Status; inputs?: string[] };
export type RoughResult = {
  plan_scope_confirmed?: boolean;
  wall_groups?: import("@/lib/store").WallGroup[] | null; wall_group_issues?: string[];
  totals: { code: string; name: string; quantity: number | null; unit: string; complete: boolean; status?: Status }[];
  formwork?: { name: string; quantity: number | null; complete: boolean; status?: Status }[];
  materials: { material_id?: string | null; name: string; quantity: number | null; quantity_with_waste: number | null; unit: string; complete: boolean; missing?: string[];
    uses?: { work: string; plan?: string | null; quantity: number | null; via?: string; rowIndex?: number }[];
    status?: Status; quantity_min?: number | null; quantity_max?: number | null; weight_kg?: number | null; raw_class?: string | null;
    best_price?: number | null; price_source?: string | null; est_cost?: number | null }[];
  intermediates?: { name: string; quantity: number | null; unit: string; complete: boolean }[];
  works: RoughWork[]; warnings: string[]; takeoff_id?: number | null; status?: Status;
};
export type Rough = RoughResult | { error: string } | null;

export type Offer = { price: number | null; url?: string; supplier_name?: string; supplier_id?: string; price_level?: string; data_kind?: string };
export type Confirmed = {
  file: string; plan: string; height_mm: number; groups: unknown[]; total_net_area_m2: number | null; complete?: boolean; known_net_area_m2?: number;
  pending_openings?: {id:string; wall:string; w:number|null; h:number|null}[];
  pending_groups?: {wall_type:string;role:string;wall_ids:string[];opening_ids:string[];missing:string[];net_area_m2:null}[];
  confirmed_at?: string; takeoff_id?: number | null;
  warnings: string[]; bill?: { wall_type: string; role: string; kind?: string; material_id?: string | null; material_name?: string; quantity: number | null; unit?: string;
    offers: Offer[]; est_cost: number | null }[];
  bill_total?: number | null; bill_missing?: string[];
};

export function missingWallOpenings(request?: {plans: { name:string; walls:{id:string;keep:boolean;masonry:boolean}[]; openings:{id:string;wall:string;keep:boolean;w:number|null;h:number|null}[] }[]}) {
  return (request?.plans || []).flatMap(plan => {
    const walls = new Set(plan.walls.filter(w => w.keep && w.masonry).map(w => w.id));
    return plan.openings.filter(o => o.keep && (o.w == null || o.h == null || !walls.has(o.wall))).map(o => plan.name + " · " + o.id);
  });
}
/** Giữ đường dẫn FastAPI để người dùng tìm đúng mặt bằng, tường và lỗ mở. */
export function validationMessage(detail: unknown, request: unknown, fallback: string) {
  if (typeof detail === "string") return detail || fallback;
  if (!Array.isArray(detail)) return fallback;
  type Item = { loc?: (string | number)[]; msg?: string };
  type InputPlan = { name?: string; plan?: string; openings?: { id?: string; wall?: string; w?: unknown; h?: unknown }[] };
  const input = request as (InputPlan & { plans?: InputPlan[] }) | null;
  const groups = new Map<string, Set<string>>();
  for (const issue of detail as Item[]) {
    if (!Array.isArray(issue?.loc)) continue;
    const path = issue.loc[0] === "body" ? issue.loc.slice(1) : issue.loc;
    const [list, index, field] = path.slice(-3);
    const plan = path.length === 3 ? input : path.length === 5 && path[0] === "plans" && typeof path[1] === "number" ? input?.plans?.[path[1]] : null;
    const opening = list === "openings" && typeof index === "number" ? plan?.openings?.[index] : null;
    let reason = issue.msg || "Dữ liệu chưa hợp lệ";
    let item = path.join(".") || "Yêu cầu";
    if (opening && (field === "w" || field === "h")) {
      const dimension = field === "w" ? "chiều rộng" : "chiều cao";
      reason = opening[field] == null ? `Thiếu ${dimension} (mm)` : `${dimension === "chiều rộng" ? "Chiều rộng" : "Chiều cao"} phải là số dương hữu hạn (mm)`;
      item = `${plan?.name || plan?.plan || "Mặt bằng"} · lỗ ${opening.id || Number(index) + 1}${opening.wall ? " · tường " + opening.wall : ""}`;
    }
    if (!groups.has(reason)) groups.set(reason, new Set());
    groups.get(reason)!.add(item);
  }
  return [...groups].map(([message, items]) => `${message} — ${[...items].join(", ")}`).join(". ") || fallback;
}

/** POST JSON; lỗi giữ đúng thông điệp của trang cũ (detail của FastAPI hoặc câu mặc định). */
export async function postJson<T>(path: string, data: unknown, fallback: string): Promise<T> {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
  const body = await r.json();
  if (!r.ok) throw new Error(validationMessage(body.detail, data, fallback));
  return body as T;
}
