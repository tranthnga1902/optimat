"""Tạo bản sao thử nghiệm từ pg_dump, chuyển đổi và kiểm tra; không sửa DB nguồn."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import optimat.config
from sqlalchemy import create_engine, text
from optimat.db.session import get_engine
from optimat.db.migrate20 import migrate


def main():
    source=get_engine()
    url=source.url
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    name='optimat_test_schema20_'+stamp
    backup=ROOT/'backups'/'schema20'
    backup.mkdir(parents=True,exist_ok=True)
    dump=backup/f'before_{stamp}.dump'
    bins=Path('C:/Program Files/PostgreSQL/17/bin')
    env={**os.environ,'PGPASSWORD':url.password or '','PYTHONIOENCODING':'utf-8'}
    common=['-h',url.host or 'localhost','-p',str(url.port or 5432),'-U',url.username or 'postgres']
    dumped=subprocess.run([str(bins/'pg_dump.exe'),*common,'-d',url.database,'-Fc','-f',str(dump)],env=env,capture_output=True)
    if dumped.returncode:
        raise RuntimeError(dumped.stderr.decode('utf-8',errors='replace'))
    with source.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        conn.exec_driver_sql(f'CREATE DATABASE "{name}"')
    subprocess.run([str(bins/'pg_restore.exe'),*common,'-d',name,'--no-owner','--exit-on-error',str(dump)],env=env,check=True,capture_output=True)
    target_url=url.set(database=name)
    target=create_engine(target_url,hide_parameters=True)
    with target.begin() as conn:
        report=migrate(conn)
    report['test_database']=name
    report['source_backup']=str(dump)
    report_path=backup/f'check_{stamp}.json'
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # Cấu hình riêng, không chứa mật khẩu trong báo cáo hay dòng lệnh.
    (backup/'test_url.txt').write_text(target_url.render_as_string(hide_password=False),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':
    main()
