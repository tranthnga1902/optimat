"""Định mức công tác phần thô và cấp phối bê tông trộn tại chỗ: data/rules/dinh_muc_phan_tho.csv (sửa bằng Excel).

    work_code    = mã công tác (TRAT, CAN_NEN, COT_THEP, CHONG_THAM, NEN_DEM_CAT, COP_PHA) hoặc BE_TONG_TRON (cấp phối)
    variant      = chiều dày (TRAT, CAN_NEN: mm), mác (BE_TONG_TRON: M250), mã vật liệu (CHONG_THAM: CT02); trống: mọi trường hợp
    material_id  = mã danh mục; "@VUA" là vữa (mác lấy từ thông số công trình); trống: danh mục chưa có mã (xem material_name)
    qty, qty_unit= lượng vật liệu trên 1 đơn vị công tác, ví dụ "kg / m³"; trống: chưa tra, công tác không ra vật liệu
    norm_code    = số hiệu bảng của TT 38/2026/TT-BXD (bắt buộc khi điền qty, Quy ước B7)

Xây tường không nằm ở đây: định mức gạch và vữa theo phương án tường (wall_systems). Cấp phối vữa nằm trong quan hệ
COMPOSED_OF của danh mục (material_relations), cùng một nguồn với tối ưu.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from .. import config
from ..db.session import read_rule_table
from .models import WORKS

NORMS_PATH = config.DATA_DIR / "rules" / "dinh_muc_phan_tho.csv"
MORTAR = "@VUA"
MIX = "BE_TONG_TRON"


@dataclass(frozen=True)
class Norm:
    work_code: str
    variant: str
    material_id: str | None
    material_name: str
    qty: float | None
    qty_unit: str
    norm_code: str
    source: str
    note: str

    @property
    def numerator_unit(self) -> str:
        """Đơn vị của lượng vật liệu: "kg / m³" -> "kg"."""
        return self.qty_unit.split("/")[0].strip()


@lru_cache(maxsize=4)
def load_norms(path: str | None = None) -> tuple[Norm, ...]:
    df = read_rule_table("rough_norms", path, NORMS_PATH)
    out = []
    for r in df.to_dict("records"):
        code = r["work_code"].strip()
        if code not in WORKS and code != MIX:
            raise ValueError(f"Định mức phần thô: mã công tác không hợp lệ: {code}")
        qty = r["qty"].strip().replace(",", ".")
        out.append(Norm(work_code=code, variant=r["variant"].strip(), material_id=r["material_id"].strip() or None,
                        material_name=r["material_name"].strip(), qty=float(qty) if qty else None,
                        qty_unit=r["qty_unit"].strip(), norm_code=r["norm_code"].strip(), source=r["source"].strip(),
                        note=r["note"].strip()))
    return tuple(out)


def norms_for(code: str, variant: str | None, norms: tuple[Norm, ...] | None = None) -> list[Norm]:
    """Dòng định mức của công tác. Dòng có variant trống áp dụng cho mọi variant."""
    norms = load_norms() if norms is None else norms
    v = (variant or "").strip()
    return [n for n in norms if n.work_code == code and n.variant in ("", v)]


def variants_of(code: str, norms: tuple[Norm, ...] | None = None) -> list[str]:
    norms = load_norms() if norms is None else norms
    return sorted({n.variant for n in norms if n.work_code == code and n.variant})


# Quy đổi đơn vị của lượng định mức sang đơn vị tính của vật liệu trong danh mục
_UNIT_FACTOR = {("kg", "tấn"): 0.001, ("tấn", "kg"): 1000.0, ("m3", "m³"): 1.0, ("m2", "m²"): 1.0}


def unit_factor(from_unit: str, to_unit: str) -> float | None:
    """Hệ số đổi từ đơn vị của định mức sang đơn vị của vật liệu; None: không đổi được."""
    a, b = from_unit.strip().split(" ")[0], to_unit.strip()
    if a == b:
        return 1.0
    return _UNIT_FACTOR.get((a, b))
