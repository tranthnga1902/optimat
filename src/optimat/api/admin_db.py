"""Quản trị cơ sở dữ liệu trên trang /app (vai trò quản trị viên).

    GET    /api/admin/db                       nguồn dữ liệu, trạng thái kết nối, số dòng 26 bảng theo cụm
    GET    /api/admin/tables/{bảng}            cột và dòng của một bảng (tối đa MAX_ROWS)
    POST   /api/admin/tables/{bảng}            thêm dòng            ┐ chỉ 6 bảng quy tắc (EDITABLE),
    PUT    /api/admin/tables/{bảng}/{id}       sửa dòng             │ chỉ khi có PostgreSQL (DATABASE_URL);
    DELETE /api/admin/tables/{bảng}/{id}       xóa dòng             ┘ mỗi lần sửa ghi audit_logs
    GET    /api/admin/tables/{bảng}/csv        bảng hiện hành dạng file data/rules/*.csv để chép đè trước --reload-rules

Danh mục vật liệu, phương án tường sửa ở data/catalog/materials_master.xlsx (một nguồn), không sửa ở đây.
"""
from __future__ import annotations

import csv
import io
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import Boolean, Float, Integer, func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from .. import config
from ..db.models import Base
from ..db.session import get_database_url, get_engine

router = APIRouter()
MAX_ROWS = 2000
RULES = config.DATA_DIR / "rules"
# bảng quy tắc sửa được -> file CSV nguồn (cùng tên cột, trừ id)
EDITABLE = {"material_rules": "material_rules.csv", "material_notes": "material_notes.csv", "room_rules": "room_rules.csv",
            "rough_norms": "dinh_muc_phan_tho.csv", "drawing_concepts": "concepts.csv", "convention_clauses": "quy_uoc.csv"}
CLUSTERS = {
    "Danh mục vật liệu": ["material_groups", "material_families", "materials", "wall_systems", "material_relations",
                          "material_aliases", "standards", "material_standards"],
    "Quy tắc nhận dạng": ["material_rules", "material_notes", "drawing_concepts", "convention_clauses", "room_rules", "rough_norms"],
    "Nguồn cung và giá": ["suppliers", "supplier_materials", "vehicles", "price_records", "labor_rates"],
    "Người dùng và dự án": ["users", "projects", "project_files", "takeoff_results", "optimization_runs"],
    "Vận hành": ["model_versions", "audit_logs"],
}


def _masked(url: str) -> str:
    return re.sub(r"://([^:/@]+):[^@]*@", r"://\1:***@", url)


def _table(name: str):
    t = Base.metadata.tables.get(name)
    if t is None:
        raise HTTPException(404, f"Không có bảng {name}.")
    return t


def _csv_path(name: str):
    if name in EDITABLE:
        return RULES / EDITABLE[name]
    p = config.CATALOG_DIR / f"{name}.csv"
    return p if p.exists() else None


def _clear_caches(name: str) -> None:
    """Lần đọc bản vẽ / bóc tách sau dùng ngay quy tắc vừa sửa."""
    from ..drawing import concepts, material_notes, material_rules
    from ..rough import areas, norms
    {"material_rules": material_rules.load_rules, "material_notes": material_notes.load_note_rules,
     "room_rules": areas.load_room_rules, "rough_norms": norms.load_norms, "drawing_concepts": concepts.load_signals,
     "convention_clauses": concepts.load_clauses}[name].cache_clear()


