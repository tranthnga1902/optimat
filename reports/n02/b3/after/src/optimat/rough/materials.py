"""Từ khối lượng công tác ra vật liệu mua về (đặc tả phần thô mục 4).

    xây          -> gạch (định mức phương án tường) + vữa xây -> xi măng, cát (cấp phối COMPOSED_OF)
    trát, cán nền-> vữa (định mức theo chiều dày) -> xi măng, cát
    bê tông      -> thương phẩm: giữ m³ theo mác; trộn tại chỗ: xi măng, cát, đá theo cấp phối BE_TONG_TRON
    cốt thép     -> tấn thép (chưa chia nhóm đường kính) + dây buộc
    chống thấm, đệm cát, cốp pha -> theo định mức trong dinh_muc_phan_tho.csv

Thiếu định mức, cấp phối hay thông số thì phần đó không ra số: dòng vật liệu ghi complete=False và lý do trong missing.
Hao hụt lấy theo materials.waste_pct; trống thì không cộng và báo.
"""
from __future__ import annotations

import re
from math import isfinite
from typing import Optional

import pandas as pd

from ..catalog.repository import Catalog
from .models import (CONCRETE_WORKS, IntermediateLine, MaterialLine, MaterialUse, ProjectParams, RoughBill, WorkItem,
                     RAW_CLASS_BY_NAME, worst_status)
from .norms import MIX, MORTAR, Norm, load_norms, norms_for, unit_factor

STEEL_NAME = "Cốt thép (chưa chia nhóm đường kính)"


