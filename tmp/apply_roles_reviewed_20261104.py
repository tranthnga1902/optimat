"""Áp đúng delta đã duyệt, dừng nếu bằng chứng đích hoặc lược đồ không khớp."""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
DELTA = ROOT / 'scripts/db/project_document_roles.sql'
ROLLBACK = ROOT / 'scripts/db/project_document_roles_rollback.sql'
RECEIPT = ROOT / 'tmp/roles_apply_receipt_20261104.json'
HASHES = {'delta': '547b8b44bc2154fe97c4e236f7239283ea55abca5a3e12397e21e4acfaed9a6d',
          'rollback': '0c547c4ddd73e73ddc655c60cd86d47eaa42c4a73be5985aa583472276adc5f2'}
TABLES = ('project_document_revisions', 'project_profile_revisions', 'projects', 'project_files', 'takeoff_results')


def check_api():
    command = ("$p=Get-Process -Id 10060 -ErrorAction Stop; "
               "if ($p.StartTime.ToString('yyyy-MM-ddTHH:mm:ss') -ne '2026-11-04T08:24:49') { exit 1 }; "
               "$l=@(Get-NetTCPConnection -OwningProcess 10060 -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue); "
               "$c=@(Get-NetTCPConnection -OwningProcess 10060 -LocalPort 63224 -RemotePort 5432 -State Established -ErrorAction SilentlyContinue | "
               "Where-Object { $_.LocalAddress -eq '::1' -and $_.RemoteAddress -eq '::1' }); "
               "if ($l.Count -lt 1 -or $c.Count -ne 1) { exit 1 }; 'ok'")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                            capture_output=True, timeout=12, check=False,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode or result.stdout.strip() != b'ok':
        raise RuntimeError('Không còn xác minh được PID và kết nối TCP API.')


def metadata(conn):
    result = {}
    for name in TABLES:
        oid = conn.exec_driver_sql('SELECT to_regclass(%s)::oid', ('public.' + name,)).scalar_one()
        if oid is None:
            raise RuntimeError('Thiếu bảng cần đối chiếu.')
        result[name] = {'oid': oid, 'count': conn.exec_driver_sql('SELECT count(*) FROM public."'+name+'"').scalar_one()}
    row = conn.exec_driver_sql("SELECT convalidated,pg_get_constraintdef(oid) FROM pg_constraint "
                               "WHERE conrelid=%s AND conname='ck_document_role'", (result[TABLES[0]]['oid'],)).all()
    if len(row) != 1:
        raise RuntimeError('Constraint vai trò thiếu hoặc trùng.')
    result['constraint'] = {'validated': row[0][0], 'definition': row[0][1]}
    result['role_counts'] = dict(conn.exec_driver_sql('SELECT role,count(*) FROM public.project_document_revisions GROUP BY role').all())
    return result


def roles(metadata):
    return set(re.findall(r"'([^']+)'::", metadata['constraint']['definition']))


def verify_session(conn):
    check_api()
    rows = conn.exec_driver_sql("SELECT datname,client_addr::text,client_port,backend_start FROM pg_stat_activity "
                                "WHERE client_port=%s AND client_addr='::1'::inet", (63224,)).all()
    if len(rows) != 1 or rows[0][0] != 'optimat':
        raise RuntimeError('Không chứng minh được kết nối API tới database optimat.')
    return {'api_pid': 10060, 'api_start': '2026-11-04T08:24:49', 'api_port': 8000,
            'client_address': rows[0][1], 'client_port': rows[0][2],
            'database': rows[0][0], 'backend_start': rows[0][3].isoformat()}