@router.get("/api/admin/db")
def db_overview() -> dict:
    url = get_database_url()
    out: dict[str, Any] = {"source": "postgresql" if url else "csv", "url": _masked(url) if url else None,
                           "connected": False, "error": None, "clusters": []}
    counts: dict[str, int | None] = {}
    if url:
        try:
            with get_engine().connect() as conn:
                out["server"] = conn.execute(text("SHOW server_version")).scalar()
                have = set(conn.execute(text("SELECT table_name FROM information_schema.tables "
                                             "WHERE table_schema = 'public'")).scalars())
                for name, t in Base.metadata.tables.items():
                    counts[name] = conn.execute(select(func.count()).select_from(t)).scalar() if name in have else None
            out["connected"] = True
        except DBAPIError as exc:
            out["error"] = str(exc.orig).splitlines()[0] if exc.orig else str(exc).splitlines()[0]
    if not out["connected"]:
        import pandas as pd
        for name in Base.metadata.tables:
            p = _csv_path(name)
            counts[name] = len(pd.read_csv(p, dtype=str)) if p else None
    listed = {n for names in CLUSTERS.values() for n in names}
    clusters = {**CLUSTERS, "Khác": [n for n in Base.metadata.tables if n not in listed]}
    out["clusters"] = [{"name": c, "tables": [{"name": n, "rows": counts.get(n), "editable": n in EDITABLE and out["connected"],
                                               "doc": (Base.metadata.tables[n].comment or _doc(n))}
                                              for n in names if n in Base.metadata.tables]}
                       for c, names in clusters.items() if names]
    return out


def _doc(name: str) -> str:
    for m in Base.registry.mappers:
        if m.local_table.name == name:
            return (m.class_.__doc__ or "").strip().split("\n")[0]
    return ""


def _columns(t) -> list[dict]:
    return [{"name": c.name, "type": str(c.type).split("(")[0].lower(), "nullable": bool(c.nullable),
             "key": bool(c.primary_key)} for c in t.columns]


