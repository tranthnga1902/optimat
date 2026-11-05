"""Gán trạng thái dữ liệu A/B/C/D cho từng khối lượng công tác (đặc tả 30/10/2026 mục 3).

Gán tập trung sau khi mọi công tác đã sinh (compute_rough), theo các đầu vào của từng mã công tác; mỗi đầu vào có trạng
thái riêng, công tác lấy trạng thái YẾU NHẤT. Không đổi công thức nào; chỉ ghi nhãn và danh sách đầu vào để truy vết.

Đầu vào và trạng thái của nó:
    hình học tường, cột, phòng trên mặt bằng       A (đã qua trang kiểm tra; người dùng vẽ thêm vẫn là A: theo bản vẽ)
    chiều cao tầng                                 theo PlanInput.height_source: cao độ / chuỗi cao độ: B; nhập tay: C; chưa có: D
    thông số công trình (ProjectParams)            C (dày sàn, cao dầm, lanh tô, mác, hàm lượng thép, cổ tường chống thấm…)
    dầm                                            structural: A; manual: C; inferred (suy từ tường, cột): B
    đường bao sàn, diện tích sử dụng               phòng khép kín / bao lồi: B (suy từ tường); nhập tay: C
    thép                                           bảng thống kê trên bản vẽ: A; tấn nhập tay / hàm lượng người dùng: C
    móng, mái, thang, giằng, sê nô                 nhập tay: C; đọc bản vẽ kết cấu: A
    quantity trống hoặc còn missing                 D (giữ phần số đã biết)
"""
from __future__ import annotations

from typing import Optional

from .models import STEEL_ELEMENTS, WORK_STAGE, ProjectParams, WorkItem, worst_status

Input = tuple[Optional[str], str]


def _param(value, label: str) -> Input:
    """Thông số công trình: có thì C (giả định người dùng), không có thì D."""
    return ("C", f"{label}: C (thông số công trình)") if value is not None else ("D", f"{label}: D (chưa nhập)")


def _src(source: Optional[str], label: str, auto_status: str, auto_text: str) -> Input:
    """Đầu vào theo WorkItem.source: manual -> C, structural -> A, còn lại -> auto_status."""
    if source == "manual":
        return "C", f"{label}: C (nhập tay)"
    if source == "structural":
        return "A", f"{label}: A (bản vẽ kết cấu)"
    return auto_status, f"{label}: {auto_status} ({auto_text})"


def height_status(height_source: Optional[str]) -> str:
    """Chiều cao tầng theo nguồn (PlanTakeoff.height_source): suy từ cao độ bản vẽ là B, nhập tay là C, chưa có là D."""
    s = (height_source or "").lower()
    if not s or "chưa có" in s:
        return "D"
    if "cao độ" in s or "chuỗi" in s:
        return "B"
    return "C"



