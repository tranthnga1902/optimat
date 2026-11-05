"""Delta role trong schema tạm; chỉ chạy khi fixture DB cô lập được bật và duyệt."""
from pathlib import Path

import pytest
from sqlalchemy.exc import DBAPIError

from test_project_files_db import isolated_db  # noqa: F401


def _statements(name):
    path = Path(__file__).resolve().parents[1] / 'scripts/db' / name
    lines = [line for line in path.read_text(encoding='utf-8').splitlines() if not line.lstrip().startswith('--')]
    script = '\n'.join(lines).strip()
    assert script.startswith('BEGIN;') and script.endswith('COMMIT;')
    return script[len('BEGIN;'):-len('COMMIT;')].replace('public.project_document_revisions',
                                                         'pg_temp.project_document_revisions')


def test_roles_delta_and_guarded_rollback(isolated_db):
    conn = isolated_db
    conn.exec_driver_sql("INSERT INTO projects (user_id,name) VALUES (101,'test')")
    conn.exec_driver_sql("INSERT INTO project_files (project_id,filename,file_type,stored_path) VALUES (1,'a.pdf','pdf','a')")
    conn.exec_driver_sql(_statements('project_document_roles.sql'))
    conn.exec_driver_sql("INSERT INTO project_document_revisions "
                         "(file_id,version,sha256,stored_path,size_bytes,format,role) "
                         "VALUES (1,1,'hash','path',1,'pdf','HO_SO')")
    with pytest.raises(DBAPIError), conn.begin_nested():
        conn.exec_driver_sql(_statements('project_document_roles_rollback.sql'))
    assert conn.exec_driver_sql("SELECT role FROM project_document_revisions WHERE file_id=1").scalar_one() == 'HO_SO'
    conn.exec_driver_sql('DELETE FROM project_document_revisions WHERE file_id=1')
    conn.exec_driver_sql(_statements('project_document_roles_rollback.sql'))
    with pytest.raises(DBAPIError), conn.begin_nested():
        conn.exec_driver_sql("INSERT INTO project_document_revisions "
                             "(file_id,version,sha256,stored_path,size_bytes,format,role) "
                             "VALUES (1,1,'hash','path',1,'pdf','HO_SO')")
