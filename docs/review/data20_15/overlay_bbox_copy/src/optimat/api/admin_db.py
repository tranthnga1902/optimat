"""Quản trị cơ sở dữ liệu cho trang /co-so-du-lieu của frontend (vai trò quản trị viên).

    GET    /api/admin/db                       nguồn dữ liệu, trạng thái kết nối, số dòng 26 bảng theo cụm
    GET    /api/admin/tables/{bảng}            cột và dòng của một bảng (tối đa MAX_ROWS)
    POST   /api/admin/tables/{bảng}            thêm dòng            ┐ chỉ 6 bảng quy tắc (EDITABLE) và 2 bảng đại lý
    PUT    /api/admin/tables/{bảng}/{khóa}     sửa dòng             │ (DEALER_TABLES), chỉ khi có PostgreSQL (DATABASE_URL);
    DELETE /api/admin/tables/{bảng}/{khóa}     xóa dòng             ┘ mỗi lần sửa ghi audit_logs
    GET    /api/admin/tables/{bảng}/csv        bảng hiện hành dạng file CSV nguồn (data/rules, data/catalog) để chép đè trước khi nạp lại

Danh mục vật liệu, phương án tường sửa ở data/catalog/materials_master.xlsx (một nguồn), không sửa ở đây.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import Boolean, Date, Float, Integer, func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from .. import config
from ..db.models import Base
from ..db.schema20 import metadata as storage_metadata
from ..db.session import get_database_url, get_engine
from .auth import audit, require_admin

router = APIRouter(dependencies=[Depends(require_admin)])   # mọi API ở đây chỉ dành cho quản trị viên
MAX_ROWS = 2000
HIDDEN = {"password_hash"}   # không bao giờ trả ra trang quản trị
RULES = config.DATA_DIR / "rules"
# bảng quy tắc sửa được -> file CSV nguồn (cùng tên cột, trừ id)
EDITABLE = {"material_rules": "material_rules.csv", "material_notes": "material_notes.csv", "room_rules": "room_rules.csv",
            "rough_norms": "dinh_muc_phan_tho.csv", "drawing_concepts": "concepts.csv", "convention_clauses": "quy_uoc.csv"}
# quản lý đại lý: nhà cung cấp và giá đại lý -> file data/catalog/*.csv (nguồn init_db.py nạp khi bảng trống)
DEALER_TABLES = {"suppliers": "suppliers.csv", "supplier_materials": "supplier_materials.csv"}
WRITABLE = {**EDITABLE, **DEALER_TABLES}
CLUSTERS = {
    "Tài khoản và hồ sơ": ["users", "projects", "document_revisions"],
    "Nhận dạng và bóc tách": ["analysis_runs", "building_elements", "element_measurements", "evidence_sources", "takeoff_items"],
    "Vật liệu và định mức": ["materials", "wall_systems", "material_relations", "work_norms"],
    "Nguồn cung và chi phí": ["suppliers", "supplier_materials", "price_records", "cost_parameters"],
    "Phương án và vận hành": ["material_scenarios", "optimization_runs", "rule_sets", "audit_logs"],
}


def _masked(url: str) -> str:
    return re.sub(r"://([^:/@]+):[^@]*@", r"://\1:***@", url)


def _table(name: str):
    t = storage_metadata.tables.get(name)
    if t is None:
        t = Base.metadata.tables.get(name)
    if t is None:
        raise HTTPException(404, f"Không có bảng {name}.")
    return t


def _csv_path(name: str):
    if name in EDITABLE:
        return RULES / EDITABLE[name]
    p = config.CATALOG_DIR / f"{name}.csv"
    return p if p.exists() else None


def _source_file(name: str) -> str:
    return f"data/rules/{EDITABLE[name]}" if name in EDITABLE else f"data/catalog/{DEALER_TABLES[name]}"


def _clear_caches(name: str) -> None:
    """Lần đọc bản vẽ / bóc tách / tra giá sau dùng ngay dữ liệu vừa sửa."""
    if name in DEALER_TABLES:
        from ..catalog.repository import default_catalog
        default_catalog.cache_clear()
        return
    from ..drawing import concepts, material_notes, material_rules
    from ..rough import areas, norms
    {"material_rules": material_rules.load_rules, "material_notes": material_notes.load_note_rules,
     "room_rules": areas.load_room_rules, "rough_norms": norms.load_norms, "drawing_concepts": concepts.load_signals,
     "convention_clauses": concepts.load_clauses}[name].cache_clear()


@router.get("/api/admin/db")
def db_overview() -> dict:
    url = get_database_url()
    out: dict[str, Any] = {"source": "postgresql" if url else "csv", "url": _masked(url) if url else None,
                           "connected": False, "error": None, "clusters": [], "schema_version": 20,
                           "expected_table_count": 20, "physical_table_count": None}
    counts: dict[str, int | None] = {}
    if url:
        try:
            with get_engine().connect() as conn:
                out["server"] = conn.execute(text("SHOW server_version")).scalar()
                have = set(conn.execute(text("SELECT table_name FROM information_schema.tables "
                                             "WHERE table_schema = 'public'")).scalars())
                physical=set(conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")).scalars())
                out['physical_table_count']=len(physical)
                out['schema_ready']=physical==set(storage_metadata.tables)
                for name, t in storage_metadata.tables.items():
                    counts[name] = conn.execute(select(func.count()).select_from(t)).scalar() if name in have else None
                for name in EDITABLE:
                    if name in have:
                        counts[name]=conn.execute(select(func.count()).select_from(Base.metadata.tables[name])).scalar()
            out["connected"] = True
        except DBAPIError as exc:
            out["error"] = str(exc.orig).splitlines()[0] if exc.orig else str(exc).splitlines()[0]
    if not out["connected"]:
        import pandas as pd
        for name in storage_metadata.tables:
            p = _csv_path(name)
            counts[name] = len(pd.read_csv(p, dtype=str)) if p else None
        for name in EDITABLE:
            counts[name]=len(pd.read_csv(RULES/EDITABLE[name],dtype=str))
    listed = {n for names in CLUSTERS.values() for n in names}
    clusters = {**CLUSTERS, "Khác": [n for n in storage_metadata.tables if n not in listed]}
    out["clusters"] = [{"name": c, "tables": [{"name": n, "rows": counts.get(n), "editable": n in WRITABLE and out["connected"],
                                               "doc": (storage_metadata.tables[n].comment or _doc(n)),
                                               "title": storage_metadata.tables[n].info.get("title"),
                                               "kind": "rule" if n in EDITABLE else "dealer" if n in DEALER_TABLES else None,
                                               "source_file": _source_file(n) if n in WRITABLE else None}
                                              for n in names if n in storage_metadata.tables]}
                       for c, names in clusters.items() if names]
    out['rule_views']=[{'name':n,'title':Base.metadata.tables[n].info.get('title'),
                       'rows':counts.get(n),'editable':out['connected'],'kind':'rule',
                       'source_file':_source_file(n),'doc':Base.metadata.tables[n].comment or _doc(n)} for n in EDITABLE]
    return out


def _doc(name: str) -> str:
    for m in Base.registry.mappers:
        if m.local_table.name == name:
            return (m.class_.__doc__ or "").strip().split("\n")[0]
    return ""


def _columns(t) -> list[dict]:
    return [{"name": c.name, "type": str(c.type).split("(")[0].lower(), "nullable": bool(c.nullable),
             "key": bool(c.primary_key), "comment": c.comment} for c in t.columns if c.name not in HIDDEN]


@router.get("/api/admin/tables/{name}")
def table_rows(name: str) -> dict:
    t = _table(name)
    pk = [c.name for c in t.primary_key.columns]
    if get_database_url():
        try:
            with get_engine().connect() as conn:
                rows = [{k: v for k, v in r._mapping.items() if k not in HIDDEN} for r in conn.execute(select(t).order_by(*t.primary_key.columns).limit(MAX_ROWS))]
                total = conn.execute(select(func.count()).select_from(t)).scalar()
            return {"name": name, "source": "postgresql", "columns": _columns(t), "key": pk, "rows": rows, "total": total,
                    "editable": name in WRITABLE, "source_file": _source_file(name) if name in WRITABLE else None}
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


def _coerce(t, body: dict, insert: bool) -> dict:
    """Giá trị từ biểu mẫu (chuỗi) -> kiểu của cột; ô trống -> NULL. Cột lạ bị bỏ qua; khóa chính chỉ nhận khi thêm
    dòng và là mã nhập tay (supplier_id), không đổi khi sửa vì bảng khác tham chiếu tới."""
    out = {}
    for c in t.columns:
        if c.name not in body or (c.primary_key and (not insert or isinstance(c.type, Integer))):
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
            elif isinstance(c.type, Date):
                out[c.name] = date.fromisoformat(str(v).strip()[:10])
            else:
                out[c.name] = str(v).strip()
        except ValueError as exc:
            raise HTTPException(422, f"Cột {c.name}: {v!r} không đúng kiểu {str(c.type).lower()}.") from exc
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


def _write(name: str, action: str, body: dict | None, row_id: str | None, user: dict | None = None) -> dict:
    if name not in WRITABLE:
        raise HTTPException(403, f"Bảng {name} không sửa trên trang quản trị (danh mục sửa ở materials_master.xlsx).")
    if not get_database_url():
        raise HTTPException(409, "Chưa kết nối PostgreSQL (DATABASE_URL trong .env): chỉ xem được. Sửa file "
                                 f"{_source_file(name)} bằng Excel.")
    t = _table(name)
    pk = next(iter(t.primary_key.columns))
    if row_id is not None and isinstance(pk.type, Integer):
        try:
            row_id = int(row_id)
        except ValueError as exc:
            raise HTTPException(404, f"Không có dòng {row_id} trong {name}.") from exc
    try:
        with get_engine().begin() as conn:
            if action != "insert" and conn.execute(select(pk).where(pk == row_id)).first() is None:
                raise HTTPException(404, f"Không có dòng {pk.name} = {row_id} trong {name}.")
            if action == "delete":
                old = dict(conn.execute(select(t).where(pk == row_id)).first()._mapping)
                conn.execute(t.delete().where(pk == row_id))
                row = old
            else:
                values = _coerce(t, body or {}, action == "insert")
                if action == "update":
                    current = dict(conn.execute(select(t).where(pk == row_id)).first()._mapping)
                    _validate(name, {**current, **values}, conn)
                    conn.execute(t.update().where(pk == row_id).values(**values))
                else:
                    _validate(name, values, conn)
                    row_id = conn.execute(t.insert().values(**values).returning(pk)).scalar()
                row = dict(conn.execute(select(t).where(pk == row_id)).first()._mapping)
            audit(conn, f"admin_{action}", user, {"table": name, "id": row_id,
                                                  "row": {k: (str(v) if v is not None else None) for k, v in row.items()}})
    except IntegrityError as exc:
        raise HTTPException(422, f"Vi phạm ràng buộc dữ liệu: {str(exc.orig).splitlines()[0]}") from exc
    except DBAPIError as exc:
        raise HTTPException(422, f"PostgreSQL từ chối: {str(exc.orig).splitlines()[0]}") from exc
    _clear_caches(name)
    return {"action": action, "row": row}


@router.post("/api/admin/tables/{name}")
def row_create(name: str, body: dict, user: dict | None = Depends(require_admin)) -> dict:
    return _write(name, "insert", body, None, user)


@router.put("/api/admin/tables/{name}/{row_id}")
def row_update(name: str, row_id: str, body: dict, user: dict | None = Depends(require_admin)) -> dict:
    return _write(name, "update", body, row_id, user)


@router.delete("/api/admin/tables/{name}/{row_id}")
def row_delete(name: str, row_id: str, user: dict | None = Depends(require_admin)) -> dict:
    return _write(name, "delete", None, row_id, user)


@router.get("/api/admin/tables/{name}/csv", response_class=PlainTextResponse)
def table_csv(name: str) -> PlainTextResponse:
    """Bảng hiện hành dạng file CSV nguồn (bỏ cột id): chép đè file đó để lần nạp lại (init_db.py --reload-rules
    với quy tắc, --reset với đại lý) không xóa các sửa đổi trên trang quản trị."""
    if name not in WRITABLE:
        raise HTTPException(403, f"Bảng {name} không xuất CSV ở đây.")
    data = table_rows(name)
    cols = [c["name"] for c in data["columns"] if c["name"] != "id"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in data["rows"]:
        w.writerow({k: ("" if r.get(k) is None else f"{r[k]:g}" if isinstance(r.get(k), float) else r.get(k)) for k in cols})
    return PlainTextResponse(buf.getvalue(), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{WRITABLE[name]}"'})
