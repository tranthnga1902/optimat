"""Đăng nhập, đăng xuất và phân quyền (AD01-03).

    POST /api/auth/login    email + mật khẩu → cookie phiên (httponly, ký HMAC), ghi audit_logs
    POST /api/auth/logout   xóa cookie
    GET  /api/auth/me       {"auth": có bật đăng nhập không, "user": người đang đăng nhập hoặc null, "setup": chưa có quản trị viên nào}
    POST /api/auth/setup    tạo quản trị viên đầu tiên từ trang đăng nhập; chỉ được khi database chưa có admin nào

Đăng nhập chỉ bật khi có PostgreSQL (DATABASE_URL): bảng users nằm ở đó. Không có database là chế độ kiểm thử đọc CSV
(CLAUDE.md), không có người dùng nào, trang quản trị chỉ xem và ghi được file quy tắc như trước.
Mật khẩu băm PBKDF2-SHA256 (thư viện chuẩn), phiên là token ký HMAC chứa user_id và hạn dùng; mỗi lần gọi API đọc lại
users để tài khoản bị khóa hay đổi vai trò có hiệu lực ngay. Tạo quản trị viên đầu tiên: scripts/create_admin.py.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from .. import config  # noqa: F401  (nạp .env trước khi đọc OPTIMAT_SECRET_KEY)
from ..db.models import Base
from ..db.session import get_database_url, get_engine

router = APIRouter()
COOKIE = "optimat_session"
TTL = 12 * 3600
ITERATIONS = 310_000
# shortcut: thiếu OPTIMAT_SECRET_KEY thì sinh khóa mỗi lần khởi động, phiên cũ mất hiệu lực khi khởi động lại; đặt khóa trong .env khi triển khai
_SECRET = (os.environ.get("OPTIMAT_SECRET_KEY") or secrets.token_hex(32)).encode()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${h}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, it, salt, h = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(it)).hex(), h)


def check_password_rule(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(422, "Mật khẩu cần ít nhất 8 ký tự.")


def make_token(user_id: int, now: float | None = None) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"uid": user_id, "exp": int((now or time.time()) + TTL)}).encode()).decode()
    return f"{body}.{hmac.new(_SECRET, body.encode(), hashlib.sha256).hexdigest()}"


def read_token(token: str) -> int | None:
    body, _, sig = token.partition(".")
    if not hmac.compare_digest(hmac.new(_SECRET, body.encode(), hashlib.sha256).hexdigest(), sig):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(body))
    except ValueError:
        return None
    return data["uid"] if data.get("exp", 0) > time.time() else None


def public(row) -> dict:
    """Thông tin người dùng trả ra ngoài: không bao giờ kèm password_hash."""
    m = row._mapping
    return {"user_id": m["user_id"], "email": m["email"], "full_name": m["full_name"], "role": m["role"],
            "is_active": m["is_active"], "created_at": m["created_at"].isoformat() if m["created_at"] else None}


def current_user(request: Request) -> dict | None:
    """Người đang đăng nhập (tài khoản còn mở), None nếu chưa đăng nhập hoặc không có database."""
    token = request.cookies.get(COOKIE)
    if not token or not get_database_url():
        return None
    uid = read_token(token)
    if uid is None:
        return None
    users = Base.metadata.tables["users"]
    try:
        with get_engine().connect() as conn:
            row = conn.execute(select(users).where(users.c.user_id == uid)).first()
    except DBAPIError as exc:
        raise _db_down(exc) from exc
    return public(row) if row is not None and row.is_active else None


def require_user(user: dict | None = Depends(current_user)) -> dict | None:
    if get_database_url() and user is None:
        raise HTTPException(401, "Chưa đăng nhập hoặc phiên đã hết hạn.")
    return user


def require_admin(user: dict | None = Depends(require_user)) -> dict | None:
    """Chặn API quản trị ở phía máy chủ: người dùng thường gọi thẳng API cũng bị từ chối (403)."""
    if user is not None and user["role"] != "admin":
        raise HTTPException(403, "Chỉ quản trị viên được dùng chức năng này.")
    return user


def _db_down(exc: DBAPIError) -> HTTPException:
    return HTTPException(503, f"Không đọc được bảng users trong PostgreSQL: {str(exc.orig).splitlines()[0]}")


def audit(conn, action: str, user: dict | None, detail: dict) -> None:
    conn.execute(Base.metadata.tables["audit_logs"].insert().values(
        action=action, user_id=user["user_id"] if user else None, detail=detail))


class Login(BaseModel):
    email: str
    password: str


@router.post("/api/auth/login")
def login(body: Login, response: Response) -> dict:
    if not get_database_url():
        raise HTTPException(409, "Chưa kết nối PostgreSQL: chưa bật đăng nhập (chế độ kiểm thử đọc CSV).")
    users, email = Base.metadata.tables["users"], body.email.strip().lower()
    try:
        with get_engine().begin() as conn:   # ghi nhật ký trước khi báo lỗi, để lần đăng nhập sai không bị rollback mất
            row = conn.execute(select(users).where(users.c.email == email)).first()
            ok = row is not None and verify_password(body.password, row.password_hash)
            if not ok:
                audit(conn, "login_failed", None, {"email": email})
            elif row.is_active:
                audit(conn, "login", public(row), {})
    except DBAPIError as exc:
        raise _db_down(exc) from exc
    if not ok:
        raise HTTPException(401, "Sai email hoặc mật khẩu.")
    if not row.is_active:
        raise HTTPException(403, "Tài khoản đã bị khóa. Liên hệ quản trị viên.")
    user = public(row)
    response.set_cookie(COOKIE, make_token(user["user_id"]), max_age=TTL, httponly=True, samesite="lax")
    return {"user": user}


@router.post("/api/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE)
    return {"ok": True}


def _has_admin(conn) -> bool:
    u = Base.metadata.tables["users"]
    return conn.execute(select(func.count()).select_from(u).where(u.c.role == "admin", u.c.is_active)).scalar() > 0


@router.get("/api/auth/me")
def me(user: dict | None = Depends(current_user)) -> dict:
    if not get_database_url():
        return {"auth": False, "user": None, "setup": False}
    try:
        with get_engine().connect() as conn:
            setup = not _has_admin(conn)
    except DBAPIError as exc:
        raise _db_down(exc) from exc
    return {"auth": True, "user": user, "setup": setup}


class Setup(BaseModel):
    email: str
    full_name: str = ""
    password: str


@router.post("/api/auth/setup")
def setup(body: Setup, response: Response) -> dict:
    """Tạo quản trị viên đầu tiên (thay cho scripts/create_admin.py). Đã có admin đang mở thì từ chối: thêm người dùng ở trang Người dùng."""
    if not get_database_url():
        raise HTTPException(409, "Chưa kết nối PostgreSQL: chưa bật đăng nhập.")
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, "Email không hợp lệ.")
    check_password_rule(body.password)
    users = Base.metadata.tables["users"]
    with get_engine().begin() as conn:
        conn.execute(text("LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE"))   # hai người cùng gửi: chỉ một người thành admin đầu tiên
        if _has_admin(conn):
            raise HTTPException(409, "Đã có quản trị viên. Đăng nhập, hoặc nhờ quản trị viên tạo tài khoản.")
        values = {"password_hash": hash_password(body.password), "role": "admin", "is_active": True, "full_name": body.full_name.strip()}
        uid = conn.execute(select(users.c.user_id).where(users.c.email == email)).scalar()
        if uid is None:
            uid = conn.execute(users.insert().values(email=email, **values).returning(users.c.user_id)).scalar()
        else:   # email đã có (người dùng thường hoặc admin bị khóa): nâng thành admin, đặt mật khẩu mới
            conn.execute(users.update().where(users.c.user_id == uid).values(**values))
        user = public(conn.execute(select(users).where(users.c.user_id == uid)).first())
        audit(conn, "user_create", user, {"user_id": uid, "email": email, "role": "admin", "by": "setup"})
    response.set_cookie(COOKIE, make_token(uid), max_age=TTL, httponly=True, samesite="lax")
    return {"user": user}
