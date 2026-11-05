"""Bảng còn lại -> bản ghi theo đúng ý nghĩa, giữ nguyên mã nguồn và trục điều kiện."""
from __future__ import annotations

import json
import re
from decimal import Decimal

from quantity_completion import UNIT_LABEL, clean, parse_basis, code_prefixes


def compact(text):
    return re.sub(r"\s+", "", clean(text).lower()).replace("\uf0a3", "≤").replace("\uf0b3", "≥")


def number(text):
    s = clean(text).replace("−", "-")
    if re.fullmatch(r"-?[1-9]\d{0,2}(?:\.\d{3})+(?:,\d+)?", s):
        return str(Decimal(s.replace(".", "").replace(",", ".")))
    if re.fullmatch(r"-?\d+(?:[.,]\d+)?", s):
        return str(Decimal(s.replace(",", ".")))
    return None


def text_lines(words, box):
    if not box:
        return []
    x0, y0, x1, y1 = box
    groups = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        x, y = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        if not x0 - .5 <= x <= x1 + .5 or not y0 - .5 <= y <= y1 + .5:
            continue
        target = next((g for g in groups if abs(g["y"] - y) < 3), None)
        if target is None:
            target = {"y": y, "words": []}
            groups.append(target)
        target["words"].append(w)
    return [{"y": round(g["y"], 3), "text": clean(" ".join(w["text"] for w in sorted(g["words"], key=lambda w: w["x0"]))) }
            for g in sorted(groups, key=lambda g: g["y"])]


def source_codes(text):
    text = clean(text).replace("ẠK.", "AK.")
    text = re.sub(r"\b([A-Z])\s+([A-Z])\s*\.", r"\1\2.", text)
    text = re.sub(r"([A-Z]{1,2})\s*\.\s*", r"\1.", clean(text))
    return list(dict.fromkeys(re.findall(r"[A-Z]{2}\.\d{2,5}|\d{2}\.\d{3,5}|\b[A-Z]{1,2}\d{2,4}\b", text)))


def body_start(t):
    for ri, row in enumerate(t["grid"][1:], 1):
        if any(source_codes(c) for c in row[:3]):
            return ri
    if t["rows"] > 1 and t["grid"][1][0] is None:
        return next((i for i, row in enumerate(t["grid"][1:], 1) if row[0] is not None), 1)
    return 1


def headers(t, start):
    paths = []
    for ci in range(t["columns"]):
        boxes = [c["bbox_pt"] for c in t["cells"] if c["column"] == ci and c["bbox_pt"]]
        x = next(((b[0] + b[2]) / 2 for b in boxes if b[2] - b[0] < 180), (boxes[-1][0] + boxes[-1][2]) / 2 if boxes else 0)
        labels = []
        for ri in range(start):
            cells = [c for c in t["cells"] if c["row"] == ri and c["bbox_pt"] and c["bbox_pt"][0] - .1 <= x <= c["bbox_pt"][2] + .1]
            for cell in cells:
                text = clean(cell["text_raw"])
                if text and text not in labels:
                    labels.append(text)
        paths.append(labels)
    return paths


def classify(t):
    h = compact(" ".join(cell or "" for row in t["grid"][:3] for cell in row))
    if t["columns"] == 1:
        return "layout_fragment"
    if "nộidung" in h and "trang" in h:
        return "document_index"
    if t["source_id"] == "TT38_2026_9":
        return "cost_rate"
    if "haohụt" in h or "hệsố" in h or "bùhaohụt" in h:
        return "coefficient_lookup"
    if re.search(r"công\s*/\s*đơn vị vật liệu", t["context_before"], re.I):
        return "labor_matrix"
    if "mãhiệu" in h or "mãhiệu" in h:
        if "thànhphần" in h or "vậtliệu" in h:
            return "resource_matrix"
        return "labor_matrix"
    if "hệsố" in h or "bùhaohụt" in h:
        return "coefficient_lookup"
    if "trọnglượng" in h or "khốilượng" in h or "bềdầy" in h or "chiềudày" in h or "đườngkính" in h:
        return "material_property"
    if any(x in h for x in ("cấp", "nhóm", "tên", "đặctính", "loại", "đặcđiểm", "sốtt", "stt", "tt")):
        return "classification"
    return "narrative_note"


