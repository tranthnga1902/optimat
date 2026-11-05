import json
import hashlib
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient

from optimat.api import project_analysis as api
from optimat.api.project_files import ProfilePayload, StoredAnalysisFile


def test_document_candidates_reads_revision_without_cross_project_access(tmp_path, monkeypatch):
    from openpyxl import Workbook
    path = tmp_path / 'estimate.xlsx'
    book = Workbook()
    sheet = book.active
    sheet.title = 'Tiên lượng'
    sheet.append(['Tên công tác', 'Đơn vị', 'Khối lượng', 'Đơn giá'])
    sheet.append(['Bê tông lót móng', 'm3', 3.25, 1100000])
    sheet.append(['Cấu kiện DC-1', 'm3', 0.32, None])
    book.save(path)
    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    rev = SimpleNamespace(role='TIEN_LUONG', format='xlsx', sha256=source_hash)
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    async def run_inline(fn, *args):
        return fn(*args)
    monkeypatch.setattr(api, 'run_in_threadpool', run_inline)
    monkeypatch.setattr(api.project_files, '_user', lambda user: 42)
    def owned(db, project_id, uid):
        if project_id != 7:
            raise HTTPException(404, 'Không tìm thấy dự án.')
    monkeypatch.setattr(api.project_files, '_project', owned)
    monkeypatch.setattr(api.project_files, '_revision', lambda db, project_id, file_id, revision_id:
                        (SimpleNamespace(filename='estimate.xlsx'), rev))
    monkeypatch.setattr(api.project_files, '_verified_path', lambda revision: path)
    result = asyncio.run(api.document_candidates(7, 9, 11, 1, {'user_id': 42}))
    first, second = result['candidates']
    assert first['fields'] == {'work': 'Bê tông lót móng', 'unit': 'm3', 'quantity': '3.25', 'unit_price': '1100000'}
    assert first['source']['cells']['quantity'] == 'C2' and first['source']['sheet'] == 'Tiên lượng'
    assert first['source']['project_id'] == 7 and first['source']['revision_id'] == 11
    assert first['source']['sha256'] == source_hash and first['price_kind'] == 'estimate_reference'
    assert second['fields']['quantity'] == '0.32' and len(result['candidates']) == 2
    assert result['cached_values_only'] and 'chưa xác nhận' in result['notice']
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api.document_candidates(8, 9, 11, 1, {'user_id': 42}))
    assert exc.value.status_code == 404
    rev.format = 'pdf'
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api.document_candidates(7, 9, 11, 1, {'user_id': 42}))
    assert exc.value.status_code == 422


def test_uses_only_versioned_dimensions():
    profile = ProfilePayload.model_validate({
        'effective_values': {'floor_height_mm': 'h', 'door_width_mm': 'd', 'floors': 'n'},
        'source_values': {'h': {'source': 'manual', 'unit': 'mm', 'value': 3330},
                          'd': {'source': 'manual', 'unit': 'mm', 'value': 840},
                          'n': {'source': 'manual', 'unit': 'tầng', 'value': 3}}})
    height, doors = api._dimensions(profile)
    assert height == 3330 and doors.door_width_mm == 840 and doors.window_width_mm is None
    assert api._dimensions(ProfilePayload()) == (None, None)
    profile.source_values['h'].unit = 'm'
    with pytest.raises(HTTPException) as exc:
        api._dimensions(profile)
    assert exc.value.status_code == 422


