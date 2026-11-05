"""Sinh SQL bổ sung ACTUAL từ bảng duyệt + biên nhận import cũ; không kết nối DB.

    .venv/Scripts/python.exe reports/demo_0511/build_demo_actual_sql.py

Không thực thi SQL dump bằng chứng; chỉ đọc các INSERT price_records dạng pg_dump.
Ngày/VAT/điều kiện giữ từ lần nhập nguồn, không suy theo tên file CSV.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from optimat.catalog.bulletin import load_rules, supplier_id, text_key, unit_key


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_evidence(path):
    """Chỉ đọc literal INSERT đúng bảng; không chạy bất kỳ câu SQL nào."""
    rows = []
    pattern = re.compile(r"^INSERT INTO public\.price_records \(([^)]+)\) VALUES \((.*)\);$")
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        match = pattern.fullmatch(line)
        if not match:
            continue
        columns = [c.strip() for c in match[1].split(",")]
        values = next(csv.reader(io.StringIO(match[2]), quotechar="'", doublequote=True, skipinitialspace=True))
        if len(columns) != len(values):
            raise ValueError("Biên nhận INSERT không đúng số cột")
        row = dict(zip(columns, values))
        if row.get("data_kind") == "ACTUAL" and row.get("price_level") == "BULLETIN":
            rows.append(row)
    if not rows:
        raise ValueError("Không có biên nhận ACTUAL/BULLETIN để xác nhận metadata")
    return rows


def positive(value, field):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field}: cần số dương hữu hạn") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field}: cần số dương hữu hạn")
    return number


def prepare(rows, materials, rules, evidence):
    """Dòng không ghép mã/đang bị từ chối bỏ qua; dòng đã ghép nhưng sai phải dừng."""
    suppliers, prices, seen = {}, [], set()
    skipped = 0
    for row in rows:
        if not row.get("material_id") or row.get("ly_do", "").strip():
            skipped += 1
            continue
        if row.get("data_kind", "ACTUAL") != "ACTUAL":
            raise ValueError("Không nhận dữ liệu khác ACTUAL")
        mid = row["material_id"]
        material, rule = materials.get(mid), rules.get(row.get("quy_tac"))
        if not material or material.get("data_kind") != "ACTUAL" or not material.get("unit"):
            raise ValueError(f"{mid}: thiếu vật liệu ACTUAL/đơn vị danh mục")
        name, raw_unit = row.get("ten", ""), row.get("don_vi", "")
        key = text_key(name)
        if (not rule or rule.material_id != mid or not rule.pattern.search(key)
                or (rule.exclude and rule.exclude.search(key)) or unit_key(raw_unit) not in rule.units):
            raise ValueError(f"{mid}: mapping không khớp quy tắc/đơn vị nguồn")
        amount = positive(row.get("gia_theo_dvt_danh_muc"), mid)
        if not math.isclose(amount, positive(row.get("gia"), mid) * rule.factor, rel_tol=1e-10):
            raise ValueError(f"{mid}: giá quy đổi không khớp hệ số nguồn")
        supplier = row.get("nha_cung_cap", "").strip()
        if not supplier or not name or not row.get("trang", "").isdigit() or int(row["trang"]) < 1:
            raise ValueError(f"{mid}: thiếu nhà cung cấp/tên/trang nguồn")
        sid = supplier_id(supplier)
        tail = f", tr.{row['trang']}: {name} ({raw_unit})"
        matches = [e for e in evidence if e.get("material_id") == mid and e.get("supplier_id") == sid
                   and e.get("source", "").endswith(tail)]
        if len(matches) != 1:
            raise ValueError(f"{mid}: cần đúng một biên nhận metadata có nguồn")
        old = matches[0]
        # Metadata được giữ nguyên từ lần nhập đã có, không suy ngày/tháng từ tên file.
        import datetime
        import_date = datetime.date.fromisoformat(old["date"]).isoformat()
        if (old.get("unit") != material["unit"] or not math.isclose(positive(old.get("unit_price"), mid), amount)
                or positive(old.get("quantity"), mid) != 1 or not old.get("province")
                or not old["source"].startswith("Công bố giá ")
                or old.get("vat_included") not in {"YES", "NO", "UNKNOWN"}
                or old.get("transport_included") not in {"YES", "NO", "UNKNOWN"}):
            raise ValueError(f"{mid}: biên nhận khác giá/đơn vị/điều kiện đã duyệt")
        record = {"date": import_date, "material_id": mid, "supplier_id": sid, "province": old["province"],
                  "quantity": 1.0, "unit": material["unit"], "unit_price": amount,
                  "vat_included": old["vat_included"], "transport_included": old["transport_included"],
                  "source": old["source"], "data_kind": "ACTUAL", "price_level": "BULLETIN"}
        natural = (mid, sid, import_date, 1.0, old["source"])
        if natural in seen:
            raise ValueError(f"{mid}: bảng duyệt lặp khóa nguồn")
        seen.add(natural)
        prices.append(record)
        suppliers.setdefault(sid, {"supplier_id": sid, "name": supplier[:255], "province": old["province"],
                                  "lat": None, "lon": None, "lead_time_days": None, "data_kind": "ACTUAL",
                                  "verified": False, "collected_at": import_date,
                                  "source": old["source"].removesuffix(tail)})
    return list(suppliers.values()), prices, skipped


def literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ValueError("Không ghi số vô hạn vào SQL")
        return repr(value)
    if "\x00" in str(value):
        raise ValueError("Không ghi NUL vào SQL")
    return "'" + str(value).replace("'", "''") + "'"


def render_sql(suppliers, prices):
    lines = ["-- ACTUAL có nguồn; BULLETIN không phải báo giá mua/giao hàng hiện tại.",
             "-- Chỉ thêm; xung đột giữ nguyên dữ liệu DB. Không UPDATE/DELETE/schema.",
             "-- Chạy cả script trong một transaction. PostgreSQL hiện hành cần có schema/danh mục.",
             "BEGIN;", "SET LOCAL standard_conforming_strings = on;"]
    for table, rows in (("suppliers", suppliers), ("price_records", prices)):
        if not rows:
            continue
        columns = list(rows[0])
        returning = "supplier_id" if table == "suppliers" else "id, material_id, supplier_id, date, quantity, source"
        for row in rows:
            lines.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(literal(row[c]) for c in columns)}) ON CONFLICT DO NOTHING RETURNING {returning};")
    lines.extend(["COMMIT;", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=ROOT / "data/cong_bo_gia/02.01_2026_CBGVL-SXD.csv")
    parser.add_argument("--materials", type=Path, default=ROOT / "data/catalog/materials.csv")
    parser.add_argument("--rules", type=Path, default=ROOT / "data/rules/cong_bo_gia.csv")
    parser.add_argument("--evidence", type=Path, default=ROOT / "sql/optimat_day_du.sql")
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("06_demo_actual.sql"))
    args = parser.parse_args()
    sources = {name: {"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
               for name, path in (("csv", args.csv), ("materials", args.materials), ("rules", args.rules), ("metadata_evidence", args.evidence))}
    suppliers, prices, skipped = prepare(read_csv(args.csv), {r["material_id"]: r for r in read_csv(args.materials)},
                                        {r.rule_id: r for r in load_rules(args.rules)}, read_evidence(args.evidence))
    sql = "-- Nguồn/sha256: " + json.dumps(sources, ensure_ascii=False) + "\n" + render_sql(suppliers, prices)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(sql, encoding="utf-8")
    manifest = {"sources": sources, "suppliers": suppliers, "price_records": prices, "skipped_unmapped_or_rejected": skipped,
                "sql_sha256": hashlib.sha256(sql.encode()).hexdigest(), "executed": False,
                "rollback": "Chỉ rollback ID/khóa thực sự INSERT RETURNING ở lượt apply; manifest là ứng viên, không được DELETE mọi khóa ứng viên."}
    args.out.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"suppliers_candidates": len(suppliers), "prices_candidates": len(prices), "skipped": skipped,
                      "dates": sorted({p['date'] for p in prices}), "executed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
