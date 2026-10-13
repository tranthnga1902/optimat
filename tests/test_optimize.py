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
