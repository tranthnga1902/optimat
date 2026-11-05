"""Kiểm tra chéo bảng khối lượng (đặc tả 30/10/2026 mục 7) và gom tường bao theo hướng nhà (mục 11).

Mọi phép kiểm chỉ SINH CẢNH BÁO, không thay số: lượng bê tông, thép, khối xây trên m² sàn so với khoảng thông thường
trong data/rules/khoang_hop_ly.csv (mỗi dòng có định nghĩa và nguồn; khoảng là đề xuất, chưa có nguồn đã mở thì ghi rõ).
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from .. import config
from .models import CONCRETE_WORKS, WorkItem

RANGES_PATH = config.DATA_DIR / "rules" / "khoang_hop_ly.csv"


@dataclass(frozen=True)
class Range:
    ma: str
    dai_luong: str
    don_vi: str
    lo: float
    hi: float
    dinh_nghia: str
    nguon: str


@lru_cache(maxsize=1)
def load_ranges() -> dict[str, Range]:
    out = {}
    with open(RANGES_PATH, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            lo, hi = float(r["gia_tri_min"]), float(r["gia_tri_max"])
            if lo > hi or not r["dinh_nghia"].strip() or not r["nguon"].strip():
                raise ValueError(f"khoang_hop_ly.csv {r['ma']}: khoảng sai hoặc thiếu định nghĩa / nguồn.")
            out[r["dai_luong"]] = Range(r["ma"], r["dai_luong"], r["don_vi"], lo, hi, r["dinh_nghia"], r["nguon"])
    return out


def _sum(works: list[WorkItem], pred) -> tuple[float, bool]:
    """(tổng khối lượng đã có số, mọi dòng đều có số) của các công tác thỏa pred."""
    items = [w for w in works if pred(w)]
    known = [w.quantity for w in items if w.quantity is not None]
    return sum(known), bool(items) and len(known) == len(items)


def cross_checks(works: list[WorkItem], slab_area_m2: Optional[float]) -> list[str]:
    """Tỷ số bê tông, thép, khối xây trên m² sàn so với khoảng thông thường. slab_area_m2: tổng m² sàn các tầng
    (không kể nền tầng trệt); trống hoặc 0 thì không kiểm được."""
    out: list[str] = []
    ranges = load_ranges()
    concrete, c_ok = _sum(works, lambda w: w.code in CONCRETE_WORKS and w.code != "MONG")
    steel_t, s_ok = _sum(works, lambda w: w.code == "COT_THEP" and w.steel_element != "MONG")
    masonry, m_ok = _sum(works, lambda w: w.code == "XAY")

    def check(key: str, value: Optional[float], complete: bool, label: str) -> None:
        r = ranges.get(key)
        if r is None or value is None:
            return
        if not (r.lo <= value <= r.hi):
            out.append(f"Kiểm tra chéo {r.ma}: {label} = {value:.2f} {r.don_vi}, ngoài khoảng thông thường "
                       f"{r.lo:g}–{r.hi:g} ({r.nguon}). Chỉ cảnh báo, không thay số"
                       + ("" if complete else "; một số dòng còn trống nên tỷ số là cận dưới") + ".")

    if slab_area_m2:
        check("be_tong_tren_san", concrete / slab_area_m2 if concrete else None, c_ok, "bê tông kết cấu trên m² sàn")
        check("xay_tren_san", masonry / slab_area_m2 if masonry else None, m_ok, "khối xây trên m² sàn")
    if concrete and steel_t:
        check("thep_tren_m3_be_tong", steel_t * 1000 / concrete, c_ok and s_ok, "thép trên m³ bê tông")
    return out


def floor_area_checks(floor_areas: dict[str, float], building_area_m2: Optional[float]) -> list[str]:
    """Diện tích sàn từng tầng (trong tim tường bao) so với diện tích xây dựng: tầng ngoài khoảng KH05 là dấu hiệu bỏ sót
    hoặc nhân đôi sàn. Chỉ cảnh báo; thiếu diện tích xây dựng thì không kiểm."""
    r = load_ranges().get("san_tren_dien_tich_xay_dung")
    if r is None or not building_area_m2 or not floor_areas:
        return []
    out = []
    for plan, area in floor_areas.items():
        ratio = area / building_area_m2
        if not (r.lo <= ratio <= r.hi):
            out.append(f"Kiểm tra chéo {r.ma}: sàn {plan} {area:.2f} m² = {ratio:.2f} × diện tích xây dựng "
                       f"{building_area_m2:g} m², ngoài khoảng {r.lo:g}–{r.hi:g} ({r.nguon}). Chỉ cảnh báo, không thay số.")
    total = sum(floor_areas.values())
    out.append(f"Tổng diện tích sàn {len(floor_areas)} tầng (trong tim tường bao) {total:.2f} m², "
               f"diện tích xây dựng {building_area_m2:g} m² (thông số nhập, C).")
    return out


# ---- tường bao theo hướng nhà (đặc tả mục 11: vỏ bao che) ----
DIRECTIONS = (("B", 90.0), ("Đ", 0.0), ("N", 270.0), ("T", 180.0))   # tên hướng -> góc pháp tuyến (độ, bắc = +y khi north_deg = 90)


def wall_orientation(x1: float, y1: float, x2: float, y2: float, north_deg: float, inside_sign: float = 1.0) -> str:
    """Hướng mặt ngoài của một tường bao: pháp tuyến quay ra ngoài nhà (inside_sign = +1 khi phía trong nằm bên trái
    đoạn x1y1 -> x2y2), so với hướng bắc north_deg (góc của hướng bắc trên bản vẽ, từ +x ngược chiều kim đồng hồ).
    Trả B | Đ | N | T (chia 4 góc phần tư 90°)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    nx, ny = (dy / L, -dx / L) if inside_sign > 0 else (-dy / L, dx / L)      # pháp tuyến quay ra ngoài
    ang = (math.degrees(math.atan2(ny, nx)) - north_deg + 90.0) % 360.0        # 90° = bắc sau khi quy về bắc = +y
    return min(DIRECTIONS, key=lambda d: min(abs(ang - d[1]), 360 - abs(ang - d[1])))[0]


