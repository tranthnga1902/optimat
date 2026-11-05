"use client";
import { useLayoutEffect, useMemo } from "react";
import { clsColor, type Data } from "./model";
import { useViewport } from "./viewport";
import type { LinePreview } from "./read-progress";
import s from "./review.module.css";

export function ReadPreview({ preview, recognized, label = "Nét bản vẽ đang nhận diện" }: { preview: LinePreview; recognized?: Data; label?: string }) {
  const { svgRef, scaleRef, fitSize, onPointerDown } = useViewport();
  useLayoutEffect(() => { fitSize(preview.size); }, [preview, fitSize]);
  const path = useMemo(() => preview.segments.map(([x1, y1, x2, y2]) => `M${x1} ${y1}L${x2} ${y2}`).join(""), [preview]);

  return <div className="absolute inset-0 bg-white">
    <svg ref={svgRef} role="img" aria-label={label} onPointerDown={onPointerDown}>
      <path d={path} fill="none" stroke="#475569" strokeWidth={1} vectorEffect="non-scaling-stroke" />
      {recognized?.plans.map((plan, i) => {
        const [x, y] = plan.origin || [0, 0];
        return <g key={i} transform={`translate(${x - preview.origin[0]} ${preview.origin[1] - y})`}>
          {plan.walls.map((wall) => <line key={wall.id} x1={wall.x1} y1={wall.y1} x2={wall.x2} y2={wall.y2}
            stroke={clsColor(wall.cls)} strokeWidth={3} vectorEffect="non-scaling-stroke" />)}
        </g>;
      })}
    </svg>
    {preview.shown < preview.total && <small role="status" className="absolute left-2 top-2 rounded bg-white px-2 py-1 text-slate-700">Bản xem nhanh: {preview.shown.toLocaleString("vi-VN")} / {preview.total.toLocaleString("vi-VN")} đoạn nét.</small>}
    <div className={s.scale} ref={scaleRef} />
  </div>;
}
