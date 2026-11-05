import pytest
from pydantic import ValidationError

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewOpening, ReviewPlan, ReviewWall, compute_review
from optimat.rough.checks import envelope_by_orientation
from optimat.rough.models import ProjectParams
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough


def test_partial_opening_keeps_id_and_does_not_block_other_wall_group():
    walls = [ReviewWall(id='A', cls='110', x1=0, y1=0, x2=4000, y2=0),
             ReviewWall(id='B', cls='220', x1=0, y1=1000, x2=4000, y2=1000)]
    openings = [ReviewOpening(id='known', wall='A', w=800, h=2000),
                ReviewOpening(id='missing', wall='A', w=None, h=2000),
                ReviewOpening(id='removed', wall='B', w=None, h=None, keep=False)]
    params = ProjectParams(beam_depth_mm=0, lintel_height_mm=100, lintel_bearing_mm=100,
                           plaster_thickness_mm=15)
    request = RoughRequest(plans=[PlanInput(name='T1', height_mm=3000, walls=walls, openings=openings)], params=params)
    result = compute_rough(request, Catalog.from_csv())
    xay = [work for work in result.works if work.code == 'XAY']
    affected = next(work for work in xay if '110' in work.element)
    independent = next(work for work in xay if '220' in work.element)
    assert affected.quantity is None and any('missing' in m and 'rộng mm' in m for m in affected.missing)
    assert independent.quantity is not None and not any('removed' in m for m in independent.missing)
    assert next(w for w in result.works if w.code == 'LANH_TO').quantity is None
    assert next(w for w in result.works if w.code == 'TRAT' and '110' in w.element).quantity is None
    assert next(w for w in result.works if w.code == 'TRAT' and '220' in w.element).quantity is not None
    assert request.plans[0].openings[1].id == 'missing' and request.plans[0].openings[1].wall == 'A'
    plan = ReviewPlan(file='test.dxf', plan='T1', height_mm=3000, walls=walls, openings=openings)
    partial = compute_review(plan, Catalog.from_csv())
    assert not partial.complete and partial.total_net_area_m2 is None and partial.bill_total is None
    assert [group.wall_type for group in partial.groups] == ['220']
    assert partial.known_net_area_m2 == partial.groups[0].net_area_m2
    assert partial.pending_groups[0].net_area_m2 is None and partial.pending_groups[0].opening_ids == ['missing']
    assert partial.pending_openings[0].id == 'missing' and partial.pending_openings[0].wall == 'A'
    assert all(o.id != 'removed' for o in partial.pending_openings)
    assert envelope_by_orientation([walls[0].model_copy(update={'role': 'envelope'})], openings, 3000, 0) == {}


def test_missing_height_keeps_width_but_blocks_dependent_deductions():
    wall = ReviewWall(id='A', cls='110', x1=0, y1=0, x2=4000, y2=0)
    opening = ReviewOpening(id='O2', wall='A', w=900, h=None)
    request = RoughRequest(plans=[PlanInput(name='T2', height_mm=3000, walls=[wall], openings=[opening])],
                           params=ProjectParams(beam_depth_mm=0, lintel_height_mm=100, lintel_bearing_mm=100))
    result = compute_rough(request, Catalog.from_csv())
    for work in result.works:
        if work.code in ('XAY', 'TRAT'):
            assert work.quantity is None and any('O2' in m and 'cao mm' in m for m in work.missing)
    assert next(w for w in result.works if w.code == 'LANH_TO').quantity is not None
    assert next(w for w in result.works if w.code == 'COP_PHA' and w.formwork_of == 'LANH_TO').quantity is not None
    assert any('chưa đối chiếu giao dầm' in w for w in result.warnings)
    assert request.plans[0].openings[0].w == 900