def _inputs(w: WorkItem, params: ProjectParams, h: Optional[str], beam_sources: set[str]) -> list[Input]:
    code = w.code
    out: list[Input] = []
    if code in ("XAY", "TRAT", "LANH_TO"):
        out.append(("A", "chiều dài, dày tường: A (hình học mặt bằng)"))
        if h:
            out.append((h, f"chiều cao tầng: {h}"))
        if params.beam_depth_mm is not None:
            out.append(("C", "cao dầm trừ khỏi tường: C"))
        if any("wall_systems_by_class" in e for e in w.evidence):
            out.append(("C", "phương án tường: C (người dùng chọn theo lớp, bản vẽ không ghi vật liệu)"))
        if code == "TRAT":
            out.append(_param(params.plaster_thickness_mm, "dày trát"))
        if code == "LANH_TO":
            out.append(("C", "cao lanh tô, gối: C"))
    elif code == "COT":
        if w.plan == "bảng thống kê cột":
            out.append(("A", "tiết diện, cao độ cột: A (bảng thống kê cột)"))
        else:
            out.append(("A", "tiết diện cột: A (mặt bằng)"))
            if h:
                out.append((h, f"chiều cao tầng: {h}"))
            out.append(("C", "dày sàn trừ khỏi cột: C") if params.slab_thickness_mm is not None
                       else ("B", "dày sàn: B (chưa trừ, lấy cả chiều cao tầng)"))
    elif code == "DAM":
        if beam_sources and beam_sources <= {"inferred"}:
            out.append(("B", "vị trí, nhịp dầm: B (suy từ tường và cột)"))
        elif "structural" in beam_sources:
            out.append(("A", "vị trí, nhịp dầm: A (bản vẽ kết cấu)"))
        else:
            out.append(("C", "dầm: C (nhập tay)"))
        common = params.beam_width_mm is not None or params.beam_depth_mm is not None
        out.append(("C", "tiết diện dầm: C (thông số chung)") if common else ("A", "tiết diện dầm: A (ghi trên bản vẽ)"))
        out.append(_param(params.slab_thickness_mm, "dày sàn"))
    elif code == "SAN":
        out.append(_src(w.source, "diện tích sàn", "B", "đường bao tường"))
        out.append(_param(params.slab_thickness_mm, "dày sàn"))
    elif code in ("CAN_NEN", "NEN_DEM_CAT", "BE_TONG_LOT") and w.plan:
        out.append(_src(w.source, "diện tích sử dụng", "B", "phòng khép kín"))
        out.append(("C", "chiều dày lớp: C"))
    elif code == "CHONG_THAM":
        out.append(_src(w.source, "diện tích", "B", "phòng WC theo tên phòng"))
        out.append(("C", "cổ tường, vật liệu chống thấm: C"))
    elif code == "COT_THEP":
        if w.basis == "bang_thong_ke":
            out.append(_src(w.source, "thép", "A", "bảng thống kê trên bản vẽ"))
        else:
            out.append(("C", "hàm lượng kg/m³: C (người dùng nhập, tạm tính)"))
    elif code == "COP_PHA":
        out.append(("A", f"hình học {STEEL_ELEMENTS.get(w.formwork_of, w.formwork_of or 'cấu kiện')}: theo trạng thái cấu kiện"))
    elif code in ("MONG", "DAO_DAT", "DAP_DAT"):
        out.append(("C", "kích thước móng, cao độ: C (nhập tay)"))
    elif code == "CAU_THANG":
        out.append(_src(w.source, "thang", "B", "suy từ nét mũi bậc trên mặt bằng"))
        out.append(_param(params.stair_slab_thickness_mm, "dày bản thang"))
        out.append((h or "D", f"chiều cao tầng: {h or 'D (chưa có nguồn)'}"))
    else:   # MAI, GIANG_TUONG, SE_NO, BE_TONG_LOT chung
        out.append(_src(w.source, w.name.lower(), "C", "nhập tay"))
    return out


def assign_status(works: list[WorkItem], params: ProjectParams, height_sources: dict[str, Optional[str]],
                  beam_sources: dict[str, set[str]] | None = None) -> None:
    """Gán WorkItem.status, inputs, stage tại chỗ. height_sources: tên mặt bằng -> nguồn chiều cao tầng;
    beam_sources: tên mặt bằng -> tập source của dầm đã dùng (inferred | manual | structural)."""
    beam_sources = beam_sources or {}
    for w in works:
        w.stage = WORK_STAGE.get(w.code)
        prior_status, prior_inputs = w.status, list(w.inputs)
        if w.quantity is None or w.missing:
            w.status = "D"
            reasons = [f"thiếu: {m}" for m in w.missing] or ["chưa có khối lượng: D"]
            w.inputs = list(dict.fromkeys([*prior_inputs, *reasons]))
            continue
        h = height_status(height_sources.get(w.plan)) if w.plan in height_sources else None
        inputs = _inputs(w, params, h, beam_sources.get(w.plan or "", set()))
        w.status = worst_status(prior_status, *(s for s, _ in inputs)) or "C"
        dependency = [f"phụ thuộc đã có: {prior_status}"] if prior_status and not prior_inputs else []
        w.inputs = list(dict.fromkeys([*prior_inputs, *(t for _, t in inputs), *dependency]))
    # cốp pha và cốt thép theo hàm lượng kế thừa trạng thái của cấu kiện bê tông cùng mặt bằng (xấu nhất)
    by_key: dict[tuple[Optional[str], str], list[str]] = {}
    for w in works:
        if w.code in STEEL_ELEMENTS and w.status:
            by_key.setdefault((w.plan, w.code), []).append(w.status)
    for w in works:
        parent = w.formwork_of if w.code == "COP_PHA" else w.steel_element if (w.code == "COT_THEP" and w.basis == "ham_luong") else None
        if parent and w.status != "D":
            parents = by_key.get((w.plan, parent)) or [s for (_, c), ss in by_key.items() if c == parent for s in ss]
            if parents:
                w.status = worst_status(w.status, *parents)
