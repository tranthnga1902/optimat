"""Kiểm thử route trên PostgreSQL thử nghiệm, chỉ dùng schema tạm và rollback."""
import hashlib
import os
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from optimat.api import project_files as api
from optimat.api.auth import require_user


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    if os.environ.get('OPTIMAT_PROJECT_DB_TEST') != '1':
        pytest.skip('Chưa bật kiểm thử route trên database thử nghiệm riêng.')
    raw = os.environ.get('OPTIMAT_TEST_DATABASE_URL')
    if not raw:
        pytest.fail('Chưa cấu hình OPTIMAT_TEST_DATABASE_URL.', pytrace=False)
    try:
        url = make_url(raw)
    except Exception:
        pytest.fail('Cấu hình database thử nghiệm không hợp lệ.', pytrace=False)
    name = url.database or ''
    if (url.get_backend_name() != 'postgresql' or url.host not in ('localhost', '127.0.0.1', '::1')
            or not (name == 'optimat_test' or name.startswith('optimat_test_'))):
        pytest.fail('Chỉ nhận PostgreSQL local tên optimat_test hoặc bắt đầu optimat_test_.', pytrace=False)
    # Điều kiện trên không tự chứng minh cô lập: cần xác minh target khác database ứng dụng trước khi bật.
    engine = create_engine(url, hide_parameters=True, connect_args={'connect_timeout': 3})
    try:
        with engine.connect() as conn:
            tx = conn.begin()
            public_query = ("SELECT c.relname, c.oid FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                            "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') ORDER BY c.relname")
            public_before = None
            try:
                assert conn.exec_driver_sql('SELECT current_database()').scalar_one() == name
                public_before = conn.exec_driver_sql(public_query).all()
                conn.exec_driver_sql('CREATE TEMP TABLE users (user_id INTEGER PRIMARY KEY)')
                conn.exec_driver_sql('INSERT INTO users VALUES (101), (102)')
                conn.exec_driver_sql("""CREATE TEMP TABLE projects (
                    project_id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(user_id),
                    name VARCHAR(255) NOT NULL, address VARCHAR(512) NOT NULL DEFAULT '',
                    site_lat FLOAT, site_lon FLOAT, floor_height_mm FLOAT, door_width_mm FLOAT,
                    door_height_mm FLOAT, window_width_mm FLOAT, window_height_mm FLOAT,
                    budget FLOAT, deadline_days FLOAT, max_vehicle_ton FLOAT,
                    excluded_materials JSONB NOT NULL DEFAULT '[]',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
                conn.exec_driver_sql("""CREATE TEMP TABLE project_files (
                    file_id SERIAL PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(project_id),
                    filename VARCHAR(255) NOT NULL, file_type VARCHAR(16) NOT NULL,
                    stored_path VARCHAR(1024) NOT NULL, uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
                conn.exec_driver_sql('CREATE TEMP TABLE takeoff_results (takeoff_id SERIAL PRIMARY KEY)')
                conn.exec_driver_sql('SET LOCAL search_path = pg_temp')
                assert conn.exec_driver_sql('SELECT current_schema() = '
                                            '(SELECT nspname FROM pg_namespace WHERE oid = pg_my_temp_schema())').scalar_one()
                sql = (Path(__file__).resolve().parents[1] / 'scripts/db/project_documents.sql').read_text(encoding='utf-8')
                statements = [s.strip() for s in '\n'.join(line for line in sql.splitlines()
                                      if not line.lstrip().startswith('--')).split(';') if s.strip()]
                assert statements[0] == 'BEGIN' and statements[-1] == 'COMMIT'
                for statement in statements[1:-1]:
                    conn.exec_driver_sql(statement)
                names = conn.exec_driver_sql("SELECT relname FROM pg_class WHERE relnamespace=pg_my_temp_schema() "
                                            "AND relkind='r' AND relname IN "
                                            "('users','projects','project_files','takeoff_results',"
                                            "'project_document_revisions','project_profile_revisions') ORDER BY relname").scalars().all()
                assert names == ['project_document_revisions', 'project_files', 'project_profile_revisions',
                                 'projects', 'takeoff_results', 'users']
                monkeypatch.setattr(api, 'get_database_url', lambda: 'configured')
                monkeypatch.setattr(api, 'get_engine', lambda: engine)
                monkeypatch.setattr(api, 'Session', lambda *args, **kwargs: Session(bind=conn, join_transaction_mode='create_savepoint'))
                monkeypatch.setattr(api.config, 'DATA_DIR', tmp_path)
                yield conn
            finally:
                tx.rollback()
                if public_before is not None:
                    assert conn.exec_driver_sql(public_query).all() == public_before
    finally:
        engine.dispose()


def test_owned_project_files_and_profile_route(isolated_db, monkeypatch):
    from optimat.agent import llm
    from optimat.drawing import review, takeoff
    from optimat.rough import takeoff as rough

    def forbidden(*args, **kwargs):
        raise AssertionError('Upload/preview không được chạy phân tích, LLM hoặc lưu kết quả.')
    for module, names in ((takeoff, ('compute_takeoff', 'takeoff_plans')),
                          (rough, ('compute_rough', 'save_rough')),
                          (review, ('save_review',)), (llm, ('write_explanation', 'parse_constraints'))):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(api, 'read_drawing', lambda path: object())
    monkeypatch.setattr(api, 'line_preview', lambda drawing: {'origin': [0, 0], 'size': [1, 1],
                                                               'segments': [], 'total': 0, 'shown': 0})
    active = {'user_id': 101, 'is_active': True}
    app = FastAPI()
    app.include_router(api.router)
    app.dependency_overrides[require_user] = lambda: active.copy() if active else None
    dxf1 = b'0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n'
    dxf2 = b'0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF\n'
    with TestClient(app) as client:
        create = client.post('/api/projects', json={'name': 'Nha thu A', 'address': 'Gia lap'})
        assert create.status_code == 201
        project_a = create.json()['project_id']
        active.update(user_id=102)
        project_b = client.post('/api/projects', json={'name': 'Nha thu B'}).json()['project_id']
        assert client.get(f'/api/projects/{project_a}').status_code == 404
        active.update(user_id=101)
        assert [p['project_id'] for p in client.get('/api/projects').json()] == [project_a]
        assert client.patch(f'/api/projects/{project_a}', json={'name': 'Nha A sua', 'address': 'Gia lap'}).status_code == 200
        assert client.get(f'/api/projects/{project_b}').status_code == 404
        route = f'/api/projects/{project_a}/files'
        first = client.post(route, data={'role': 'KT'}, files={'file': ('mau.dxf', dxf1, 'application/dxf')})
        assert first.status_code == 201
        v1 = first.json()
        second = client.post(route, data={'role': 'KT', 'file_id': str(v1['file_id'])},
                             files={'file': ('mau.dxf', dxf2, 'application/dxf')})
        assert second.status_code == 201
        v2 = second.json()
        assert v1['file_id'] == v2['file_id'] and (v1['version'], v2['version']) == (1, 2)
        assert len(client.get(route).json()) == 2
        original = f"{route}/{v1['file_id']}/revisions/{v1['revision_id']}/original"
        preview = f"{route}/{v1['file_id']}/revisions/{v1['revision_id']}/preview"
        download = client.get(original)
        assert download.status_code == 200 and download.content == dxf1
        assert hashlib.sha256(download.content).hexdigest() == v1['sha256']
        assert client.get(preview).status_code == 200
        assert isolated_db.exec_driver_sql('SELECT count(*) FROM takeoff_results').scalar_one() == 0

        ref = {key: v1[key] for key in ('file_id', 'revision_id', 'sha256', 'role')}
        payload = api.ProfilePayload(selected_revisions=[api.SelectedFile(**ref)]).model_dump()
        profile = client.patch(f'/api/projects/{project_a}/profile', json={'expected_version': 0, 'payload': payload})
        assert profile.status_code == 200 and profile.json()['version'] == 1
        assert client.patch(f'/api/projects/{project_a}/profile', json={'expected_version': 0, 'payload': payload}).status_code == 409
        with Session(bind=isolated_db, join_transaction_mode='create_savepoint') as db:
            result = api.resolve_analysis_files(db, project_a, 101, 1, [api.SelectedFile(**ref)])
            assert len(result) == 1 and result[0].revision_id == v1['revision_id']
            assert result[0].path.read_bytes() == dxf1
            with pytest.raises(HTTPException) as exc:
                api.resolve_analysis_files(db, project_a, 102, 1, [api.SelectedFile(**ref)])
            assert exc.value.status_code == 404
        active.update(user_id=102)
        assert client.get(original).status_code == 404
        assert client.get(preview).status_code == 404
        cross_original = f"/api/projects/{project_b}/files/{v1['file_id']}/revisions/{v1['revision_id']}/original"
        assert client.get(cross_original).status_code == 404
        assert client.get(cross_original.removesuffix('/original') + '/preview').status_code == 404
        assert client.patch(f'/api/projects/{project_b}/profile', json={'expected_version': 0, 'payload': payload}).status_code == 404
        with Session(bind=isolated_db, join_transaction_mode='create_savepoint') as db:
            with pytest.raises(HTTPException) as exc:
                api.resolve_analysis_files(db, project_b, 102, 0, [api.SelectedFile(**ref)])
            assert exc.value.status_code == 409
        active.clear()
        assert client.get(original).status_code == 401
        assert isolated_db.exec_driver_sql('SELECT count(*) FROM takeoff_results').scalar_one() == 0
