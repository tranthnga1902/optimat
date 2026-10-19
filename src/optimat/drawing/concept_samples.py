"""Hình mẫu cho trang Ký hiệu nhận diện: mỗi ký hiệu block vẽ lại block khớp trong các bản vẽ mẫu,
mỗi ký hiệu layer liệt kê các layer thật mà nó thắng (đúng thứ tự ưu tiên của match_layer)."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .. import config
from . import concepts
from .encoding import normalize

SAMPLE_DIRS = (config.DATA_DIR / "drawings" / "thu_vien", config.DATA_DIR / "drawings" / "build", config.DATA_DIR / "sample")
DRAWN = {"LINE", "ARC", "CIRCLE", "ELLIPSE", "LWPOLYLINE", "POLYLINE", "SPLINE", "SOLID"}   # bỏ chữ, hatch


@lru_cache(maxsize=1)
def _scan() -> tuple[dict[str, tuple[str, list]], dict[str, str]]:
    """Đọc mỗi bản vẽ mẫu một lần: tên block → (bản vẽ, các nét đã rời rạc hóa), tên layer → bản vẽ.
    shortcut: thêm bản vẽ mẫu mới cần khởi động lại máy chủ để quét lại."""
    import ezdxf
    from ezdxf import disassemble
    blocks: dict[str, tuple[str, list]] = {}
    layers: dict[str, str] = {}
    for path in sorted(p for d in SAMPLE_DIRS if d.exists() for p in d.glob("*.dxf")):
        try:
            doc = ezdxf.readfile(path)
        except Exception:     # bản vẽ hỏng thì bỏ qua, các bản khác vẫn có hình
            continue
        for layer in doc.layers:
            layers.setdefault(layer.dxf.name, path.stem)
        for blk in doc.blocks:
            if blk.name.startswith("*") or blk.name.upper() in blocks:
                continue
            ents = (e for e in disassemble.recursive_decompose(blk) if e.dxftype() in DRAWN)
            lines = [[(round(v.x, 1), round(v.y, 1)) for v in p.vertices()] for p in disassemble.to_primitives(ents)]
            lines = [ln for ln in lines if len(ln) > 1]
            if lines:
                blocks[blk.name.upper()] = (path.stem, lines)
    return blocks, layers


def _svg(lines: list) -> str:
    xs = [x for ln in lines for x, _ in ln]
    ys = [y for ln in lines for _, y in ln]
    x0, y1 = min(xs), max(ys)
    w, h = max(max(xs) - x0, 1), max(y1 - min(ys), 1)
    pad = max(w, h) * 0.06
    pts = " ".join(f'<polyline points="{" ".join(f"{x - x0:g},{y1 - y:g}" for x, y in ln)}"/>' for ln in lines)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad:g} {-pad:g} {w + 2 * pad:g} {h + 2 * pad:g}" '
            f'fill="none" stroke="currentColor">{pts}</svg>')


def samples() -> dict[str, dict]:
    """Mã ký hiệu → {matches: tên block/layer khớp trong bản vẽ mẫu, svg: hình block đầu tiên (chỉ ký hiệu block)}."""
    blocks, layers = _scan()
    out: dict[str, dict] = {}
    for s in concepts.load_signals():
        if s.tin_hieu == "block":
            names = sorted(n for n in blocks if re.fullmatch(rf"{re.escape(s.mau.upper())}\d*", n)
                           and concepts.match_block_signal(n) == s)
            out[s.ma] = {"matches": [f"{n} ({blocks[n][0]})" for n in names],
                         "svg": _svg(blocks[names[0]][1]) if names else None}
        else:
            names = sorted(n for n in layers
                           if concepts.match_layer(normalize(n).replace("_", " ").replace("-", " ")) == s)
            out[s.ma] = {"matches": [f"{n} ({layers[n]})" for n in names], "svg": None}
    return out
