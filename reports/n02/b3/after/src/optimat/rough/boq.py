"""Xuất BOQ phần thô ra Excel (S07-06): mọi dòng có công thức, nguồn (evidence) và lý do thiếu (missing_reason).

Sheet: Tổng hợp · Theo tầng · Theo cấu kiện · Cốt thép (dòng bảng thống kê) · Vật liệu · Theo nhóm · Theo loại · Cảnh báo · Phạm vi hỗ trợ.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font

from .. import config
from .models import RAW_CLASSES, STAGES, STATUS_LABEL, STEEL_ELEMENTS, WORKS

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


def _status(s) -> str:
    return f"{s} ({STATUS_LABEL[s]})" if s in STATUS_LABEL else ""


def _row(w) -> list:
    return [w.plan or COMMON, _component(w), w.name, w.element or "", w.unit, w.quantity, _status(w.status),
            STAGES.get(w.stage or "", ""), w.basis or w.source, w.formula, " | ".join(w.inputs), " | ".join(w.evidence),
            "; ".join(w.missing)]


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
    head = ["Tầng", "Cấu kiện", "Công tác", "Chi tiết", "Đơn vị", "Khối lượng", "Trạng thái (A đọc / B suy / C tạm tính / D thiếu)",
            "Giai đoạn", "Nguồn số (basis)", "formula", "Đầu vào quyết định trạng thái", "evidence", "missing_reason"]
    _sheet(wb, "Tổng hợp", ["Mã", "Công tác", "Đơn vị", "Khối lượng", "Đủ số", "Trạng thái", "Số dòng"],
           [[t.code, t.name, t.unit, t.quantity, "có" if t.complete else "thiếu", _status(t.status), t.items] for t in result.totals]
           + [["COP_PHA/" + t.code, t.name, t.unit, t.quantity, "có" if t.complete else "thiếu", _status(t.status), t.items]
              for t in result.formwork])
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
    _sheet(wb, "Vật liệu", ["Mã", "Vật liệu", "Nhóm", "Loại", "Đơn vị", "Khối lượng", "Khoảng (min–max)", "Khối lượng kg", "Đủ số",
                            "Trạng thái", "Mức xác nhận hệ số", "missing_reason", "Từ công tác"],
           [[m.material_id or "", m.name, m.group_id or "", RAW_CLASSES.get(m.raw_class or "", ""), m.unit, m.quantity,
             f"{m.quantity_min} – {m.quantity_max}" if m.quantity_min is not None else "", m.weight_kg,
             "có" if m.complete else "thiếu", _status(m.status), m.confirmation or "", "; ".join(m.missing),
             "; ".join(u.via for u in m.uses[:8])] for m in result.materials])
    groups = getattr(result, "by_group", [])
    _sheet(wb, "Theo nhóm", ["Nhóm", "Tên nhóm", "Trong phạm vi phần thô", "Vật liệu", "Khối lượng kg", "Đủ kg", "Trạng thái"],
           [[g.group_id, g.name, "có" if g.in_scope else "ngoài phạm vi", ", ".join(g.materials), g.weight_kg,
             "có" if g.weight_complete else "chưa đủ dữ liệu khối lượng", _status(g.status)] for g in groups])
    classes = getattr(result, "by_class", [])
    _sheet(wb, "Theo loại", ["Loại", "Tên loại", "Vật liệu", "Khối lượng kg", "Đủ kg", "Trạng thái"],
           [[g.group_id, g.name, ", ".join(g.materials), g.weight_kg, "có" if g.weight_complete else "chưa đủ dữ liệu khối lượng",
             _status(g.status)] for g in classes])
    _sheet(wb, "Cảnh báo", ["#", "Cảnh báo"], [[i, w] for i, w in enumerate(result.warnings, start=1)])
    m = support_matrix()
    _sheet(wb, "Phạm vi hỗ trợ", list(m.columns), m.values.tolist())
    return wb


def export_for_optimizer(result) -> dict:
    """Bảng vật liệu thô cho bộ tối ưu (đặc tả 1A, 11): mỗi vật liệu có nhóm, số lượng (khoảng nếu có), kg, m³ vận chuyển,
    trạng thái, mức xác nhận và lượng theo giai đoạn thi công. Quy tắc 3.1: dòng D không xuất số mà vào danh sách thiếu."""
    materials, missing = [], []
    for m in result.materials:
        if m.status == "D":
            missing.append({"material_id": m.material_id, "name": m.name, "raw_class": m.raw_class, "unit": m.unit, "known_part": m.quantity,
                            "reason": "; ".join(m.missing)})
            continue
        stages: dict[str, float] = {}
        for u in m.uses:
            if u.quantity is not None:
                stages[u.stage or "chua_ro"] = round(stages.get(u.stage or "chua_ro", 0.0) + u.quantity, 3)
        materials.append({"material_id": m.material_id, "name": m.name, "group_id": m.group_id, "raw_class": m.raw_class, "unit": m.unit,
                          "quantity": m.quantity, "quantity_min": m.quantity_min, "quantity_max": m.quantity_max,
                          "weight_kg": m.weight_kg, "transport_volume_m3": m.transport_volume_m3, "status": m.status,
                          "provisional": m.status == "C", "confirmation": m.confirmation, "by_stage": stages})
    return {"status": result.status, "stages": STAGES, "materials": materials, "missing": missing,
            "groups": [g.model_dump(mode="json") for g in result.by_group],
            "classes": [g.model_dump(mode="json") for g in getattr(result, "by_class", [])],
            "envelope_by_orientation": result.envelope_by_orientation}


def boq_bytes(result, req=None) -> bytes:
    buf = BytesIO()
    boq_workbook(result, req).save(buf)
    return buf.getvalue()
