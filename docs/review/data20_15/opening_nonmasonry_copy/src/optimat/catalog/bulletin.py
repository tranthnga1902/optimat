"""Đọc file PDF công bố giá vật liệu của Sở Xây dựng và ghép từng dòng với mã vật liệu trong danh mục.

Bảng công bố có hai dạng:
    4 cột  (STT, tên, đơn vị, giá): cát, đá theo bãi / mỏ; dòng không có giá là tên bãi (= nhà cung cấp).
    12 cột (STT, nhóm, tên, đơn vị, tiêu chuẩn, quy cách, nhà sản xuất, xuất xứ, điều kiện thương mại, vận chuyển,
           ghi chú, giá): dòng có STT và không có giá là tên công ty (= nhà cung cấp). Ô gộp đọc ra None thì lấy giá trị
           của dòng trên.
Ghép mã theo data/rules/cong_bo_gia.csv (quy tắc đầu tiên khớp thì dùng); không khớp thì để trống, không đoán.
"""
from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from ..drawing.encoding import normalize

RULES_CSV = Path(__file__).resolve().parents[3] / "data/rules/cong_bo_gia.csv"
_ORG = re.compile(r"cong ty|c\.? ?ty|chi nhanh|tap doan|nha may|hop tac xa|htx|xi nghiep|doanh nghiep")


@dataclass
class BulletinRow:
    page: int
    supplier: str
    name: str
    unit: str
    price: Optional[float]
    maker: str = ""
    terms: str = ""                   # điều kiện thương mại + vận chuyển
    material_id: Optional[str] = None
    rule_id: Optional[str] = None
    catalog_price: Optional[float] = None   # giá theo đơn vị tính của danh mục
    reason: str = ""


@dataclass
class Rule:
    rule_id: str
    pattern: re.Pattern
    exclude: Optional[re.Pattern]
    units: set[str]
    material_id: str
    factor: float
    note: str = ""


@dataclass
class Bulletin:
    doc_no: str
    date: Optional[str]
    rows: list[BulletinRow] = field(default_factory=list)


def text_key(s: str) -> str:
    """Chữ thường bỏ dấu, 220 x 105 * 60 -> 220x105x60, gộp khoảng trắng."""
    s = normalize(s or "").replace("×", "x").replace("*", "x")
    s = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "x", s)
    return re.sub(r"\s+", " ", s).strip()


def unit_key(u: str) -> str:
    """'đồng/t\\nấn' -> 'tan', 'm 3' / 'm³' -> 'm3'."""
    u = normalize((u or "").replace("³", "3").replace("²", "2"))
    u = re.sub(r"\s+", "", u)
    return re.sub(r"^(dong|vnd|d)/", "", u)


def parse_price(s) -> Optional[float]:
    """'1.810.000', '4,700,000', '5.010' -> số; chuỗi khác (khoảng giá, chữ) -> None."""
    s = re.sub(r"\s+", "", s or "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+|\d{1,3}(,\d{3})+|\d+", s):
        return float(re.sub(r"[.,]", "", s))
    return None


def load_rules(path: Path = RULES_CSV) -> list[Rule]:
    with open(path, encoding="utf-8-sig") as f:
        return [Rule(r["rule_id"], re.compile(r["pattern"]), re.compile(r["exclude"]) if r["exclude"] else None,
                     set(r["bulletin_unit"].split("|")), r["material_id"], float(r["price_factor"]), r["note"])
                for r in csv.DictReader(f)]


def supplier_id(name: str) -> str:
    """Mã ổn định theo tên (bỏ dấu, dấu câu, khoảng trắng): nạp lại không sinh nhà cung cấp trùng."""
    return "CBG-" + hashlib.md5(re.sub(r"[^a-z0-9]", "", text_key(name)).encode()).hexdigest()[:10].upper()


def transport_included(terms: str) -> str:
    t = text_key(terms)
    if re.search(r"tai nha may|tai mo|tai bai|ben mua|khong bao gom (chi phi )?van chuyen|chua bao gom (chi phi )?van chuyen", t):
        return "NO"
    if re.search(r"den (chan )?cong trinh|den hien truong|den tan|da (bao gom|co) (chi phi )?van chuyen", t):
        return "YES"
    return "UNKNOWN"


