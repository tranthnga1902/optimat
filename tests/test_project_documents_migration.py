"""Test migration chỉ chạy khi cấu hình database thử nghiệm PostgreSQL riêng."""
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


def test_project_documents_migration_isolated():
    if os.environ.get('OPTIMAT_PROJECT_MIGRATION_TEST') != '1':
        pytest.skip('Chưa bật kiểm thử migration trên database thử nghiệm riêng.')
    raw = os.environ.get('OPTIMAT_TEST_DATABASE_URL')
    if not raw:
        pytest.fail('Chưa cấu hình OPTIMAT_TEST_DATABASE_URL.')
    try:
        url = make_url(raw)
    except Exception:
        pytest.fail('Cấu hình database thử nghiệm không hợp lệ.', pytrace=False)
    name = url.database or ''
    if (url.get_backend_name() != 'postgresql' or url.host not in ('localhost', '127.0.0.1', '::1')
            or not (name == 'optimat_test' or name.startswith('optimat_test_'))):
        pytest.fail('Database thử nghiệm phải là PostgreSQL local tên optimat_test hoặc bắt đầu optimat_test_.', pytrace=False)
    # Tên và opt-in không chứng minh database cô lập; phải xác minh môi trường trước khi bật test.
    sql = (Path(__file__).resolve().parents[1] / 'scripts/db/project_documents.sql').read_text(encoding='utf-8')
    statements = [s.strip() for s in '\n'.join(line for line in sql.splitlines()
                                                if not line.lstrip().startswith('--')).split(';') if s.strip()]
    assert statements[0] == 'BEGIN' and statements[-1] == 'COMMIT'
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                actual = conn.exec_driver_sql('SELECT current_database()').scalar_one()
                assert actual == name, 'Database kết nối không khớp cấu hình thử nghiệm.'
                public_query = ("SELECT c.relname, c.oid FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                                "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') ORDER BY c.relname")
                public_before = conn.exec_driver_sql(public_query).all()
                conn.exec_driver_sql('CREATE TEMP TABLE projects (project_id INTEGER PRIMARY KEY)')
                conn.exec_driver_sql('CREATE TEMP TABLE project_files (file_id INTEGER PRIMARY KEY)')
                conn.exec_driver_sql('SET LOCAL search_path = pg_temp')
                assert conn.exec_driver_sql('SELECT current_schema() = '
                                            '(SELECT nspname FROM pg_namespace WHERE oid = pg_my_temp_schema())').scalar_one()
                for statement in statements[1:-1]:
                    conn.exec_driver_sql(statement)
                created = conn.exec_driver_sql("SELECT c.relname FROM pg_class c WHERE c.relnamespace = pg_my_temp_schema() "
                                               "AND c.relkind = 'r' AND c.relname IN "
                                               "('project_document_revisions', 'project_profile_revisions') ORDER BY c.relname").scalars().all()
                assert created == ['project_document_revisions', 'project_profile_revisions']
                conn.exec_driver_sql('INSERT INTO projects VALUES (1)')
                conn.exec_driver_sql('INSERT INTO project_files VALUES (1)')
                conn.exec_driver_sql("INSERT INTO project_document_revisions "
                                     "(file_id, version, sha256, stored_path, size_bytes, format, role) "
                                     "VALUES (1, 1, 'hash', 'path', 10, 'dxf', 'KT')")
                conn.exec_driver_sql("INSERT INTO project_profile_revisions (project_id, version, payload) "
                                     "VALUES (1, 1, '{}'::jsonb)")
                with pytest.raises(IntegrityError), conn.begin_nested():
                    conn.exec_driver_sql("INSERT INTO project_document_revisions "
                                         "(file_id, version, sha256, stored_path, size_bytes, format, role) "
                                         "VALUES (1, 1, 'hash', 'path', 10, 'dxf', 'KT')")
                with pytest.raises(IntegrityError), conn.begin_nested():
                    conn.exec_driver_sql("INSERT INTO project_document_revisions "
                                         "(file_id, version, sha256, stored_path, size_bytes, format, role) "
                                         "VALUES (1, 2, 'hash', 'path', 10, 'dxf', 'BAD')")
                with pytest.raises(IntegrityError), conn.begin_nested():
                    conn.exec_driver_sql("INSERT INTO project_profile_revisions (project_id, version, payload) "
                                         "VALUES (1, 1, '{}'::jsonb)")
                assert conn.exec_driver_sql('SELECT count(*) FROM project_document_revisions').scalar_one() == 1
            finally:
                transaction.rollback()
            assert conn.exec_driver_sql(public_query).all() == public_before
    finally:
        engine.dispose()
