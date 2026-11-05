"""Áp đúng migration đã kiểm thử; snapshot chỉ chứa cấu trúc, số đếm và digest."""
import hashlib
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / 'scripts/db/project_documents.sql'
EXPECTED = '6d322334a36dc8a09d72be1352469661123f85f46d238fd34fb9f49d73467575'
OUT = ROOT / 'tmp/project_documents_schema_receipt_20261103.json'
BASE = ('projects', 'project_files', 'takeoff_results')
NEW = ('project_document_revisions', 'project_profile_revisions')


def snapshot(conn):
    result = {}
    for table in BASE:
        oid = conn.exec_driver_sql('SELECT to_regclass(%s)::oid', ('public.' + table,)).scalar_one()
        if oid is None:
            raise RuntimeError('Thiếu bảng hiện hữu cần đối chiếu.')
        cols = conn.exec_driver_sql("SELECT column_name, data_type, udt_name, is_nullable, column_default "
                                    "FROM information_schema.columns WHERE table_schema='public' AND table_name=%s "
                                    "ORDER BY ordinal_position", (table,)).all()
        constraints = conn.exec_driver_sql("SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint "
                                           "WHERE conrelid=%s ORDER BY conname", (oid,)).all()
        indexes = conn.exec_driver_sql("SELECT indexname, indexdef FROM pg_indexes "
                                       "WHERE schemaname='public' AND tablename=%s ORDER BY indexname", (table,)).all()
        digest = hashlib.sha256()
        count = 0
        # Tên bảng được lấy từ whitelist nội bộ; chỉ ghi digest, không ghi dữ liệu hàng.
        rows = conn.exec_driver_sql(f'SELECT row_to_json(t)::text FROM public."{table}" t ORDER BY row_to_json(t)::text')
        for (row,) in rows:
            b = row.encode('utf-8')
            digest.update(len(b).to_bytes(8, 'big'))
            digest.update(b)
            count += 1
        result[table] = {'oid': oid, 'columns': [list(r) for r in cols],
                         'constraints': [list(r) for r in constraints], 'indexes': [list(r) for r in indexes],
                         'count': count, 'sha256_rows': digest.hexdigest()}
    return result


def new_schema(conn):
    result = {}
    for table in NEW:
        oid = conn.exec_driver_sql('SELECT to_regclass(%s)::oid', ('public.' + table,)).scalar_one()
        if oid is None:
            result[table] = None
            continue
        cols = conn.exec_driver_sql("SELECT column_name, data_type, udt_name, is_nullable "
                                    "FROM information_schema.columns WHERE table_schema='public' AND table_name=%s "
                                    "ORDER BY ordinal_position", (table,)).all()
        constraints = conn.exec_driver_sql("SELECT conname, contype, pg_get_constraintdef(oid) FROM pg_constraint "
                                           "WHERE conrelid=%s ORDER BY conname", (oid,)).all()
        indexes = conn.exec_driver_sql("SELECT indexname, indexdef FROM pg_indexes "
                                       "WHERE schemaname='public' AND tablename=%s ORDER BY indexname", (table,)).all()
        result[table] = {'oid': oid, 'columns': [list(r) for r in cols],
                         'constraints': [list(r) for r in constraints], 'indexes': [list(r) for r in indexes]}
    return result


