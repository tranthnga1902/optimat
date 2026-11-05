"""Nhóm tường để lập vật tư từ dòng xây cuối cùng của bảng phần thô."""
from __future__ import annotations

import math

from ..catalog.repository import Catalog
from ..schemas import WallGroup
from .materials import _num, mortar_material
from .models import ProjectParams, WorkItem


def _design_mortar(system, units, grade: str, catalog: Catalog) -> tuple[str | None, list[str]]:
    """Chỉ chuyển mã vữa đã đối chiếu. Định mức 0 có nguồn không cần mã mua."""
    rate = _num(system.get("mortar_m3_per_m3"))
    issues = []
    if rate == 0:
        if any(isinstance(ref, str) and ref.strip() for ref in (system.get("norm_code"), system.get("norm_source"))):
            return None, []
        issues.append("thiếu nguồn xác nhận định mức vữa bằng 0")
    elif rate is None or not math.isfinite(rate) or rate < 0:
        issues.append("chưa có định mức vữa hợp lệ")
    base = system.get("mortar_material_id")
    unit = units.get(base)
    override = None
    if not isinstance(unit, str) or not unit.strip():
        label = f" {base}" if isinstance(base, str) and base.strip() else ""
        issues.append(f"cần xác minh mã và đơn vị vật liệu liên kết{label}" + (f" theo mác {grade}" if grade else ""))
    elif grade:
        if unit != "m³":
            issues.append(f"chưa có căn cứ xác nhận vật liệu liên kết {base} đáp ứng mác {grade}")
        else:
            override = mortar_material(catalog, grade)
            if override is None:
                issues.append(f"chưa xác định được vữa xây đúng mác {grade} trong danh mục")
    return override, issues


def final_wall_groups(works: list[WorkItem], params: ProjectParams, catalog: Catalog) -> tuple[list[WallGroup], list[str]]:
    groups: dict[tuple, WallGroup] = {}
    issues: list[str] = []
    systems = catalog.wall_systems.set_index("wall_system_id")
    units = dict(zip(catalog.materials.material_id, catalog.materials.unit))
    grade = (params.masonry_mortar_grade or "").strip()
    for work in works:
        if work.code != "XAY":
            continue
        geometry = work.masonry_geometry
        missing = list(work.missing)
        if geometry:
            missing.extend(geometry.issues)
            if not math.isfinite(geometry.thickness_m) or geometry.thickness_m <= 0:
                missing.append("bề dày khối xây không hợp lệ")
        if not geometry or work.wall_system_id not in systems.index:
            missing.append("chưa xác định cấu tạo tường")
        if work.quantity is None or not math.isfinite(work.quantity) or work.quantity < 0 or work.status == "D":
            missing.append("khối xây chưa đủ căn cứ")
        if missing:
            issues.append(f"{work.plan}, {work.element}: {', '.join(dict.fromkeys(missing))}")
            continue
        if work.quantity == 0:
            continue
        system = systems.loc[work.wall_system_id]
        mortar_id, gaps = _design_mortar(system, units, grade, catalog)
        if gaps:
            issues.append(f"{work.plan}, {work.element} ({work.wall_system_id}): {', '.join(gaps)}")
            continue
        key = (geometry.wall_type, geometry.role, work.wall_system_id)
        if key not in groups:
            groups[key] = WallGroup(wall_type=geometry.wall_type, role=geometry.role, length_m=0,
                                    gross_area_m2=0, opening_area_m2=0, net_area_m2=0, min_confidence=None,
                                    design_wall_system_id=work.wall_system_id, design_material_id=system.material_id,
                                    design_mortar_material_id=mortar_id, design_material_share=1)
        g = groups[key]
        g.length_m += geometry.length_m
        g.gross_area_m2 += geometry.gross_area_m2
        g.opening_area_m2 += geometry.opening_area_m2
        g.net_area_m2 += work.quantity / geometry.thickness_m
    return list(groups.values()), issues
