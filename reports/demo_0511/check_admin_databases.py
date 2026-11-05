"""Locate an existing active admin locally without reading credentials or changing users."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from optimat import config  # noqa: E402,F401
from optimat.db.session import get_engine  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

base = get_engine()
with base.connect() as conn:
    databases = conn.execute(text("SELECT datname FROM pg_database WHERE NOT datistemplate AND datallowconn AND has_database_privilege(datname,'CONNECT')")).scalars().all()
result = []
for name in databases:
    if "test" in name.lower():
        continue
    engine = create_engine(base.url.set(database=name), connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            has_users = conn.execute(text("SELECT to_regclass('public.users') IS NOT NULL")).scalar_one()
            roles = [list(r) for r in conn.execute(text("SELECT role,is_active,count(*) FROM public.users GROUP BY role,is_active"))] if has_users else []
            result.append({"database": name, "has_users": has_users, "roles": roles})
    except Exception as exc:
        result.append({"database": name, "error_type": type(exc).__name__})
    finally:
        engine.dispose()
Path(__file__).with_name("admin_database_inventory.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