def typed_records(t, words, paths, start):
    """Tách hàng vật lý ở ô gộp; trường nào không có số rõ giữ dạng chuỗi, không đoán."""
    records = []
    boxes = {(c["row"], c["column"]): c["bbox_pt"] for c in t["cells"]}
    for ri in range(start, t["rows"]):
        row = t["grid"][ri]
        primary = text_lines(words, boxes.get((ri, 0)))
        anchors = [p for p in primary if re.fullmatch(r"(?:[IVX]+|\d+(?:[.,]\d+)?|\d+[x×]\d+|[A-Z]{2}\.\d+|\d{2}\.\d+)", p["text"])]
        if len(anchors) < 2:
            anchors = [{"y": None, "text": clean(row[0])}]
        for ai, a in enumerate(anchors):
            lo = (anchors[ai - 1]["y"] + a["y"]) / 2 if a["y"] is not None and ai else -1e10
            hi = (a["y"] + anchors[ai + 1]["y"]) / 2 if a["y"] is not None and ai + 1 < len(anchors) else 1e10
            fields = []
            for ci, raw in enumerate(row):
                box = boxes.get((ri, ci))
                physical_lines = text_lines(words, box)
                selected = [p for p in physical_lines if lo <= p["y"] < hi]
                text = "\n".join(p["text"] for p in selected) if a["y"] is not None else raw
                fields.append({"column": ci, "header_path": paths[ci], "text_raw": text,
                               "decimal": number(text), "bbox_pt": box,
                               "lines": [{**p, "decimal": number(p["text"])} for p in selected]})
            if any(f["text_raw"] for f in fields):
                records.append({"row": ri, "physical_row": ai, "key_raw": a["text"], "fields": fields})
    return records


RESOURCE_UNITS = {"kg", "g", "m", "m2", "m3", "m²", "m³", "tấn", "t", "lít", "l", "lit", "công", "ca", "%", "cái", "bộ", "viên", "cây", "thanh", "tấm", "chai", "ống", "kwh", "kWh", "cuộn", "mối"}


def unit_name(unit):
    return {"m³": "m3", "m²": "m2", "tấn": "t", "lít": "l", "lit": "l", "kwh": "kWh"}.get(unit, unit)


def resource_template(t, code, codes, name, unit, raw, ri, ci, y, box, paths, resolver):
    value = number(raw)
    result = {"source_id": t["source_id"], "pdf_page": t["pdf_page"], "table_id": t["table_id"],
              "norm_code": code, "source_codes": codes, "reference_code": codes[0] if len(codes) == 1 else None,
              "resource_name": name, "resource_kind": "labor" if unit == "công" else "machine" if unit == "ca" or name.startswith("Máy khác") else "material",
              "resource_unit": unit_name(unit), "quantity": value, "quantity_raw": raw,
              "value_type": "percentage" if unit == "%" else "resource_quantity", "value_status": "numeric" if value is not None else "not_specified",
              "conditions_raw": paths[ci], "grid_row": ri, "grid_column": ci, "row_y_pt": y,
              "source_bbox_pt": box, "review_status": "structure_checked_pending_review", "enabled": False}
    basis = resolver.resolve(result)
    result["basis"], result["basis_evidence"] = basis if basis else (None, None)
    return result


