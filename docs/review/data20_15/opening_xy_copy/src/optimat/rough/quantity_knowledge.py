"""Đọc bộ nguồn đo bóc JSON; dữ liệu chờ duyệt chỉ được trả khi yêu cầu xem nháp."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data/rules/vn_quantity"


def _decimal(value) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Số lượng không phải số thập phân hợp lệ.") from None
    if not number.is_finite() or number < 0:
        raise ValueError("Số lượng phải hữu hạn và không âm.")
    return number


def _approved(row: dict) -> bool:
    return (row.get("enabled") is True and row.get("review_status") == "approved"
            and bool(row.get("approved_by")) and bool(row.get("approved_on")))


def _in_period(row: dict, as_of: date) -> bool:
    start, end = row.get("effective_from"), row.get("effective_to_exclusive")
    return bool(start) and date.fromisoformat(start) <= as_of and (not end or as_of < date.fromisoformat(end))


class QuantityKnowledge:
    """Tra cứu nguồn bổ trợ, không ghi DB hoặc ghi đè các định mức đang vận hành."""

    def __init__(self, path: str | Path = DEFAULT_PATH):
        self.path = Path(path)
        self.manifest = json.loads((self.path / "manifest.json").read_text(encoding="utf-8"))
        if self.manifest.get("schema_version") != "optimat.quantity-knowledge.v1":
            raise ValueError("Phiên bản bộ dữ liệu đo bóc không được hỗ trợ.")

    def _records(self, filename: str):
        p = self.path / filename
        expected = self.manifest["files"][filename]["sha256"]
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Tệp dữ liệu đã thay đổi hoặc hỏng: {filename}")
        if p.suffix == ".jsonl":
            with p.open(encoding="utf-8") as stream:
                for line in stream:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError(f"Dòng dữ liệu không phải đối tượng JSON: {filename}")
                    yield row
        else:
            yield from json.loads(p.read_text(encoding="utf-8"))

    def norms_for_code(self, norm_code: str, *, as_of: date, include_candidates: bool = False) -> list[dict]:
        if not re.fullmatch(r"(?:[A-Z]{2}\.\d{5}|\d{2}\.\d{5})", norm_code):
            raise ValueError("Cần mã định mức đầy đủ, ví dụ AK.21120 hoặc 11.11321.")
        return [r for r in self._records("norms.jsonl") if r["norm_code"] == norm_code
                and _in_period(r, as_of) and (include_candidates or _approved(r))]

    def rules_for_work(self, work_code: str, *, as_of: date, purpose: str,
                       include_candidates: bool = False) -> list[dict]:
        if purpose not in ("estimate", "payment"):
            raise ValueError("Mục đích phải là estimate (dự toán) hoặc payment (thanh toán).")
        return [r for r in self._records("measurement_rules.json")
                if (r["work_scope"] == "all" or work_code in r["work_codes"])
                and purpose in r["purposes"] and _in_period(r, as_of)
                and (include_candidates or _approved(r))]

    def reference_table(self, table_id: str, *, include_candidates: bool = False) -> dict | None:
        """Tra bảng tỷ lệ, hệ số, thuộc tính hoặc bảng tài nguyên theo ID nguồn; không tự nội suy."""
        return next((r for r in self._records("reference_tables.jsonl") if r["table_id"] == table_id
                     and (include_candidates or _approved(r))), None)


def resource_consumption(record: dict, work_quantity, work_unit: str, *, preview: bool = False) -> Decimal:
    """Nhân lượng công tác / quy mô định mức; % cần cơ sở chi phí riêng, không nhân như vật liệu."""
    if not preview and not _approved(record):
        raise ValueError("Định mức chưa được duyệt; chỉ được tính thử bằng preview=True.")
    if record.get("value_type") != "resource_quantity" or record.get("resource_unit") == "%" or record.get("quantity") is None:
        raise ValueError("Dòng phần trăm hoặc thiếu số không phải lượng tài nguyên để nhân trực tiếp.")
    basis = record.get("basis")
    if not basis or basis.get("unit") != work_unit:
        raise ValueError("Thiếu cơ sở định mức hoặc đơn vị công tác không khớp.")
    scale = _decimal(basis["quantity"])
    if scale == 0:
        raise ValueError("Quy mô đơn vị định mức phải lớn hơn 0.")
    return _decimal(work_quantity) * _decimal(record["quantity"]) / scale
