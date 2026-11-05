"""Nét xem sớm, không chạy lại bộ đọc hoặc dùng như kết quả đo bóc."""
from __future__ import annotations
import math


def line_preview(drawing, limit: int = 80_000) -> dict:
    segments = [s for s in drawing.segments if s.kind != "hatch"] or list(drawing.segments)
    if not segments:
        return {"origin": [0, 0], "size": [1, 1], "segments": [], "total": 0, "shown": 0}
    ox = min(min(s.x1, s.x2) for s in segments)
    oy = max(max(s.y1, s.y2) for s in segments)
    width = max(max(s.x1, s.x2) for s in segments) - ox
    height = oy - min(min(s.y1, s.y2) for s in segments)
    stride = max(1, math.ceil(len(segments) / limit))
    lines = [[round(s.x1 - ox, 1), round(oy - s.y1, 1), round(s.x2 - ox, 1), round(oy - s.y2, 1)]
             for s in segments[::stride]]
    return {"origin": [ox, oy], "size": [max(width, 1), max(height, 1)], "segments": lines,
            "total": len(segments), "shown": len(lines)}
