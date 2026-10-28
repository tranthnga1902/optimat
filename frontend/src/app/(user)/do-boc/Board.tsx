"use client";
// Bàn vẽ: nền bản vẽ gốc hoặc nét đã đọc, tường nhận dạng tô theo loại, lỗ mở, cột, khung mặt bằng (xem toàn bộ), thanh công cụ nổi.
import { useEffect, useImperativeHandle, useLayoutEffect, useMemo, useRef, useState, type MouseEvent, type PointerEvent, type ReactNode, type Ref } from "react";
import s from "./review.module.css";
import { useWallClasses } from "@/lib/reference";
import { ROLE, band, clsColor, fmt, wallLen, type Data, type Plan, type PlanCol, type PlanState } from "./model";
import type { Viewport } from "./viewport";

type VP = Pick<Viewport, "svgRef" | "scaleRef" | "movedRef" | "toWorld" | "onPointerDown" | "fitSize">;

export type Mode = "select" | "wall" | "open";
export type Pt = [number, number];

type TipHandle = { show: (e: PointerEvent, c: ReactNode) => void; move: (e: PointerEvent) => void; hide: () => void };

/** Chú thích nổi: tự giữ nội dung, rê chuột không dựng lại bản vẽ. */
function Tip({ ref, boardRef }: { ref: Ref<TipHandle>; boardRef: React.RefObject<HTMLDivElement | null> }) {
  const [content, setContent] = useState<ReactNode>(null);
  const el = useRef<HTMLDivElement>(null), last = useRef({ x: 0, y: 0 });
  const place = () => {
    const tip = el.current, board = boardRef.current;
    if (!tip || !board) return;
    const r = board.getBoundingClientRect();
    let x = last.current.x - r.left + 14, y = last.current.y - r.top + 14;
    if (x + tip.offsetWidth > r.width - 8) x -= tip.offsetWidth + 28;
    if (y + tip.offsetHeight > r.height - 8) y -= tip.offsetHeight + 28;
    tip.style.left = x + "px"; tip.style.top = y + "px";
  };
  useImperativeHandle(ref, () => ({
    show: (e, c) => { last.current = { x: e.clientX, y: e.clientY }; setContent(c); },
    move: (e) => { last.current = { x: e.clientX, y: e.clientY }; place(); },
    hide: () => setContent(null),
  }));
  useLayoutEffect(place);
  return content == null ? null : <div ref={el} className={s.tip}>{content}</div>;
}

/** Đường tường đang vẽ: theo chuột từ điểm đầu tới điểm hút gần nhất. */
function DraftLayer({ from, svgRef, snap, toWorld, unit }: { from: Pt; svgRef: Viewport["svgRef"]; snap: (p: Pt) => Pt; toWorld: Viewport["toWorld"]; unit: number }) {
  const [q, setQ] = useState<Pt | null>(null);
  useEffect(() => {
    const svg = svgRef.current!;
    const move = (e: globalThis.PointerEvent) => setQ(snap(toWorld(e)));
    svg.addEventListener("pointermove", move);
    return () => svg.removeEventListener("pointermove", move);
  }, [svgRef, snap, toWorld]);
  if (!q) return null;
  return (
    <>
      <line x1={from[0]} y1={from[1]} x2={q[0]} y2={q[1]} stroke="var(--accent)" strokeWidth={2} strokeDasharray="6 4" vectorEffect="non-scaling-stroke" />
      <circle cx={q[0]} cy={q[1]} r={unit * 0.6} fill="var(--accent)" />
    </>
  );
}

/** Nét đã đọc gộp thành ba path (chỉ đổi khi đổi mặt bằng). */
function linePaths(P: Plan) {
  const wallLayers = new Set(P.wall_layers || []);
  const out = { wall: [] as string[], other: [] as string[], hatch: [] as string[] };
  for (const [x1, y1, x2, y2, li, isH] of P.segs) {
    const d = `M${x1} ${y1}L${x2} ${y2}`;
    if (isH) { out.hatch.push(d); continue; }
    (wallLayers.has(P.layers[li].name) ? out.wall : out.other).push(d);
  }
  return { wall: out.wall.join(""), other: out.other.join(""), hatch: out.hatch.join("") };
}

