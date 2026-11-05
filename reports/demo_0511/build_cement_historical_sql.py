"""Sinh gói07 từ staging đã được review; không kết nối DB."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("demo_sql", HERE / "build_demo_actual_sql.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
staging = json.loads((HERE / "cement_historical_proposed.json").read_text(encoding="utf-8"))
suppliers = [staging["supplier_candidate"]]
prices = [row["proposed_record"] for row in staging["records"]]
assert len(prices) == 4 and all(r["data_kind"] == "ACTUAL" and r["price_level"] == "BULLETIN" and r["unit"] == "tấn" and r["vat_included"] == "YES" and r["transport_included"] == "UNKNOWN" for r in prices)
paths = [HERE / n for n in ("cemia_ximang_thang3_2026.pdf", "cement_historical_proposed.json", "07_cement_review.md", "build_demo_actual_sql.py", Path(__file__).name)] + [ROOT / "data/catalog/materials.csv"]
sources = {str(p.relative_to(ROOT)): {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths}
sql = "-- Giá lịch sử17/03/2026; đãVAT; vận chuyểnUNKNOWN; không phải báo giá mua hiện hành.\n" + module.render_sql(suppliers, prices)
manifest = {"sources": sources, "suppliers": suppliers, "price_records": prices, "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(), "executed": False, "review": "Parent reviewed both page images; see07_cement_review.md", "rollback": "Only IDs actually INSERT RETURNING in the apply receipt; never all candidate keys."}
(HERE / "07_cement_historical_actual.sql").write_text(sql, encoding="utf-8")
(HERE / "07_cement_historical_actual.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"suppliers_candidates": len(suppliers), "prices_candidates": len(prices), "executed": False, "sql_sha256": manifest["sql_sha256"]}))
