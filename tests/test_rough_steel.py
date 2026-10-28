"""Phần thô S5a, S5b: cốt thép theo hàm lượng hoặc bảng thép, móng nhập tay."""
import pytest

from optimat.rough.models import WORKS, FoundationItem, ProjectParams, WorkItem
from optimat.rough.foundations import foundation_works
from optimat.rough.steel import steel_works


def work(code, qty, plan="T1"):
    return WorkItem(code=code, name=WORKS[code][0], unit=WORKS[code][1], quantity=qty, plan=plan)


def test_steel_by_ratio_per_element():
    works = [work("COT", 2.0), work("COT", 1.0, "T2"), work("DAM", 3.0), work("SAN", None)]
    out, _ = steel_works(works, ProjectParams(steel_kg_per_m3={"COT": 150, "SAN": 90}))
    t1 = next(w for w in out if w.steel_element == "COT" and w.plan == "T1")
    assert t1.quantity == pytest.approx(0.3)
    dam = next(w for w in out if w.steel_element == "DAM")
    assert dam.quantity is None and "hàm lượng thép dầm (kg/m³)" in dam.missing
    san = next(w for w in out if w.steel_element == "SAN")
    assert san.quantity is None and "khối lượng bê tông sàn" in san.missing


def test_steel_schedule_wins():
    out, _ = steel_works([work("COT", 2.0)], ProjectParams(steel_kg_per_m3={"COT": 150}, steel_schedule_t={"COT": 0.42}))
    assert len(out) == 1 and out[0].quantity == 0.42 and out[0].source == "manual"


def test_foundation_manual():
    p = ProjectParams(foundations=[FoundationItem(name="M1", count=6, length_mm=1200, width_mm=1200, height_mm=400,
                                                  lean_thickness_mm=100),
                                   FoundationItem(name="MB", volume_m3=3.5)])
    out, warnings = foundation_works(p)
    mong = [w for w in out if w.code == "MONG"]
    assert mong[0].quantity == pytest.approx(6 * 1.2 * 1.2 * 0.4, abs=1e-3) and mong[1].quantity == 3.5
    assert next(w for w in out if w.code == "BE_TONG_LOT").quantity == pytest.approx(6 * 1.44 * 0.1, abs=1e-3)
    assert next(w for w in out if w.code == "COP_PHA").quantity == pytest.approx(6 * 2 * 2.4 * 0.4, abs=1e-3)
    assert any("MB" in w for w in warnings)
