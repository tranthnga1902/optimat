import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('review_housing', Path(__file__).parents[1] / 'scripts/review_housing_quantities.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_uppercase_cad_diameter_and_comma_decimal():
    assert module.steel_cell({'handle': 'x', 'raw': '%%C16 : 92,9'}) == (16, 92.9)


def test_bm2_net_allocation_matches_independent_rectangle_union():
    result = module.foundation_overlap()
    assert result['union_area_m2'] == 47.172
    assert result['bm2_net_length_m'] == 4.89
    assert result['bottom_layer_volume_m3'] == 11.793


def test_review_labels_remain_separate_from_original_and_gate_pending_rows():
    out = module.OUT
    for cid, expected, count in [('nha_huong_hai_duong_7x12', 1.9285, 215),
                                  ('nha_sang_hai_duong_4x15', 2.9012, 249)]:
        dataset = module.read(out / f'{cid}.verified_quantities.json')
        review = module.read(out / f'{cid}.quality_review.json')
        assert dataset['labels'][0]['quantity'] == expected
        assert dataset['labels'][0]['source_quantity'] != expected
        assert dataset['human_approval'] is False
        assert not dataset['is_complete_ground_truth']
        assert len(review['rows']) == count
        assert all(r['eligible_label_id'] is None for r in review['rows'] if r['status'].startswith('quarantined'))
    huong = module.read(out / 'nha_huong_hai_duong_7x12.verified_quantities.json')
    assert huong['labels'][-1]['components'][-1]['diameter_mm'] == 16