def horizontal_recipes(t, words, paths, start, resolver):
    """Mỗi cột là một nguyên liệu có đơn vị in ở tiêu đề, mỗi hàng là một mã cấp phối."""
    ingredients = []
    for ci, path in enumerate(paths):
        for label in reversed(path):
            match = re.search(r"(.+?)?\s*\((kg|m3|m2|lít|m³|m²)\)\s*$", label)
            if match:
                name = clean(match[1]) or next((p for p in reversed(path[:-1]) if "Vật liệu dùng" not in p), "")
                if name:
                    ingredients.append((ci, name, match[2]))
                break
    if not ingredients:
        return []
    out = []
    boxes = {(c["row"], c["column"]): c["bbox_pt"] for c in t["cells"]}
    for ri in range(start, t["rows"]):
        row = t["grid"][ri]
        codes = source_codes(row[0] or "")
        if not codes or not all(re.fullmatch(r"\d{2}\.\d{5}", c) for c in codes):
            continue
        anchors = [p for p in text_lines(words, boxes.get((ri, 0))) if p["text"] in codes]
        for anchor in anchors:
            for ci, name, unit in ingredients:
                values = [p for p in text_lines(words, boxes.get((ri, ci))) if abs(p["y"] - anchor["y"]) <= 5]
                if len(values) != 1 or number(values[0]["text"]) is None:
                    continue
                record = resource_template(t, anchor["text"], [anchor["text"]], name, unit, values[0]["text"],
                                           ri, ci, anchor["y"], boxes.get((ri, ci)), paths, resolver)
                workunits = [i for i, path in enumerate(paths) if "đơnvịtính" in [compact(p) for p in path]]
                if workunits and (basis := parse_basis(row[workunits[0]])):
                    record["basis"] = basis
                    record["basis_evidence"] = {"source_id": t["source_id"], "pdf_page": t["pdf_page"], "table_id": t["table_id"], "quote": row[workunits[0]], "method": "explicit_work_row", "grid_row": ri, "grid_column": workunits[0]}
                out.append(record)
    return out


def geometric_resources(t, words, paths, start, resolver):
    """Đọc theo dải cột thực, bỏ qua cột rỗng do các đường kẻ PDF chồng nhau."""
    headercells = [c for c in t["cells"] if c["row"] < start and c["bbox_pt"]]
    unitheads = [c for c in headercells if compact(c["text_raw"]) == "đơnvị"]
    nameheads = [c for c in headercells if "thànhphần" in compact(c["text_raw"]) or "loạivậtliệu" in compact(c["text_raw"])]
    if not unitheads and nameheads:
        scores = []
        for ci in range(t["columns"]):
            cells = [c for c in t["cells"] if c["column"] == ci and c["row"] >= start and c["bbox_pt"]]
            score = sum(clean(line).lower() in RESOURCE_UNITS for c in cells for line in (c["text_raw"] or "").splitlines())
            if score >= 3:
                scores.append((score, cells[0]["bbox_pt"]))
        if scores:
            box = max(scores, key=lambda item: item[0])[1]
            unitheads = [{"bbox_pt": box}]
    if not unitheads or not nameheads:
        return []
    uh = max(unitheads, key=lambda c: c["bbox_pt"][0])
    nh = max((c for c in nameheads if c["bbox_pt"][0] < uh["bbox_pt"][0]), key=lambda c: c["bbox_pt"][0], default=None)
    if not nh:
        return []
    y0 = max(c["bbox_pt"][3] for c in headercells)
    y1 = t["bbox_pt"][3]
    unitlines = [dict(p, text=p["text"].lower()) for p in text_lines(words, (uh["bbox_pt"][0], y0, uh["bbox_pt"][2], y1)) if p["text"].lower() in RESOURCE_UNITS]
    if not unitlines:
        return []
    names = {p["y"]: [] for p in unitlines}
    for p in text_lines(words, (nh["bbox_pt"][0], y0, nh["bbox_pt"][2], y1)):
        if compact(p["text"]) in ("vậtliệu", "máythicông"):
            continue
        distance = min(abs(u["y"] - p["y"]) for u in unitlines)
        target = min(u["y"] for u in unitlines if abs(u["y"] - p["y"]) <= distance + 1)
        names[target].append(p["text"])
    data_cells = [c for c in t["cells"] if c["row"] >= start and c["bbox_pt"] and c["bbox_pt"][0] >= uh["bbox_pt"][2] - 1]
    bycol = {}
    for c in data_cells:
        bycol.setdefault(c["column"], []).append(c)
    valuecols = [ci for ci, cells in bycol.items() if any(number(x) is not None for c in cells for x in (c["text_raw"] or "").splitlines())]
    code_heads = [c for c in headercells if compact(c["text_raw"]) in ("mãhiệu", "mahiệu")]
    codebox = code_heads[0]["bbox_pt"] if code_heads else None
    codelines = [p for p in text_lines(words, (codebox[0], y0, codebox[2], y1)) if source_codes(p["text"])] if codebox else []
    allcodes = list(dict.fromkeys(code for p in codelines for code in source_codes(p["text"])))
    if not allcodes:
        # Mã nhóm in tại tiêu đề trên bảng là nguồn tường minh khi ô mã của bảng bị bỏ trống.
        matches = source_codes(t["context_before"])
        if matches:
            heading = matches[-1]
            allcodes = [heading[:-2] if re.fullmatch(r"[A-Z]{2}\.\d{5}", heading) else heading]
    out = []
    for ul in unitlines:
        name = " ".join(names[ul["y"]])
        if not name:
            continue
        for ci in valuecols:
            cells = bycol[ci]
            values = []
            for cell in cells:
                for p in text_lines(words, cell["bbox_pt"]):
                    if abs(p["y"] - ul["y"]) <= 5 and (number(p["text"]) is not None or p["text"] in ("-", "–")):
                        values.append((cell, p))
            if not values:
                continue
            cell, val = min(values, key=lambda x: (x[0]["bbox_pt"][3] - x[0]["bbox_pt"][1]))
            suffix = clean(t["grid"][-1][ci])
            code = None
            if len(allcodes) == 1 and re.fullmatch(r"\d{1,3}", suffix):
                candidate = allcodes[0] + suffix
                if re.fullmatch(r"(?:[A-Z]{2}|\d{2})\.\d{5}", candidate):
                    code = candidate
            out.append(resource_template(t, code, allcodes, name, ul["text"], val["text"], cell["row"], ci,
                                         ul["y"], cell["bbox_pt"], paths, resolver))
    return out