@router.get("/api/admin/tables/{name}")
def table_rows(name: str) -> dict:
    t = _table(name)
    pk = [c.name for c in t.primary_key.columns]
    if get_database_url():
        try:
            with get_engine().connect() as conn:
                rows = [dict(r._mapping) for r in conn.execute(select(t).order_by(*t.primary_key.columns).limit(MAX_ROWS))]
                total = conn.execute(select(func.count()).select_from(t)).scalar()
            return {"name": name, "source": "postgresql", "columns": _columns(t), "key": pk, "rows": rows, "total": total,
                    "editable": name in EDITABLE}
        except DBAPIError as exc:
            raise HTTPException(503, f"Không đọc được PostgreSQL: {str(exc.orig).splitlines()[0]}") from exc
    p = _csv_path(name)
    if p is None:
        return {"name": name, "source": "csv", "columns": _columns(t), "key": pk, "rows": [], "total": 0, "editable": False}
    with open(p, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if "id" in pk:                                   # id = số thứ tự dòng, như khi nạp vào PostgreSQL
        rows = [{"id": i, **r} for i, r in enumerate(rows, start=1)]
    return {"name": name, "source": "csv", "columns": _columns(t), "key": pk, "rows": rows[:MAX_ROWS], "total": len(rows),
            "editable": False}


def _coerce(t, body: dict) -> dict:
    """Giá trị từ biểu mẫu (chuỗi) -> kiểu của cột; ô trống -> NULL. Cột lạ và khóa chính bị bỏ qua."""
    out = {}
    for c in t.columns:
        if c.primary_key or c.name not in body:
            continue
        v = body[c.name]
        if v is None or (isinstance(v, str) and v.strip() == ""):
            if not c.nullable and c.server_default is None and c.default is None:
                raise HTTPException(422, f"Cột {c.name} không được để trống.")
            out[c.name] = None
            continue
        try:
            if isinstance(c.type, Boolean):
                out[c.name] = str(v).strip().lower() in ("1", "true", "có", "co", "x")
            elif isinstance(c.type, Integer):
                out[c.name] = int(str(v).strip())
            elif isinstance(c.type, Float):
                out[c.name] = float(str(v).strip().replace(",", "."))
            else:
                out[c.name] = str(v).strip()
        except ValueError as exc:
            raise HTTPException(422, f"Cột {c.name}: {v!r} không phải số.") from exc
    return out


def _validate(name: str, row: dict, conn) -> None:
    """Kiểm tra ngoài ràng buộc của PostgreSQL, để quy tắc sai không lọt vào bộ nhận dạng."""
    from ..drawing import concepts
    if name in ("room_rules",) or (name == "material_rules" and row.get("signal") == "block"):
        try:
            re.compile(row.get("pattern") or "")
        except re.error as exc:
            raise HTTPException(422, f"Biểu thức chính quy lỗi: {exc}.") from exc
    if name == "material_notes":
        known = set(conn.execute(text("SELECT material_id FROM materials")).scalars())
        if row.get("material_id") not in known:
            raise HTTPException(422, f"Mã vật liệu {row.get('material_id')} không có trong danh mục.")
    if name == "drawing_concepts":
        allowed = concepts.LAYER_ROLES if row.get("tin_hieu") == "layer" else concepts.BLOCK_ROLES
        if row.get("vai_tro") not in allowed:
            raise HTTPException(422, f"Vai trò của {row.get('tin_hieu')} phải là {' | '.join(allowed)}.")
        if bad := concepts.new_conflicts(row):
            raise HTTPException(422, "Ký hiệu " + "; ".join(bad) + ".")


def _write(name: str, action: str, body: dict | None, row_id: int | None) -> dict:
    if not get_database_url():
        raise HTTPException(409, "Chưa kết nối PostgreSQL (DATABASE_URL trong .env): chỉ xem được. Sửa file "
                                 f"data/rules/{EDITABLE.get(name, '')} bằng Excel.")
    if name not in EDITABLE:
        raise HTTPException(403, f"Bảng {name} không sửa trên trang quản trị (danh mục sửa ở materials_master.xlsx).")
    t = _table(name)
    pk = t.c.id
    try:
        with get_engine().begin() as conn:
            if action != "insert" and conn.execute(select(pk).where(pk == row_id)).first() is None:
                raise HTTPException(404, f"Không có dòng id {row_id} trong {name}.")
            if action == "delete":
                old = dict(conn.execute(select(t).where(pk == row_id)).first()._mapping)
                conn.execute(t.delete().where(pk == row_id))
                row = old
            else:
                values = _coerce(t, body or {})
                if action == "update":
                    current = dict(conn.execute(select(t).where(pk == row_id)).first()._mapping)
                    _validate(name, {**current, **values}, conn)
                    conn.execute(t.update().where(pk == row_id).values(**values))
                else:
                    _validate(name, values, conn)
                    row_id = conn.execute(t.insert().values(**values).returning(pk)).scalar()
                row = dict(conn.execute(select(t).where(pk == row_id)).first()._mapping)
            conn.execute(Base.metadata.tables["audit_logs"].insert().values(
                action=f"admin_{action}", detail={"table": name, "id": row_id, "row": {k: (str(v) if v is not None else None)
                                                                                   for k, v in row.items()}}))
    except IntegrityError as exc:
        raise HTTPException(422, f"Vi phạm ràng buộc dữ liệu: {str(exc.orig).splitlines()[0]}") from exc
    except DBAPIError as exc:
        raise HTTPException(422, f"PostgreSQL từ chối: {str(exc.orig).splitlines()[0]}") from exc
    _clear_caches(name)
    return {"action": action, "row": row}


@router.post("/api/admin/tables/{name}")
def row_create(name: str, body: dict) -> dict:
    return _write(name, "insert", body, None)


@router.put("/api/admin/tables/{name}/{row_id}")
def row_update(name: str, row_id: int, body: dict) -> dict:
    return _write(name, "update", body, row_id)


@router.delete("/api/admin/tables/{name}/{row_id}")
def row_delete(name: str, row_id: int) -> dict:
    return _write(name, "delete", None, row_id)


@router.get("/api/admin/tables/{name}/csv", response_class=PlainTextResponse)
def table_csv(name: str) -> PlainTextResponse:
    """Bảng hiện hành dạng file data/rules/*.csv (bỏ cột id): chép đè file đó để init_db.py --reload-rules
    không xóa các sửa đổi trên trang quản trị."""
    if name not in EDITABLE:
        raise HTTPException(403, f"Bảng {name} không xuất CSV ở đây.")
    data = table_rows(name)
    cols = [c["name"] for c in data["columns"] if c["name"] != "id"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in data["rows"]:
        w.writerow({k: ("" if r.get(k) is None else f"{r[k]:g}" if isinstance(r.get(k), float) else r.get(k)) for k in cols})
    return PlainTextResponse(buf.getvalue(), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{EDITABLE[name]}"'})