def test_structural_column_source_is_bound_only_when_unique():
    kc = {'file_id': 3, 'revision_id': 4, 'sha256': 'b' * 64, 'role': 'KC'}
    other = {'file_id': 5, 'revision_id': 6, 'sha256': 'c' * 64, 'role': 'KC'}
    original = {'structural_columns': [{'instance_id': 'x', 'code': 'C-2', 'file': '', 'evidence': ['trục 4/A']}]}
    result = api._column_sources(original, [('kc.dxf', kc, 'uploads/one.dxf')])
    col = result['structural_columns'][0]
    assert col['file'] == 'kc.dxf' and col['evidence'][0] == 'trục 4/A'
    assert 'file_id=3; revision_id=4; sha256=' + 'b' * 64 in col['evidence'][1]
    assert original['structural_columns'][0]['file'] == ''
    assert 'matched_column_id' not in col and 'grid_x' not in col
    unresolved = api._column_sources(original, [('kc.dxf', kc, 'uploads/one.dxf'), ('other.dxf', other, 'uploads/two.dxf')])
    assert unresolved['structural_columns'][0] == original['structural_columns'][0]
    assert unresolved['notes']
    named = {'structural_columns': [{'instance_id': 'y', 'code': 'C-2', 'file': 'other.dxf', 'evidence': []}]}
    assert 'file_id=5' in api._column_sources(named, [('kc.dxf', kc, 'uploads/one.dxf'), ('other.dxf', other, 'uploads/two.dxf')])['structural_columns'][0]['evidence'][0]
    stored = {'structural_columns': [{'instance_id': 'z', 'code': 'C-2', 'file': 'uploads/two.dxf', 'evidence': []}]}
    assert 'file_id=5' in api._column_sources(stored, [('kc.dxf', kc, 'uploads/one.dxf'), ('other.dxf', other, 'uploads/two.dxf')])['structural_columns'][0]['evidence'][0]
    duplicate = api._column_sources(named, [('other.dxf', kc, 'uploads/one.dxf'), ('other.dxf', other, 'uploads/two.dxf')])
    assert duplicate['structural_columns'][0]['evidence'] == [] and duplicate['notes']
    assert 'file_id=1' not in col['evidence'][1]


def test_structural_column_fields_round_trip_without_assigning_slab():
    from optimat.rough.structural_column_instances import StructuralColumnInstance
    source = {'file_id': 3, 'revision_id': 4, 'sha256': 'b' * 64, 'role': 'KC'}
    instance = StructuralColumnInstance.model_validate({
        'instance_id': 'example', 'code': 'C-9', 'file': 'stored.dxf', 'source_sha256': 'b' * 64,
        'missing': ['chưa gắn ô sàn'], 'top_slab_candidates': [{
            'thickness_mm': 140, 'level_mm': 4200, 'floor_key': 'T2', 'handles': ['ABC'],
            'evidence': ['nguồn thử'], 'region_confirmed': False}]})
    parts = api._column_sources({'structural_columns': [instance]}, [('kc.dxf', source, 'stored.dxf')])
    event = json.loads(next(api._stream(iter([{'type': 'complete', 'data': parts}]))))
    col = event['data']['structural_columns'][0]
    assert col['source_sha256'] == source['sha256'] and col['missing'] == ['chưa gắn ô sàn']
    assert col['top_slab_candidates'] == [instance.top_slab_candidates[0].model_dump()]
    assert col['top_slab_thickness_mm'] is None and col['top_slab_source'] is None
    assert col['matched_plan'] is None and col['matched_column_id'] is None
    bad = instance.model_copy(update={'source_sha256': 'c' * 64})
    unresolved = api._column_sources({'structural_columns': [bad]}, [('kc.dxf', source, 'stored.dxf')])
    assert unresolved['structural_columns'][0]['evidence'] == [] and unresolved['notes']


def test_stored_analysis_validates_all_sources_and_streams_same_result(monkeypatch):
    inputs = [StoredAnalysisFile(i, i+10, str(i)*64, role, Path(f'{i}.dxf'))
              for i, role in enumerate(['KT', 'KC', 'KT', 'KC'], 1)]
    proof = {'project_id': 21, 'profile_version': 4, 'files': [
        {key: getattr(f, key) for key in ('file_id', 'revision_id', 'sha256', 'role')} for f in inputs]}
    names = {f.file_id: str(f.path) for f in inputs}
    monkeypatch.setattr(api.Catalog, 'load', lambda: object())
    monkeypatch.setattr(api, 'read_drawing', lambda path: path)
    monkeypatch.setattr(api, 'line_preview', lambda drawing: {'drawing': drawing})
    monkeypatch.setattr(api, 'takeoff_plans', lambda drawing, height, catalog, openings: [drawing])
    monkeypatch.setattr(api, 'view_payload', lambda drawing, plans, name, cad: {
        'file': name, 'plans': [{'plan': {'name': drawing}}], 'materials': [], 'families': []})
    monkeypatch.setattr(api, 'add_cad_layers', lambda drawing, view, plans: view['plans'][0].update(cad=drawing))
    monkeypatch.setattr(api, '_input_facts', lambda drawing, name, allow_ai, need_plan: {'facts': [], 'rejected': [], 'ai': {}})
    monkeypatch.setattr(api, 'structural_parts', lambda drawings: (
        SimpleNamespace(foundations=[], lintel_height_mm=None), {'sheets': drawings, 'structural_columns': [
            {'instance_id': 'a', 'code': 'C-2', 'file': '2.dxf', 'evidence': []},
            {'instance_id': 'b', 'code': 'C-2', 'file': '', 'evidence': []}]}))
    def events():
        return api._events(inputs, names, proof, ProfilePayload())
    result = list(events())[-1]['data']
    assert [p['cad'] for p in result['view']['plans']] == ['1.dxf', '3.dxf']
    assert [p['source_revision']['revision_id'] for p in result['view']['plans']] == [11, 13]
    assert result['structural']['sheets'] == ['2.dxf', '4.dxf']
    assert 'file_id=2; revision_id=12' in result['structural']['structural_columns'][0]['evidence'][0]
    assert result['structural']['structural_columns'][1]['evidence'] == []
    assert result['structural']['notes']
    assert result['provenance'] == proof
    stream = [json.loads(line) for line in api._stream(events())]
    assert stream[-1]['data'] == result and sum(e['type'] == 'preview' for e in stream) == 2

    monkeypatch.setattr(api, 'read_drawing', lambda path: 'cùng mặt bằng')
    failed = [json.loads(line) for line in api._stream(events())]
    assert failed[-1]['type'] == 'error' and not any(e['type'] == 'complete' for e in failed)


