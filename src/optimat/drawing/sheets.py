"""Nhận loại bản vẽ trong một file theo tiêu đề hình vẽ: 14 loại cần để bóc phần thô (data/rules/loai_ban_ve.csv).

Một file thường gộp nhiều hình vẽ (mặt bằng móng, mặt bằng dầm, chi tiết móng...). Cách nhận:
1. Chữ là tiêu đề khi khớp mẫu của một loại (so trên chữ đã bỏ dấu, chữ thường, dòng đầu tiên khớp thắng) và cao chữ
   không dưới TITLE_REL_HEIGHT lần chữ tiêu đề lớn nhất (bỏ ghi chú, chữ trong khung tên).
2. Khung hình vẽ của tiêu đề: cụm nét lớn nhất phía trên tiêu đề (cùng cách tìm mặt bằng tầng, plans.view_region).
Loại bản vẽ chưa có trong file được liệt kê kèm bộ phận phần thô cần nó, để người dùng bổ sung hoặc nhập tay.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .. import config
from .dxf_reader import Drawing
from .encoding import normalize
from .plans import HEADING_WORDS, _clusters

SHEET_TYPES_FILE = config.DATA_DIR / "rules" / "loai_ban_ve.csv"
TITLE_REL_HEIGHT = 0.4
VIEW_REACH_MM = 40000.0      # khung tìm tối đa mỗi phía khi không có tiêu đề bên cạnh
CLUSTER_MIN_SHARE = 0.1


@dataclass(frozen=True)
class SheetType:
    ma: str                 # BV01…BV14
    ten: str
    nhom: str               # kien_truc | ket_cau
    mau: re.Pattern
    loai_tru: re.Pattern | None
    bo_phan: tuple[str, ...]  # vai trò phần thô lấy từ loại bản vẽ này (BEAM, FOUNDATION...)
    vat_lieu: str


@dataclass
class View:
    """Một hình vẽ trong file: tiêu đề, loại, khung."""
    title: str
    ma: str
    ten: str
    nhom: str
    x: float
    y: float
    bbox: tuple[float, float, float, float] | None = None


@lru_cache(maxsize=4)
def load_sheet_types(path: str | None = None) -> tuple[SheetType, ...]:
    # shortcut: đọc CSV, chưa có bảng PostgreSQL riêng (thêm bảng là đổi lược đồ, cần duyệt); khi có thì dùng read_rule_table
    out = []
    for r in pd.read_csv(Path(path or SHEET_TYPES_FILE), dtype=str, keep_default_na=False).to_dict("records"):
        out.append(SheetType(r["ma"], r["loai_ban_ve"], r["nhom"], re.compile(r["mau"]),
                             re.compile(r["loai_tru"]) if r["loai_tru"] else None, tuple(r["bo_phan"].split()),
                             r["vat_lieu"]))
    return tuple(out)


def sheet_type_of(text: str, types: tuple[SheetType, ...] | None = None) -> SheetType | None:
    t = re.sub(r"\s+", " ", normalize(text)).strip()
    for st in types or load_sheet_types():
        if st.mau.search(t) and not (st.loai_tru and st.loai_tru.search(t)):
            return st
    return None


def _window(t, headings) -> tuple[float, float, float, float]:
    """Khung tìm hình vẽ phía trên tiêu đề t: chia đôi khoảng cách tới tiêu đề cùng hàng, dừng ở tiêu đề phía trên.
    Không giới hạn bề rộng cố định như mặt bằng tầng: mặt bằng kết cấu hay vẽ phóng to (TL 1/50) nên rộng hơn."""
    left, right, top = t.x - VIEW_REACH_MM, t.x + VIEW_REACH_MM, t.y + VIEW_REACH_MM
    for o in headings:
        if o is not t and abs(o.y - t.y) < 5000:
            if o.x < t.x:
                left = max(left, (o.x + t.x) / 2)
            elif o.x > t.x:
                right = min(right, (o.x + t.x) / 2)
    for o in headings:
        if o.y > t.y + 1000 and left <= o.x <= right:
            top = min(top, o.y - 200)
    return left, t.y - 300, right, top


def _region(drawing: Drawing, t, headings):
    """Khung hình vẽ: bao các cụm nét đáng kể (≥ CLUSTER_MIN_SHARE cụm lớn nhất) trong khung tìm. Nét dài vẫn tính
    (dầm, đà kiềng chạy suốt nhà), nên không dùng nét khung bản vẽ để thu hẹp như mặt bằng tầng."""
    clusters = _clusters(drawing, _window(t, headings), max_line=math.inf)
    if not clusters:
        return None
    top = max(w for _, w in clusters)
    boxes = [b for b, w in clusters if w >= CLUSTER_MIN_SHARE * top]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def title_height_reference(titles) -> float:
    # Tên cấu kiện đơn lẻ (ví dụ chữ “lanh tô” phóng lớn) không đại diện cỡ tiêu đề mặt bằng.
    headings = [t.height for t in titles if normalize(t.text).startswith(HEADING_WORDS) and t.height > 0]
    return max(headings, default=0) or max((t.height for t in titles), default=0)


def find_views(drawing: Drawing, bbox_for: tuple[str, ...] | None = None) -> list[View]:
    """Hình vẽ có tiêu đề nhận được loại. bbox_for: chỉ tìm khung cho các loại này (tìm khung tốn thời gian); None: mọi loại."""
    titled = [(t, st) for t in drawing.texts if (st := sheet_type_of(t.text))]
    if not titled:
        return []
    big = title_height_reference([t for t, _ in titled])
    titled = [(t, st) for t, st in titled if t.height >= TITLE_REL_HEIGHT * big]
    headings = [t for t, _ in titled]
    views, seen = [], Counter()
    for t, st in sorted(titled, key=lambda p: (-p[0].y, p[0].x)):
        title = re.sub(r"\s+", " ", t.text).strip()
        seen[title] += 1      # QU-05: tiêu đề là khóa (dầm theo mặt bằng), trùng thì đánh số thêm
        views.append(View(title if seen[title] == 1 else f"{title} ({seen[title]})", st.ma, st.ten, st.nhom, t.x, t.y,
                          _region(drawing, t, headings) if bbox_for is None or st.ma in bbox_for else None))
    return views


def sheet_inventory(views: list[View]) -> list[dict]:
    """14 loại bản vẽ: có trong file không (tiêu đề tìm thấy), bộ phận phần thô và vật liệu lấy từ loại đó."""
    out = []
    for st in sorted(load_sheet_types(), key=lambda s: s.ma):
        titles = [v.title for v in views if v.ma == st.ma]
        out.append({"ma": st.ma, "loai_ban_ve": st.ten, "nhom": st.nhom, "co": bool(titles), "tieu_de": titles,
                    "bo_phan": list(st.bo_phan), "vat_lieu": st.vat_lieu})
    return out
