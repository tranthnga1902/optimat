"use client";
// Phóng, kéo bản vẽ: viewBox ghi thẳng vào thẻ svg qua ref để kéo chuột không phải dựng lại cả trang.
import { useCallback, useEffect, useRef, type PointerEvent as RPointerEvent } from "react";

export type VB = { x: number; y: number; w: number; h: number };

export function useViewport() {
  const svgRef = useRef<SVGSVGElement>(null), scaleRef = useRef<HTMLDivElement>(null);
  const vb = useRef<VB>({ x: 0, y: 0, w: 1, h: 1 });
  const fitWidth = useRef(1), zoomRef = useRef<HTMLInputElement>(null), zoomLabel = useRef<HTMLOutputElement>(null);
  const drag = useRef<{ x: number; y: number; vb: VB } | null>(null), moved = useRef(false);

  const setVB = useCallback((v: VB) => {
    vb.current = v;
    const svg = svgRef.current;
    if (!svg) return;
    svg.setAttribute("viewBox", `${v.x} ${v.y} ${v.w} ${v.h}`);
    const r = svg.getBoundingClientRect(), mm = v.w / (r.width || 1) * 100;
    const nice = [100, 200, 500, 1000, 2000, 5000, 10000, 20000].find((n) => n >= mm) || 50000;
    if (scaleRef.current) scaleRef.current.textContent = `${Math.round(100 * nice / mm)} px = ${nice >= 1000 ? nice / 1000 + " m" : nice + " mm"}`;
    const percent = Math.round(100 * fitWidth.current / v.w);
    if (zoomRef.current) {
      zoomRef.current.min = String(Math.min(5, percent)); zoomRef.current.max = String(Math.max(1600, percent));
      zoomRef.current.value = String(percent);
    }
    if (zoomLabel.current) zoomLabel.current.value = percent + "%";
  }, []);
  const fitBox = useCallback((x0: number, y0: number, x1: number, y1: number, padRatio = 0.08, whole = false) => {
    const r = svgRef.current?.getBoundingClientRect(), ar = (r?.width || 1) / (r?.height || 1);
    const pad = Math.max(x1 - x0, y1 - y0) * padRatio + 500;
    let w = x1 - x0 + 2 * pad, h = y1 - y0 + 2 * pad;
    if (w / h < ar) w = h * ar; else h = w / ar;
    if (whole) fitWidth.current = w;
    setVB({ x: (x0 + x1) / 2 - w / 2, y: (y0 + y1) / 2 - h / 2, w, h });
  }, [setVB]);
  const fitSize = useCallback((sz: [number, number]) => fitBox(0, 0, sz[0], sz[1], 0.03, true), [fitBox]);
  const zoomTo = useCallback((percent: number, px = 0.5, py = 0.5) => {
    const v = vb.current, width = fitWidth.current * 100 / Math.max(5, Math.min(1600, percent));
    const height = width * v.h / v.w;
    setVB({ x: v.x + (v.w - width) * px, y: v.y + (v.h - height) * py, w: width, h: height });
  }, [setVB]);
  const focusOn = useCallback((w: { x1: number; y1: number; x2: number; y2: number }) =>
    fitBox(Math.min(w.x1, w.x2), Math.min(w.y1, w.y2), Math.max(w.x1, w.x2), Math.max(w.y1, w.y2), 0.6), [fitBox]);
  const toWorld = useCallback((e: { clientX: number; clientY: number }): [number, number] => {
    const r = svgRef.current!.getBoundingClientRect(), v = vb.current;
    return [v.x + (e.clientX - r.left) / r.width * v.w, v.y + (e.clientY - r.top) / r.height * v.h];
  }, []);
  const onPointerDown = useCallback((e: RPointerEvent) => { drag.current = { x: e.clientX, y: e.clientY, vb: { ...vb.current } }; moved.current = false; }, []);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const zoom = (f: number, cx: number, cy: number) => {
      const r = svg.getBoundingClientRect(), px = (cx - r.left) / r.width, py = (cy - r.top) / r.height, v = vb.current;
      zoomTo(100 * fitWidth.current / (v.w * f), px, py);
    };
    const wheel = (e: WheelEvent) => { e.preventDefault(); zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, e.clientX, e.clientY); };
    const move = (e: PointerEvent) => {
      const d = drag.current;
      if (!d) return;
      if (Math.hypot(e.clientX - d.x, e.clientY - d.y) > 4) moved.current = true;
      if (!moved.current) return;
      const r = svg.getBoundingClientRect();
      setVB({ ...d.vb, x: d.vb.x - (e.clientX - d.x) * vb.current.w / r.width, y: d.vb.y - (e.clientY - d.y) * vb.current.h / r.height });
    };
    const up = () => { drag.current = null; setTimeout(() => (moved.current = false), 0); };
    const resize = () => setVB(vb.current);
    svg.addEventListener("wheel", wheel, { passive: false });
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
    window.addEventListener("resize", resize);
    return () => {
      svg.removeEventListener("wheel", wheel);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      window.removeEventListener("resize", resize);
    };
  }, [setVB, zoomTo]);

  return { svgRef, scaleRef, zoomRef, zoomLabel, zoomTo, vbRef: vb, movedRef: moved, fitBox, fitSize, focusOn, toWorld, onPointerDown };
}
export type Viewport = ReturnType<typeof useViewport>;