export type BoardProps = {
  svgRef: VP["svgRef"]; scaleRef: VP["scaleRef"]; movedRef: VP["movedRef"]; toWorld: VP["toWorld"]; onPointerDown: VP["onPointerDown"]; fitSize: VP["fitSize"];
  data: Data | null; pi: number; P: Plan | null; S: PlanState | null; selected: string | null;
  mode: Mode; onMode: (m: Mode) => void; hint: string; draft: Pt | null; snap: (p: Pt) => Pt; unit: number;
  bg: string; hasCad: boolean; onBg: (v: string) => void; showRec: boolean; onShowRec: (v: boolean) => void; showLabels: boolean; onShowLabels: (v: boolean) => void;
  newCls: string; onNewCls: (v: string) => void; newKind: string; onNewKind: (v: string) => void; newW: string; onNewW: (v: string) => void; newH: string; onNewH: (v: string) => void;
  cols: PlanCol[]; onToggleCol: (j: number) => void; onSvgClick: (e: MouseEvent<SVGSVGElement>) => void; onSelect: (id: string) => void; onOpenPlan: (i: number) => void;
};

export function Board(p: BoardProps) {
  const { svgRef, scaleRef, movedRef, toWorld, data, pi, P, S, selected, mode, bg, unit } = p;
  const boardRef = useRef<HTMLDivElement>(null), tip = useRef<TipHandle>(null);
  const classes = useWallClasses(p.newCls);
  const T = (c: ReactNode) => ({
    onPointerEnter: (e: PointerEvent) => tip.current?.show(e, c),
    onPointerMove: (e: PointerEvent) => tip.current?.move(e),
    onPointerLeave: () => tip.current?.hide(),
  });
  const rec = p.showRec ? undefined : "none", lines = bg === "lines";
  const overview = !!data && pi < 0 && !!data.overview;
  // bản vẽ gốc vẽ đúng như phần mềm CAD (máy chủ dựng bằng ezdxf); SVG do máy chủ sinh nên chèn nguyên văn
  const cad = overview ? data!.overview!.cad || "" : P?.cad || "";
  const L = useMemo(() => (P ? linePaths(P) : null), [P]);
  const byId = S ? Object.fromEntries(S.walls.map((w) => [w.id, w])) : {};
  const pick = (id: string) => (e: MouseEvent) => { if (mode === "select") { e.stopPropagation(); p.onSelect(id); } };

  return (
    <div ref={boardRef} className={`${s.board} ${!lines ? s.cadbg : ""} ${bg === "cad-light" ? s.light : ""}`} data-mode={mode}>
      <svg ref={svgRef} role="img" aria-label="Mặt bằng và các tường nhận dạng" onClick={p.onSvgClick} onPointerDown={p.onPointerDown}>
        {data && (overview || P) && <>
          <g className={s.cadlayer} style={{ display: lines ? "none" : undefined }} dangerouslySetInnerHTML={{ __html: cad }} />
          {overview ? (
            <g style={{ display: rec }}>
              {data.overview!.plans.map((b, i) => (
                <g key={i} onClick={(e) => { if (movedRef.current) return; e.stopPropagation(); p.onOpenPlan(i); }}>
                  <rect x={b.x} y={b.y} width={b.w} height={b.h} className={s.ovlRect} strokeWidth={2} vectorEffect="non-scaling-stroke" />
                  <text x={b.x + b.w / 2} y={b.y - unit * 0.6} textAnchor="middle" fontSize={unit * 1.2} fill="#5cb6d6" paintOrder="stroke" stroke="#000" strokeWidth={unit * 0.25}>{`${i + 1}. ${b.name}`}</text>
                </g>
              ))}
            </g>
          ) : P && S && <>
            <g style={{ display: lines ? undefined : "none" }}>
              <path d={L?.hatch} fill="none" stroke="var(--line)" strokeWidth={0.4} opacity={0.3} vectorEffect="non-scaling-stroke" />
            </g>
            <g style={{ display: lines ? undefined : "none" }}>
              <path d={L?.other} fill="none" stroke="var(--line)" strokeWidth={0.7} opacity={0.75} vectorEffect="non-scaling-stroke" />
              <path d={L?.wall} fill="none" stroke="var(--wall-line)" strokeWidth={1.1} vectorEffect="non-scaling-stroke" />
            </g>
            {/* cặp nét giống tường nhưng đã loại (bậc thang, lan can, khung cửa sổ): nét đứt xám, rê chuột xem lý do */}
            <g style={{ display: rec }}>
              {(P.rejected || []).map((r, i) => (
                <line key={i} x1={r.x1} y1={r.y1} x2={r.x2} y2={r.y2} stroke="#9aa7a2" strokeWidth={2} strokeDasharray="4 4" vectorEffect="non-scaling-stroke" opacity={0.8}
                  {...T(<>Không tính là tường: <b>{r.reason}</b></>)} />
              ))}
            </g>
            <g style={{ display: rec }}>
              {S.walls.map((w) => {
                const color = !w.masonry ? "var(--concrete)" : clsColor(w.cls), on = w.keep;
                return (
                  <g key={w.id} data-id={w.id} style={{ cursor: "pointer" }} onClick={pick(w.id)}
                    {...T(<><b>{w.id}</b> · tường {w.cls} · {ROLE[w.role]}<br />{fmt(wallLen(w))} m{on ? "" : <> · <b>đã loại</b></>}</>)}>
                    <polygon points={band(w)} fill={on ? color : "transparent"} fillOpacity={on ? 0.34 : 0}
                      stroke={w.id === selected ? "var(--sel)" : on ? color : "var(--muted)"} strokeWidth={w.id === selected ? 3 : w.role === "envelope" ? 2 : 1.1}
                      strokeDasharray={on ? (w.src === "manual" ? "6 3" : "") : "3 3"} vectorEffect="non-scaling-stroke" />
                    {!on && <line x1={w.x1} y1={w.y1} x2={w.x2} y2={w.y2} stroke="var(--open)" strokeWidth={1} vectorEffect="non-scaling-stroke" />}
                  </g>
                );
              })}
            </g>
            <g style={{ display: rec }}>
              {p.cols.map((c, j) => (
                <rect key={c.id + ":" + j} x={c.x - c.b_mm / 2} y={c.y - c.h_mm / 2} width={c.b_mm} height={c.h_mm} fill={c.keep ? "var(--concrete)" : "transparent"}
                  fillOpacity={0.55} stroke={c.keep ? "var(--ink)" : "var(--muted)"} strokeDasharray={c.keep ? "" : "3 3"} strokeWidth={1.2}
                  vectorEffect="non-scaling-stroke" style={{ cursor: "pointer" }}
                  {...T(<><b>{c.id}</b> · cột {c.b_mm}×{c.h_mm}{c.keep ? "" : <> · <b>đã bỏ</b></>}<br />Bấm để {c.keep ? "bỏ" : "giữ"}</>)}
                  onClick={(e) => { if (mode !== "select") return; e.stopPropagation(); p.onToggleCol(j); }} />
              ))}
            </g>
            <g style={{ display: rec }}>
              {S.openings.map((o) => {
                const w = byId[o.wall];
                if (!w) return null;
                const L2 = (w.x2 - w.x1) ** 2 + (w.y2 - w.y1) ** 2 || 1;
                const t = Math.max(0, Math.min(1, ((o.x - w.x1) * (w.x2 - w.x1) + (o.y - w.y1) * (w.y2 - w.y1)) / L2));
                const px = w.x1 + t * (w.x2 - w.x1), py = w.y1 + t * (w.y2 - w.y1);
                const Ln = Math.sqrt(L2), ux = (w.x2 - w.x1) / Ln, uy = (w.y2 - w.y1) / Ln, half = o.w / 2;
                const on = o.keep && w.keep;
                return <line key={o.id} x1={px - ux * half} y1={py - uy * half} x2={px + ux * half} y2={py + uy * half} stroke={on ? "var(--open)" : "var(--muted)"}
                  strokeWidth={o.id === selected ? 7 : 4} strokeLinecap="butt" vectorEffect="non-scaling-stroke" opacity={on ? 0.9 : 0.4}
                  style={{ cursor: "pointer" }} onClick={pick(o.id)} />;
              })}
            </g>
            <g style={{ display: rec }}>
              {p.showLabels && S.walls.filter((w) => w.keep).map((w) => (
                <text key={w.id} x={(w.x1 + w.x2) / 2} y={(w.y1 + w.y2) / 2} fontSize={unit * 1.5} textAnchor="middle" fill="var(--ink)"
                  fontFamily="var(--f-num)" paintOrder="stroke" stroke="var(--paper)" strokeWidth={unit * 0.4}>{w.id}</text>
              ))}
            </g>
            <g>{p.draft && <DraftLayer key={p.draft.join(",")} from={p.draft} svgRef={svgRef} snap={p.snap} toWorld={toWorld} unit={unit} />}</g>
          </>}
        </>}
      </svg>
      <div className={s.toolbar}>
        <div className={s.seg} role="group" aria-label="Chế độ">
          {([["select", "Chọn"], ["wall", "Vẽ thêm tường"], ["open", "Thêm cửa"]] as [Mode, string][]).map(([m, t]) => (
            <button key={m} type="button" aria-pressed={mode === m} onClick={() => p.onMode(m)}>{t}</button>
          ))}
        </div>
        {mode === "wall" && <label className={s.field}>Loại <select value={p.newCls} onChange={(e) => p.onNewCls(e.target.value)}>{classes.map((c) => <option key={c}>{c}</option>)}</select></label>}
        {mode === "open" && <label className={s.field}>
          <select value={p.newKind} onChange={(e) => p.onNewKind(e.target.value)}><option value="door">Cửa đi</option><option value="window">Cửa sổ</option></select>
          <input type="number" step={50} min={200} value={p.newW} onChange={(e) => p.onNewW(e.target.value)} aria-label="Rộng (mm)" /> ×{" "}
          <input type="number" step={50} min={200} value={p.newH} onChange={(e) => p.onNewH(e.target.value)} aria-label="Cao (mm)" /> mm</label>}
        <span className={s.chipset}>
          <label>Nền <select aria-label="Nền bản vẽ" value={bg} onChange={(e) => p.onBg(e.target.value)}>
            <option value="cad" disabled={!p.hasCad}>Bản vẽ gốc · nền đen</option><option value="cad-light" disabled={!p.hasCad}>Bản vẽ gốc · nền trắng</option><option value="lines">Nét đã đọc</option>
          </select></label>
          <label><input type="checkbox" checked={p.showRec} onChange={(e) => p.onShowRec(e.target.checked)} /> Nhận dạng</label>
          <label><input type="checkbox" checked={p.showLabels} onChange={(e) => p.onShowLabels(e.target.checked)} /> Nhãn</label>
        </span>
        <button className={s.btn} type="button" onClick={() => { const sz = pi < 0 ? data?.overview?.size : P?.size; if (sz) p.fitSize(sz); }}>Vừa khung</button>
      </div>
      <div className={s.hint}>{p.hint}</div>
      <div className={s.scale} ref={scaleRef} />
      <Tip ref={tip} boardRef={boardRef} />
    </div>
  );
}