def save(receipt):
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    receipt = {'status': 'started', 'hashes': HASHES, 'commit_attempted': False}
    engine = None
    tx = None
    try:
        if hashlib.sha256(DELTA.read_bytes()).hexdigest() != HASHES['delta'] or hashlib.sha256(ROLLBACK.read_bytes()).hexdigest() != HASHES['rollback']:
            raise RuntimeError('Hash delta hoặc rollback không khớp bản đã duyệt.')
        url = make_url(os.environ['DATABASE_URL'])
        if url.get_backend_name() != 'postgresql' or url.database != 'optimat' or url.host not in ('localhost', '127.0.0.1', '::1'):
            raise RuntimeError('Cấu hình không trỏ PostgreSQL local optimat.')
        lines = [line for line in DELTA.read_text(encoding='utf-8').splitlines() if not line.lstrip().startswith('--')]
        parts = [s.strip() for s in '\n'.join(lines).split(';') if s.strip()]
        expected = ["BEGIN", "ALTER TABLE public.project_document_revisions DROP CONSTRAINT ck_document_role",
                    "ALTER TABLE public.project_document_revisions ADD CONSTRAINT ck_document_role CHECK (role IN ('KT', 'KC', 'HO_SO', 'TIEN_LUONG', 'THAM_KHAO'))", "COMMIT"]
        if [' '.join(s.split()) for s in parts] != expected:
            raise RuntimeError('Câu lệnh delta không đúng phạm vi đã duyệt.')
        engine = create_engine(url, hide_parameters=True, connect_args={'connect_timeout': 5})
        with engine.connect() as conn:
            tx = conn.begin()
            conn.exec_driver_sql("SET LOCAL lock_timeout = '3s'")
            conn.exec_driver_sql("SET LOCAL statement_timeout = '30s'")
            if conn.exec_driver_sql('SELECT current_database()').scalar_one() != 'optimat':
                raise RuntimeError('Kết nối không đúng database đã duyệt.')
            receipt['target'] = verify_session(conn)
            conn.exec_driver_sql('LOCK TABLE public.project_document_revisions IN ACCESS EXCLUSIVE MODE')
            before = metadata(conn)
            old = {'KT', 'KC', 'THAM_KHAO'}
            previous = json.loads((ROOT / 'tmp/roles_app_preflight_20261104.json').read_text(encoding='utf-8'))
            if (not before['constraint']['validated'] or roles(before) != old or
                    before['constraint']['definition'] != previous['role_constraint'][0]['definition']):
                raise RuntimeError('Constraint hiện tại khác preflight; dừng.')
            receipt['before'] = before
            receipt['target_rechecked'] = verify_session(conn)
            receipt['status'] = 'precommit'
            save(receipt)
            conn.exec_driver_sql(parts[1])
            conn.exec_driver_sql(parts[2])
            after = metadata(conn)
            if (not after['constraint']['validated'] or roles(after) != old | {'HO_SO', 'TIEN_LUONG'} or
                    any(before[t] != after[t] for t in TABLES) or before['role_counts'] != after['role_counts']):
                raise RuntimeError('Kiểm tra trước commit không khớp; rollback.')
            receipt['after_in_transaction'] = after
            receipt['commit_attempted'] = True
            receipt['status'] = 'commit_attempted'
            save(receipt)
            tx.commit()
            receipt['status'] = 'committed'
            save(receipt)
            with conn.begin():
                conn.exec_driver_sql('SET TRANSACTION READ ONLY')
                if conn.exec_driver_sql('SELECT current_database()').scalar_one() != 'optimat':
                    raise RuntimeError('Kiểm tra sau commit sai đích.')
                post = metadata(conn)
                receipt['postcommit'] = post
                receipt['postcommit_schema_ok'] = (post['constraint']['validated'] and roles(post) == old | {'HO_SO', 'TIEN_LUONG'})
                receipt['postcommit_counts_match'] = all(post[t] == before[t] for t in TABLES) and post['role_counts'] == before['role_counts']
            receipt['status'] = 'committed_verified' if receipt['postcommit_schema_ok'] and receipt['postcommit_counts_match'] else 'committed_postcheck_mismatch'
            save(receipt)
            print('status=' + receipt['status'])
    except Exception as exc:
        if tx is not None and tx.is_active:
            tx.rollback()
        if receipt['status'] != 'committed':
            receipt['status'] = 'commit_uncertain' if receipt['commit_attempted'] else 'rolled_back_or_not_started'
        else:
            receipt['status'] = 'committed_postcheck_failed'
        receipt['error_class'] = type(exc).__name__
        if isinstance(exc, RuntimeError):
            receipt['reason'] = str(exc)
        save(receipt)
        print('status=' + receipt['status'] + '; error_class=' + type(exc).__name__)
        if isinstance(exc, RuntimeError):
            print('reason=' + str(exc))
        raise SystemExit(1)
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == '__main__':
    main()
