"""Apply the reviewed, INSERT-only demo package; default is a read-only preflight."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat import config  # noqa: E402,F401
from optimat.db.session import get_engine  # noqa: E402
from sqlalchemy import text  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--sql", type=Path, default=HERE / "06_demo_actual.sql")
    args = parser.parse_args()
    sql = args.sql.read_text(encoding="utf-8")
    manifest = json.loads(args.sql.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(sql.encode()).hexdigest() != manifest["sql_sha256"]:
        raise ValueError("SQL differs from reviewed manifest")
    for source in manifest["sources"].values():
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Source changed; regenerate and review the SQL package")
    inserts = [line for line in sql.splitlines() if line.startswith("INSERT INTO ")]
    if len(inserts) != len(manifest["suppliers"]) + len(manifest["price_records"]):
        raise ValueError("Unexpected statement count")
    if any(not line.startswith(("INSERT INTO suppliers (", "INSERT INTO price_records ("))
           or " ON CONFLICT DO NOTHING RETURNING " not in line for line in inserts):
        raise ValueError("Only reviewed, idempotent INSERT statements are allowed")
    receipt = {"utc": datetime.now(timezone.utc).isoformat(), "apply": args.apply,
               "sql_sha256": manifest["sql_sha256"], "inserted": {"suppliers": [], "price_records": []}}
    with get_engine().begin() as conn:
        if not args.apply:
            conn.execute(text("SET TRANSACTION READ ONLY"))
        receipt["database"] = conn.execute(text("SELECT current_database()")).scalar_one()
        index = conn.execute(text("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='price_records' AND indexname='uq_price_records_dedup'")).scalar_one_or_none()
        if not index or "UNIQUE INDEX" not in index:
            raise ValueError("Required price deduplication index is missing")
        for row in manifest["price_records"]:
            material = conn.execute(text("SELECT unit,data_kind FROM materials WHERE material_id=:material_id"), row).first()
            if material is None or tuple(material) != (row["unit"], "ACTUAL"):
                raise ValueError("Runtime material unit/kind differs: " + row["material_id"])
        for row in manifest["suppliers"]:
            kind = conn.execute(text("SELECT data_kind FROM suppliers WHERE supplier_id=:supplier_id"), row).scalar_one_or_none()
            if kind is not None and kind != "ACTUAL":
                raise ValueError("Existing supplier is not ACTUAL: " + row["supplier_id"])
        receipt["before"] = {table: conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() for table in receipt["inserted"]}
        if args.apply:
            conn.execute(text("SET LOCAL standard_conforming_strings = on"))
            for statement in inserts:
                table = "suppliers" if statement.startswith("INSERT INTO suppliers (") else "price_records"
                # The reviewed literal SQL can contain URL escapes such as %20.
                receipt["inserted"][table].extend(dict(r) for r in conn.exec_driver_sql(
                    statement, execution_options={"no_parameters": True}).mappings())
        receipt["after"] = {table: conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() for table in receipt["inserted"]}
    receipt["committed"] = args.apply
    filename = "db_apply_receipt.json" if args.apply else "db_preflight.json"
    if args.sql.stem != "06_demo_actual":
        filename = args.sql.stem + ("_apply_receipt.json" if args.apply else "_preflight.json")
    (HERE / filename).write_text(json.dumps(receipt, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"database": receipt["database"], "committed": receipt["committed"],
                      "before": receipt["before"], "after": receipt["after"],
                      "inserted": {k: len(v) for k, v in receipt["inserted"].items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
