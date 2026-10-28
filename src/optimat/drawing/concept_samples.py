"""Hình mẫu cho trang Ký hiệu nhận diện: mỗi ký hiệu block vẽ lại block khớp trong các bản vẽ mẫu,
mỗi ký hiệu layer liệt kê các layer thật mà nó thắng (đúng thứ tự ưu tiên của match_layer)."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .. import config
from . import concepts
from .encoding import normalize

# thứ tự là thứ tự ưu tiên hình: thư viện mẫu trước bản vẽ thật; không dùng data/sample (block giả của bản vẽ thử)
SAMPLE_DIRS = (config.DATA_DIR / "drawings" / "thu_vien", config.DATA_DIR / "drawings" / "build")
DRAWN = {"LINE", "ARC", "CIRCLE", "ELLIPSE", "LWPOLYLINE", "POLYLINE", "SPLINE", "SOLID"}   # bỏ chữ, hatch


@lru_cache(maxsize=1)
def _scan() -> tuple[dict[str, tuple[str, list]], dict[str, str]]:
    """Đọc mỗi bản vẽ mẫu một lần: tên block → (bản vẽ, các nét đã rời rạc hóa), tên layer → bản vẽ.
    shortcut: thêm bản vẽ mẫu mới cần khởi động lại máy chủ để quét lại."""
    import ezdxf
    from ezdxf import disassemble

    from .dxf_reader import original_block_name
    blocks: dict[str, tuple[str, list]] = {}
    layers: dict[str, str] = {}
    for path in sorted(p for d in SAMPLE_DIRS if d.exists() for p in d.glob("*.dxf")):
        try:
            doc = ezdxf.readfile(path)
        except Exception:     # bản vẽ hỏng thì bỏ qua, các bản khác vẫn có hình
            continue
        for layer in doc.layers:
            layers.setdefault(layer.dxf.name, path.stem)
        # block động: lấy hình của bản chèn thật (*U…, một trạng thái hiển thị), không lấy định nghĩa gốc
        # (vẽ chồng mọi trạng thái); mỗi tên gốc lấy bản ẩn danh đầu tiên
        anon = {b.name: original_block_name(doc, b.name) for b in doc.blocks if b.name.startswith("*")}
        for blk in sorted(doc.blocks, key=lambda b: not b.name.startswith("*")):
            name = anon.get(blk.name, blk.name)
            if name.startswith("*") or name.upper() in blocks:
                continue
            ents = (e for e in disassemble.recursive_decompose(blk) if e.dxftype() in DRAWN)
            lines = [[(round(v.x, 1), round(v.y, 1)) for v in p.vertices()] for p in disassemble.to_primitives(ents)]
            lines = [ln for ln in lines if len(ln) > 1]
            if lines:
                blocks[name.upper()] = (path.stem, lines)
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


def block_svg(name: str) -> str | None:
    """Hình một block trong bản vẽ mẫu theo tên (không phân biệt hoa thường), để người dùng chọn làm hình minh họa."""
    hit = _scan()[0].get(name.upper())
    return _svg(hit[1]) if hit else None


def samples() -> dict[str, dict]:
    """Mã ký hiệu → {matches: tên block/layer khớp trong bản vẽ mẫu, svg: hình block đầu tiên (chỉ ký hiệu block)}."""
    blocks, layers = _scan()
    out: dict[str, dict] = {}
    for s in concepts.load_signals():
        if s.tin_hieu == "block":
            order = {n: i for i, n in enumerate(blocks)}      # theo SAMPLE_DIRS: thư viện mẫu trước
            names = sorted((n for n in blocks if re.fullmatch(rf"{re.escape(s.mau.upper())}\d*", n)
                            and concepts.match_block_signal(n) == s), key=order.get)
            out[s.ma] = {"matches": [f"{n} ({blocks[n][0]})" for n in names],
                         "svg": _svg(blocks[names[0]][1]) if names else None}
        else:
            names = sorted(n for n in layers
                           if concepts.match_layer(normalize(n).replace("_", " ").replace("-", " ")) == s)
            out[s.ma] = {"matches": [f"{n} ({layers[n]})" for n in names], "svg": None}
    return out
