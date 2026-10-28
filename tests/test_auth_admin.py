"""Sprint AD-01: đăng nhập, phân quyền API quản trị, quản lý người dùng, dự án, tổng quan (api/auth.py, api/admin_ops.py)."""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from optimat.api import auth
from optimat.api.main import app

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("OPTIMAT_TEST_DATABASE_URL")


def test_password_hash_and_token():
    h = auth.hash_password("mat-khau-dai")
    assert h.startswith("pbkdf2_sha256$") and "mat-khau-dai" not in h
    assert auth.verify_password("mat-khau-dai", h) and not auth.verify_password("sai", h)
    assert not auth.verify_password("x", "chuoi-hong")
    t = auth.make_token(7)
    assert auth.read_token(t) == 7
    body, sig = t.split(".")
    assert auth.read_token(body + "." + "0" * len(sig)) is None                 # chữ ký sai
    assert auth.read_token(auth.make_token(7, now=time.time() - auth.TTL - 1)) is None   # hết hạn


def test_without_database_login_is_off(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    c = TestClient(app)
    assert c.get("/api/auth/me").json() == {"auth": False, "user": None, "setup": False}
    assert c.post("/api/auth/login", json={"email": "a@b.vn", "password": "12345678"}).status_code == 409
    assert c.get("/api/admin/dashboard").json() == {"connected": False}
    assert c.get("/api/admin/users").status_code == 409
    cols = [x["name"] for x in c.get("/api/admin/tables/users").json()["columns"]]
    assert "password_hash" not in cols and "email" in cols


@pytest.mark.skipif(not URL, reason="chưa đặt OPTIMAT_TEST_DATABASE_URL")
def test_roles_users_projects_in_postgresql(monkeypatch, login_admin):
    subprocess.run([sys.executable, str(ROOT / "scripts/init_db.py"), "--reset"], check=True, cwd=ROOT,
                   env={**os.environ, "DATABASE_URL": URL}, capture_output=True)
    monkeypatch.setenv("DATABASE_URL", URL)
    anon, admin, user = TestClient(app), TestClient(app), TestClient(app)
    # chưa đăng nhập: 401 ở mọi API quản trị, kể cả gọi thẳng
    assert anon.get("/api/auth/me").json() == {"auth": True, "user": None, "setup": True}   # chưa có admin: trang đăng nhập cho tạo
    for path in ("/api/admin/db", "/api/admin/users", "/api/admin/dashboard", "/api/admin/tables/material_notes"):
        assert anon.get(path).status_code == 401, path
    assert anon.post("/api/auth/login", json={"email": "khong@co.vn", "password": "xxxxxxxx"}).status_code == 401

    first = TestClient(app)
    assert first.post("/api/auth/setup", json={"email": "dau@test.vn", "password": "ngan"}).status_code == 422
    assert first.post("/api/auth/setup", json={"email": "Dau@Test.vn", "password": "mat-khau-dau-1"}).json()["user"]["role"] == "admin"
    assert first.get("/api/admin/users").status_code == 200                             # tạo xong là đăng nhập luôn
    assert anon.get("/api/auth/me").json()["setup"] is False
    assert anon.post("/api/auth/setup", json={"email": "ke@gian.vn", "password": "mat-khau-ke-1"}).status_code == 409
    assert first.put("/api/admin/users/1", json={"role": "user"}).status_code == 422        # không tự bỏ quyền admin
    me = login_admin(admin, URL)
    assert admin.get("/api/auth/me").json()["user"]["email"] == "admin@test.vn"
    # tạo tài khoản: email trùng, mật khẩu ngắn bị chặn; không trả password_hash
    assert admin.post("/api/admin/users", json={"email": "u@test.vn", "password": "ngan"}).status_code == 422
    u = admin.post("/api/admin/users", json={"email": " U@Test.vn ", "full_name": "Kỹ sư", "password": "mat-khau-u-1"}).json()["user"]
    assert u["email"] == "u@test.vn" and u["role"] == "user" and "password_hash" not in u
    assert admin.post("/api/admin/users", json={"email": "u@test.vn", "password": "mat-khau-u-1"}).status_code == 422
    # người dùng thường: đăng nhập được nhưng API quản trị trả 403, kể cả ghi bảng quy tắc và ký hiệu nhận diện
    assert user.post("/api/auth/login", json={"email": "u@test.vn", "password": "mat-khau-u-1"}).status_code == 200
    assert user.get("/api/admin/users").status_code == 403
    assert user.post("/api/admin/tables/material_notes", json={"pattern": "x"}).status_code == 403
    assert user.post("/api/concepts", json={"ma": "l97"}).status_code == 403
    assert user.put(f"/api/admin/users/{u['user_id']}", json={"role": "admin"}).status_code == 403
    # danh sách: tìm, lọc, phân trang, sắp xếp
    page = admin.get("/api/admin/users", params={"q": "test.vn", "sort": "email", "size": 1}).json()
    assert page["total"] == 3 and len(page["rows"]) == 1 and page["rows"][0]["email"] == "admin@test.vn"
    assert admin.get("/api/admin/users", params={"role": "user"}).json()["total"] == 1
    assert admin.get("/api/admin/users", params={"sort": "password_hash"}).status_code == 422
    # khóa: phiên đang mở mất hiệu lực ngay, đăng nhập lại bị từ chối; không tự khóa chính mình
    assert admin.put(f"/api/admin/users/{u['user_id']}", json={"is_active": False}).json()["user"]["is_active"] is False
    assert user.get("/api/auth/me").json()["user"] is None
    assert user.post("/api/auth/login", json={"email": "u@test.vn", "password": "mat-khau-u-1"}).status_code == 403
    assert admin.put(f"/api/admin/users/{me['user_id']}", json={"is_active": False}).status_code == 422
    assert admin.put(f"/api/admin/users/{u['user_id']}", json={"is_active": True, "password": "mat-khau-moi-2"}).status_code == 200
    assert user.post("/api/auth/login", json={"email": "u@test.vn", "password": "mat-khau-moi-2"}).status_code == 200
    # bảng users trên trang Cơ sở dữ liệu không lộ mật khẩu băm
    assert all("password_hash" not in r for r in admin.get("/api/admin/tables/users").json()["rows"])

    # dự án và hồ sơ liên quan, tổng quan đếm từ database
    from sqlalchemy import create_engine, text
    with create_engine(URL).begin() as conn:
        pid = conn.execute(text("INSERT INTO projects (user_id, name, address) VALUES (:u, 'Nhà phố H01', 'Hà Đông') "
                                "RETURNING project_id"), {"u": u["user_id"]}).scalar()
        fid = conn.execute(text("INSERT INTO project_files (project_id, filename, file_type, stored_path) "
                                "VALUES (:p, 'kt.dxf', 'dxf', 'x') RETURNING file_id"), {"p": pid}).scalar()
        conn.execute(text("INSERT INTO takeoff_results (project_id, file_id, result, confirmed_at) "
                          "VALUES (:p, :f, '{\"kind\": \"rough\"}', now())"), {"p": pid, "f": fid})
    lst = admin.get("/api/admin/projects", params={"q": "h01"}).json()
    assert lst["total"] == 1 and lst["rows"][0].items() >= {"email": "u@test.vn", "files": 1, "takeoffs": 1, "runs": 0}.items()
    d = admin.get(f"/api/admin/projects/{pid}").json()
    assert d["project"]["name"] == "Nhà phố H01" and d["files"][0]["filename"] == "kt.dxf" and d["takeoffs"][0]["kind"] == "rough"
    assert admin.get("/api/admin/projects/999999").status_code == 404
    dash = admin.get("/api/admin/dashboard").json()
    assert dash.items() >= {"connected": True, "projects": 1, "files": 1, "takeoffs": 1, "takeoffs_confirmed": 1, "runs": 0,
                            "users": 3, "users_active": 3, "api_cost": None}.items()
    # nhật ký ghi người thực hiện từng thao tác quản trị
    log = admin.get("/api/admin/audit", params={"user_id": me["user_id"]}).json()["rows"]
    assert {"user_create", "user_lock", "user_unlock"} <= {r["action"] for r in log} and log[0]["email"] == "admin@test.vn"
    assert admin.get("/api/admin/audit", params={"action": "login_failed"}).json()["rows"][0]["detail"] == {"email": "khong@co.vn"}
    assert admin.post("/api/auth/logout").status_code == 200 and admin.get("/api/admin/users").status_code == 401