def labor_records(t, words, paths, start, resolver):
    joined_headers = " ".join(" ".join(path) for path in paths)
    caption = t["context_before"] + "\n" + joined_headers
    numerator_proof = re.search(r"công\s*/|Nhân công", caption, re.I) or any("Nhân công" in str(row) for row in t["grid"])
    unit_columns = [i for i, p in enumerate(paths) if any(compact(x) == "đơnvị" for x in p)]
    if not numerator_proof and not unit_columns:
        return []
    out = []
    boxes = {(c["row"], c["column"]): c["bbox_pt"] for c in t["cells"]}
    for ri in range(start, t["rows"]):
        row = t["grid"][ri]
        codes = source_codes(row[0] or "")
        if not codes:
            continue
        resource_unit = "công"
        if unit_columns:
            raw_unit = clean(row[unit_columns[0]]).lower()
            if raw_unit in ("ca", "công") or set(raw_unit.split()) <= {"ca", "công"}:
                resource_unit = "ca" if "ca" in raw_unit else "công"
        codelines = [p for p in text_lines(words, boxes.get((ri, 0))) if source_codes(p["text"])]
        for ci in range(2, t["columns"]):
            for val in text_lines(words, boxes.get((ri, ci))):
                if number(val["text"]) is None:
                    continue
                applicable = codes
                if len(codelines) > 1:
                    nearest = min(codelines, key=lambda p: abs(p["y"] - val["y"]))
                    applicable = source_codes(nearest["text"])
                code = None
                suffix = clean(t["grid"][-1][ci])
                if len(applicable) == 1 and re.fullmatch(r"\d{1,3}", suffix):
                    candidate = applicable[0] + suffix
                    if re.fullmatch(r"[A-Z]{2}\.\d{5}", candidate):
                        code = candidate
                record = resource_template(t, code, applicable, "Nhân công" if resource_unit == "công" else "Máy thi công", resource_unit, val["text"], ri, ci, val["y"], boxes.get((ri, ci)), paths, resolver)
                basis_text = row[unit_columns[0]] if unit_columns else None
                if unit_columns:
                    matched_units = [p for p in text_lines(words, boxes.get((ri, unit_columns[0]))) if abs(p["y"] - val["y"]) <= 5]
                    if len(matched_units) == 1:
                        basis_text = matched_units[0]["text"]
                if unit_columns and (basis := parse_basis(basis_text)) and basis["unit"] not in ("ca", "công"):
                    record["basis"] = basis
                    record["basis_evidence"] = {"source_id": t["source_id"], "pdf_page": t["pdf_page"], "table_id": t["table_id"], "quote": basis_text, "method": "explicit_work_row", "grid_row": ri, "grid_column": unit_columns[0]}
                out.append(record)
    return out