def main(mode):
    app_raw, test_raw = os.environ.get('DATABASE_URL'), os.environ.get('OPTIMAT_TEST_DATABASE_URL')
    if not app_raw or not test_raw:
        raise RuntimeError('Thiếu cấu hình đích hoặc cấu hình database thử nghiệm.')
    app, test = make_url(app_raw), make_url(test_raw)
    if app.get_backend_name() != 'postgresql' or app.host not in ('localhost', '127.0.0.1', '::1'):
        raise RuntimeError('Đích ứng dụng không phải PostgreSQL local.')
    if not app.database or not test.database or app.database == test.database:
        raise RuntimeError('Không phân biệt được database ứng dụng và database thử nghiệm.')
    if hashlib.sha256(SQL.read_bytes()).hexdigest() != EXPECTED:
        raise RuntimeError('Migration không khớp bản đã kiểm thử.')
    engine = create_engine(app, hide_parameters=True, connect_args={'connect_timeout': 5})
    try:
        with engine.connect() as conn:
            with conn.begin():
                if mode == 'preflight':
                    conn.exec_driver_sql('SET TRANSACTION READ ONLY')
                conn.exec_driver_sql('SET LOCAL search_path = public, pg_catalog')
                actual = conn.exec_driver_sql('SELECT current_database()').scalar_one()
                if actual != app.database:
                    raise RuntimeError('Database kết nối không khớp đích ứng dụng.')
                if mode == 'apply':
                    conn.exec_driver_sql('LOCK TABLE public.projects, public.project_files, public.takeoff_results IN SHARE MODE')
                before = snapshot(conn)
                existing = new_schema(conn)
                if any(existing.values()):
                    report = {'status': 'existing_tables_stop', 'database': actual, 'tables': existing, 'base': before}
                    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                    print('status=existing_tables_stop')
                    return
                if mode == 'preflight':
                    report = {'status': 'preflight', 'database': actual, 'migration_sha256': EXPECTED,
                              'new_tables_absent': True, 'base': before}
                    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                    print('status=preflight_ok; new_tables_absent=True; target_differs_test=True')
                    return
                baseline = json.loads(OUT.read_text(encoding='utf-8'))
                if baseline.get('status') != 'preflight' or baseline.get('database') != actual or baseline.get('base') != before:
                    raise RuntimeError('Snapshot trước thay đổi không còn khớp; dừng để kiểm tra lại.')
                sql = SQL.read_text(encoding='utf-8')
                parts = [s.strip() for s in '\n'.join(line for line in sql.splitlines()
                         if not line.lstrip().startswith('--')).split(';') if s.strip()]
                if parts[0] != 'BEGIN' or parts[-1] != 'COMMIT':
                    raise RuntimeError('Giao dịch migration không đúng cấu trúc.')
                for statement in parts[1:-1]:
                    conn.exec_driver_sql(statement)
                after = snapshot(conn)
                if after != before:
                    raise RuntimeError('Dữ liệu hoặc cấu trúc bảng hiện hữu thay đổi; rollback.')
                created = new_schema(conn)
                verify_created(created)
                report = {'status': 'verified_before_commit', 'database': actual, 'migration_sha256': EXPECTED,
                          'base_before': before, 'base_after': after, 'created': created}
            report['status'] = 'committed_verified'
            OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print('status=committed_verified; base_schema_counts_fingerprints_unchanged=True')
    finally:
        engine.dispose()


def verify_created(tables):
    expected_columns = {
        'project_document_revisions': [('revision_id', 'int8'), ('file_id', 'int4'), ('version', 'int4'),
          ('sha256', 'varchar'), ('stored_path', 'text'), ('size_bytes', 'int8'), ('format', 'varchar'),
          ('role', 'varchar'), ('created_at', 'timestamptz')],
        'project_profile_revisions': [('revision_id', 'int8'), ('project_id', 'int4'), ('version', 'int4'),
          ('payload', 'jsonb'), ('created_at', 'timestamptz')],
    }
    expected_constraints = {
        'project_document_revisions': {'uq_document_file_version', 'ck_document_role', 'ck_document_version_size',
                                       'project_document_revisions_pkey', 'project_document_revisions_file_id_fkey'},
        'project_profile_revisions': {'uq_project_profile_version', 'ck_project_profile_version',
                                      'project_profile_revisions_pkey', 'project_profile_revisions_project_id_fkey'},
    }
    for name, expected in expected_columns.items():
        table = tables.get(name)
        if not table or [(c[0], c[2]) for c in table['columns']] != expected or any(c[3] != 'NO' for c in table['columns']):
            raise RuntimeError('Cấu trúc cột mới không khớp migration.')
        if {c[0] for c in table['constraints']} != expected_constraints[name]:
            raise RuntimeError('Ràng buộc mới không khớp migration.')
        if len(table['indexes']) != 3:
            raise RuntimeError('Số chỉ mục mới không khớp migration.')
        fk = [c[2] for c in table['constraints'] if c[1] == 'f']
        expected_parent = 'project_files' if name == 'project_document_revisions' else 'projects'
        if len(fk) != 1 or expected_parent not in fk[0] or 'ON DELETE CASCADE' not in fk[0]:
            raise RuntimeError('Khóa ngoại mới không khớp migration.')


if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except Exception as exc:
        print('status=failed; error_class=' + type(exc).__name__)
        if isinstance(exc, RuntimeError):
            print('reason=' + str(exc))
        sys.exit(1)