def test_receipt_hashes_exact_completed_event_and_preserves_provenance():
    proof = {'project_id': 777, 'profile_version': 8,
             'files': [{'file_id': 901, 'revision_id': 1, 'sha256': 'a' * 64, 'role': 'KT'}],
             'analysis_id': 'server-id', 'client_analysis_id': 'client-id', 'request_sha256': 'b' * 64}
    lines = list(api._stream(iter([{'type': 'complete', 'data': {'provenance': proof, 'value': 'Việt Nam'}}]), proof))
    assert len(lines) == 2
    receipt = json.loads(lines[1])['receipt']
    assert receipt['response_sha256'] == hashlib.sha256(lines[0].removesuffix('\n').encode('utf-8')).hexdigest()
    assert receipt['files'] == proof['files'] and receipt['profile_version'] == 8
    assert receipt['completed_at'] and receipt['analysis_id'] == 'server-id'


def test_failed_stream_does_not_emit_success_receipt():
    def failed():
        yield {'type': 'status', 'message': 'Đang đọc'}
        raise ValueError('Lỗi đọc')
    events = [json.loads(line) for line in api._stream(failed(), {'analysis_id': 'server-id'})]
    assert events[-1]['type'] == 'error'
    assert not any(e['type'] == 'receipt' for e in events)


def test_route_receipt_binds_request_and_response_without_database(monkeypatch):
    from optimat.api.auth import require_user
    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def scalar(self, query): return ProfilePayload().model_dump()
        def execute(self, query): return SimpleNamespace(all=lambda: [(1, 'mau.dxf')])
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api.project_files, '_user', lambda user: user['user_id'])
    monkeypatch.setattr(api.project_files, 'resolve_analysis_files', lambda *args: [
        StoredAnalysisFile(1, 2, 'a' * 64, 'KT', Path('mau.dxf'))])
    monkeypatch.setattr(api, '_events', lambda inputs, names, proof, profile, allow_ai=False: iter([
        {'type': 'complete', 'data': {'view': {'file': 'mau.dxf', 'plans': []}, 'provenance': proof}}]))
    app = FastAPI()
    app.include_router(api.router)
    app.dependency_overrides[require_user] = lambda: {'user_id': 1}
    body = {'files': [{'file_id': 1, 'revision_id': 2, 'sha256': 'a' * 64, 'role': 'KT'}],
            'profile_version': 8, 'progressive': True, 'client_analysis_id': '00000000-0000-4000-8000-000000000001'}
    with TestClient(app) as client:
        response = client.post('/api/projects/777/analysis', json=body)
    assert response.status_code == 200
    lines = response.content.splitlines()
    result, event = (json.loads(line) for line in lines)
    receipt = event['receipt']
    assert receipt['request_sha256'] == hashlib.sha256(response.request.content).hexdigest()
    assert receipt['response_sha256'] == hashlib.sha256(lines[0]).hexdigest()
    assert receipt['project_id'] == 777 and receipt['profile_version'] == 8
    assert receipt['files'] == body['files'] == result['data']['provenance']['files']
    assert receipt['client_analysis_id'] == body['client_analysis_id']
    assert receipt['analysis_id'] != receipt['client_analysis_id']
