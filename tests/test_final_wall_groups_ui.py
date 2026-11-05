"""Cầu nối kết quả phần thô sang Giá/Tối ưu, không dùng TestClient hoặc database thật."""
from dataclasses import replace

import pytest
from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewWall, ReviewOpening
from optimat.rough.models import ProjectParams
from optimat.rough.walls import wall_works
from optimat.rough.wall_groups import final_wall_groups
from optimat.rough.takeoff import RoughRequest, PlanInput, compute_rough

@pytest.fixture(scope="module")
def catalog():
    return Catalog.from_csv(None)


def test_final_group_uses_final_quantity_and_selected_mortar(catalog):
    params = ProjectParams(beam_depth_mm=300, masonry_mortar_grade="M75")
    wall = ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    works, _ = wall_works("T1", 3400, [wall], [], params, catalog)
    work = next(w for w in works if w.code == "XAY")
    work.quantity -= 0.22  # phép trừ sau bước đo tường, ví dụ giằng
    groups, issues = final_wall_groups(works, params, catalog)
    assert not issues and len(groups) == 1
    assert groups[0].net_area_m2 == pytest.approx(work.quantity / 0.22)
    assert groups[0].design_material_id == "GN01"
    assert groups[0].design_mortar_material_id == "VU02"


def test_unresolved_opening_stops_price_group(catalog):
    wall = ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    params = ProjectParams(beam_depth_mm=300)
    works, _ = wall_works("T1", 3400, [wall], [ReviewOpening(id="O1", wall="W1", kind="door", w=900, h=None)], params, catalog)
    groups, issues = final_wall_groups(works, params, catalog)
    assert not groups and any("lỗ O1" in issue and "thiếu cao" in issue for issue in issues)


def test_rough_response_publishes_wall_groups(catalog):
    wall = ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    request = RoughRequest(params=ProjectParams(beam_depth_mm=300, masonry_mortar_grade="M75"),
                           plans=[PlanInput(name="T1", height_mm=3400, height_source="nhập tay", walls=[wall])])
    result = compute_rough(request, catalog)
    assert not result.wall_group_issues and len(result.wall_groups) == 1
    xay = next(w for w in result.works if w.code == "XAY")
    assert result.wall_groups[0].net_area_m2 == pytest.approx(xay.quantity / xay.masonry_geometry.thickness_m)
    assert result.model_dump()["wall_groups"][0]["design_material_id"] == "GN01"


def test_aac_grade_gap_keeps_known_work_and_blocks_partial_purchase(catalog):
    walls = [ReviewWall(id="A", cls="110", role="partition", x1=0, y1=0, x2=10000, y2=0, mat="AAC01"),
             ReviewWall(id="B", cls="220", role="envelope", x1=0, y1=5000, x2=10000, y2=5000, mat="GN01")]
    request = RoughRequest(plans=[PlanInput(name="T1", height_mm=3400, height_source="nhập tay", walls=walls)],
                           params=ProjectParams(beam_depth_mm=300), plan_scope_confirmed=True)
    before = compute_rough(request, catalog)
    assert not before.wall_group_issues and {g.design_material_id for g in before.wall_groups} == {"AAC01", "GN01"}
    result = compute_rough(request.model_copy(update={"params": ProjectParams(beam_depth_mm=300, masonry_mortar_grade="M75")}), catalog)
    assert not result.wall_groups and len(result.wall_group_issues) == 1
    assert all(t in result.wall_group_issues[0] for t in ("T1", "W-AAC01-100", "VU04", "M75"))
    def masonry(result):
        return [(w.wall_system_id, w.quantity, w.masonry_geometry) for w in result.works if w.code == "XAY"]
    assert masonry(result) == masonry(before)
    assert all(q and geom for _, q, geom in masonry(result))


@pytest.mark.parametrize("grade", ["M999", "M75/M100", "M75.5"])
def test_unresolved_design_grade_is_not_replaced(catalog, grade):
    params = ProjectParams(beam_depth_mm=300, masonry_mortar_grade=grade)
    wall = ReviewWall(id="B", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    works, _ = wall_works("T1", 3400, [wall], [], params, catalog)
    groups, issues = final_wall_groups(works, params, catalog)
    assert not groups and any(grade in issue and "W-GN01-220" in issue for issue in issues)


@pytest.mark.parametrize("rate,source,binder,grade,gap", [
    ("0", "Chỉ dẫn thử xác nhận định mức bằng 0", None, "M75", None),
    (0, None, None, "M75", "nguồn"),
    (None, None, None, None, "định mức"),
    (None, None, "VU02", "M75", "định mức"),
    (0.29, None, None, None, "liên kết"),
    (0.29, None, "VU99", "M75", "VU99"),
])
def test_binder_norm_zero_and_unknown_are_distinct(catalog, rate, source, binder, grade, gap):
    systems = catalog.wall_systems.copy()
    mask = systems.wall_system_id == "W-GN01-220"
    systems["mortar_m3_per_m3"] = systems.mortar_m3_per_m3.astype(object)
    systems.loc[mask, ["mortar_m3_per_m3", "norm_source", "norm_code", "mortar_material_id"]] = [rate, source, None, binder]
    amended = replace(catalog, wall_systems=systems)
    params = ProjectParams(beam_depth_mm=300, masonry_mortar_grade=grade)
    wall = ReviewWall(id="B", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    works, _ = wall_works("T1", 3400, [wall], [], params, amended)
    groups, issues = final_wall_groups(works, params, amended)
    if gap:
        assert not groups and any(gap in issue and "W-GN01-220" in issue for issue in issues)
    else:
        assert not issues and len(groups) == 1 and groups[0].design_mortar_material_id is None
