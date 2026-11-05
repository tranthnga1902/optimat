import pytest
from pydantic import ValidationError

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewOpening, ReviewPlan, ReviewWall, compute_review
from optimat.rough.takeoff import PlanInput, RoughRequest


def test_coordinates_round_trip_through_confirm_and_rough_inputs():
    wall = ReviewWall(id='W', cls='110', x1=0, y1=0, x2=3000, y2=0)
    source = {'id': 'O', 'wall': 'W', 'w': None, 'h': 2000, 'x': -125.5, 'y': 0, 'keep': True}
    plan = ReviewPlan(file='a.dxf', plan='T1', height_mm=3000, walls=[wall], openings=[source])
    snapshot = plan.model_dump(mode='json')
    assert snapshot['openings'][0]['x'] == -125.5 and snapshot['openings'][0]['y'] == 0
    assert ReviewPlan.model_validate(snapshot).openings[0].model_dump() == plan.openings[0].model_dump()
    partial = compute_review(plan, Catalog.from_csv())
    assert partial.pending_openings[0].x == -125.5 and partial.pending_openings[0].y == 0
    rough = RoughRequest(plans=[PlanInput(name='T1', height_mm=3000, walls=[wall], openings=[source])])
    restored = RoughRequest.model_validate(rough.model_dump(mode='json'))
    assert restored.plans[0].openings[0].x == -125.5 and restored.plans[0].openings[0].y == 0


def test_legacy_missing_coordinates_stay_unknown_not_zero():
    opening = ReviewOpening(id='O', wall='W', w=900, h=2000)
    assert opening.x is None and opening.y is None
    restored = ReviewOpening.model_validate(opening.model_dump(mode='json'))
    assert restored.x is None and restored.y is None
    assert ReviewOpening(id='O', wall='W', x=0, y=None).x == 0


@pytest.mark.parametrize('axis', ['x', 'y'])
@pytest.mark.parametrize('value', [float('nan'), float('inf'), float('-inf'), 'bad', '12'])
def test_non_finite_or_string_coordinates_rejected(axis, value):
    with pytest.raises(ValidationError):
        ReviewOpening.model_validate({'id': 'O', axis: value})
