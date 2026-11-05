"""Phần thô S4c: cầu thang."""
import math

import pytest

from optimat.rough.models import ProjectParams
from optimat.rough.stairs import Stair, stair_works


def test_two_flight_stair():
    s = Stair(steps=22, flight_width_mm=1000, tread_mm=250, landing_area_m2=2.0)
    works, warnings = stair_works("T1", [s], 3300, ProjectParams(stair_slab_thickness_mm=120))
    riser, slope = 3.3 / 22, math.hypot(22 * 0.25, 3.3)
    beton = next(w for w in works if w.code == "CAU_THANG")
    assert beton.quantity == pytest.approx(slope * 0.12 + 22 * 0.25 * riser / 2 + 2 * 0.12, abs=1e-3)
    cp = next(w for w in works if w.code == "COP_PHA")
    assert cp.quantity == pytest.approx(slope + 2.0 + 22 * riser, abs=1e-3)
    assert "giảng viên" in warnings[0]


def test_stair_missing_inputs():
    works, _ = stair_works("T1", [Stair(steps=20)], 3300, ProjectParams())
    assert works[0].quantity is None and set(works[0].missing) == {"bề rộng vế", "bề rộng bậc", "dày bản thang"}
