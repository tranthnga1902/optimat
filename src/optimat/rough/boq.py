"""Xuất BOQ phần thô ra Excel (S07-06): mọi dòng có công thức, nguồn (evidence) và lý do thiếu (missing_reason).

Sheet: Tổng hợp · Theo tầng · Theo cấu kiện · Cốt thép (dòng bảng thống kê) · Vật liệu · Cảnh báo · Phạm vi hỗ trợ.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font

from .. import config
from .models import STEEL_ELEMENTS, WORKS

SUPPORT_FILE = config.DATA_DIR / "rules" / "ho_tro_cau_kien.csv"
COMMON = "Chung (không theo tầng)"


def support_matrix() -> pd.DataFrame:
    return pd.read_csv(SUPPORT_FILE, dtype=str, keep_default_na=False)


def _component(w) -> str:
    """Cấu kiện của một công tác: cốp pha, cốt thép quy về cấu kiện bê tông của nó."""
    code = w.formwork_of if w.code == "COP_PHA" else w.steel_element if w.code == "COT_THEP" else w.code
    if code in STEEL_ELEMENTS:
        return WORKS[code][0].replace("Bê tông ", "").capitalize()
    return WORKS[code][0] if code in WORKS else "Chưa rõ cấu kiện"


def _row(w) -> list:
    return [w.plan or COMMON, _component(w), w.name, w.element or "", w.unit, w.quantity, w.basis or w.source,
            w.formula, " | ".join(w.evidence), "; ".join(w.missing)]


def _sheet(wb, title: str, header: list[str], rows: list[list]) -> None:
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append(r)
    ws.freeze_panes = "A2"
    for i, h in enumerate(header, start=1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = max(10, min(60, len(h) + 4))


def boq_workbook(result, req=None) -> Workbook:
    wb = Workbook()
    wb.remove(wb.active)
    head = ["Tầng", "Cấu kiện", "Công tác", "Chi tiết", "Đơn vị", "Khối lượng", "Nguồn số (basis)", "formula",
            "evidence", "missing_reason"]
    _sheet(wb, "Tổng hợp", ["Mã", "Công tác", "Đơn vị", "Khối lượng", "Đủ số", "Số dòng"],
           [[t.code, t.name, t.unit, t.quantity, "có" if t.complete else "thiếu", t.items] for t in result.totals]
           + [["COP_PHA/" + t.code, t.name, t.unit, t.quantity, "có" if t.complete else "thiếu", t.items] for t in result.formwork])
    plan_order = {p.name: i for i, p in enumerate(req.plans)} if req is not None else {}
    works = sorted(result.works, key=lambda w: (plan_order.get(w.plan, len(plan_order) + (w.plan is None)), list(WORKS).index(w.code)))
    _sheet(wb, "Theo tầng", head, [_row(w) for w in works])
    _sheet(wb, "Theo cấu kiện", head[1:2] + head[:1] + head[2:],
           [[r[1], r[0]] + r[2:] for r in sorted((_row(w) for w in result.works), key=lambda r: (r[1], r[0]))])
    rebar = req.rebar if req is not None else []
    _sheet(wb, "Cốt thép", ["Bảng", "Dòng", "Cấu kiện", "Mã cấu kiện", "Số hiệu", "Hình dạng", "Ø (mm)", "Chiều dài cắt (mm)",
                            "Số thanh", "kg/m", "Nguồn kg/m", "kg (tính)", "kg (bảng ghi)", "formula", "evidence",
                            "missing_reason", "Ghi chú"],
           [[r.table, r.row, r.element, r.element_code or "Not supported", r.mark, r.shape, r.dia_mm, r.cut_length_mm,
             r.total_bars, r.kg_per_m, r.kg_per_m_source, r.kg, r.schedule_kg, r.formula, r.evidence, "; ".join(r.missing),
             "; ".join(r.notes)] for r in rebar])
    _sheet(wb, "Vật liệu", ["Mã", "Vật liệu", "Đơn vị", "Khối lượng", "Đủ số", "missing_reason", "Từ công tác"],
           [[m.material_id or "", m.name, m.unit, m.quantity, "có" if m.complete else "thiếu", "; ".join(m.missing),
             "; ".join(u.via for u in m.uses[:8])] for m in result.materials])
    _sheet(wb, "Cảnh báo", ["#", "Cảnh báo"], [[i, w] for i, w in enumerate(result.warnings, start=1)])
    m = support_matrix()
    _sheet(wb, "Phạm vi hỗ trợ", list(m.columns), m.values.tolist())
    return wb


def boq_bytes(result, req=None) -> bytes:
    buf = BytesIO()
    boq_workbook(result, req).save(buf)
    return buf.getvalue()
