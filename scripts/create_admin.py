"""Tạo hoặc đặt lại tài khoản quản trị viên (đăng nhập trang quản trị, Sprint AD-01).

    python scripts/create_admin.py --email admin@optimat.vn --name "Quản trị viên"
Mật khẩu nhập ở dấu nhắc (không hiện, không ghi vào lịch sử lệnh). Email đã có thì đặt lại mật khẩu, mở khóa và cấp quyền admin.
"""
import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sqlalchemy import select  # noqa: E402

from optimat import config  # noqa: E402,F401  (nạp .env)
from optimat.api.auth import audit, hash_password  # noqa: E402
from optimat.db.models import Base  # noqa: E402
from optimat.db.session import get_engine  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email", required=True)
    ap.add_argument("--name", default="")
    args = ap.parse_args()
    password = getpass.getpass("Mật khẩu (ít nhất 8 ký tự): ")
    if password != getpass.getpass("Nhập lại mật khẩu: "):
        sys.exit("Hai lần nhập không khớp.")
    if len(password) < 8:
        sys.exit("Mật khẩu cần ít nhất 8 ký tự.")
    email, u = args.email.strip().lower(), Base.metadata.tables["users"]
    with get_engine().begin() as conn:
        uid = conn.execute(select(u.c.user_id).where(u.c.email == email)).scalar()
        values = {"password_hash": hash_password(password), "role": "admin", "is_active": True}
        if args.name:
            values["full_name"] = args.name
        if uid is None:
            uid = conn.execute(u.insert().values(email=email, **values).returning(u.c.user_id)).scalar()
            audit(conn, "user_create", None, {"user_id": uid, "email": email, "role": "admin", "by": "create_admin.py"})
            print(f"Đã tạo quản trị viên {email} (user_id {uid}).")
        else:
            conn.execute(u.update().where(u.c.user_id == uid).values(**values))
            audit(conn, "user_update", None, {"user_id": uid, "fields": ["password", "role", "is_active"], "by": "create_admin.py"})
            print(f"Đã đặt lại mật khẩu và quyền quản trị cho {email} (user_id {uid}).")


if __name__ == "__main__":
    main()
