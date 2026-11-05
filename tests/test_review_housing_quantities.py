import importlib.util
import shutil
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


def test_regeneration_keeps_metadata_driven_quarantine_and_source(tmp_path, monkeypatch):
    original_out = module.OUT
    for p in original_out.glob('*.json'):
        shutil.copyfile(p, tmp_path / p.name)
    # Read CAD evidence from the existing report directory, but write receipts in isolation.
    original_report = module.REPORT
    for p in original_report.glob('*_ket_cau_text.json'):
        shutil.copyfile(p, tmp_path / p.name)
    monkeypatch.setattr(module, 'OUT', tmp_path)
    monkeypatch.setattr(module, 'REPORT', tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.glob('*.estimate.json')}
    receipts = module.build()
    module.build()
    assert sum(r['eligible_schedule_labels'] for r in receipts) == 9
    assert sum(r['quarantined'] for r in receipts) == 455
    for cid, work in [('nha_huong_hai_duong_7x12', 'W005'), ('nha_sang_hai_duong_4x15', 'W007')]:
        review = module.read(tmp_path / f'{cid}.quality_review.json')
        row = next(r for r in review['rows'] if r['work_id'].endswith(work))
        assert row['status'] == 'quarantined_inconsistent_schedule'
        assert row['eligible_label_id'] is None and row['blocking_issue_ids']
        assert row['arithmetic_status'] == 'inconsistent_schedule'
        data = module.read(tmp_path / f'{cid}.verified_quantities.json')
        assert data['human_approval'] is False
        assert not data['labels'][0]['eligible_for_development_comparison']
    assert all((tmp_path/name).read_bytes() == value for name, value in before.items())


def test_gate_uses_issue_type_and_status_not_case_names():
    assert module.blocking_issues([dict(issue_type='source_schedule_mismatch', status='reviewed_unresolved')]) == []
    issue = dict(id='any-case', issue_type='internal_schedule_arithmetic_conflict', status='reviewed_unresolved')
    assert module.blocking_issues([issue]) == [issue]
