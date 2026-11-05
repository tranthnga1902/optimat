"""KD01: phân tích lại cùng hồ sơ dùng cache, đổi tệp/thông số/quy tắc thì tính lại."""
import json
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from optimat import analysis_cache, config
from optimat.api import project_analysis as api
from optimat.api.auth import require_user
from optimat.api.project_files import ProfilePayload, StoredAnalysisFile


def _client(monkeypatch, tmp_path, calls, sha='a' * 64):
    monkeypatch.setenv('OPTIMAT_ANALYSIS_CACHE', '1')
    monkeypatch.setenv('OPTIMAT_CACHE_DIR', str(tmp_path / 'cache'))

    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def scalar(self, query): return ProfilePayload().model_dump()
        def execute(self, query): return SimpleNamespace(all=lambda: [(1, 'mau.dxf')])

    def events(inputs, names, proof, profile, allow_ai=False):
        calls.append(proof['files'][0]['sha256'])
        yield {'type': 'status', 'stage': 'reading', 'message': 'đọc'}
        yield {'type': 'complete', 'data': {'view': {'file': 'mau.dxf', 'plans': [{'cad': '<svg/>'}]}, 'provenance': proof}}

    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api.project_files, '_user', lambda user: user['user_id'])
    monkeypatch.setattr(api.project_files, 'resolve_analysis_files', lambda *args: [
        StoredAnalysisFile(1, 2, sha, 'KT', Path('mau.dxf'))])
    monkeypatch.setattr(api, '_events', events)
    app = FastAPI()
    app.include_router(api.router)
    app.dependency_overrides[require_user] = lambda: {'user_id': 1}
    return TestClient(app)


def _body(sha='a' * 64, version=1, progressive=False):
    return {'files': [{'file_id': 1, 'revision_id': 2, 'sha256': sha, 'role': 'KT'}],
            'profile_version': version, 'progressive': progressive}


def test_second_run_replays_cache_with_current_provenance(monkeypatch, tmp_path):
    calls = []
    with _client(monkeypatch, tmp_path, calls) as client:
        first = client.post('/api/projects/7/analysis', json=_body(version=1)).json()
        second = client.post('/api/projects/7/analysis', json=_body(version=2)).json()
        lines = client.post('/api/projects/7/analysis', json=_body(progressive=True)).content.splitlines()
    assert calls == ['a' * 64]                      # chỉ chạy pipeline một lần
    assert second['view'] == first['view']
    assert second['provenance']['profile_version'] == 2   # nguồn gốc là của lần gọi hiện tại, không phải bản cache
    events = [json.loads(line) for line in lines]
    assert events[0]['stage'] == 'cache' and events[-2]['type'] == 'complete' and events[-1]['type'] == 'receipt'


def test_changed_file_or_rules_recompute(monkeypatch, tmp_path):
    calls = []
    rules = tmp_path / 'data' / 'rules'
    rules.mkdir(parents=True)
    (rules / 'x.csv').write_text('a\n1\n', encoding='utf-8')
    monkeypatch.setattr(config, 'DATA_DIR', tmp_path / 'data')
    with _client(monkeypatch, tmp_path, calls) as client:
        client.post('/api/projects/7/analysis', json=_body())
        (rules / 'x.csv').write_text('a\n2\n', encoding='utf-8')
        client.post('/api/projects/7/analysis', json=_body())
    with _client(monkeypatch, tmp_path, calls, sha='b' * 64) as client:
        client.post('/api/projects/7/analysis', json=_body(sha='b' * 64))
    assert calls == ['a' * 64, 'a' * 64, 'b' * 64]


def test_corrupt_or_disabled_cache_falls_back(monkeypatch, tmp_path):
    calls = []
    with _client(monkeypatch, tmp_path, calls) as client:
        client.post('/api/projects/7/analysis', json=_body())
        for f in (tmp_path / 'cache').glob('*.json'):
            f.write_text('{hỏng', encoding='utf-8')
        client.post('/api/projects/7/analysis', json=_body())
        monkeypatch.setenv('OPTIMAT_ANALYSIS_CACHE', '0')
        client.post('/api/projects/7/analysis', json=_body())
    assert len(calls) == 3
    assert not list((tmp_path / 'cache').glob('*.tmp'))


def test_failed_run_is_not_cached(monkeypatch, tmp_path):
    monkeypatch.setenv('OPTIMAT_CACHE_DIR', str(tmp_path))

    def broken():
        yield {'type': 'status', 'stage': 'reading', 'message': 'đọc'}
        raise ValueError('hỏng')
    try:
        list(api._recording(broken(), 'k'))
    except ValueError:
        pass
    assert analysis_cache.load('k') is None
