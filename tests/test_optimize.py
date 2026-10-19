import numpy as np

from optimat.catalog.repository import Catalog
from optimat.drawing.takeoff import takeoff_from_file
from optimat.optimize.problem import build_space, non_dominated, optimize, solve_brute_force, solve_nsga2
from optimat.schemas import Constraints


def _objs(result):
    return {(s.total_cost, s.supply_days, s.u_value) for s in result.solutions}


def test_non_dominated():
    pts = np.array([[1, 5, 1], [2, 4, 1], [2, 6, 2], [1, 5, 1.5]])
    assert non_dominated(pts).tolist() == [True, True, False, False]


def test_constraints_filter(sample_dxf):
    groups = takeoff_from_file(sample_dxf, 3300).groups
    cons = Constraints(max_vehicle_ton=2.5, excluded_materials=["CLAY_SOLID", "CLAY_HOLLOW"], budget=80e6)
    result = optimize(groups, cons, Catalog.load(), None, method="brute")
    assert result.solutions
    for s in result.solutions:
        assert s.total_cost <= 80e6
        for c in s.choices:
            assert not c.material_id.startswith("GN")
            assert c.wall_system_id and c.wall_system_id.startswith("W-")
            assert c.vehicle_id in ("VEH_1T25", "VEH_2T5")
            assert c.product_url.startswith("http")


def test_nsga2_matches_brute_force(sample_dxf):
    """Trên bài toán nhỏ, NSGA-II phải tìm lại được phần lớn tập Pareto chính xác của vét cạn."""
    groups = takeoff_from_file(sample_dxf, 3300).groups
    cons = Constraints()
    spaces, vehicles, _ = build_space(groups, cons, Catalog.load(), None)
    exact = _objs(solve_brute_force(spaces, vehicles, cons))
    found = _objs(solve_nsga2(spaces, vehicles, cons, seed=1))
    assert found <= exact, "NSGA-II trả về điểm không thuộc tập Pareto chính xác"
    assert len(found) >= 0.8 * len(exact)


def test_labor_rate_from_table(sample_dxf):
    """Đơn giá nhân công lấy từ bảng labor_rates; bảng trống thì không điền số mặc định, chi phí nhân công = 0 kèm ghi chú."""
    import pandas as pd
    cat = Catalog.load()
    rate, _ = cat.labor_rate("Hà Nội")
    assert rate == 350000
    assert cat.labor_rate("Hải Phòng")[0] is None
    groups = takeoff_from_file(sample_dxf, 3300).groups
    cat.labor_rates = cat.labor_rates.iloc[0:0]
    result = optimize(groups, Constraints(max_vehicle_ton=2.5), cat, None, method="brute")
    assert any("Chưa có đơn giá nhân công" in n for n in result.notes)
    assert all(c.install_cost == 0 for s in result.solutions for c in s.choices)
    cat.labor_rates = pd.DataFrame([{"province": "A", "grade": "3/7", "rate_per_day": 1, "valid_from": None},
                                    {"province": "B", "grade": "3/7", "rate_per_day": 2, "valid_from": None}])
    assert cat.labor_rate()[0] is None and cat.labor_rate("B")[0] == 2


def test_wall_families_from_catalog():
    fams = Catalog.load().wall_families()
    assert list(fams)[0] == "CLAY_SOLID" and "AAC" in fams
