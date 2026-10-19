"""Khái niệm đọc bản vẽ theo Quy ước bản vẽ đầu vào v1.0 (15/10/2026).

Hai file định nghĩa, sửa bằng Excel, không viết cứng trong mã:
    data/rules/quy_uoc.csv    23 điều khoản QU-01…QU-23: nhóm, nội dung, mức B (bắt buộc) / K (khuyến nghị), cách kiểm
    data/rules/concepts.csv   ký hiệu nhận dạng: tên layer -> vai trò (QU-08), tiền tố block -> cửa đi / cửa sổ (QU-14)
                              hoặc đối tượng không phải cửa (cột, cao độ, trục, nội thất: ANNOTATION / IGNORE)
Thứ tự dòng trong concepts.csv là thứ tự ưu tiên: dòng khớp đầu tiên thắng (layer "CUA_TUONG" là cửa).
Kiểm tra từng điều khoản trên một bản vẽ: drawing/convention_check.py; trang quan sát: drawing/concept_view.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .. import config

QU_FILE = config.DATA_DIR / "rules" / "quy_uoc.csv"
CONCEPTS_FILE = config.DATA_DIR / "rules" / "concepts.csv"
LAYER_ROLES = ("WALL", "OPENING", "ANNOTATION", "IGNORE")
OPENING_KINDS = ("door", "window")
BLOCK_ROLES = OPENING_KINDS + ("ANNOTATION", "IGNORE")   # block không phải cửa: cột, cao độ, trục, nội thất


@dataclass(frozen=True)
class Clause:
    """Một điều khoản của quy ước."""
    ma: str              # QU-01
    nhom: str            # Định dạng và đơn vị, Tường, Cửa...
    dieu_khoan: str
    muc: str             # B | K
    cach_kiem: str


@dataclass(frozen=True)
class Signal:
    """Một ký hiệu nhận dạng: tín hiệu trên bản vẽ (layer, block) -> khái niệm."""
    ma: str              # L01, B01
    khai_niem: str       # Tường, Cửa đi...
    qu: str              # điều khoản quy ước định nghĩa ký hiệu này
    tin_hieu: str        # layer | block
    mau: str             # layer: chuỗi con của tên đã bỏ dấu, chữ thường; block: tiền tố tên (D -> D1, D12)
    vai_tro: str         # layer: WALL | OPENING | ANNOTATION | IGNORE; block: door | window
    rong_mm: Optional[float] = None
    cao_mm: Optional[float] = None
    ghi_chu: str = ""


def _rows(table: str, path: str | None, default_csv: Path) -> list[dict]:
    """Bảng trong PostgreSQL khi có DATABASE_URL (thứ tự theo id), không thì file CSV."""
    from ..db.session import read_rule_table
    return read_rule_table(table, path, default_csv).to_dict("records")


def _num(v: str) -> Optional[float]:
    return float(v) if v and v.strip() else None


@lru_cache(maxsize=4)
def load_clauses(path: str | None = None) -> tuple[Clause, ...]:
    out = []
    for r in _rows("convention_clauses", path, QU_FILE):
        if r["muc"] not in ("B", "K"):
            raise ValueError(f"quy_uoc.csv, {r['ma']}: mức phải là B hoặc K, đang là {r['muc']!r}.")
        out.append(Clause(r["ma"], r["nhom"], r["dieu_khoan"], r["muc"], r["cach_kiem"]))
    return tuple(out)


@lru_cache(maxsize=4)
def load_signals(path: str | None = None) -> tuple[Signal, ...]:
    out = []
    for r in _rows("drawing_concepts", path, CONCEPTS_FILE):
        kind, role = r["tin_hieu"], r["vai_tro"]
        allowed = LAYER_ROLES if kind == "layer" else BLOCK_ROLES if kind == "block" else None
        if allowed is None:
            raise ValueError(f"concepts.csv, {r['ma']}: tín hiệu phải là layer hoặc block, đang là {kind!r}.")
        if role not in allowed:
            raise ValueError(f"concepts.csv, {r['ma']}: vai trò của {kind} phải là {' | '.join(allowed)}, đang là {role!r}.")
        out.append(Signal(r["ma"], r["khai_niem"], r["qu"], kind, r["mau"].strip(), role,
                          _num(r["rong_mm"]), _num(r["cao_mm"]), r["ghi_chu"]))
    return tuple(out)


def clause(ma: str) -> Clause:
    return next(c for c in load_clauses() if c.ma == ma)


def layer_signals() -> list[Signal]:
    return [s for s in load_signals() if s.tin_hieu == "layer"]


def match_layer(normalized: str) -> Optional[Signal]:
    """Ký hiệu layer đầu tiên khớp tên đã chuẩn hóa (bỏ dấu, chữ thường, _ và - đổi thành dấu cách)."""
    compact = normalized.replace(" ", "")
    for s in layer_signals():
        if s.mau in normalized or s.mau.replace(" ", "") in compact:
            return s
    return None


def block_signals() -> list[Signal]:
    return [s for s in load_signals() if s.tin_hieu == "block"]


def match_block_signal(name: str) -> Optional[Signal]:
    """Ký hiệu block bất kỳ (cửa, cột, cao độ, nội thất...): tên = tiền tố + số (D1, CS2). Tiền tố dài xét trước (CD trước D)."""
    for s in sorted(block_signals(), key=lambda s: -len(s.mau)):
        if re.fullmatch(rf"{re.escape(s.mau.upper())}\d*", name.upper()):
            return s
    return None


def match_block(name: str) -> Optional[Signal]:
    """Block cửa theo QU-14 (vai trò door | window); block khớp ký hiệu khác không phải cửa."""
    s = match_block_signal(name)
    return s if s and s.vai_tro in OPENING_KINDS else None

