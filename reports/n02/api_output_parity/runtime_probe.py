"""Probe HTTP SYNTHETIC; không mock compute/BOQ/export hoặc ghi dữ liệu nguồn."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import time
import traceback
from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
for key in ("DATABASE_URL", "OPTIMAT_TEST_DATABASE_URL", "OPTIMAT_CATALOG_OVERLAY"):
    os.environ.pop(key, None)
os.environ.update(OPTIMAT_NO_DOTENV="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot():
    paths = set()
    for folder in ("src", "scripts", "tests"):
        paths.update((ROOT / folder).rglob("*.py"))
    for folder in ("data/catalog", "data/rules"):
        paths.update((ROOT / folder).rglob("*.csv"))
    for suffix in ("*.csv", "*.json"):
        paths.update((ROOT / "data/ground_truth").rglob(suffix))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def records(workbook, sheet):
    rows = list(workbook[sheet].values)
    return [dict(zip(rows[0], row)) for row in rows[1:]]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    if (OUT / "report.json").exists():
        raise RuntimeError("Report exists; refusing implicit rerun")
    before = snapshot()
    save("hash_before.json", before)
    started = time.monotonic()
    report = {"fixture_kind": "SYNTHETIC", "cases": [], "failures": []}
    try:
        from fastapi.testclient import TestClient
        from openpyxl import load_workbook
        from optimat.api import main as api
        from optimat.catalog import pricing
        from optimat.catalog.repository import Catalog
        from optimat.rough import takeoff
        from optimat.rough.models import ProjectParams
        from optimat.rough.takeoff import RoughRequest

        fixture = runpy.run_path(str(ROOT / "tests/test_rough_partial.py"))
        rows_for = fixture["rows_for"]
        original = Catalog.from_csv(None)
        mats = original.materials.copy(deep=True)
        mats.loc[mats.material_id == "TH10", "waste_pct"] = 0
        catalog = replace(original, materials=mats)
        check(api.compute_rough is takeoff.compute_rough, "main.compute_rough must be real compute_rough")
        save("environment.json", {
            "python": sys.version, "command": [sys.executable, str(Path(__file__).resolve())],
            "DATABASE_URL_present": bool(os.environ.get("DATABASE_URL")),
            "OPTIMAT_TEST_DATABASE_URL_present": bool(os.environ.get("OPTIMAT_TEST_DATABASE_URL")),
            "OPTIMAT_NO_DOTENV": os.environ["OPTIMAT_NO_DOTENV"], "outside_sandbox": True,
            "patches": ["takeoff.default_catalog -> CSV catalog copy in RAM; TH10 waste_pct=0",
                        "pricing.price_offers -> TH10 SYNTHETIC QUOTE 100/kg"],
            "compute_boq_export_mocked": False,
            "fixture_source": "tests/test_rough_partial.py::rows_for via runpy; no pytest invocation",
            "outside_hash_scope": ["frontend", "SQL", "docs", "other reports"],
        })
        offer = SimpleNamespace(price=100, unit="kg", price_level="QUOTE", supplier_name="SYNTHETIC",
                                price_date="", data_kind="SYNTHETIC")
        cases = [
            ("pending_two_tables", (None, None), None, True, 0.063, 0.753),
            ("pending_manual_00632", (None, None), 0.0632, True, 0.063, 0.753),
            ("resolved_same_scope", (1, 1), None, False, 0.032, 0.383),
            ("resolved_two_floors", (1, 2), None, False, 0.063, 0.753),
        ]
        # Chỉ patch dữ liệu catalog/giá trong RAM; ba endpoint gọi nguyên compute/BOQ/export thật.
        with patch.object(takeoff, "default_catalog", return_value=catalog), \
             patch.object(pricing, "price_offers", return_value={"TH10": [offer]}), \
             TestClient(api.app) as client:
            for name, levels, manual, pending, steel_qty, wire_qty in cases:
                row = {"case": name, "status": "RUNNING", "http": {}}
                report["cases"].append(row)
                try:
                    req = RoughRequest(plans=[], rebar=rows_for(levels), project_id=None,
                                       params=ProjectParams(steel_schedule_t={} if manual is None else {"DAM": manual}))
                    payload = req.model_dump(mode="json")
                    save(name + "_request.json", payload)
                    responses = {}
                    for label, suffix in (("json", ""), ("excel", "/excel"), ("optimizer", "/optimizer")):
                        response = client.post("/api/takeoff/rough" + suffix, json=payload)
                        row["http"][label] = response.status_code
                        responses[label] = response
                        if label == "excel" and response.status_code == 200:
                            (OUT / (name + ".xlsx")).write_bytes(response.content)
                        else:
                            save(name + "_" + label + "_response.json", response.json())
                    check(all(status == 200 for status in row["http"].values()), str(row["http"]))
                    data = responses["json"].json()
                    optimizer = responses["optimizer"].json()
                    wb = load_workbook(BytesIO(responses["excel"].content), data_only=True)
                    total = next(t for t in data["totals"] if t["code"] == "COT_THEP")
                    steel = next(w for w in data["works"] if w["code"] == "COT_THEP")
                    wire = next(m for m in data["materials"] if m["material_id"] == "TH10")
                    excel_total = next(r for r in records(wb, "Tổng hợp") if r["Mã"] == "COT_THEP")
                    excel_wire = next(r for r in records(wb, "Vật liệu") if r["Mã"] == "TH10")
                    excel_steel = [r for r in records(wb, "Theo tầng") if r["Công tác"] == steel["name"]]
                    check(total["quantity"] == steel_qty and total["complete"] is (not pending), "COT_THEP total mismatch")
                    check(excel_total["Khối lượng"] == total["quantity"], "Excel/JSON steel quantity")
                    check(excel_total["Đủ số"] == ("có" if total["complete"] else "thiếu"), "Excel/JSON steel completeness")
                    check(excel_total["Trạng thái"].startswith(total["status"] + " "), "Excel/JSON steel status")
                    check(len(excel_steel) == 1, "Expected one aggregate steel work in Excel")
                    check((excel_steel[0]["missing_reason"] or "") == "; ".join(steel["missing"]), "Excel/JSON steel missing reasons")
                    check(wire["quantity"] == wire_qty and wire["complete"] is (not pending), "TH10 quantity/completeness")
                    check(wire["best_price"] == 100 and "SYNTHETIC" in wire["price_source"], "SYNTHETIC reference price")
                    check(wire["est_cost"] == (None if pending else round(wire_qty * 100)), "Partial cost must stay None; resolved cost must match")
                    check(excel_wire["Khối lượng"] == wire["quantity"], "Excel/JSON wire quantity")
                    check(excel_wire["Đủ số"] == ("thiếu" if pending else "có"), "Excel wire complete label")
                    check(excel_wire["Trạng thái"].startswith(wire["status"] + " "), "Excel/JSON wire status")
                    check((excel_wire["missing_reason"] or "") == "; ".join(wire["missing"]), "Excel wire missing reason parity")
                    if pending:
                        check(total["status"] == "D" and steel["missing"], "Pending steel must remain D with reason")
                        check(wire["status"] == "D" and any("chờ xác nhận" in s for s in wire["missing"]), "Pending wire must retain scope reason")
                        check(not any(m["material_id"] == "TH10" for m in optimizer["materials"]), "Partial wire must not be exported as complete optimizer quantity")
                        missing = next(m for m in optimizer["missing"] if m["material_id"] == "TH10")
                        check(missing["known_part"] == wire["quantity"] and missing["reason"] == "; ".join(wire["missing"]), "optimizer known_part/reason mismatch")
                    else:
                        check(wire["status"] != "D" and not any("chờ xác nhận" in s for s in wire["missing"]), "Resolved wire still pending")
                        material = next(m for m in optimizer["materials"] if m["material_id"] == "TH10")
                        check(material["quantity"] == wire["quantity"] and material["status"] == wire["status"], "Resolved optimizer wire parity")
                        check(not any(m["material_id"] == "TH10" for m in optimizer["missing"]), "Resolved wire still in optimizer missing")
                    group = next(g for g in data["by_group"] if g["group_id"] == wire["group_id"])
                    group_row = next(r for r in records(wb, "Theo nhóm") if r["Nhóm"] == wire["group_id"])
                    expected_label = "có" if group["weight_complete"] else "chưa đủ dữ liệu khối lượng"
                    check(group_row["Đủ kg"] == expected_label, "Group partial label parity")
                    check(group_row["Đủ kg"] != "thiếu khối lượng riêng", "Obsolete density-only label")
                    row.update(status="PASS", steel_total=total, steel_missing=steel["missing"],
                               wire={k: wire[k] for k in ("quantity", "complete", "status", "missing", "best_price", "price_source", "est_cost")},
                               excel_total=excel_total, excel_wire=excel_wire, group_label=group_row["Đủ kg"],
                               optimizer_wire_in="missing" if pending else "materials")
                    wb.close()
                except Exception:
                    row["status"] = "FAIL"
                    row["traceback"] = traceback.format_exc()
                    report["failures"].append({"case": name, "traceback": row["traceback"]})
    except Exception:
        report["failures"].append({"case": "setup", "traceback": traceback.format_exc()})
    finally:
        after = snapshot()
        save("hash_after.json", after)
        diff = {"changed": [p for p in sorted(set(before) & set(after)) if before[p] != after[p]],
                "added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after))}
        save("hash_diff.json", diff)
        report.update(hash_before_count=len(before), hash_after_count=len(after), hash_diff=diff,
                      elapsed_seconds=round(time.monotonic() - started, 2),
                      passed=sum(c["status"] == "PASS" for c in report["cases"]))
        report["exit_code"] = 1 if report["failures"] or any(diff.values()) else 0
        save("report.json", report)
        (OUT / "tracebacks.log").write_text("\n".join(f["traceback"] for f in report["failures"]) or "No failures.\n", encoding="utf-8")
        print(json.dumps({k: report[k] for k in ("passed", "exit_code", "elapsed_seconds", "hash_diff")}, ensure_ascii=False), flush=True)
        for failure in report["failures"]:
            print(failure["case"] + "\n" + failure["traceback"], flush=True)
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
