"""Nhập 20 hồ sơ giả lập vào dự án PostgreSQL, an toàn khi chạy lại."""
import hashlib
import json
import secrets
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import optimat.config  # nạp cấu hình kết nối
from sqlalchemy import select
from sqlalchemy.orm import Session
from optimat.api.auth import hash_password
from optimat.db.models import AuditLog, Project, ProjectFile, TakeoffResultRow, User
from optimat.db.session import get_engine

SOURCE = ROOT / 'data/ground_truth/du_toan/synthetic_20_normalized.jsonl'
TARGET = ROOT / 'data/drawings/synthetic_20'
EMAIL = 'synthetic-housing@import.invalid'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records = [json.loads(line) for line in SOURCE.read_text(encoding='utf-8').splitlines() if line]
    if len(records) != 20 or len({r['house_id'] for r in records}) != 20:
        raise ValueError('Cần đúng 20 hồ sơ với mã duy nhất')
    for rec in records:
        if rec['data_kind'] != 'SYNTHETIC':
            raise ValueError('Dữ liệu nhập phải được đánh dấu giả lập')
        for file in rec['files']:
            src = ROOT.parent / file['path']
            if not src.is_file() or digest(src) != file['sha256']:
                raise ValueError(f"Tệp nguồn thiếu hoặc thay đổi: {file['path']}")
            dest = TARGET / rec['house_id'] / src.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists() and digest(dest) != file['sha256']:
                raise ValueError(f'Tệp đích đã tồn tại và khác nội dung: {dest}')
            if not dest.exists():
                shutil.copy2(src, dest)
            if digest(dest) != file['sha256']:
                raise ValueError(f'Lỗi kiểm tra tệp đích: {dest}')
            file['stored_path'] = dest.relative_to(ROOT).as_posix()

    engine = get_engine()
    saved = []
    with Session(engine) as session, session.begin():
        owner = session.scalar(select(User).where(User.email == EMAIL))
        if owner is None:
            owner = User(email=EMAIL, full_name='Kho nhà giả lập', role='user', is_active=False,
                         password_hash=hash_password(secrets.token_urlsafe(48)))
            session.add(owner)
            session.flush()
        for rec in records:
            cid = rec['house_id']
            name = f'[SYNTHETIC:{cid}] Hồ sơ nhà ở giả lập'
            matches = session.scalars(select(Project).where(Project.user_id == owner.user_id, Project.name == name)).all()
            if len(matches) > 1:
                raise ValueError(f'Dự án trùng: {cid}')
            project = matches[0] if matches else Project(user_id=owner.user_id, name=name,
                        address=rec['data']['project']['address'], excluded_materials=[])
            if not matches:
                session.add(project)
                session.flush()
            for file in rec['files']:
                pf = session.scalar(select(ProjectFile).where(ProjectFile.project_id == project.project_id,
                                                               ProjectFile.stored_path == file['stored_path']))
                if pf is None:
                    pf = ProjectFile(project_id=project.project_id, filename=Path(file['stored_path']).name,
                                     file_type=Path(file['stored_path']).suffix.lstrip('.'), stored_path=file['stored_path'])
                    session.add(pf)
            session.flush()
            source = next(f for f in rec['files'] if f['stored_path'].endswith('_data.json'))
            pf = session.scalar(select(ProjectFile).where(ProjectFile.project_id == project.project_id,
                                                           ProjectFile.stored_path == source['stored_path']))
            rows = session.scalars(select(TakeoffResultRow).where(TakeoffResultRow.project_id == project.project_id,
                TakeoffResultRow.result['kind'].astext == 'synthetic_housing')).all()
            if len(rows) > 1:
                raise ValueError(f'Kết quả trùng: {cid}')
            if rows:
                if rows[0].confirmed_at is not None or rows[0].result != rec:
                    raise ValueError(f'Kết quả đã tồn tại khác nội dung hoặc được xác nhận: {cid}')
                result = rows[0]
            else:
                result = TakeoffResultRow(project_id=project.project_id, file_id=pf.file_id,
                                          result=rec, layer_overrides={}, confirmed_at=None)
                session.add(result)
                session.flush()
            saved.append({'house_id': cid, 'project_id': project.project_id, 'takeoff_id': result.takeoff_id,
                          'quantity_rows': len(rec['data']['quantities'])})
        session.add(AuditLog(action='IMPORT_SYNTHETIC_HOUSING', detail={'records': saved, 'data_kind': 'SYNTHETIC'}))
    with Session(engine) as session:
        for item in saved:
            row = session.get(TakeoffResultRow, item['takeoff_id'])
            if row is None or row.confirmed_at is not None or row.result['data_kind'] != 'SYNTHETIC' or len(row.result['data']['quantities']) != item['quantity_rows']:
                raise ValueError(f"Kiểm tra sau nhập thất bại: {item['house_id']}")
            files = session.scalars(select(ProjectFile).where(ProjectFile.project_id == item['project_id'])).all()
            if len(files) != 5:
                raise ValueError(f"Sai số tệp: {item['house_id']}")
    receipt = ROOT / 'data/ground_truth/du_toan/synthetic_20_database_receipt.json'
    receipt.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Đã nhập và kiểm tra {len(saved)} hồ sơ')


if __name__ == '__main__':
    main()
