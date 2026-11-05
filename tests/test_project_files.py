import hashlib
import asyncio
import threading
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from optimat.api import project_files as api
def test_no_database_fails_closed(monkeypatch):
    monkeypatch.setattr(api, 'get_database_url', lambda: None)
    with pytest.raises(HTTPException) as e:
        api.list_projects({'user_id': 1, 'is_active': True})
    assert e.value.status_code == 503


def test_no_user_fails_closed(monkeypatch):
    monkeypatch.setattr(api, 'get_database_url', lambda: 'configured')
    with pytest.raises(HTTPException) as e:
        api._user(None)
    assert e.value.status_code == 401


def test_owned_project_query_rejects_missing():
    class DB:
        def scalar(self, query):
            assert 'projects.user_id' in str(query)
            return None
    with pytest.raises(HTTPException) as e:
        api._project(DB(), 5, 7)
    assert e.value.status_code == 404


def test_original_path_and_hash(monkeypatch, tmp_path):
    monkeypatch.setattr(api.config, 'DATA_DIR', tmp_path)
    root = tmp_path / 'project_documents'
    root.mkdir()
    path = root / 'sample.dxf'
    path.write_bytes(b'hello')
    rev = SimpleNamespace(stored_path=str(path), size_bytes=5, sha256=hashlib.sha256(b'hello').hexdigest())
    assert api._verified_path(rev) == path
    path.write_bytes(b'other')
    with pytest.raises(HTTPException) as e:
        api._verified_path(rev)
    assert e.value.status_code == 409
    rev.stored_path = str(tmp_path / 'outside.dxf')
    (tmp_path / 'outside.dxf').write_bytes(b'hello')
    with pytest.raises(HTTPException) as e:
        api._verified_path(rev)
    assert e.value.status_code == 404


def test_analysis_rejects_stale_profile_and_reference(monkeypatch):
    monkeypatch.setattr(api, '_project', lambda *args: object())
    monkeypatch.setattr(api, '_latest_profile', lambda *args: SimpleNamespace(version=2, payload={}))
    ref = api.SelectedFile(file_id=1, revision_id=1, sha256='a' * 64, role='THAM_KHAO')
    kt = api.SelectedFile(file_id=2, revision_id=2, sha256='b' * 64, role='KT')
    with pytest.raises(HTTPException) as e:
        api.resolve_analysis_files(None, 1, 1, 1, [kt])
    assert e.value.status_code == 409
    with pytest.raises(HTTPException) as e:
        api.resolve_analysis_files(None, 1, 1, 2, [kt, ref])
    assert e.value.status_code == 422


def test_analysis_keeps_selected_older_revision_and_rejects_two_versions(monkeypatch, tmp_path):
    v1 = api.SelectedFile(file_id=1, revision_id=10, sha256='a' * 64, role='KT')
    v2 = api.SelectedFile(file_id=1, revision_id=11, sha256='b' * 64, role='KT')
    monkeypatch.setattr(api, '_project', lambda *args: object())
    monkeypatch.setattr(api, '_latest_profile', lambda *args: SimpleNamespace(
        version=3, payload={'selected_revisions': [v1.model_dump()]}))
    monkeypatch.setattr(api, '_revision', lambda *args: (None, SimpleNamespace(role='KT', format='dxf')))
    seen = []
    monkeypatch.setattr(api, '_check_selection', lambda db, project_id, selection, verify_bytes: seen.append(selection.revision_id) or tmp_path)
    result = api.resolve_analysis_files(None, 7, 1, 3, [v1])
    assert result[0].revision_id == 10 and seen == [10]
    with pytest.raises(HTTPException) as e:
        api.resolve_analysis_files(None, 7, 1, 3, [v1, v2])
    assert e.value.status_code == 422


def test_selection_rejects_changed_hash_and_role(monkeypatch):
    selected = api.SelectedFile(file_id=1, revision_id=10, sha256='a' * 64, role='KT')
    monkeypatch.setattr(api, '_revision', lambda *args: (None, SimpleNamespace(sha256='b' * 64, role='KT')))
    with pytest.raises(HTTPException) as e:
        api._check_selection(None, 1, selected)
    assert e.value.status_code == 409
    monkeypatch.setattr(api, '_revision', lambda *args: (None, SimpleNamespace(sha256='a' * 64, role='KC')))
    with pytest.raises(HTTPException) as e:
        api._check_selection(None, 1, selected)
    assert e.value.status_code == 409


def test_change_role_creates_new_metadata_revision(monkeypatch):
    entry = SimpleNamespace(project_id=1, file_id=4, filename='a.pdf')
    old = SimpleNamespace(version=1, role='KT', sha256='a' * 64, stored_path='saved.pdf', size_bytes=8, format='pdf')
    class DB:
        created = None
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def begin(self): return self
        def scalar(self, query): return 1
        def add(self, obj): self.created = obj
        def flush(self): self.created.revision_id = 12
    db = DB()
    monkeypatch.setattr(api, 'get_database_url', lambda: 'configured')
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: db)
    monkeypatch.setattr(api, '_project', lambda *args, **kwargs: object())
    monkeypatch.setattr(api, '_revision', lambda *args: (entry, old))
    monkeypatch.setattr(api, '_verified_path', lambda *args: 'saved.pdf')
    result = api.change_role(1, 4, api.RoleUpdate(revision_id=5, expected_version=1, role='HO_SO'),
                             {'user_id': 1, 'is_active': True})
    assert result['version'] == 2 and result['role'] == 'HO_SO'
    assert db.created.stored_path == old.stored_path and db.created.sha256 == old.sha256
    assert old.role == 'KT' and old.version == 1
    with pytest.raises(HTTPException) as e:
        api.change_role(1, 4, api.RoleUpdate(revision_id=5, expected_version=2, role='HO_SO'),
                        {'user_id': 1, 'is_active': True})
    assert e.value.status_code == 409