def _cell(v) -> Optional[str]:
    return None if v is None else re.sub(r"\s+", " ", str(v)).strip()


def parse_tables(tables: Iterable[tuple[int, list[list]]]) -> list[BulletinRow]:
    """tables: (số trang từ 0, bảng do pdfplumber trả về). Trạng thái nhà cung cấp nối tiếp qua các trang."""
    rows: list[BulletinRow] = []
    supplier, carry = "", {6: "", 8: "", 9: ""}
    for page, table in tables:
        for raw in table:
            r = [_cell(c) for c in raw]
            if not r or (r[0] or "").upper() == "STT":
                continue
            if len(r) == 4:
                name, unit, price = r[1] or "", r[2] or "", r[3] or ""
                if not price:
                    if name and not re.match(r"^[IVX]+\s*-", name):      # bỏ dòng nhóm "I - NHÓM VẬT LIỆU CÁT"
                        supplier = name
                    continue
                # cát, đá: giá tại bãi / mỏ, chưa gồm vận chuyển (mục 1 văn bản công bố)
                rows.append(BulletinRow(page, supplier, name, unit, parse_price(price), terms="giá tại bãi, chưa bao gồm vận chuyển"))
                continue
            if len(r) < 12:
                continue
            name, price = r[2] or "", r[11] or ""
            if not price:
                if (r[0] or "").isdigit() and name and not any(r[3:11]) and _ORG.search(text_key(name)):
                    supplier, carry = name, {6: "", 8: "", 9: ""}
                continue
            for i in carry:
                if r[i]:                          # None = ô gộp, "" = ô trống khi bảng sang trang: giữ giá trị trên
                    carry[i] = r[i]
            rows.append(BulletinRow(page, supplier, name, r[3] or "", parse_price(price), maker=carry[6],
                                    terms="; ".join(x for x in (carry[8], carry[9]) if x)))
    return rows


def match(rows: list[BulletinRow], rules: list[Rule]) -> list[BulletinRow]:
    """Gán mã vật liệu; mỗi cặp (nhà cung cấp, mã) chỉ giữ dòng đầu tiên."""
    taken: set[tuple[str, str]] = set()
    for row in rows:
        key = text_key(row.name)
        rule = next((r for r in rules if r.pattern.search(key) and not (r.exclude and r.exclude.search(key))), None)
        if rule is None:
            row.reason = "không có quy tắc khớp"
        elif unit_key(row.unit) not in rule.units:
            row.reason = f"{rule.rule_id}: đơn vị '{row.unit}' khác '{'|'.join(sorted(rule.units))}'"
        elif row.price is None:
            row.reason = f"{rule.rule_id}: giá không đọc được"
        elif not row.supplier:
            row.reason = f"{rule.rule_id}: không xác định được nhà cung cấp"
        elif (row.supplier, rule.material_id) in taken:
            row.reason = f"{rule.rule_id}: trùng nhà cung cấp + mã {rule.material_id}, giữ dòng đầu"
        else:
            taken.add((row.supplier, rule.material_id))
            row.material_id, row.rule_id, row.catalog_price = rule.material_id, rule.rule_id, row.price * rule.factor
    return rows


def read_pdf(path: Path) -> Bulletin:
    """Đọc toàn bộ bảng trong PDF (cần pdfplumber; ~5 phút cho 700 trang)."""
    import pdfplumber

    tables, doc_no, date = [], "", None
    with pdfplumber.open(path) as pdf:
        first = pdf.pages[0].extract_text() or ""
        m = re.search(r"Số:\s*(\S*CBGVL\S*)", first)
        doc_no = m.group(1) if m else Path(path).stem
        for i, p in enumerate(pdf.pages):
            if date is None:                      # dấu thời gian chữ ký số: "...CBGVL-SXD; 20/06/2026; 11:25:01"
                d = re.search(r"CBGVL\S*;\s*(\d{2})/(\d{2})/(\d{4});", p.extract_text() or "")
                date = f"{d.group(3)}-{d.group(2)}-{d.group(1)}" if d else None
            tables += [(i, t) for t in p.extract_tables()]
            p.flush_cache()
    return Bulletin(doc_no, date, parse_tables(tables))
