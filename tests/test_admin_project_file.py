"""Bản kiểm thử đề xuất; chỉ chạy sau khi áp patch vào bản checkout phù hợp."""
import hashlib
from urllib.parse import unquote
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from optimat.api import admin_ops, auth
from optimat.api.main import app


@pytest.fixture
def mock_storage(tmp_path, monkeypatch):
    old_overrides = app.dependency_overrides.copy()
    monkeypatch.setattr(admin_ops.config, 'ROOT', tmp_path)
    monkeypatch.setattr(admin_ops.config, 'DATA_DIR', tmp_path / 'data')
    monkeypatch.setattr(admin_ops, 'get_database_url', lambda: 'configured')
    monkeypatch.setattr(auth, 'get_database_url', lambda: 'configured')
    base = tmp_path / 'data' / 'drawings'; base.mkdir(parents=True)
    entries = {}
    class Result:
        def __init__(self, path): self.path = path
        def first(self): return SimpleNamespace(stored_path=self.path) if self.path is not None else None
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, statement):
            params = statement.compile().params
            vals = list(params.values())
            return Result(entries.get(tuple(vals)))
    class Engine:
        def connect(self): return Connection()
    monkeypatch.setattr(admin_ops, 'get_engine', lambda: Engine())
    yield base, entries
    app.dependency_overrides.clear()
    app.dependency_overrides.update(old_overrides)


def set_user(user):
    app.dependency_overrides[auth.current_user] = lambda: user


def test_anonymous_and_nonadmin(mock_storage):
    client = TestClient(app)
    set_user(None)
    assert client.get('/api/admin/projects/1/files/1').status_code == 401
    set_user({'role':'user'})
    assert client.get('/api/admin/projects/1/files/1').status_code == 403


@pytest.mark.parametrize('suffix,media', [
    ('.dxf','application/octet-stream'),('.pdf','application/pdf'),
    ('.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    ('.json','application/json'),('.md','text/plain')])
def test_file_bytes_and_headers(mock_storage,suffix,media):
    base, entries = mock_storage; data = b'du-lieu-mau\x00\x01'; path=base/('file'+suffix);path.write_bytes(data)
    entries[(1,7)] = str(path.relative_to(admin_ops.config.ROOT))
    set_user({'role':'admin'})
    response=TestClient(app).get('/api/admin/projects/1/files/7')
    assert response.status_code==200
    assert hashlib.sha256(response.content).digest()==hashlib.sha256(data).digest()
    assert response.headers['content-type'].startswith(media)
    assert response.headers['content-disposition'].startswith('attachment')
    assert response.headers['x-content-type-options']=='nosniff'
    assert response.headers['cache-control']=='private, no-store'


def test_cross_project_missing_and_traversal(mock_storage,tmp_path):
    base,entries=mock_storage; set_user({'role':'admin'});client=TestClient(app)
    outside=tmp_path/'outside.txt';outside.write_text('khong duoc doc')
    entries[(1,7)]='data/drawings/missing.pdf'
    assert client.get('/api/admin/projects/2/files/7').status_code==404
    assert client.get('/api/admin/projects/1/files/999').status_code==404
    assert client.get('/api/admin/projects/1/files/7').status_code==404
    entries[(1,8)]='data/drawings/../../outside.txt'
    assert client.get('/api/admin/projects/1/files/8').status_code==404


def test_symlink_escape(mock_storage,tmp_path):
    base,entries=mock_storage;set_user({'role':'admin'});client=TestClient(app)
    outside=tmp_path/'outside.txt';outside.write_text('khong duoc doc')
    link=base/'escape.txt'
    try: link.symlink_to(outside)
    except OSError: pytest.skip('Không thể tạo symlink trong môi trường kiểm thử')
    entries[(1,9)]=str(link.relative_to(tmp_path))
    assert client.get('/api/admin/projects/1/files/9').status_code==404


def test_vietnamese_filename(mock_storage):
    base,entries=mock_storage;path=base/'Bản vẽ nhà ở.pdf';path.write_bytes(b'pdf')
    entries[(1,7)]=str(path.relative_to(admin_ops.config.ROOT));set_user({'role':'admin'})
    response=TestClient(app).get('/api/admin/projects/1/files/7')
    assert response.status_code==200
    disposition=response.headers['content-disposition']
    assert disposition.startswith('attachment') and 'Bản vẽ nhà ở.pdf' in unquote(disposition)
    assert '\r' not in disposition and '\n' not in disposition
