"""Collector của một lượt focused được 01 cấp; không chạy full, DB hoặc CAD thật."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/g8_detail/area_producer"
if len(sys.argv) > 1:
    OUT = OUT / sys.argv[1]
OUT.mkdir(parents=True, exist_ok=True)


def hashes():
    paths = [p for folder in ("src", "scripts", "tests") for p in (ROOT / folder).rglob("*.py")]
    paths += [p for folder in ("data/catalog", "data/rules", "data/ground_truth")
              for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix.lower() in (".csv", ".json")]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}


before = hashes()
(OUT / "focused_hash_before.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
env = dict(os.environ)
for key in ("DATABASE_URL", "OPTIMAT_TEST_DATABASE_URL", "OPTIMAT_CATALOG_OVERLAY"):
    env.pop(key, None)
env.update(OPTIMAT_NO_DOTENV="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
files = ["test_rough_area_details.py", "test_rough_areas.py", "test_rough_partial.py", "test_rough_takeoff.py", "test_rough_quantity_details.py"]
cmd = [sys.executable, "-m", "pytest", *["tests/" + f for f in files], "-ra", "-p", "no:cacheprovider",
       "-o", "faulthandler_timeout=120", "--basetemp=" + str(OUT / "pytest_temp")]
start = time.monotonic()
with (OUT / "focused.log").open("w", encoding="utf-8") as log:
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    (OUT / "process.json").write_text(json.dumps({"pid": proc.pid, "command": cmd,
        "started_utc": datetime.now(timezone.utc).isoformat(), "no_db": True,
        "no_dotenv": True, "metadata_catalog": "Catalog.from_csv(None)",
        "test_overlay": "tests/conftest.py có thể dùng data/sample/catalog cho các hồi quy cũ"},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PID={proc.pid}", flush=True)
    code = proc.wait()
    log.write(f"\nEXIT={code}\n")
after = hashes()
(OUT / "focused_hash_after.json").write_text(json.dumps(after, indent=2), encoding="utf-8")
delta = {"changed": [p for p in before if p in after and before[p] != after[p]],
         "added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after))}
log_text = (OUT / "focused.log").read_text(encoding="utf-8")
counts = {name: int(found[-1]) if (found := re.findall(r"(\d+) " + name + r"\b", log_text)) else 0
          for name in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed")}
result = {"exit_code": code, "elapsed_seconds": round(time.monotonic()-start, 2), "counts": counts,
          "collected": re.findall(r"collected (\d+) items?", log_text),
          "hash_before_count": len(before), "hash_after_count": len(after), "hash_diff": delta}
(OUT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False), flush=True)
sys.exit(code)