def resource_records(t, words, paths, start, resolver):
    heads = [compact(" ".join(p)) for p in paths]
    # Bảng theo hàng vật liệu có cột đơn vị công tác riêng và cột đơn vị tài nguyên riêng.
    unitcols = [i for i, path in enumerate(paths) if any(compact(label) in ("đơnvị", "đơnvịtính") for label in path)]
    resource_col = next((i for i, h in enumerate(heads) if "thànhphần" in h or "loạivậtliệu" in h), None)
    if resource_col is None and t["source_id"] == "TT38_2026_8":
        resource_col = 1 if unitcols and unitcols[-1] == 2 else None
    if resource_col is None or not unitcols:
        return []
    uc = unitcols[-1]
    if uc <= resource_col:
        return []
    valuecols = list(range(uc + 1, t["columns"]))
    if not valuecols:
        return []
    boxes = {(c["row"], c["column"]): c["bbox_pt"] for c in t["cells"]}
    footer = t["grid"][-1]
    has_footer = not any(clean(x) for x in footer[:uc + 1]) and all(re.fullmatch(r"\d{1,3}", clean(footer[c])) for c in valuecols)
    result = []
    for ri in range(start, t["rows"] - int(has_footer)):
        row = t["grid"][ri]
        codes = source_codes(" ".join(x or "" for x in row[:resource_col]))
        if not codes:
            continue
        unitlines = [dict(p, text=p["text"].lower()) for p in text_lines(words, boxes.get((ri, uc))) if p["text"].lower() in RESOURCE_UNITS]
        namelines = [p for p in text_lines(words, boxes.get((ri, resource_col))) if compact(p["text"]) not in ("vậtliệu", "máythicông")]
        if not unitlines:
            continue
        names = {p["y"]: [] for p in unitlines}
        for line in namelines:
            distance = min(abs(p["y"] - line["y"]) for p in unitlines)
            choices = [p["y"] for p in unitlines if abs(p["y"] - line["y"]) <= distance + 1]
            names[min(choices)].append(line["text"])
        for ul in unitlines:
            name = " ".join(names[ul["y"]])
            if not name:
                continue
            # Nếu mã đầy đủ chia hàng theo cao độ thì dùng mã gần phía trên của dòng hao phí.
            current_codes = codes
            if all(re.fullmatch(r"\d{2}\.\d{5}", c) for c in codes) and len(codes) > 1:
                code_lines = [p for p in text_lines(words, boxes.get((ri, 0))) if source_codes(p["text"])]
                above = [p for p in code_lines if p["y"] <= ul["y"] + 3]
                if above:
                    current_codes = source_codes(above[-1]["text"])
            for ci in valuecols:
                vals = text_lines(words, boxes.get((ri, ci)))
                aligned = [p for p in vals if abs(p["y"] - ul["y"]) <= 5]
                if len(aligned) != 1:
                    continue
                raw = aligned[0]["text"]
                value = number(raw)
                if value is None and raw not in ("-", "–"):
                    continue
                norm_code = None
                refcode = current_codes[0] if len(current_codes) == 1 else None
                if len(current_codes) == len(valuecols):
                    refcode = current_codes[valuecols.index(ci)]
                if refcode:
                    candidate = refcode if re.fullmatch(r"(?:[A-Z]{2}|\d{2})\.\d{5}", refcode) else refcode + clean(footer[ci]) if has_footer else None
                    if candidate and re.fullmatch(r"(?:[A-Z]{2}|\d{2})\.\d{5}", candidate):
                        norm_code = candidate
                template = {"source_id": t["source_id"], "pdf_page": t["pdf_page"], "table_id": t["table_id"],
                            "norm_code": norm_code, "source_codes": current_codes, "reference_code": refcode,
                            "resource_name": name, "resource_kind": "labor" if ul["text"] == "công" else "machine" if ul["text"] == "ca" else "material",
                            "resource_unit": unit_name(ul["text"]), "quantity": value, "quantity_raw": raw,
                            "value_type": "percentage" if ul["text"] == "%" else "resource_quantity",
                            "value_status": "numeric" if value is not None else "not_specified",
                            "conditions_raw": paths[ci], "grid_row": ri, "grid_column": ci, "row_y_pt": ul["y"],
                            "source_bbox_pt": boxes.get((ri, ci)), "work_description_raw": row[1] if resource_col > 1 else None,
                            "review_status": "structure_checked_pending_review", "enabled": False}
                b = resolver.resolve(template)
                # Đơn vị công tác được ghi trong cột riêng của chính hàng vật liệu.
                if len(unitcols) > 1:
                    unittext = clean(row[unitcols[0]])
                    parsed = parse_basis(unittext)
                    if parsed:
                        b = parsed, {"source_id": t["source_id"], "pdf_page": t["pdf_page"], "table_id": t["table_id"],
                                     "quote": row[unitcols[0]], "method": "explicit_work_row", "grid_row": ri, "grid_column": unitcols[0]}
                template["basis"] = b[0] if b else None
                template["basis_evidence"] = b[1] if b else None
                if "Nước (lít)" in paths[ci]:
                    template["resource_name"], template["resource_unit"] = "Nước", "l"
                result.append(template)
    return result