def _num(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(f) else f


def _fmt(v: float) -> str:
    return f"{v:,.3f}".rstrip("0").rstrip(".").replace(",", " ").replace(".", ",")


_CONFIRMATION_ORDER = {"nguon": 0, "tinh": 1, "kinh_nghiem": 2}


def _worse_confirmation(a: str | None, b: str | None) -> str | None:
    """Mức xác nhận yếu nhất của hệ số (đặc tả 3B): kinh_nghiem > tinh > nguon."""
    known = [c for c in (a, b) if c in _CONFIRMATION_ORDER]
    return max(known, key=_CONFIRMATION_ORDER.__getitem__) if known else a or b


def _grade_number(grade: str | None) -> str | None:
    m = re.search(r"(\d+)", grade or "")
    return m.group(1) if m else None


def mortar_material(catalog: Catalog, grade: str | None) -> str | None:
    """Vữa trộn tại chỗ (đơn vị m³) có "mác <số>" trong tên, ví dụ M75 -> VU02."""
    n = _grade_number(grade)
    if n is None:
        return None
    m = catalog.materials
    hit = m[(m.unit == "m³") & m.usage_role.fillna("").str.contains("MORTAR")
            & m.name.str.contains(rf"mác\s*{n}\b", case=False, regex=True)]
    return None if hit.empty else str(hit.material_id.iloc[0])


def ready_mix_material(catalog: Catalog, grade: str | None) -> str | None:
    """Bê tông thương phẩm đúng mác (bỏ loại có phụ gia chống thấm), ví dụ M250 -> BT03."""
    n = _grade_number(grade)
    if n is None:
        return None
    m = catalog.materials
    hit = m[m.name.str.startswith("Bê tông thương phẩm") & m.name.str.contains(rf"\bM{n}\b", regex=True)]
    return None if hit.empty else str(hit.material_id.iloc[0])


class _Bill:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.mats = catalog.materials.set_index("material_id")
        self.lines: dict[str, MaterialLine] = {}
        # Tổng phần góp số thô: đã gồm, chưa gồm, có phần khác 0 cần tỷ lệ hao hụt.
        self.waste_parts: dict[str, tuple[float, float, bool]] = {}
        self.inter: dict[tuple, IntermediateLine] = {}
        self.warnings: list[str] = []

    def warn(self, text: str) -> None:
        if text not in self.warnings:
            self.warnings.append(text)

    def add(self, material_id: str | None, name: str, unit: str, qty: float | None, w: WorkItem, via: str,
            missing: list[str] | None = None, confirmation: str | None = None,
            qty_range: tuple[float | None, float | None] | None = None, waste_included: bool = False) -> None:
        """confirmation: mức xác nhận của hệ số đã nhân (nguon | tinh | kinh_nghiem); tinh / kinh_nghiem hạ trạng thái xuống C.
        qty_range: (min, max) khi hệ số là khoảng (đặc tả 3B)."""
        if material_id is not None and material_id in self.mats.index:
            name, unit = str(self.mats.loc[material_id, "name"]), str(self.mats.loc[material_id, "unit"])
        key = material_id or f"{name}|{unit}"
        line = self.lines.setdefault(key, MaterialLine(material_id=material_id, name=name, unit=unit))
        missing = list(dict.fromkeys([*w.missing, *(missing or [])]))
        if w.status == "D" and not w.missing:
            missing.append(f"khối lượng {w.element or w.name}: D (nguồn công tác chưa đầy đủ)")
        status = "D" if qty is None or missing else worst_status(w.status, "C" if confirmation in ("tinh", "kinh_nghiem") else None)
        line.uses.append(MaterialUse(work=w.code, plan=w.plan, quantity=None if qty is None else round(qty, 4), via=via,
                                     status=status, stage=w.stage, waste_included=waste_included))
        if qty is None or missing:
            line.complete = False             # thiếu số, hoặc chưa xác định được vật liệu cụ thể để mua
        if qty is not None:
            included, extra, needs_pct = self.waste_parts.get(key, (0.0, 0.0, False))
            self.waste_parts[key] = (included + (qty if waste_included else 0.0),
                                     extra + (0.0 if waste_included else qty),
                                     needs_pct or (not waste_included and qty != 0))
            line.quantity = (line.quantity or 0.0) + qty
            lo, hi = qty_range or (qty, qty)
            line.quantity_min = (line.quantity_min or 0.0) + (lo if lo is not None else qty)
            line.quantity_max = (line.quantity_max or 0.0) + (hi if hi is not None else qty)
        if confirmation:
            line.confirmation = _worse_confirmation(line.confirmation, confirmation)
        for m in missing or []:
            if m not in line.missing:
                line.missing.append(m)

    def intermediate(self, kind: str, grade: str | None, material_id: str | None, name: str, qty: float | None,
                     *, work: WorkItem) -> None:
        line = self.inter.setdefault((kind, grade, material_id), IntermediateLine(
            kind=kind, grade=grade, material_id=material_id, name=name))
        if qty is None or work.missing or work.status == "D":
            line.complete = False
        if qty is not None:
            line.quantity = (line.quantity or 0.0) + qty

    # ---------------------------------------------------------------- vữa và bê tông
    def mortar(self, mortar_id: str | None, grade: str | None, m3: float | None, w: WorkItem, via: str,
               density: float | None = None, label: str = "Vữa", waste_included: bool = False) -> None:
        """m³ vữa -> vật liệu gốc theo cấp phối COMPOSED_OF; không có cấp phối thì giữ vữa làm vật liệu mua về."""
        if mortar_id is None:
            name = f"{label} {grade}" if grade else f"{label} (chưa chọn mác)"
            self.intermediate("vua", grade, None, name, m3, work=w)
            need = "mác vữa" if grade is None else f"vữa mác {grade} trong danh mục"
            self.add(None, name, "m³", m3, w, via, [f"{need} (để tách xi măng, cát)"])
            return
        name = str(self.mats.loc[mortar_id, "name"]) if mortar_id in self.mats.index else mortar_id
        self.intermediate("vua", grade, mortar_id, name, m3, work=w)
        rel = self.catalog.relations
        parts = rel[(rel.material_id == mortar_id) & (rel.relation_type == "COMPOSED_OF")]
        if parts.empty:
            unit = str(self.mats.loc[mortar_id, "unit"]) if mortar_id in self.mats.index else "m³"
            if unit == "m³":
                self.add(mortar_id, name, unit, m3, w, via + " (vữa)", waste_included=waste_included)
            elif unit == "tấn":
                qty = m3 * density / 1000 if m3 is not None and density else None
                self.add(mortar_id, name, unit, qty, w, via + (f" × {_fmt(density)} kg/m³" if density else ""),
                         [] if density else ["khối lượng thể tích vữa (đổi m³ sang tấn)"], waste_included=waste_included)
            else:
                self.add(mortar_id, name, unit, None, w, via, [f"cách đổi m³ vữa sang {unit}"])
            return
        for p in parts.itertuples():
            target = str(p.related_material_id)
            to_unit = str(self.mats.loc[target, "unit"]) if target in self.mats.index else ""
            per = _num(p.quantity)
            factor = unit_factor(str(p.quantity_unit or "").split("/")[0], to_unit)
            miss = []
            if per is None:
                miss.append(f"cấp phối {mortar_id} → {target}")
            if factor is None:
                miss.append(f"đổi đơn vị {p.quantity_unit} sang {to_unit}")
            qty = m3 * per * factor if m3 is not None and per is not None and factor is not None else None
            self.add(target, target, to_unit, qty, w, f"{via} × {_fmt(per) if per is not None else '?'} {p.quantity_unit}", miss,
                     waste_included=waste_included)

    def concrete(self, grade: str | None, supply: str | None, m3: float | None, w: WorkItem, norms: tuple[Norm, ...]) -> None:
        q = "?" if m3 is None else _fmt(m3)
        via = f"{w.code} {q} m³"
        if grade is None:
            self.intermediate("be_tong", None, None, "Bê tông (chưa chọn mác)", m3, work=w)
            self.add(None, "Bê tông (chưa chọn mác)", "m³", m3, w, via, ["mác bê tông"])
            return
        if supply is None:
            self.intermediate("be_tong", grade, None, f"Bê tông {grade}", m3, work=w)
            self.add(None, f"Bê tông {grade}", "m³", m3, w, via, ["bê tông thương phẩm hay trộn tại chỗ"])
            return
        if supply == "ready_mix":
            mid = ready_mix_material(self.catalog, grade)
            self.intermediate("be_tong", grade, mid, f"Bê tông thương phẩm {grade}", m3, work=w)
            self.add(mid, f"Bê tông thương phẩm {grade}", "m³", m3, w, via,
                     [] if mid else [f"bê tông thương phẩm {grade} trong danh mục"])
            return
        self.intermediate("be_tong", grade, None, f"Bê tông trộn tại chỗ {grade}", m3, work=w)
        rows = norms_for(MIX, grade, norms)
        if not rows:
            self.add(None, f"Bê tông trộn tại chỗ {grade}", "m³", m3, w, via, [f"cấp phối bê tông {grade}"])
            return
        for n in rows:
            self.norm_line(n, m3, w, via)

    def norm_line(self, n: Norm, base: float | None, w: WorkItem, via: str, grade: str | None = None) -> None:
        """Một dòng định mức: lượng = khối lượng gốc × qty, đổi đơn vị sang đơn vị của vật liệu."""
        label = f"định mức {n.work_code}{' ' + n.variant if n.variant else ''} → {n.material_name or n.material_id}"
        value = n.value                      # qty, hoặc giữa khoảng min–max khi dòng chỉ ghi khoảng
        miss = [] if value is not None else [f"{label} (chưa tra TT 38/2026)"]
        # mức xác nhận của hệ số (đặc tả 3B): có số hiệu bảng TT 38 -> nguon; không có -> hệ số tham khảo (đặc tả 1A):
        # vẫn dùng nhưng dòng vật liệu hạ xuống C (tạm tính), cảnh báo nêu nguồn
        confirmation = n.confirmation
        provisional = value is not None and not n.norm_code
        if provisional:
            self.warn(f"Định mức {label}: hệ số tham khảo ({n.confirmation or 'chưa ghi mức xác nhận'}; {n.source or 'không rõ nguồn'}), "
                      "chưa có số hiệu bảng TT 38/2026/TT-BXD: vật liệu từ dòng này là tạm tính (C).")
            if confirmation not in ("tinh", "kinh_nghiem"):
                confirmation = "tinh"     # nguồn ngoài bộ định mức: coi như hệ số tính/tham khảo, không phải định mức chính thức
        elif value is not None and confirmation is None:
            confirmation = "nguon"
        if n.material_id == MORTAR:
            m3 = base * value if base is not None and value is not None else None
            mid = mortar_material(self.catalog, grade)
            self.mortar(mid, grade, m3, w, f"{via} × {_fmt(value) if value is not None else '?'} {n.qty_unit}",
                        label=n.material_name or "Vữa", waste_included=bool(n.norm_code))
            if miss:
                self.lines_missing(mid, grade, miss)
            return
        if n.material_id is not None and n.material_id not in self.mats.index:
            miss.append(f"mã {n.material_id} không có trong danh mục")
        to_unit = str(self.mats.loc[n.material_id, "unit"]) if n.material_id in self.mats.index else n.numerator_unit
        factor = unit_factor(n.numerator_unit, to_unit)
        if factor is None:
            miss.append(f"đổi đơn vị {n.qty_unit} sang {to_unit}")
        if n.material_id is None:
            miss.append("danh mục chưa có mã vật liệu")
        qty = base * value * factor if base is not None and value is not None and factor is not None else None
        rng = None
        if qty is not None and n.qty_range is not None:
            lo, hi = n.qty_range
            rng = (base * lo * factor if lo is not None else None, base * hi * factor if hi is not None else None)
        q_txt = (f"{_fmt(n.qty_min)}–{_fmt(n.qty_max)}" if rng and None not in rng else _fmt(value)) if value is not None else "?"
        self.add(n.material_id, n.material_name or str(n.material_id), to_unit, qty, w, f"{via} × {q_txt} {n.qty_unit}", miss,
                 confirmation=confirmation, qty_range=rng, waste_included=bool(n.norm_code))

    def lines_missing(self, mortar_id: str | None, grade: str | None, miss: list[str]) -> None:
        """Định mức vữa chưa tra: ghi lý do vào các dòng vật liệu tách từ vữa đó."""
        rel = self.catalog.relations
        targets = rel[(rel.material_id == mortar_id) & (rel.relation_type == "COMPOSED_OF")].related_material_id.tolist()
        keys = (targets or [mortar_id]) if mortar_id else [k for k in self.lines if k.startswith("Vữa")]
        for k in keys:
            line = self.lines.get(k)
            if line is not None:
                line.missing += [m for m in miss if m not in line.missing]
                line.complete = False

    # ---------------------------------------------------------------- kết quả
    def result(self, works: list[WorkItem]) -> RoughBill:
        lines = list(self.lines.values())
        for key, line in self.lines.items():
            if line.quantity is not None:
                line.quantity = round(line.quantity, 3)
            # khoảng giá trị chỉ giữ khi khác tổng (hệ số có min–max, đặc tả 3B)
            if line.quantity_min is not None and line.quantity_max is not None:
                line.quantity_min, line.quantity_max = round(line.quantity_min, 3), round(line.quantity_max, 3)
                if line.quantity_min == line.quantity_max == line.quantity:
                    line.quantity_min = line.quantity_max = None
            if line.material_id in self.mats.index:
                row = self.mats.loc[line.material_id]
                line.waste_pct = _num(row.get("waste_pct"))
                g = row.get("group")
                line.group_id = str(g) if isinstance(g, str) and g else None
                c = row.get("raw_class")
                line.raw_class = str(c) if isinstance(c, str) and c else None
                kg = _num(row.get("unit_weight_kg"))
                vol = _num(row.get("transport_volume_m3"))
                if line.quantity is not None:
                    line.weight_kg = round(line.quantity * kg, 1) if kg is not None else None
                    line.transport_volume_m3 = round(line.quantity * vol, 3) if vol is not None else None
                if kg is None:
                    line.missing.append("khối lượng riêng (kg / đơn vị) để tính vận chuyển")
            if line.raw_class is None:        # dòng chưa có mã danh mục (hoặc danh mục chưa xếp loại): xếp theo tên
                low = line.name.lower()
                line.raw_class = next((c for k, c in RAW_CLASS_BY_NAME if k in low), "khac")
            if line.weight_kg is None and line.unit == "tấn" and line.quantity is not None:   # đổi đơn vị, không cần khối lượng riêng
                line.weight_kg = round(line.quantity * 1000, 1)
            # định mức TT 38 đã gồm hao hụt thi công (PL II, quy định chung 1): không cộng thêm; chỉ cần % hao hụt khi còn phần
            # không qua định mức (bê tông thương phẩm, thép theo hàm lượng, mức dùng của hãng)
            included, extra, needs_pct = self.waste_parts.get(key, (0.0, 0.0, False))
            if needs_pct and (line.waste_pct is None or not isfinite(line.waste_pct) or line.waste_pct < 0):
                reason = "hao hụt thi công (%)" if line.waste_pct is None else "hao hụt thi công (%) phải hữu hạn và không âm"
                if reason not in line.missing:
                    line.missing.append(reason)
                line.quantity_with_waste = None
                line.complete = False
                line.waste_pct = None       # không xuất tỷ lệ NaN/inf/âm không hợp lệ
            elif line.quantity is not None:
                line.quantity_with_waste = round(included + extra * (1 + line.waste_pct / 100), 3) if needs_pct else line.quantity
            # Thiếu hao hụt làm lượng mua chưa đủ; thiếu riêng khối lượng riêng chỉ ảnh hưởng vận chuyển.
            line.status = "D" if not line.complete else worst_status(*(u.status for u in line.uses))
        for i in self.inter.values():
            if i.quantity is not None:
                i.quantity = round(i.quantity, 3)
        return RoughBill(works=works, intermediates=list(self.inter.values()), materials=lines, warnings=self.warnings)


def materials_for_works(works: list[WorkItem], params: ProjectParams, catalog: Catalog,
                        norms: tuple[Norm, ...] | None = None) -> RoughBill:
    """Cộng vật liệu mua về của mọi công tác. Công tác không có khối lượng vẫn sinh dòng vật liệu (trống số)."""
    norms = load_norms() if norms is None else norms
    bill = _Bill(catalog)
    view = catalog.wall_view().set_index("wall_system_id") if not catalog.wall_systems.empty else pd.DataFrame()
    for w in works:
        if w.basis == "not_supported":
            continue                      # cấu kiện chưa có quy ước: không sinh vật liệu, đã báo trong công tác
        q = w.quantity
        via = f"{w.code} {'?' if q is None else _fmt(q)} {w.unit}"
        if q is None:
            bill.warn(f"{w.name}{' (' + w.plan + ')' if w.plan else ''}: chưa có khối lượng, thiếu {', '.join(w.missing) or 'thông tin'}.")
        if w.code == "XAY":
            _masonry(bill, w, q, via, view, params)
        elif w.code in ("TRAT", "CAN_NEN"):
            grade = params.plaster_mortar_grade if w.code == "TRAT" else params.screed_mortar_grade
            key, base = w.variant, ""
            if w.code == "TRAT":           # trát: định mức theo dày + họ vật liệu nền (AK.211/212, gạch rỗng +10% đã nhân trong CSV)
                fam = _family_of(bill, view, w.wall_system_id)
                key = f"{w.variant}/{fam}" if w.variant and fam else None
                base = f" trên nền {fam or 'chưa rõ (chưa có phương án tường hoặc họ vật liệu)'}"
            rows = [] if w.code == "TRAT" and key is None else norms_for(w.code, key, norms)
            if not rows:
                bill.add(None, f"Vữa {'trát' if w.code == 'TRAT' else 'cán nền'}", "m³", None, w, via,
                         [f"định mức {w.code} cho chiều dày {w.variant or '(chưa nhập)'} mm{base}"])
            for n in rows:
                bill.norm_line(n, q, w, via, grade)
        elif w.code in CONCRETE_WORKS:
            bill.concrete(params.concrete_grade, params.concrete_supply, q, w, norms)
        elif w.code == "BE_TONG_LOT":
            bill.concrete(params.lean_concrete_grade, params.concrete_supply, q, w, norms)
        elif w.code == "COT_THEP":
            bill.add(None, STEEL_NAME, "tấn", q, w, via,
                     [] if w.basis == "bang_thong_ke" else ["bảng thống kê thép để chia nhóm đường kính"])
            for n in norms_for("COT_THEP", None, norms):
                bill.norm_line(n, q, w, via)
        elif w.code == "COP_PHA":
            kind = (params.formwork_type or "").upper()
            rows = norms_for(w.code, f"GO_{w.formwork_of}" if kind == "GO" else kind, norms) if kind else []
            if not rows:
                bill.add(None, "Vật liệu cốp pha", "", None, w, via,
                         ["loại ván khuôn (gỗ | ván ép)" if not kind else f"định mức ván khuôn {params.formwork_type} cho {w.formwork_of}"])
            for n in rows:
                bill.norm_line(n, q, w, via)
        elif w.code == "CHONG_THAM":
            rows = norms_for(w.code, w.variant, norms) if w.variant else []
            if not rows:
                bill.add(None, "Vật liệu chống thấm", "", None, w, via,
                         ["chọn vật liệu chống thấm" if not w.variant else f"định mức chống thấm {w.variant}"])
            for n in rows:
                bill.norm_line(n, q, w, via)
        else:
            for n in norms_for(w.code, w.variant, norms):
                bill.norm_line(n, q, w, via)
    return bill.result(works)


def _family_of(bill: _Bill, view: pd.DataFrame, system_id: str | None) -> str | None:
    """Họ vật liệu chính của phương án tường (materials.family); không có phương án hoặc họ thì None."""
    if system_id is None or system_id not in view.index:
        return None
    mid = view.loc[system_id].get("material_id")
    fam = bill.mats.loc[mid].get("family") if isinstance(mid, str) and mid in bill.mats.index else None
    return fam if isinstance(fam, str) and fam else None


def _masonry(bill: _Bill, w: WorkItem, q: float | None, via: str, view: pd.DataFrame, params: ProjectParams) -> None:
    if w.wall_system_id is None or w.wall_system_id not in view.index:
        bill.add(None, "Gạch xây (chưa chọn phương án tường)", "", None, w, via, ["phương án tường (vật liệu xây)"])
        return
    s = view.loc[w.wall_system_id]
    per = _num(s.units_per_m3)
    factor = _num(s.unit_factor) if _num(s.unit_factor) is not None else 1.0
    qty = q * per * factor if q is not None and per is not None else None
    code = s.get("norm_code")
    in_norm = isinstance(code, str) and code.startswith("AE")      # định mức xây TT 38 (AE...) đã gồm hao hụt thi công
    bill.add(str(s.material_id), str(s.material_id), "", qty, w,
             f"{via} × {_fmt(per) if per is not None else '?'} viên/m³" + (f" × {_fmt(factor)}" if factor != 1.0 else ""),
             [] if per is not None else [f"định mức gạch / m³ xây của {w.wall_system_id}"], waste_included=in_norm)
    mortar_id = s.get("mortar_material_id")
    mortar_id = mortar_id if isinstance(mortar_id, str) and mortar_id else None
    per_m = _num(s.mortar_m3_per_m3)
    grade = None
    if params.masonry_mortar_grade and mortar_id and str(bill.mats.loc[mortar_id, "unit"]) == "m³":
        chosen = mortar_material(bill.catalog, params.masonry_mortar_grade)
        grade = params.masonry_mortar_grade
        if chosen is None:
            bill.warn(f"Danh mục chưa có vữa xây mác {grade}; dùng vữa của phương án {w.wall_system_id} ({mortar_id}).")
        else:
            mortar_id = chosen
    if mortar_id is None:
        return
    m3 = q * per_m if q is not None and per_m is not None else None
    m_via = f"{via} × {_fmt(per_m) if per_m is not None else '?'} m³ vữa/m³"
    bill.mortar(mortar_id, grade, m3, w, m_via, _num(s.get("mortar_density")), waste_included=in_norm)
    if per_m is None:
        bill.lines_missing(mortar_id, grade, [f"định mức vữa / m³ xây của {w.wall_system_id}"])
