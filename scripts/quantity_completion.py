"""Đọc cơ sở đơn vị từ đúng bảng hoặc chuỗi tiếp nối cùng mã, luôn kèm chứng cứ."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal


def clean(text):
    return " ".join(unicodedata.normalize("NFC", text or "").split())


UNIT_LABEL = r"(?:Đ[ơợ]n\s*vị\s*tính|Đơn\s*vị\s*:|ĐVT)\s*[:：]?\s*"
UNITS = ("mặt cắt ngang", "cây tiêu chuẩn", "gốc cây", "chu kỳ đo", "chỉ tiêu", "hệ thống", "cặp bích", "nguyên bộ", "điểm đo", "thí nghiệm", "ống cống", "tấn", "m³", "m²", "m3", "m2", "km", "ha", "kg", "bộ", "cái", "chiếc", "viên", "máy", "hộp", "bảng", "cửa", "mối", "bể", "sàn", "mẫu", "cọc", "cột", "cây", "bụi", "điểm", "lít", "công", "ca", "tấm", "sứ", "ống", "v", "m", "t")


def parse_basis(raw):
    """Đơn vị có ghi tên tương đương 1 đơn vị; giữ nguyên điều kiện lần đầu/lần di chuyển."""
    raw = clean(raw)
    raw_for_match = re.sub(r"^Cắt\s+", "", raw, flags=re.I)
    pattern = r"^(?:(\d+(?:[.,]\d+)?)\s*)?(" + "|".join(map(re.escape, UNITS)) + r")(?=$|[^\w]|\s)"
    match = re.match(pattern, raw_for_match, re.I)
    if not match:
        return None
    number = str(Decimal((match[1] or "1").replace(",", ".")))
    if Decimal(number) <= 0:
        return None
    token = match[2].lower()
    unit = {"tấn": "t", "m³": "m3", "m²": "m2", "lít": "l"}.get(token, token)
    suffix = raw_for_match[match.end():].strip()
    qualifiers = []
    if suffix.startswith("/"):
        qualifier = suffix[1:].strip()
        qualifiers.append(qualifier)
        # Không làm mất ý nghĩa mỗi lần của đơn vị phức hợp.
        unit += "/" + re.sub(r"\s+", "_", qualifier)
    return {"quantity": number, "unit": unit, "unit_raw": raw, "qualifiers": qualifiers}


def code_prefixes(table):
    result = []
    for row in table["grid"]:
        text = clean(row[0])
        text = re.sub(r"([A-Z]{2})\s*\.\s*", r"\1.", text)
        for code in re.findall(r"[A-Z]{2}\.\d{2,5}|\d{2}\.\d{3,5}|\b[A-Z]{1,2}\d{2,4}\b", text):
            prefix = code[:-2] if "." in code and len(code.split(".")[1]) == 5 else code
            if prefix not in result:
                result.append(prefix)
    return result


def evidence(table, quote, method, **extra):
    return {"source_id": table["source_id"], "pdf_page": table["pdf_page"], "table_id": table["table_id"],
            "quote": quote, "method": method, **extra}


def local_basis(table):
    # Đọc ở phần trước bảng: lấy lần khai báo gần bảng nhất, không lấy đơn vị tài nguyên trong thân bảng.
    text = unicodedata.normalize("NFC", table["context_before"])
    labels = list(re.finditer(UNIT_LABEL + r"([^\n]+)", text, re.I))
    if labels:
        match = labels[-1]
        raw = clean(match[1])
        if raw.lower().startswith("công/") or raw.lower().startswith("công /"):
            basis = parse_basis(raw.split("/", 1)[1])
        else:
            basis = parse_basis(raw)
        if basis:
            return basis, evidence(table, match[0], "explicit_unit_caption")
    # Cấp phối ghi cơ sở ngay trong tiêu đề bảng.
    for ri, row in enumerate(table["grid"][:2]):
        for ci, cell in enumerate(row):
            match = re.search(r"(?:Vật liệu|vật liệu).*?(?:dùng\s+)?cho\s+(\d+\s*m[23³²][^\n]*)", clean(cell))
            if match:
                basis = parse_basis(match[1])
                if basis:
                    return basis, evidence(table, cell, "explicit_table_header", grid_row=ri, grid_column=ci)
    title = list(re.finditer(r"(?:ĐỊNH MỨC|Định mức|CẤP PHỐI|Cấp phối)[^\n]*?(\d+\s*m[23³²])[^\n]*", text))
    if title and (basis := parse_basis(title[-1][1])):
        return basis, evidence(table, title[-1][0], "explicit_volume_in_recipe_title")
    return None


def column_basis(table, column):
    grid = table["grid"]
    # Chỉ đơn vị gắn trực tiếp cột công tác, không lấy (mm)/(cm) của biến kích thước làm đơn vị công tác.
    bodyboxes = [c["bbox_pt"] for c in table["cells"] if c["column"] == column and c["bbox_pt"]]
    x = (bodyboxes[-1][0] + bodyboxes[-1][2]) / 2 if bodyboxes else 0
    candidates = [(c["row"], c["column"], c["text_raw"]) for c in table["cells"] if c["row"] < 3 and c["bbox_pt"] and c["bbox_pt"][0] <= x <= c["bbox_pt"][2]]
    for ri, owner_col, cell in candidates:
        text = clean(cell)
        label = re.search(UNIT_LABEL + r"(.+)", text, re.I)
        if "sứ (hoặc sứ nguyên bộ)" in clean(table["context_before"]):
            if re.fullmatch(r"[234] sứ", text):
                return ({"quantity": "1", "unit": "sứ_nguyên_bộ", "unit_raw": "sứ nguyên bộ", "qualifiers": [text]},
                        evidence(table, "Đơn vị tính: sứ (hoặc sứ nguyên bộ); " + text, "explicit_work_column", grid_row=ri, grid_column=owner_col, target_grid_column=column))
        if label:
            raw = label[1]
            if re.match(r"công\s*/", raw, re.I):
                raw = raw.split("/", 1)[1]
            b = parse_basis(raw)
        else:
            matches = re.findall(r"\(([^()]+)\)", text)
            dimension_axis = re.search(r"chiều cao|chiều dài|khẩu độ|độ sâu|kích thước|đường kính|chiều dày", text, re.I)
            b = parse_basis(matches[-1]) if matches and not dimension_axis and matches[-1] in ("cái", "m", "tấm", "bộ") else None
        if b:
            return b, evidence(table, cell, "explicit_work_column", grid_row=ri, grid_column=owner_col, target_grid_column=column)
    return None


class BasisResolver:
    def __init__(self, tables, native=None):
        self.tables = tables
        self.ordered = sorted(tables.values(), key=lambda t: (t["source_id"], t["pdf_page"], t["bbox_pt"][1]))
        self.local = {t["table_id"]: local_basis(t) for t in self.ordered}
        self.prefixes = {t["table_id"]: code_prefixes(t) for t in self.ordered}
        self.native = native or {}

    def resolve(self, record):
        table = self.tables[record["table_id"]]
        col = record.get("grid_column")
        if col is not None:
            result = column_basis(table, col)
            if result:
                return result
        result = self.local[table["table_id"]]
        if result:
            return result
        prefixes = self.prefixes[table["table_id"]]
        if not prefixes:
            prefixes = [code[:-2] if "." in code and len(code.split(".")[-1]) == 5 else code
                        for code in record.get("source_codes", [])]
        if not prefixes:
            return None
        # Cùng mã nhóm là chứng cứ tiếp nối. Không lấy tùy tiện đơn vị của trang trước.
        prior = [t for t in self.ordered if t["source_id"] == table["source_id"]
                 and (t["pdf_page"], t["bbox_pt"][1]) < (table["pdf_page"], table["bbox_pt"][1])]
        for candidate in reversed(prior):
            cp = self.prefixes[candidate["table_id"]]
            if set(cp) & set(prefixes) and self.local[candidate["table_id"]]:
                b, e = self.local[candidate["table_id"]]
                return b, {**e, "method": "same_code_continuation", "target_table_id": table["table_id"],
                           "matched_code_prefixes": sorted(set(cp) & set(prefixes))}
        # Tiêu đề và đơn vị có thể nằm cuối trang trước, còn bảng bắt đầu trang sau.
        rows = self.native.get(table["source_id"], [])
        if table["pdf_page"] > 1 and rows:
            text = unicodedata.normalize("NFC", rows[table["pdf_page"] - 2]["text"])
            for prefix in prefixes:
                matches = list(re.finditer(re.escape(prefix) + r"\d{0,3}[^\n]*\n" + UNIT_LABEL + r"([^\n]+)", text, re.I))
                if matches and (basis := parse_basis(matches[-1][1])):
                    return basis, {"source_id": table["source_id"], "pdf_page": table["pdf_page"] - 1,
                                   "quote": matches[-1][0], "method": "heading_caption_before_page_break", "target_table_id": table["table_id"]}
        scopes = [("TT38_2026_3", 327, 332, r"B\d{3}", 327, "m3", "vữa xây, vữa trát"),
                  ("TT38_2026_3", 486, 502, r"C\d{3}", 485, "m3", "bê tông"),
                  ("TT38_2026_8", 104, 105, r"16\.3\d{4}", 104, "m", "ống dẫn gas")]
        if table["source_id"] == "TT38_2026_8" and 27 <= table["pdf_page"] <= 28 and any(re.fullmatch(r"AO[3-6]0", c) for c in record.get("source_codes", [])):
            text = self.native["TT38_2026_8"][26]["text"]
            match = re.search(r"III\.2[^\n]+Đơn vị tính\s*:\s*1 tấn\)", text)
            if match:
                return {"quantity": "1", "unit": "t", "unit_raw": "tấn bê tông nhựa", "qualifiers": []}, {
                    "source_id": table["source_id"], "pdf_page": 27, "quote": match[0], "method": "explicit_appendix_scope", "scope_code_pattern": "AO[3-6]0", "target_table_id": table["table_id"]}
        for sid, low, high, pattern, origin, unit, qualifier in scopes:
            if table["source_id"] == sid and low <= table["pdf_page"] <= high and any(re.fullmatch(pattern, c) for c in record.get("source_codes", [])):
                text = self.native[sid][origin - 1]["text"]
                match = re.search(r"Định mức dự toán cấp phối vật liệu cho 1m\s*3[^.]+", text) if sid == "TT38_2026_3" else re.search(r"16\.30000[^\n]+\nỐNG DẪN GAS", text)
                if match:
                    b = {"quantity": "1", "unit": unit, "unit_raw": f"{unit} {qualifier}", "qualifiers": []}
                    return b, {"source_id": sid, "pdf_page": origin, "quote": match[0], "method": "explicit_appendix_scope", "scope_code_pattern": pattern, "target_table_id": table["table_id"]}
        return None