def normalize_table(t, words, resolver):
    start = body_start(t)
    paths = headers(t, start)
    kind = classify(t)
    result = {"source_id": t["source_id"], "pdf_page": t["pdf_page"], "table_id": t["table_id"], "table_kind": kind,
              "header_rows": start, "column_paths": paths, "source_bbox_pt": t["bbox_pt"],
              "records": typed_records(t, words, paths, start), "resources": [],
              "review_status": "source_structured_pending_review", "enabled": False}
    if kind == "resource_matrix":
        result["resources"] = resource_records(t, words, paths, start, resolver)
        if not result["resources"]:
            result["resources"] = horizontal_recipes(t, words, paths, start, resolver)
        if not result["resources"]:
            result["resources"] = geometric_resources(t, words, paths, start, resolver)
        if not result["resources"]:
            result["resources"] = labor_records(t, words, paths, start, resolver)
    elif kind == "labor_matrix":
        result["resources"] = labor_records(t, words, paths, start, resolver)
    if kind == "layout_fragment":
        result["disposition"] = "layout_fragment_preserved_not_a_separate_norm"
    elif kind == "narrative_note":
        result["disposition"] = "narrative_preserved_not_a_numeric_norm"
    elif kind == "document_index":
        result["disposition"] = "document_navigation_not_a_norm"
    else:
        result["disposition"] = "typed_records_with_source_coordinates"
    for record in result["records"]:
        for field in record["fields"]:
            if field["decimal"] is None:
                continue
            if kind == "cost_rate":
                path = compact(" ".join(field["header_path"]))
                field["value_type"] = "cost_axis" if field["column"] == 0 and "chiphí" in path else "ordinal" if field["column"] == 0 else "percentage"
                field["unit"] = "tỷ đồng" if field["value_type"] == "cost_axis" else "%" if field["value_type"] == "percentage" else None
            elif kind == "coefficient_lookup":
                field["value_type"] = "percentage" if "haohụt" in compact(" ".join(field["header_path"])) else "coefficient_or_axis"
            elif kind == "material_property":
                field["value_type"] = "property_or_dimension"
    return result
