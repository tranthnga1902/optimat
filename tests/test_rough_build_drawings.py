"""Phần thô trên bản vẽ thật nhóm build (data/drawings/build, không vào git). Bỏ qua khi máy không có file."""
from pathlib import Path

import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.dxf_reader import read_drawing
from optimat.rough.takeoff import compute_rough, rough_from_drawing

BUILD = Path(__file__).resolve().parents[1] / "data/drawings/build"


def _need(name: str) -> Path:
    path = BUILD / name
    if not path.exists():
        pytest.skip(f"không có {path.name}")
    return path


def test_nha_dan_columns_and_rough():
    req = rough_from_drawing(read_drawing(str(_need("nha_dan.dxf"))))
    assert [p.is_ground for p in req.plans] == [True, False, False]
    # cột 200×200, đếm trên bản vẽ 17/10/2026; lầu 1 có thêm cột (-82340, 120157) vẽ bằng SOLID lật, trước đọc sai chỗ
    assert [len(p.columns) for p in req.plans] == [10, 10, 12]
    assert {(c.b_mm, c.h_mm) for p in req.plans for c in p.columns} == {(200, 200)}
    res = compute_rough(req, Catalog.from_csv(None))
    assert next(t for t in res.totals if t.code == "XAY").quantity > 20


def test_nha_pho_columns():
    req = rough_from_drawing(read_drawing(str(_need("nha_pho.dxf"))))
    assert req.plans[0].is_ground and len(req.plans) == 4
    assert all(5 <= len(p.columns) <= 8 for p in req.plans)
