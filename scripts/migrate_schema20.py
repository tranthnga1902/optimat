"""Sao lưu bắt buộc và chuyển database sang 20 bảng. Mặc định chỉ kiểm kê."""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import optimat.config  # nạp .env; không in mật khẩu
from optimat.db.session import get_engine
from optimat.db.migrate20 import migrate, physical_tables
from optimat.db.schema20 import NAMES
from sqlalchemy import text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='Sao lưu rồi chuyển đổi trong một giao dịch')
    parser.add_argument('--backup-dir',default=str(ROOT/'backups'/'schema20'))
    args=parser.parse_args()
    engine=get_engine()
    with engine.connect() as conn:
        have=physical_tables(conn)
        print(json.dumps({'database':engine.url.database,'physical_tables':len(have),'target_tables':sorted(NAMES)},ensure_ascii=True))
    if not args.apply or have==NAMES:
        return
    backup=Path(args.backup_dir).resolve()
    backup.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    dump=backup/f'{engine.url.database}_{stamp}.dump'
    exe=shutil.which('pg_dump') or 'C:/Program Files/PostgreSQL/17/bin/pg_dump.exe'
    restore=shutil.which('pg_restore') or str(Path(exe).with_name('pg_restore.exe'))
    url=engine.url
    env={**os.environ,'PGPASSWORD':url.password or ''}
    command=[exe,'-h',url.host or 'localhost','-p',str(url.port or 5432),'-U',url.username or 'postgres','-d',url.database,'-Fc','-f',str(dump)]
    subprocess.run(command,env=env,check=True,capture_output=True)
    subprocess.run([restore,'--list',str(dump)],check=True,capture_output=True)
    if not dump.is_file() or dump.stat().st_size==0:
        raise RuntimeError('Sao lưu chưa hợp lệ; không thay đổi database.')
    with engine.begin() as conn:
        conn.exec_driver_sql("SET LOCAL lock_timeout='15s'")
        report=migrate(conn)
    report['backup']=str(dump)
    path=backup/f'migration_{stamp}.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':
    main()
