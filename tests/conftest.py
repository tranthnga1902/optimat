import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# Danh mục thật còn trống số liệu của nhiều phương án tường: kiểm thử tối ưu dùng thêm số MẪU (data/sample/catalog).
# kiểm thử không đọc .env (DATABASE_URL thật); database kiểm thử đặt riêng bằng OPTIMAT_TEST_DATABASE_URL
os.environ["OPTIMAT_NO_DOTENV"] = "1"
# DATABASE_URL đặt ở biến môi trường Windows (database thật) cũng bỏ: bài nào cần database tự đặt từ OPTIMAT_TEST_DATABASE_URL
os.environ.pop("DATABASE_URL", None)
# script con in tiếng Việt ra ống dẫn: Windows mặc định cp1252 làm script dừng giữa chừng (init_db.py --reset)
os.environ["PYTHONIOENCODING"] = "utf-8"
if not os.environ.get("OPTIMAT_CATALOG_OVERLAY"):
    os.environ["OPTIMAT_CATALOG_OVERLAY"] = str(ROOT / "data/sample/catalog")


@pytest.fixture(scope="session")
def sample_openings():
    """Kích thước cửa của dự án mẫu: block D1, S1 trong bản vẽ mẫu không ghi kích thước."""
    from optimat.schemas import OpeningDefaults
    return OpeningDefaults(door_width_mm=900, door_height_mm=2200, window_width_mm=1200, window_height_mm=1400)


@pytest.fixture(scope="session")
def sample_dxf() -> str:
    path = ROOT / "data/sample/sample_floor.dxf"
    if not path.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/make_sample_dxf.py")], check=True)
    return str(path)


@pytest.fixture(scope="session")
def sample_prices() -> str:
    path = ROOT / "data/sample/prices_sample.csv"
    if not path.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/make_sample_data.py")], check=True)
    return str(path)


@pytest.fixture
def login_admin():
    """Hàm (client, url): tạo (hoặc đặt lại) tài khoản quản trị trong database kiểm thử rồi đăng nhập client.
    Có PostgreSQL thì API quản trị đòi đăng nhập (api/auth.py)."""
    def go(client, url, email="admin@test.vn", role="admin", password="matkhau-test-1"):
        from sqlalchemy import create_engine, select

        from optimat.api.auth import hash_password
        from optimat.db.models import Base
        u = Base.metadata.tables["users"]
        with create_engine(url).begin() as conn:
            if conn.execute(select(u.c.user_id).where(u.c.email == email)).first() is None:
                conn.execute(u.insert().values(email=email, role=role, password_hash=hash_password(password)))
            else:
                conn.execute(u.update().where(u.c.email == email).values(role=role, is_active=True, password_hash=hash_password(password)))
        r = client.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        return r.json()["user"]
    return go
