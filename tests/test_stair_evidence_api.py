from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from optimat.api import project_analysis as api
from optimat.api.stair_evidence import StairEvidenceRequest, stair_from_evidence


def test_stair_draft_preserves_source_and_blocks_other_projects(monkeypatch):
    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    source = {'file_id': 9, 'revision_id': 11, 'sha256': 'b' * 64, 'role': 'KC'}
    payload = {'profile_version': 3, 'stair_id': 'thang-1', 'parts': [
        {'part_id': 'scope', 'kind': 'stair', 'facts': [
            {'field': 'from_floor', 'value': 'T1', 'source': source, 'location': {'page': 5}},
            {'field': 'to_floor', 'value': 'T2', 'source': source, 'location': {'page': 5}}]},
        {'part_id': 've-a', 'kind': 'flight', 'facts': [
            {'field': 'waist_thickness_mm', 'value': 110, 'source': source, 'location': {'page': 5}},
            {'field': 'run_mm', 'value': None}, {'field': 'rise_mm', 'value': None}]},
        {'part_id': 'nghi', 'kind': 'landing', 'facts': [
            {'field': 'ownership', 'value': 'unknown', 'source': source, 'location': {'page': 5}}]},
        {'part_id': 'bac', 'kind': 'steps', 'facts': [
            {'field': 'steps_material', 'value': 'masonry', 'source': source, 'location': {'handle': 'ABC'}}]}]}
    body = StairEvidenceRequest.model_validate(payload)
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api.project_files, '_user', lambda user: 2)
    def owned(db, project_id, uid):
        if project_id != 7:
            raise HTTPException(404, 'Không tìm thấy dự án.')
    monkeypatch.setattr(api.project_files, '_project', owned)
    monkeypatch.setattr(api.project_files, '_latest_profile', lambda db, project_id:
                        SimpleNamespace(version=3, payload={'selected_revisions': [source]}))
    verified = []
    monkeypatch.setattr(api.project_files, '_check_selection', lambda db, project_id, selected, verify_bytes:
                        verified.append((project_id, selected.revision_id, verify_bytes)))
    result = api.validate_stair_evidence(7, body, {'user_id': 2})
    assert result['status'] == 'user_selected_unreviewed' and not result['saved']
    assert result['parts'][0]['facts'][0]['source'] == source
    assert result['parts'][1]['facts'][1]['value'] is None
    assert result['parts'][2]['facts'][0]['value'] == 'unknown'
    assert result['parts'][3]['facts'][0]['value'] == 'masonry'
    stair = result['stair']
    assert stair['id'] == 'thang-1' and stair['from_floor'] == 'T1' and stair['to_floor'] == 'T2'
    assert stair['flights'][0]['waist_thickness_mm'] == 110 and stair['flights'][0]['run_mm'] is None
    assert stair['landings'][0]['ownership'] == 'unknown' and stair['steps_material'] == 'masonry'
    assert 'revision_id=11' in stair['flights'][0]['field_sources']['waist_thickness_mm']
    assert 'chưa kiểm' in stair['steps_material_source']
    changed = body.model_copy(update={'parts': [body.parts[0], body.parts[2]]})
    cleared = api.validate_stair_evidence(7, changed, {'user_id': 2})['stair']
    assert cleared['flights'] is None and cleared['steps_material'] == 'unknown'
    assert verified == [(7, 11, True), (7, 11, True)]
    with pytest.raises(HTTPException) as err:
        api.validate_stair_evidence(8, body, {'user_id': 2})
    assert err.value.status_code == 404
    with pytest.raises(HTTPException) as err:
        api.validate_stair_evidence(7, body.model_copy(update={'profile_version': 2}), {'user_id': 2})
    assert err.value.status_code == 409
    monkeypatch.setattr(api.project_files, '_latest_profile', lambda db, project_id:
                        SimpleNamespace(version=3, payload={'selected_revisions': []}))
    with pytest.raises(HTTPException) as err:
        api.validate_stair_evidence(7, body, {'user_id': 2})
    assert err.value.status_code == 409


def test_stair_fact_requires_source_and_separate_parts():
    with pytest.raises(ValidationError):
        StairEvidenceRequest.model_validate({'profile_version': 1, 'stair_id': 'x', 'parts': [
            {'part_id': 'v', 'kind': 'flight', 'facts': [{'field': 'waist_thickness_mm', 'value': 110}]}]})
    with pytest.raises(ValidationError):
        StairEvidenceRequest.model_validate({'profile_version': 1, 'stair_id': 'x', 'parts': [
            {'part_id': 'v', 'kind': 'flight', 'facts': [{'field': 'steps_material', 'value': None}]}]})


def test_sourced_draft_to_real_rough_partial_and_material_conflict():
    from optimat.catalog.repository import Catalog
    from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough
    source = {'file_id': 9, 'revision_id': 11, 'sha256': 'b' * 64, 'role': 'KC'}
    def fact(field, value):
        return {'field': field, 'value': value, 'source': source, 'location': {'page': 5}}
    body = StairEvidenceRequest.model_validate({'profile_version': 3, 'stair_id': 'S1', 'parts': [
        {'part_id': 'scope', 'kind': 'stair', 'facts': [fact('from_floor', 'T1'), fact('to_floor', 'T2'),
                                                       fact('steps_material', 'masonry')]},
        {'part_id': 'V1', 'kind': 'flight', 'facts': [fact('run_mm', 3000), fact('rise_mm', 1000),
            fact('width_mm', 1000), fact('waist_thickness_mm', 120), fact('thickness_basis', 'normal')]},
        {'part_id': 'L1', 'kind': 'landing', 'facts': [fact('area_m2', 1.5), fact('thickness_mm', 150)]}]})
    model, unmapped = stair_from_evidence(body)
    assert not unmapped
    req = RoughRequest(plans=[PlanInput(name='T1', height_mm=None, walls=[], stairs=[model])])
    result = compute_rough(req, Catalog.from_csv())
    work = next(w for w in result.works if w.code == 'CAU_THANG')
    rows = work.quantity_detail.rows
    waist = next(r for r in rows if r.row_id == 'V1:waist')
    steps = next(r for r in rows if r.row_id == 'V1:steps')
    landing = next(r for r in rows if r.row_id == 'L1:landing')
    assert float(waist.raw_quantity) == pytest.approx((10 ** 0.5) * .12)
    assert steps.role == 'reference' and float(steps.raw_quantity) == 0
    assert landing.raw_quantity is None and not work.quantity_detail.complete
    assert any('revision_id=11' in text for text in waist.sources)
    form = next(w for w in result.works if w.code == 'COP_PHA' and w.formwork_of == 'CAU_THANG')
    assert not form.quantity_detail.complete
    conflict = body.model_dump()
    conflict['parts'].append({'part_id': 'bac-2', 'kind': 'steps', 'facts': [fact('steps_material', 'concrete')]})
    changed, unmapped = stair_from_evidence(StairEvidenceRequest.model_validate(conflict))
    assert changed['steps_material'] == 'unknown' and unmapped
    missing = body.model_dump()
    missing['parts'][1]['facts'] = [x for x in missing['parts'][1]['facts'] if x['field'] != 'rise_mm']
    changed, _ = stair_from_evidence(StairEvidenceRequest.model_validate(missing))
    incomplete = compute_rough(RoughRequest(plans=[PlanInput(name='T1', height_mm=None, walls=[], stairs=[changed])]), Catalog.from_csv())
    row = next(r for w in incomplete.works if w.code == 'CAU_THANG' for r in w.quantity_detail.rows if r.row_id == 'V1:waist')
    assert row.raw_quantity is None