def envelope_by_orientation(walls, openings, height_mm: Optional[float], north_deg: Optional[float],
                            centroid: tuple[float, float] | None = None) -> dict[str, dict[str, float]]:
    """Diện tích tường bao (gross, cửa, net) theo 4 hướng B/Đ/N/T. walls: ReviewWall (role = envelope, keep, masonry);
    openings: ReviewOpening có wall + h. Phía trong nhà lấy theo tâm các tường bao (nhà lồi); north_deg trống -> {}."""
    if north_deg is None or not height_mm:
        return {}
    env = [w for w in walls if w.keep and w.masonry and w.role == "envelope"]
    if not env:
        return {}
    if any(o.keep and o.wall in {w.id for w in env} and (o.w is None or o.h is None) for o in openings):
        return {}
    cx, cy = centroid or (sum((w.x1 + w.x2) / 2 for w in env) / len(env), sum((w.y1 + w.y2) / 2 for w in env) / len(env))
    by_wall: dict[str, float] = {}
    for o in openings:
        if o.keep and o.wall and o.h is not None:
            by_wall[o.wall] = by_wall.get(o.wall, 0.0) + o.w * min(o.h, height_mm) / 1e6
    out = {d: {"gross_m2": 0.0, "opening_m2": 0.0, "net_m2": 0.0, "length_m": 0.0} for d, _ in DIRECTIONS}
    for w in env:
        mx, my = (w.x1 + w.x2) / 2, (w.y1 + w.y2) / 2
        side = (w.x2 - w.x1) * (cy - my) - (w.y2 - w.y1) * (cx - mx)     # > 0: tâm nhà ở bên trái đoạn
        d = wall_orientation(w.x1, w.y1, w.x2, w.y2, north_deg, 1.0 if side >= 0 else -1.0)
        L = math.hypot(w.x2 - w.x1, w.y2 - w.y1) / 1000
        gross = L * height_mm / 1000
        op = min(by_wall.get(w.id, 0.0), gross)
        out[d]["length_m"] += L
        out[d]["gross_m2"] += gross
        out[d]["opening_m2"] += op
        out[d]["net_m2"] += gross - op
    return {d: {k: round(v, 3) for k, v in vals.items()} for d, vals in out.items() if vals["length_m"] > 0}
