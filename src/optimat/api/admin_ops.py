"""Tổng quan, người dùng, dự án và nhật ký cho trang quản trị (Sprint AD-01). Chỉ quản trị viên, chỉ khi có PostgreSQL.

    GET  /api/admin/dashboard            số liệu thật trong database: dự án, bản vẽ, bóc tách, lần tối ưu, lỗi dữ liệu, hoạt động gần đây
    GET  /api/admin/users                danh sách (tìm, lọc vai trò/trạng thái, phân trang, sắp xếp)
    POST /api/admin/users                tạo tài khoản
    PUT  /api/admin/users/{id}           sửa họ tên, vai trò, khóa/mở khóa, đặt lại mật khẩu (không xóa: xóa user xóa luôn dự án)
    GET  /api/admin/projects             danh sách dự án kèm chủ dự án và số file, lần bóc tách, lần tối ưu
    GET  /api/admin/projects/{id}        chi tiết dự án và hồ sơ liên quan
    GET  /api/admin/audit                nhật ký thao tác (lọc theo hành động, người dùng)
Mọi thao tác ghi đều ghi audit_logs kèm người thực hiện.
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError

from ..db.models import Base
from ..db.session import get_database_url, get_engine
from .auth import audit, check_password_rule, hash_password, public, require_admin

router = APIRouter(dependencies=[Depends(require_admin)])
T = Base.metadata.tables
MAX_SIZE = 200


def _need_db() -> None:
    if not get_database_url():
        raise HTTPException(409, "Chưa kết nối PostgreSQL (DATABASE_URL): người dùng, dự án chỉ có trong database.")


def _page(conn, q: Select, sort_cols: dict, sort: str, order: str, page: int, size: int) -> tuple[int, list]:
    """Đếm tổng rồi lấy một trang; cột sắp xếp chỉ nhận trong danh sách cho phép."""
    if sort not in sort_cols:
        raise HTTPException(422, f"Không sắp xếp được theo {sort}; chọn: {', '.join(sort_cols)}.")
    page, size = max(page, 1), min(max(size, 1), MAX_SIZE)
    total = conn.execute(select(func.count()).select_from(q.subquery())).scalar()
    col = sort_cols[sort]
    rows = conn.execute(q.order_by(col.desc() if order == "desc" else col.asc()).offset((page - 1) * size).limit(size)).all()
    return total, rows


def _iso(v):
    return v.isoformat() if v is not None else None


# ------------------------------ Tổng quan ------------------------------

@router.get("/api/admin/dashboard")
def dashboard() -> dict:
    if not get_database_url():
        return {"connected": False}
    u, tr, r, a = T["users"], T["takeoff_results"], T["optimization_runs"], T["audit_logs"]
    try:
        with get_engine().connect() as conn:
            count = lambda t, *w: conn.execute(select(func.count()).select_from(t).where(*w)).scalar()  # noqa: E731
            out = {
                "connected": True,
                "projects": count(T["projects"]), "files": count(T["project_files"]),
                "takeoffs": count(tr), "takeoffs_confirmed": count(tr, tr.c.confirmed_at.is_not(None)),
                "runs": count(r), "runs_agent": count(r, r.c.llm_model.is_not(None)),
                "users": count(u), "users_active": count(u, u.c.is_active),
                "recent": [{"log_id": x.log_id, "action": x.action, "email": x.email, "detail": x.detail, "created_at": _iso(x.created_at)}
                           for x in conn.execute(select(a, u.c.email).outerjoin(u, a.c.user_id == u.c.user_id)
                                                 .order_by(a.c.log_id.desc()).limit(10))],
            }
    except DBAPIError as exc:
        raise HTTPException(503, f"Không đọc được PostgreSQL: {str(exc.orig).splitlines()[0]}") from exc
    try:
        from ..data_check import run_checks
        out["data_errors"] = run_checks()["counts"]["error"]
    except Exception:  # kiểm soát dữ liệu lỗi không được làm hỏng trang tổng quan: để trống, trang ghi "chưa kiểm được"
        out["data_errors"] = None
    out["api_cost"] = None   # chưa ghi chi phí gọi mô hình ngôn ngữ vào database (AD05-08)
    return out


# ------------------------------ Người dùng ------------------------------

class NewUser(BaseModel):
    email: str
    full_name: str = ""
    password: str
    role: Literal["admin", "user"] = "user"


class UserPatch(BaseModel):
    full_name: Optional[str] = None
    role: Optional[Literal["admin", "user"]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


@router.get("/api/admin/users")
def users_list(q: str = "", role: str = "", active: str = "", page: int = 1, size: int = 50,
               sort: str = "user_id", order: Literal["asc", "desc"] = "asc") -> dict:
    _need_db()
    u = T["users"]
    stmt = select(u)
    if q.strip():
        stmt = stmt.where(or_(u.c.email.ilike(f"%{q.strip()}%"), u.c.full_name.ilike(f"%{q.strip()}%")))
    if role:
        stmt = stmt.where(u.c.role == role)
    if active in ("true", "false"):
        stmt = stmt.where(u.c.is_active == (active == "true"))
    with get_engine().connect() as conn:
        total, rows = _page(conn, stmt, {k: u.c[k] for k in ("user_id", "email", "full_name", "role", "is_active", "created_at")},
                            sort, order, page, size)
    return {"total": total, "page": page, "size": size, "rows": [public(x) for x in rows]}


@router.post("/api/admin/users")
def user_create(body: NewUser, actor: dict | None = Depends(require_admin)) -> dict:
    _need_db()
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, "Email không hợp lệ.")
    check_password_rule(body.password)
    u = T["users"]
    try:
        with get_engine().begin() as conn:
            uid = conn.execute(u.insert().values(email=email, full_name=body.full_name.strip(), role=body.role,
                                                 password_hash=hash_password(body.password)).returning(u.c.user_id)).scalar()
            row = public(conn.execute(select(u).where(u.c.user_id == uid)).first())
            audit(conn, "user_create", actor, {"user_id": uid, "email": email, "role": body.role})
    except IntegrityError as exc:
        raise HTTPException(422, f"Email {email} đã có tài khoản.") from exc
    return {"user": row}


@router.put("/api/admin/users/{user_id}")
def user_update(user_id: int, body: UserPatch, actor: dict | None = Depends(require_admin)) -> dict:
    _need_db()
    values = body.model_dump(exclude_none=True)
    if actor and actor["user_id"] == user_id and (values.get("is_active") is False or values.get("role") == "user"):
        raise HTTPException(422, "Không tự khóa hoặc tự bỏ quyền quản trị của chính mình (tránh mất quyền truy cập).")
    if "password" in values:
        check_password_rule(values["password"])
        values["password_hash"] = hash_password(values.pop("password"))
    if "full_name" in values:
        values["full_name"] = values["full_name"].strip()
    if not values:
        raise HTTPException(422, "Không có gì để sửa.")
    u = T["users"]
    with get_engine().begin() as conn:
        if conn.execute(select(u.c.user_id).where(u.c.user_id == user_id)).first() is None:
            raise HTTPException(404, f"Không có người dùng {user_id}.")
        conn.execute(u.update().where(u.c.user_id == user_id).values(**values))
        row = public(conn.execute(select(u).where(u.c.user_id == user_id)).first())
        action = ("user_lock" if values.get("is_active") is False else "user_unlock" if values.get("is_active") else "user_update")
        audit(conn, action, actor, {"user_id": user_id, "fields": sorted(k for k in values if k != "password_hash")
                                    + (["password"] if "password_hash" in values else [])})
    return {"user": row}


# ------------------------------ Dự án ------------------------------

def _project_counts():
    p, f, tr, r = T["projects"], T["project_files"], T["takeoff_results"], T["optimization_runs"]
    n = lambda t: select(func.count()).select_from(t).where(t.c.project_id == p.c.project_id).scalar_subquery()  # noqa: E731
    return p, n(f).label("files"), n(tr).label("takeoffs"), n(r).label("runs")


@router.get("/api/admin/projects")
def projects_list(q: str = "", user_id: Optional[int] = None, page: int = 1, size: int = 50,
                  sort: str = "updated_at", order: Literal["asc", "desc"] = "desc") -> dict:
    _need_db()
    p, files, takeoffs, runs = _project_counts()
    u = T["users"]
    stmt = select(p.c.project_id, p.c.name, p.c.address, p.c.created_at, p.c.updated_at, p.c.user_id, u.c.email,
                  files, takeoffs, runs).join(u, u.c.user_id == p.c.user_id)
    if q.strip():
        stmt = stmt.where(or_(p.c.name.ilike(f"%{q.strip()}%"), p.c.address.ilike(f"%{q.strip()}%"), u.c.email.ilike(f"%{q.strip()}%")))
    if user_id is not None:
        stmt = stmt.where(p.c.user_id == user_id)
    with get_engine().connect() as conn:
        total, rows = _page(conn, stmt, {"project_id": p.c.project_id, "name": p.c.name, "created_at": p.c.created_at,
                                         "updated_at": p.c.updated_at, "email": u.c.email}, sort, order, page, size)
    return {"total": total, "page": page, "size": size,
            "rows": [{**x._mapping, "created_at": _iso(x.created_at), "updated_at": _iso(x.updated_at)} for x in rows]}


@router.get("/api/admin/projects/{project_id}")
def project_detail(project_id: int) -> dict:
    _need_db()
    p, u, f, tr, r = T["projects"], T["users"], T["project_files"], T["takeoff_results"], T["optimization_runs"]
    with get_engine().connect() as conn:
        row = conn.execute(select(p, u.c.email).join(u, u.c.user_id == p.c.user_id).where(p.c.project_id == project_id)).first()
        if row is None:
            raise HTTPException(404, f"Không có dự án {project_id}.")
        files = conn.execute(select(f).where(f.c.project_id == project_id).order_by(f.c.file_id)).all()
        takeoffs = conn.execute(select(tr.c.takeoff_id, tr.c.file_id, tr.c.confirmed_at, tr.c.created_at,
                                       tr.c.result["kind"].astext.label("kind"))
                                .where(tr.c.project_id == project_id).order_by(tr.c.takeoff_id.desc())).all()
        runs = conn.execute(select(r.c.run_id, r.c.takeoff_id, r.c.method, r.c.model_version, r.c.llm_model, r.c.chosen_index,
                                   func.jsonb_array_length(r.c.solutions).label("solutions"), r.c.created_at)
                            .where(r.c.project_id == project_id).order_by(r.c.run_id.desc())).all()
    m = dict(row._mapping)
    return {"project": {k: (_iso(v) if k in ("created_at", "updated_at") else v) for k, v in m.items()},
            "files": [{**x._mapping, "uploaded_at": _iso(x.uploaded_at)} for x in files],
            "takeoffs": [{**x._mapping, "kind": x.kind or "walls", "confirmed_at": _iso(x.confirmed_at), "created_at": _iso(x.created_at)}
                         for x in takeoffs],
            "runs": [{**x._mapping, "created_at": _iso(x.created_at)} for x in runs]}


# ------------------------------ Nhật ký ------------------------------

@router.get("/api/admin/audit")
def audit_list(action: str = "", user_id: Optional[int] = None, page: int = 1, size: int = 50) -> dict:
    _need_db()
    a, u = T["audit_logs"], T["users"]
    stmt = select(a, u.c.email).outerjoin(u, a.c.user_id == u.c.user_id)
    if action:
        stmt = stmt.where(a.c.action == action)
    if user_id is not None:
        stmt = stmt.where(a.c.user_id == user_id)
    with get_engine().connect() as conn:
        total, rows = _page(conn, stmt, {"log_id": a.c.log_id}, "log_id", "desc", page, size)
    return {"total": total, "page": page, "size": size,
            "rows": [{**x._mapping, "created_at": _iso(x.created_at)} for x in rows]}
