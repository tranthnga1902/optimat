import pytest

from optimat.catalog.pricing import bill_of_materials
from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewOpening, ReviewWall
from optimat.rough.models import ProjectParams
from optimat.rough.secondary import LinearMember
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough


@pytest.fixture(scope="module")
def catalog():
    return Catalog.from_csv()


def floor(name="Tầng 1", **kwargs):
    wall = ReviewWall(id="W1", cls="110", role="partition", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    return PlanInput(name=name, walls=[wall], height_mm=kwargs.pop("height_mm", 3300), **kwargs)


def rough(plans, catalog, **kwargs):
    return compute_rough(RoughRequest(plans=plans, plan_scope_confirmed=True,
                                      params=ProjectParams(beam_depth_mm=300, **kwargs)), catalog)


def test_bill_uses_built_masonry_volume_and_ae_waste(catalog):
    r = rough([floor()], catalog)
    xay = next(w for w in r.works if w.code == "XAY")
    assert r.plan_scope_confirmed and not r.wall_group_issues
    assert xay.quantity == 3.15 and r.wall_groups[0].net_area_m2 == pytest.approx(30)
    brick = next(b for b in bill_of_materials(r.wall_groups, catalog, actual_only=True) if b.kind == "main")
    purchased = next(m for m in r.materials if m.material_id == brick.material_id)
    assert brick.quantity == pytest.approx(purchased.quantity_with_waste, abs=0.001)


def test_final_tie_deduction_reaches_procurement(catalog):
    tie = LinearMember(id="G1", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0, b_mm=105, d_mm=150, z_bottom_mm=1000)
    r = rough([floor(members=[tie])], catalog)
    assert not r.wall_group_issues and r.wall_groups[0].net_area_m2 == pytest.approx(29.4)
    unknown = tie.model_copy(update={"d_mm": None})
    partial = rough([floor(members=[unknown]), floor("Tầng 2")], catalog)
    assert next(w for w in partial.works if w.code == "XAY").status == "D"
    assert not partial.wall_groups and partial.wall_group_issues


def test_counted_plans_with_same_title_and_incomplete_floor(catalog):
    result = rough([floor(), floor()], catalog)
    assert result.wall_groups[0].net_area_m2 == pytest.approx(60)
    incomplete = rough([floor(), floor("Tầng 2", height_mm=None)], catalog)
    assert not incomplete.wall_groups and any("Tầng 2" in i for i in incomplete.wall_group_issues)


def test_kept_opening_must_be_assigned_to_a_wall(catalog):
    opening = ReviewOpening(id="O1", wall=None, w=900, h=2100)
    assert rough([floor(openings=[opening])], catalog).wall_group_issues
    removed = opening.model_copy(update={"keep": False})
    assert not rough([floor(openings=[removed])], catalog).wall_group_issues


def test_zero_and_unknown_masonry_are_different(catalog):
    from optimat.rough.wall_groups import final_wall_groups
    result = rough([floor()], catalog)
    w = next(item for item in result.works if item.code == "XAY")
    assert final_wall_groups([w.model_copy(update={"quantity": 0})], ProjectParams(), catalog) == ([], [])
    for invalid in (None, -1, float("nan")):
        groups, issues = final_wall_groups([w.model_copy(update={"quantity": invalid})], ProjectParams(), catalog)
        assert not groups and issues


def test_omitted_beam_depth_requires_confirmation(catalog):
    req = RoughRequest(plans=[floor()], plan_scope_confirmed=True)
    incomplete = compute_rough(req, catalog)
    assert not incomplete.wall_groups and any("dầm" in issue for issue in incomplete.wall_group_issues)
    explicit = compute_rough(req.model_copy(update={"params": ProjectParams(beam_depth_mm=0)}), catalog)
    assert explicit.wall_groups[0].net_area_m2 == pytest.approx(33)