def test_orphan_opening_leaves_only_its_plan_pending():
    wall = ReviewWall(id='A', cls='110', x1=0, y1=0, x2=4000, y2=0)
    missing_parent = ReviewOpening(id='O3', wall=None, w=900, h=2000)
    params = ProjectParams(beam_depth_mm=0, lintel_height_mm=100, lintel_bearing_mm=100)
    request = RoughRequest(plans=[PlanInput(name='T1', height_mm=3000, walls=[wall], openings=[missing_parent]),
                                  PlanInput(name='T2', height_mm=3000, walls=[wall], openings=[])], params=params)
    result = compute_rough(request, Catalog.from_csv())
    affected = next(w for w in result.works if w.code == 'XAY' and w.plan == 'T1')
    independent = next(w for w in result.works if w.code == 'XAY' and w.plan == 'T2')
    assert affected.quantity is None and any('O3' in m for m in affected.missing)
    assert independent.quantity is not None
    assert next(w for w in result.works if w.code == 'LANH_TO' and w.plan == 'T1').quantity is None
    assert not result.wall_groups and any('chưa gán tường' in i for i in result.wall_group_issues)


def test_review_complete_and_unassigned_are_not_misrepresented():
    wall = ReviewWall(id='A', cls='110', x1=0, y1=0, x2=4000, y2=0)
    valid = ReviewOpening(id='O1', wall='A', w=1000, h=2000)
    plan = ReviewPlan(file='x', plan='T1', height_mm=3000, walls=[wall], openings=[valid])
    result = compute_review(plan, Catalog.from_csv())
    assert result.complete and result.total_net_area_m2 == 10 and result.pending_groups == []
    unassigned = ReviewOpening(id='O2', wall=None, w=800, h=2000)
    partial = compute_review(plan.model_copy(update={'openings': [valid, unassigned]}), Catalog.from_csv())
    assert not partial.complete and partial.total_net_area_m2 is None
    assert partial.pending_openings[0].id == 'O2' and partial.pending_openings[0].wall is None


@pytest.mark.parametrize('width,height', [(900, 2000), (None, 2000), (900, None), (None, None)])
def test_non_masonry_parent_preserves_opening_without_blocking_masonry(width, height):
    walls = [ReviewWall(id='A', cls='110', x1=0, y1=0, x2=3000, y2=0),
             ReviewWall(id='B', cls='220', x1=0, y1=1000, x2=3000, y2=1000, masonry=False)]
    opening = ReviewOpening(id='O-B', wall='B', w=width, h=height)
    plan = ReviewPlan(file='x', plan='T1', height_mm=3000, walls=walls, openings=[opening])
    result = compute_review(plan, Catalog.from_csv())
    assert result.complete and result.total_net_area_m2 == 9 and result.pending_groups == []
    assert result.pending_openings == [] and result.outside_masonry_openings[0].model_dump() == opening.model_dump()
    assert any('O-B' in w and 'không áp dụng khối xây' in w for w in result.warnings)
    assert plan.model_dump()['openings'][0]['wall'] == 'B'
    removed = plan.model_copy(update={'walls': [walls[0], walls[1].model_copy(update={'keep': False})]})
    pending = compute_review(removed, Catalog.from_csv())
    assert not pending.complete and pending.total_net_area_m2 is None
    assert pending.pending_openings[0].id == 'O-B' and pending.outside_masonry_openings == []
    independent = compute_review(ReviewPlan(file='x', plan='T2', height_mm=3000,
                                             walls=[walls[0]], openings=[]), Catalog.from_csv())
    assert independent.complete and independent.total_net_area_m2 == 9


@pytest.mark.parametrize('field', ['w', 'h'])
@pytest.mark.parametrize('value', ['bad', '100', 0, -1, float('nan'), float('inf'), float('-inf')])
def test_invalid_dimensions_are_rejected(field, value):
    args = {'id': 'O', 'wall': 'A', 'w': 1000, 'h': 2000}
    args[field] = value
    with pytest.raises(ValidationError):
        ReviewOpening(**args)