def test_analysis_rejects_pdf_before_reader(monkeypatch):
    selection = api.SelectedFile(file_id=1, revision_id=2, sha256='a' * 64, role='KT')
    monkeypatch.setattr(api, '_project', lambda *args: object())
    monkeypatch.setattr(api, '_latest_profile', lambda *args: SimpleNamespace(
        version=1, payload={'selected_revisions': [selection.model_dump()]}))
    monkeypatch.setattr(api, '_revision', lambda *args: (None, SimpleNamespace(role='KT', format='pdf')))
    with pytest.raises(HTTPException) as e:
        api.resolve_analysis_files(None, 1, 1, 1, [selection])
    assert e.value.status_code == 422


def test_profile_requires_validated_source_references():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        api.ProfilePayload(design_facts={'floors': 'missing'})
    with pytest.raises(ValidationError):
        api.ProfilePayload(source_values={'x': {'source': 'document', 'value': 2}})
    with pytest.raises(ValidationError):
        api.ProfilePayload(source_values={'x': {'source': 'manual', 'value': {'document': 'foreign'}}})
    profile = api.ProfilePayload(design_facts={'floors': 'x'}, source_values={'x': {'source': 'manual', 'value': 2}})
    assert profile.design_facts['floors'] == 'x'


def test_preview_calls_only_reader_and_line_preview(monkeypatch):
    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(api, 'get_database_url', lambda: 'configured')
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api, '_project', lambda *args: object())
    monkeypatch.setattr(api, '_revision', lambda *args: (None, SimpleNamespace(format='dxf')))
    monkeypatch.setattr(api, '_verified_path', lambda *args: 'saved.dxf')
    calls = []
    monkeypatch.setattr(api, 'read_drawing', lambda path: calls.append(('read', path)) or object())
    monkeypatch.setattr(api, 'line_preview', lambda drawing: calls.append(('preview', drawing)) or {'shown': 1, 'total': 2})
    async def run_inline(func): return func()
    monkeypatch.setattr(api, 'run_in_threadpool', run_inline)
    coroutine = api.preview(1, 2, 3, {'user_id': 1, 'is_active': True})
    with pytest.raises(StopIteration) as done:
        coroutine.send(None)
    response = done.value.value
    assert response['warnings']
    assert [call[0] for call in calls] == ['read', 'preview']


def test_xls_preview_route_calls_xls_reader(monkeypatch):
    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(api, 'get_database_url', lambda: 'configured')
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api, '_project', lambda *args: object())
    monkeypatch.setattr(api, '_revision', lambda *args: (None, SimpleNamespace(format='xls', sha256='a' * 64)))
    monkeypatch.setattr(api, '_verified_path', lambda *args: 'saved.xls')
    monkeypatch.setattr(api, 'capabilities', lambda *args: {'can_preview': True})
    seen = []
    monkeypatch.setattr(api, 'xls_preview', lambda path, sheet: seen.append((path, sheet)) or {'rows': [[None, '0.0']]})
    async def run_inline(func): return func()
    monkeypatch.setattr(api, 'run_in_threadpool', run_inline)
    coroutine = api.preview(1, 2, 3, {'user_id': 1, 'is_active': True}, sheet=2)
    with pytest.raises(StopIteration) as done:
        coroutine.send(None)
    assert done.value.value['kind'] == 'xls' and seen == [('saved.xls', 2)]


def test_upload_validation_does_not_block_event_loop(monkeypatch):
    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class File:
        filename = 'slow.xls'
        content_type = 'application/octet-stream'
        async def read(self, size): return b'content'
    started, release = threading.Event(), threading.Event()
    def slow_validator(*args):
        started.set()
        release.wait(2)
        raise api.UploadRejected('Kiểm thử từ chối')
    monkeypatch.setattr(api, 'get_database_url', lambda: 'configured')
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api, '_project', lambda *args: object())
    monkeypatch.setattr(api, 'validate_document', slow_validator)

    async def exercise():
        task = asyncio.create_task(api.upload_file(1, File(), 'KT', None, {'user_id': 1, 'is_active': True}))
        try:
            await asyncio.sleep(0.2)
            assert started.is_set() and not task.done()
            release.set()
            with pytest.raises(HTTPException) as error:
                await task
            assert error.value.status_code == 422
        finally:
            release.set()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(exercise())
    finally:
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()


@pytest.mark.parametrize('sheet', [0, -1, 999])
def test_xls_preview_route_reports_invalid_sheet(monkeypatch, sheet):
    class DB:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(api, 'get_database_url', lambda: 'configured')
    monkeypatch.setattr(api, 'get_engine', lambda: None)
    monkeypatch.setattr(api, 'Session', lambda *args: DB())
    monkeypatch.setattr(api, '_project', lambda *args: object())
    monkeypatch.setattr(api, '_revision', lambda *args: (None, SimpleNamespace(format='xls', sha256='a' * 64)))
    monkeypatch.setattr(api, '_verified_path', lambda *args: 'saved.xls')
    monkeypatch.setattr(api, 'capabilities', lambda *args: {'can_preview': True})
    def invalid(*args): raise ValueError('Số sheet không hợp lệ')
    monkeypatch.setattr(api, 'xls_preview', invalid)
    async def run_inline(func): return func()
    monkeypatch.setattr(api, 'run_in_threadpool', run_inline)
    coroutine = api.preview(1, 2, 3, {'user_id': 1, 'is_active': True}, sheet=sheet)
    with pytest.raises(HTTPException) as error:
        coroutine.send(None)
    assert error.value.status_code == 422
