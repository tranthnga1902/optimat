"""Read-only local demo inventory; never prints credentials or supplier contacts."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from optimat import config  # noqa: E402,F401
from optimat.db.session import get_engine  # noqa: E402
from sqlalchemy import text  # noqa: E402

TABLES = ("materials", "wall_systems", "suppliers", "supplier_materials", "vehicles", "labor_rates", "price_records", "users")
with get_engine().connect() as conn:
    conn.execute(text("SET TRANSACTION READ ONLY"))
    result = {"counts": {}, "data_kinds": {}}
    result["database"] = conn.execute(text("SELECT current_database()" )).scalar_one()
    result["user_roles"] = [list(row) for row in conn.execute(text("SELECT role,is_active,count(*) FROM users GROUP BY role,is_active"))]
    for table in TABLES:
        result["counts"][table] = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        columns = set(conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:table"), {"table": table}).scalars())
        if "data_kind" in columns:
            result["data_kinds"][table] = {str(k): n for k, n in conn.execute(text(f"SELECT data_kind,count(*) FROM {table} GROUP BY data_kind"))}
    result["supplier_price_materials"] = [list(row) for row in conn.execute(text("SELECT material_id,data_kind,count(*) FROM supplier_materials GROUP BY material_id,data_kind ORDER BY material_id"))]
Path(__file__).with_name("db_readiness.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
