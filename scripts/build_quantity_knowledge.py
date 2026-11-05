"""Đóng gói bản OCR, bảng và quy tắc đã thu thập thành dữ liệu JSON cho OptiMat."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from quantity_completion import BasisResolver
from quantity_semantic_tables import normalize_table

ROOT = Path(__file__).resolve().parents[1]
VERSION = "optimat.quantity-knowledge.v1"
WORK_MAP = {"dat": ["DAO_DAT", "DAP_DAT"], "xay": ["XAY"], "be_tong": ["LANH_TO", "COT", "DAM", "SAN", "CAU_THANG", "GIANG_TUONG", "SE_NO", "MAI", "MONG", "BE_TONG_LOT"],
            "van_khuon": ["COP_PHA"], "cot_thep": ["COT_THEP"], "hoan_thien": ["TRAT", "CAN_NEN"],
            "trat_op_lat": ["TRAT", "CAN_NEN"], "cua_tran_mai": ["MAI"], "gian_giao": ["COP_PHA"]}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def clean(text):
    return " ".join((text or "").split())


def table_decimal(text):
    text = clean(text)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", text) and not text.startswith("0."):
        return str(Decimal(text.replace(".", "").replace(",", ".")))
    if re.fullmatch(r"-?\d+(?:[.,]\d+)?", text):
        return str(Decimal(text.replace(",", ".")))
    return None


def header_path(table, row, col):
    box = next(c["bbox_pt"] for c in table["cells"] if c["row"] == row and c["column"] == col)
    if not box:
        return []
    center = (box[0] + box[2]) / 2
    parts = []
    first_body = next((i for i, r in enumerate(table["grid"]) if re.search(r"[A-Z]{2}\s*\.\s*\d|\d{2}\.\d", r[0] or "")), row)
    for ri in range(first_body):
        for c in table["cells"]:
            b = c["bbox_pt"]
            if c["row"] == ri and b and b[0] <= center <= b[2] and c["text_raw"]:
                text = clean(c["text_raw"])
                if text not in parts:
                    parts.append(text)
    return parts


def scalar_material_rows(table):
    """Bảng vật liệu theo hàng: chỉ bung khi số dòng tên/đơn vị/số lượng khớp hoàn toàn."""
    if table["source_id"] != "TT38_2026_8" or table["columns"] != 5:
        return []
    rows = table["grid"]
    header = str(rows[:2])
    if "Số" not in header or "lượng" not in header or "Đơn" not in header:
        return []
    records = []
    for ri, row in enumerate(rows):
        code = clean(row[0])
        if not re.fullmatch(r"\d{2}\.\d{5}", code):
            continue
        names, units, quantities = [(s or "").splitlines() for s in row[2:5]]
        if not names or not len(names) == len(units) == len(quantities):
            continue
        for n, (name, unit, raw) in enumerate(zip(names, units, quantities)):
            if not re.fullmatch(r"\d+(?:,\d+)?", clean(raw)):
                continue
            records.append({"source_id": table["source_id"], "pdf_page": table["pdf_page"], "table_id": table["table_id"],
                            "norm_code": code, "resource_name": clean(name), "resource_kind": "material",
                            "resource_unit": {"m³": "m3", "m²": "m2", "tấn": "t", "lít": "l"}.get(clean(unit), clean(unit)),
                            "quantity": str(Decimal(clean(raw).replace(",", "."))), "quantity_raw": raw,
                            "value_type": "percentage" if clean(unit) == "%" else "resource_quantity", "value_status": "numeric",
                            "basis": None, "conditions_raw": row[1], "grid_row": ri, "grid_column": 4,
                            "resource_line_index": n, "review_status": "structure_checked_pending_review", "enabled": False})
    return records


def normalize_resource(record, table, source, labels):
    r = dict(record)
    ri, ci = r["grid_row"], r["grid_column"]
    matrix = isinstance(r["conditions_raw"], str) and "resource_line_index" not in r
    wrapped = False
    if matrix:
        code_text = re.sub(r"([A-Z]{2})\s*\.\s*(?=\d)", r"\1.", table["grid"][ri][0] or "")
        prefixes = re.findall(r"[A-Z]{2}\.\d{2,5}", re.sub(r"(?<=\d) +(?=\d)", "", code_text))
        last = table["grid"][-1]
        numeric_cols = [i for i, value in enumerate(last) if re.fullmatch(r"\d{1,3}", clean(value))]
        if len(prefixes) not in (1, len(numeric_cols)) or ci not in numeric_cols:
            return None
        prefix = prefixes[0] if len(prefixes) == 1 else prefixes[numeric_cols.index(ci)]
        r["norm_code"] = prefix + clean(last[ci])
        if not re.fullmatch(r"[A-Z]{2}\.\d{5}", r["norm_code"]):
            return None
        unit_col = min(numeric_cols) - 1
        names = [clean(x) for x in (table["grid"][ri][unit_col - 1] or "").splitlines()
                 if clean(x) not in ("Vật liệu", "Máy thi công")]
        units = (table["grid"][ri][unit_col] or "").splitlines()
        wrapped = len(names) != len(units)
    if isinstance(r["conditions_raw"], str):
        r["conditions_raw"] = header_path(table, ri, ci)
        r["work_description_raw"] = table["grid"][ri][1]
    else:
        conditions = dict(r["conditions_raw"])
        codes = re.findall(r"11\.\d{5}", table["grid"][ri][0] or "")
        grades = (table["grid"][ri][2] or "").splitlines()
        if len(codes) == len(grades) and r["norm_code"] in codes:
            conditions["grade"] = clean(grades[codes.index(r["norm_code"])])
        r["conditions_raw"] = conditions
    r["source_bbox_pt"] = next(c["bbox_pt"] for c in table["cells"] if c["row"] == ri and c["column"] == ci)
    if not r["basis"]:
        explicit = list(re.finditer(r"Đơn vị(?: tính)?\s*:\s*([^\n]+)", table["context_before"], re.I))
        if explicit:
            unit_raw = clean(explicit[-1][1])
            unit = {"m³": "m3", "m²": "m2", "tấn": "t", "lít": "l"}.get(unit_raw.split()[0], unit_raw.split()[0])
            if unit in ("m", "m2", "m3", "t", "kg", "bộ", "cái", "viên", "l", "công", "ca", "ha"):
                r["basis"] = {"quantity": "1", "unit": unit, "unit_raw": unit_raw}
    r.update(document_number=source["document_number"], source_url=source["source_url"], source_sha256=source["sha256"],
             effective_from=source["effective_from"], effective_to_exclusive=source["effective_to_exclusive"],
             quantity_per_basis_unit=None, review_issues=[])
    if matrix:
        label = labels.get(f"{r['table_id']}:{ri}:{r.get('row_y_pt')}")
        if label:
            r["resource_name_before_alignment"] = r["resource_name"]
            r["resource_name"] = label
            r["label_method"] = "nearest_unit_row_geometry"
        elif wrapped:
            r["review_issues"].append("wrapped_resource_label_alignment_requires_review")
    if re.fullmatch(r"[1-9]\d*\.\d{3}", clean(r["quantity_raw"])):
        r["number_format"] = "vi_dot_thousands"
        r["review_issues"].append("dot_thousands_separator_normalized")
    if not r["basis"]:
        r["review_issues"].append("missing_explicit_work_basis")
    elif r["value_type"] == "resource_quantity" and r["quantity"] is not None:
        r["quantity_per_basis_unit"] = str(Decimal(r["quantity"]) / Decimal(r["basis"]["quantity"]))
    if r["value_type"] == "percentage":
        r["review_issues"].append("percentage_requires_cost_base")
    if r["quantity"] is None:
        r["review_issues"].append("dash_or_empty_is_not_zero")
    return r


def normalize_rule(row, source_pages):
    r = dict(row)
    r["work_codes"] = WORK_MAP.get(r["work_group"], [])
    r["work_scope"] = "selected" if r["work_codes"] else "all" if r["work_group"] in (
        "chung", "giao_nhau", "don_vi", "truy_nguon", "lam_tron", "so_bo_tong_muc", "tong_muc", "du_toan", "bim", "phan_mem", "thanh_toan"
    ) else "outside_current_rough_module"
    r["purposes"] = ["payment"] if r["work_group"] == "thanh_toan" else ["estimate"]
    r["rule_type"] = "measurement" if r["work_codes"] else "reference"
    r["predicate"] = None
    r["effect"] = None
    r["missing_data_behavior"] = "needs_review"
    r["source_text_raw"] = source_pages[r["source_id"]][r["pdf_page"] - 1]["text"]
    r["legal_selection_note"] = "Kiểm tra chuyển tiếp, hồ sơ dự án và hợp đồng; thời gian không đủ để kết luận áp dụng."
    r["approved_by"] = None
    r["approved_on"] = None
    r["review_status"] = "candidate_requires_QS_review"
    if r["source_id"] == "TT01_2025_CONGBAO":
        r["work_codes"] = WORK_MAP["be_tong"]
        r["work_scope"] = "selected"
        r["supersedes"] = ["TT13_2021_1:Phụ lục VI II.5.4"]
    if r["source_id"] == "QD1041_2026":
        r["authority_type"] = "huong_dan_tham_khao"
    # Chỉ chuyển ngoại lệ đơn giản, có điều kiện rõ, thành biểu thức máy đọc.
    params = r["parameters"]
    if len(params) == 2 and r["work_group"] not in ("be_tong", "van_khuon"):
        key = next((k for k in params if k.endswith("_lt_m2")), None)
        if key:
            r["predicate"] = {"field": "opening_area_m2", "operator": "lt", "value": str(params[key]), "unit": "m2"}
            r["effect"] = {"action": "do_not_deduct_opening"}
    if r["work_group"] == "lam_tron":
        r["rule_type"] = "rounding"
        r["effect"] = {"action": "round_aggregate", "decimal_places": 3, "tie_breaking": "not_specified_by_source"}
    return r


def data_schema():
    decimal = {"type": "string", "pattern": r"^\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?$"}
    nullable_decimal = {"anyOf": [decimal, {"type": "null"}]}
    nullable_date = {"type": ["string", "null"], "format": "date"}
    base = {"source_id": {"type": "string", "minLength": 1}, "pdf_page": {"type": "integer", "minimum": 1}}
    bbox = {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4}
    norm = {**base, "record_id": {"type": "string"}, "table_id": {"type": "string"},
            "norm_code": {"type": "string", "pattern": r"^(?:[A-Z]{2}|\d{2})\.\d{5}$"},
            "resource_name": {"type": "string", "minLength": 1}, "resource_kind": {"enum": ["material", "labor", "machine"]},
            "resource_unit": {"type": "string"}, "quantity": nullable_decimal, "quantity_raw": {"type": "string"},
            "value_type": {"enum": ["resource_quantity", "percentage"]}, "quantity_per_basis_unit": nullable_decimal,
            "basis": {"anyOf": [{"type": "null"}, {"type": "object", "required": ["quantity", "unit", "unit_raw"],
                                                     "properties": {"quantity": decimal, "unit": {"type": "string"}, "unit_raw": {"type": "string"}}}]},
            "source_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "effective_from": nullable_date, "effective_to_exclusive": nullable_date,
            "enabled": {"type": "boolean"}, "review_status": {"type": "string"}, "review_issues": {"type": "array", "items": {"type": "string"}}}
    rule = {**base, "rule_id": {"type": "string"}, "source_locator": {"type": "string"}, "summary_vi": {"type": "string"},
            "work_codes": {"type": "array", "items": {"type": "string"}}, "work_scope": {"enum": ["all", "selected", "outside_current_rough_module"]},
            "purposes": {"type": "array", "items": {"enum": ["estimate", "payment"]}},
            "predicate": {"type": ["object", "null"]}, "effect": {"type": ["object", "null"]},
            "effective_from": nullable_date, "effective_to_exclusive": nullable_date,
            "enabled": {"type": "boolean"}, "review_status": {"type": "string"}}
    table = {**base, "table_id": {"type": "string"}, "bbox_pt": bbox, "rows": {"type": "integer", "minimum": 2},
             "columns": {"type": "integer", "minimum": 1}, "grid": {"type": "array", "items": {"type": "array", "items": {"type": ["string", "null"]}}},
             "cells": {"type": "array", "items": {"type": "object", "required": ["row", "column", "text_raw", "bbox_pt", "decimal"],
                        "properties": {"row": {"type": "integer", "minimum": 0}, "column": {"type": "integer", "minimum": 0},
                                       "text_raw": {"type": ["string", "null"]}, "bbox_pt": {"anyOf": [bbox, {"type": "null"}]}, "decimal": {"type": ["string", "null"]}}}}}
    page = {**base, "text": {"type": "string"}, "method": {"enum": ["native_pdf", "tesseract_vie"]},
            "mean_word_confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 100}, "review_status": {"type": "string"}}
    reference = {**base, "table_id": {"type": "string"}, "table_kind": {"enum": ["classification", "material_property", "document_index", "resource_matrix", "labor_matrix", "coefficient_lookup", "layout_fragment", "narrative_note", "cost_rate"]},
                 "column_paths": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                 "records": {"type": "array", "items": {"type": "object", "required": ["row", "physical_row", "key_raw", "fields"],
                             "properties": {"row": {"type": "integer", "minimum": 0}, "physical_row": {"type": "integer", "minimum": 0},
                                            "key_raw": {"type": "string"}, "fields": {"type": "array", "items": {"type": "object", "required": ["column", "header_path", "text_raw", "decimal", "bbox_pt", "lines"]}}}}},
                 "resources": {"type": "array", "items": {"type": "object", "required": ["source_id", "pdf_page", "table_id", "resource_name", "resource_unit", "quantity", "source_codes", "basis", "basis_evidence"],
                               "properties": {"quantity": nullable_decimal, "resource_name": {"type": "string", "minLength": 1}, "resource_unit": {"type": "string", "minLength": 1}, "basis": norm["basis"]}}},
                 "source_sha256": norm["source_sha256"], "enabled": {"type": "boolean"}, "review_status": {"type": "string"}}
    basis_resolution = {"record_id": {"type": "string"}, "table_id": {"type": "string"}, "basis": norm["basis"],
                        "evidence": {"type": "object", "required": ["source_id", "pdf_page", "quote", "method"],
                                     "properties": {**base, "quote": {"type": "string", "minLength": 1}, "method": {"type": "string"}}}}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:optimat:quantity-knowledge:v1",
            "description": "Chọn $defs theo loại bản ghi; JSONL mỗi dòng là một đối tượng.",
            "$defs": {name: {"type": "object", "required": list(props), "properties": props}
                      for name, props in [("norm", norm), ("measurement_rule", rule), ("table", table), ("page", page), ("reference_table", reference), ("basis_resolution", basis_resolution)]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "data/rules/vn_quantity")
    args = ap.parse_args()
    source, out = args.source.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    registry = read(source / "danh-muc-nguon.json")
    sources = {r["source_id"]: r for r in registry}
    native = {p.stem: read(p) for p in (source / "02-van-ban-trich-xuat").glob("*.json")}
    ocr = {(p.parent.name, int(p.stem[1:])): read(p) for p in (source / "05-ocr").glob("*/p*.json")}
    pages, ocr_counts = [], Counter()
    for sid, rows in native.items():
        for row in rows:
            record = {"source_id": sid, "pdf_page": row["page"], "text": row["text"], "method": "native_pdf",
                      "review_status": "native_text_unreviewed", "mean_word_confidence": None, "source_sha256": sources[sid]["sha256"]}
            if (sid, row["page"]) in ocr:
                scanned = ocr[sid, row["page"]]
                record.update(text=scanned["text"], method="tesseract_vie", review_status=scanned["review_status"],
                              mean_word_confidence=scanned["mean_word_confidence"])
                ocr_counts[scanned["review_status"]] += 1
            pages.append(record)
    for sid, s in sources.items():
        s["ocr_pages"] = sum(key[0] == sid for key in ocr)
        if s["ocr_pages"]:
            s["extraction_status"] = "native_and_ocr_unreviewed"
    write(out / "sources.json", list(sources.values()))
    with (out / "page_text.jsonl").open("w", encoding="utf-8") as f:
        for row in sorted(pages, key=lambda r: (r["source_id"], r["pdf_page"])):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    rules = [normalize_rule(r, native) for r in read(source / "03-du-lieu-module/quy-tac-ung-vien.json")]
    write(out / "measurement_rules.json", rules)
    write(out / "applicability.json", read(source / "03-du-lieu-module/ho-so-ap-dung.json"))
    tables = {}
    for line in (source / "06-bang-dinh-muc/tables.jsonl").read_text(encoding="utf-8").splitlines():
        t = json.loads(line)
        tables[t["table_id"]] = t
    labels = read(source / "06-bang-dinh-muc/resource-labels.json")
    with (out / "tables.jsonl").open("w", encoding="utf-8") as stream:
        for table in tables.values():
            for cell in table["cells"]:
                cell["decimal"] = table_decimal(cell["text_raw"])
                cell["decimal_lines"] = [table_decimal(line) for line in (cell["text_raw"] or "").splitlines()]
            stream.write(json.dumps(table, ensure_ascii=False) + "\n")
    resource_rows = [json.loads(line) for line in (source / "06-bang-dinh-muc/resources-v2.jsonl").read_text(encoding="utf-8").splitlines()]
    for t in tables.values():
        resource_rows.extend(scalar_material_rows(t))
    norms, represented = [], set()
    for n, row in enumerate(resource_rows, 1):
        record = normalize_resource(row, tables[row["table_id"]], sources[row["source_id"]], labels)
        if record is None:
            continue
        record["record_id"] = f"VN-NORM-{len(norms) + 1:06}"
        norms.append(record)
        represented.add(row["table_id"])
    resolver = BasisResolver(tables, native)
    missing_before = [r["record_id"] for r in norms if r["basis"] is None]
    evidence_rows = []
    for record in norms:
        if record["basis"] is None and (resolved := resolver.resolve(record)):
            record["basis"], record["basis_evidence"] = resolved
            record["review_issues"].remove("missing_explicit_work_basis")
            if record["value_type"] == "resource_quantity" and record["quantity"] is not None:
                record["quantity_per_basis_unit"] = str(Decimal(record["quantity"]) / Decimal(record["basis"]["quantity"]))
            evidence_rows.append({"record_id": record["record_id"], "table_id": record["table_id"], "basis": record["basis"], "evidence": record["basis_evidence"]})
    pending_tables = sorted(set(tables) - represented)
    reference_tables = []
    for tid in pending_tables:
        table = tables[tid]
        cache = source / f"07-hoan-thien/words/{table['source_id']}/p{table['pdf_page']:04}.json"
        page_words = read(cache)
        if page_words["source_id"] != table["source_id"] or page_words["pdf_page"] != table["pdf_page"]:
            raise ValueError(f"Cache tọa độ không khớp trang PDF: {tid}")
        semantic = normalize_table(table, page_words["words"], resolver)
        origin = sources[table["source_id"]]
        semantic.update(document_number=origin["document_number"], source_url=origin["source_url"], source_sha256=origin["sha256"])
        reference_tables.append(semantic)
        for item in semantic["resources"]:
            # Mã bảng cấp phối dạng B/C/AO được giữ nguyên ở bảng tham chiếu; không tự chế mã công tác.
            if item["norm_code"] is None or item["basis"] is None:
                continue
            row = dict(item)
            origin = sources[row["source_id"]]
            row.update(record_id=f"VN-NORM-{len(norms) + 1:06}", document_number=origin["document_number"],
                       source_url=origin["source_url"], source_sha256=origin["sha256"],
                       effective_from=origin["effective_from"], effective_to_exclusive=origin["effective_to_exclusive"],
                       quantity_per_basis_unit=None, review_issues=[])
            if row["resource_name"].startswith("Nếu dùng"):
                row["review_issues"].append("conditional_resource_do_not_sum_alternatives")
            if row["quantity"] is not None and row["value_type"] == "resource_quantity":
                row["quantity_per_basis_unit"] = str(Decimal(row["quantity"]) / Decimal(row["basis"]["quantity"]))
            if row["value_type"] == "percentage":
                row["review_issues"].append("percentage_requires_cost_base")
            if row["quantity"] is None:
                row["review_issues"].append("dash_or_empty_is_not_zero")
            norms.append(row)
            represented.add(tid)
    with (out / "reference_tables.jsonl").open("w", encoding="utf-8") as stream:
        for t in reference_tables:
            stream.write(json.dumps(t, ensure_ascii=False) + "\n")
    write(out / "basis_evidence.json", evidence_rows)
    values = defaultdict(set)
    for r in norms:
        values[(r["source_id"], r["norm_code"], r["resource_name"], r["resource_unit"])].add(r["quantity"])
    conflicts = {key for key, numbers in values.items() if len(numbers) > 1}
    for r in norms:
        if (r["source_id"], r["norm_code"], r["resource_name"], r["resource_unit"]) in conflicts:
            r["review_issues"].append("conflicting_values_require_variant_or_code_review")
    with (out / "norms.jsonl").open("w", encoding="utf-8") as f:
        for row in norms:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    review = {"ocr": dict(ocr_counts), "tables_total": len(tables), "tables_with_resource_records": len(represented),
              "tables_grid_only": len(set(tables) - represented - {t['table_id'] for t in reference_tables}),
              "tables_without_indexed_norms": len(tables) - len(represented), "resource_records": len(norms),
              "completion": {"initial_unparsed_tables": len(pending_tables), "typed_tables": len(reference_tables),
                             "table_kinds": dict(Counter(t["table_kind"] for t in reference_tables)),
                             "initial_missing_basis": len(missing_before), "basis_added_with_evidence": len(evidence_rows),
                             "initial_rows_still_missing_basis": len(missing_before) - len(evidence_rows),
                             "auxiliary_resource_records": sum(len(t["resources"]) for t in reference_tables),
                             "auxiliary_records_missing_basis": sum(r["basis"] is None for t in reference_tables for r in t["resources"])},
              "norm_codes": len({r["norm_code"] for r in norms}), "resource_issues": dict(Counter(issue for r in norms for issue in r["review_issues"])),
              "conflicting_code_resource_keys": [list(k) for k in sorted(conflicts)],
              "ocr_low_confidence_pages": [{"source_id": s, "pdf_page": p, "mean_word_confidence": o["mean_word_confidence"]}
                                           for (s, p), o in ocr.items() if o["review_status"] == "ocr_low_confidence"],
              "grid_only_tables": sorted(set(tables) - represented - {t['table_id'] for t in reference_tables}),
              "note": "Bảng còn lại đã có kiểu, trục cột, hàng và giá trị có tọa độ; mục lục/ghi chú không phải định mức hao phí. Tất cả bản ghi còn chờ duyệt chuyên môn."}
    write(out / "quality_report.json", review)
    write(out / "schema.json", data_schema())
    filenames = ["sources.json", "page_text.jsonl", "measurement_rules.json", "applicability.json", "tables.jsonl", "norms.jsonl", "quality_report.json", "schema.json", "reference_tables.jsonl", "basis_evidence.json"]
    files = {name: {"sha256": hashlib.sha256((out / name).read_bytes()).hexdigest(), "bytes": (out / name).stat().st_size} for name in filenames}
    manifest = {"schema_version": VERSION, "dataset_version": "2026-11-04.complete2", "production_ready": False,
                "default_enabled": False, "source_bundle": source.name, "files": files,
                "counts": {"sources": len(sources), "pdf_pages": len(pages), "ocr_pages": len(ocr), "rules": len(rules),
                           "tables": len(tables), "resource_records": len(norms), "norm_codes": review["norm_codes"]},
                "decimal_policy": "Decimal strings; dấu phẩy đổi sang dấu chấm; dấu gạch và ô trống không đổi thành 0.",
                "legal_selection": "Phải xét mục đích, thời gian, chuyển tiếp, hồ sơ được duyệt và hợp đồng.",
                "runtime_integration": "optimat.rough.quantity_knowledge.QuantityKnowledge"}
    write(out / "manifest.json", manifest)
    print(json.dumps(manifest["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
