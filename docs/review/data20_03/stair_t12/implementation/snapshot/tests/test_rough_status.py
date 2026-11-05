"""Trạng thái dữ liệu A/B/C/D, nhóm vật liệu, khối lượng kg, kiểm tra chéo, tường bao theo hướng (đặc tả 30/10/2026 mục 3, 7, 11)."""
from copy import deepcopy

import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewOpening
from optimat.rough.checks import cross_checks, envelope_by_orientation, load_ranges, wall_orientation
from optimat.rough.models import ProjectParams, WorkItem, worst_status
from optimat.rough.status import assign_status, height_status
from optimat.rough.stairs import Stair, stair_works
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough
from tests.test_rough_takeoff import FULL, plan, walls


def test_worst_status_order():
    assert worst_status("A", "B") == "B" and worst_status("C", "A", "D") == "D" and worst_status(None, "A") == "A"
    assert worst_status() is None and worst_status(None) is None
    assert height_status("cao độ tầng trên") == "B" and height_status("nhập tay") == "C" and height_status("chưa có") == "D"


def test_auto_stair_status_includes_thickness_height_and_formwork():
    params = ProjectParams(stair_slab_thickness_mm=120)
    stair = Stair(steps=22, flight_width_mm=1000, tread_mm=250, source="auto")
    works, _ = stair_works("Tầng 1", [stair], 3300, params)
    quantities = [w.quantity for w in works]
    assign_status(works, params, {"Tầng 1": "cao độ tầng trên"})
    concrete, formwork = works
    assert concrete.status == "C" and formwork.status == "C"
    assert any(i.startswith("thang: B") for i in concrete.inputs)
    assert "dày bản thang: C (thông số công trình)" in concrete.inputs
    assert "chiều cao tầng: B" in concrete.inputs
    assert [w.quantity for w in works] == quantities


@pytest.mark.parametrize("source, expected", [("auto", "B"), ("manual", "C"), ("structural", "A")])
def test_stair_status_keeps_geometry_source(source, expected):
    w = WorkItem(code="CAU_THANG", name="Bê tông cầu thang", unit="m³", quantity=1.0,
                 plan="Tầng 1", source=source)
    assign_status([w], ProjectParams(stair_slab_thickness_mm=120), {"Tầng 1": "nhập tay"})
    assert w.status == "C" and w.inputs[0].startswith(f"thang: {expected}")
    assert "chiều cao tầng: C" in w.inputs


def test_stair_without_thickness_stays_missing():
    params = ProjectParams()
    works, _ = stair_works("Tầng 1", [Stair(steps=22, flight_width_mm=1000, tread_mm=250, source="auto")], 3300, params)
    assign_status(works, params, {"Tầng 1": "cao độ tầng trên"})
    assert all(w.quantity is None and w.status == "D" for w in works)
    assert all("thiếu: dày bản thang" in w.inputs for w in works)


def test_stair_without_height_source_is_not_reported_complete():
    params = ProjectParams(stair_slab_thickness_mm=120)
    works, _ = stair_works("Tầng 1", [Stair(steps=22, flight_width_mm=1000, tread_mm=250, source="auto")], 3300, params)
    assign_status(works, params, {})
    assert all(w.status == "D" for w in works)
    assert "chiều cao tầng: D (chưa có nguồn)" in works[0].inputs


def test_status_on_full_house():
    """Chiều cao tầng từ cao độ bản vẽ (B), thông số công trình (C): xây là C (có cao dầm C), cột C (dày sàn C),
    thép theo hàm lượng C, sàn C; dòng trống là D. Vật liệu mang trạng thái xấu nhất của các phần góp vào."""
    p1 = plan("Trệt", True).model_copy(update={"height_source": "cao độ tầng trên"})
    p2 = plan("Tầng 2", False).model_copy(update={"height_source": "cao độ tầng trên"})
    res = compute_rough(RoughRequest(params=FULL, plans=[p1, p2]), Catalog.from_csv(None))
    by = {}
    for w in res.works:
        by.setdefault(w.code, set()).add(w.status)
    assert by["XAY"] == {"C"} and by["COT"] == {"C"} and by["SAN"] == {"C"} and by["COT_THEP"] == {"C"}
    assert all(w.status for w in res.works) and all(w.inputs for w in res.works) and all(w.stage for w in res.works)
    xay = next(w for w in res.works if w.code == "XAY")
    assert any(i.startswith("chiều cao tầng: B") for i in xay.inputs) and any("cao dầm" in i for i in xay.inputs)
    assert all(t.status for t in res.totals) and res.status in ("C", "D")
    gn = next(m for m in res.materials if m.material_id == "GN01")
    assert gn.status == "C" and gn.group_id == "phan_tho" and all(u.status for u in gn.uses) and all(u.stage for u in gn.uses)
    assert gn.weight_kg is not None and gn.weight_kg > 0
    groups = {g.group_id: g for g in res.by_group}
    assert groups["phan_tho"].in_scope and "GN01" in groups["phan_tho"].materials
    assert not groups["hoan_thien"].in_scope and groups["hoan_thien"].materials == []


def test_status_without_params():
    """Không có thông số: xây = hình học (A) + chiều cao tầng nhập tay (C) -> C; dòng không có số -> D kèm lý do thiếu."""
    res = compute_rough(RoughRequest(plans=[plan("Trệt", True)]), Catalog.from_csv(None))
    xay = next(w for w in res.works if w.code == "XAY")
    assert xay.status == "C" and "chiều cao tầng: C" in xay.inputs
    assert all(w.status == "D" for w in res.works if w.quantity is None)
    dam = next(w for w in res.works if w.code == "DAM")
    assert dam.status == "D" and dam.inputs and dam.inputs[0].startswith("thiếu:")



def test_reference_factor_downgrades_material_to_c():
    """Hệ số tham khảo (có số, nguồn ngoài TT 38, norm_code trống): vật liệu ra số nhưng tạm tính C, mức xác nhận hạ xuống
    'tinh', có cảnh báo nêu nguồn; hệ số có khoảng min–max cho khoảng giá trị. Hệ số có norm_code: giữ trạng thái công tác."""
    from optimat.rough.materials import materials_for_works
    from optimat.rough.norms import Norm
    cat = deepcopy(Catalog.from_csv(None))
    synthetic = cat.materials.material_id.isin(["XM02", "CA01"])
    cat.materials.loc[synthetic, "waste_pct"] = 0.0  # chỉ cô lập trạng thái hệ số trong dữ liệu kiểm thử
    cat.materials.loc[synthetic, "data_kind"] = "SYNTHETIC"
    w = WorkItem(code="SAN", name="s", unit="m³", quantity=10.0, status="B")
    ref = Norm("BE_TONG_TRON", "M250", "XM02", "", 415.125, "kg / m³", "", "cem.gov.vn", "", confirmation="nguon", checked_on="2026-10-30")
    rng = Norm("BE_TONG_TRON", "M250", "CA01", "", None, "m³ / m³", "", "kinh nghiệm", "", qty_min=0.4, qty_max=0.5, confirmation="kinh_nghiem")
    official = Norm("BE_TONG_TRON", "M250", "DA01", "", 0.887, "m³ / m³", "BẢNG-THỬ", "TT 38", "")
    bill = materials_for_works([w], ProjectParams(concrete_supply="site_mix", concrete_grade="M250"), cat, (ref, rng, official))
    xm = next(m for m in bill.materials if m.material_id == "XM02")
    assert xm.quantity == pytest.approx(4.151, abs=1e-3) and xm.status == "C" and xm.confirmation == "tinh"
    ca = next(m for m in bill.materials if m.material_id == "CA01")
    assert ca.quantity == pytest.approx(4.5) and (ca.quantity_min, ca.quantity_max) == (4.0, 5.0) and ca.confirmation == "kinh_nghiem"
    da = next(m for m in bill.materials if m.material_id == "DA01")
    assert da.status == "B" and da.confirmation == "nguon" and da.quantity_min is None
    assert sum("hệ số tham khảo" in m for m in bill.warnings) == 2
    cat.materials.loc[synthetic, "waste_pct"] = float("nan")
    missing_waste = materials_for_works([w], ProjectParams(concrete_supply="site_mix", concrete_grade="M250"), cat,
                                       (ref, rng, official))
    for m in missing_waste.materials:
        if m.material_id in ("XM02", "CA01"):
            assert m.status == "D" and not m.complete and m.quantity_with_waste is None
            assert "hao hụt thi công (%)" in m.missing


def test_min_opening_threshold_is_a_parameter():
    small = [ReviewOpening(id="O1", wall="A", w=500, h=500)]       # 0,25 m²
    base = PlanInput(name="T", is_ground=False, height_mm=3300, walls=walls(), openings=small, void_area_m2=0)
    cat = Catalog.from_csv(None)
    a = compute_rough(RoughRequest(params=FULL, plans=[base]), cat)
    b = compute_rough(RoughRequest(params=FULL.model_copy(update={"min_opening_m2": 0.5}), plans=[base]), cat)
    xa = next(w for w in a.works if w.code == "XAY" and "bao che" in (w.element or ""))
    xb = next(w for w in b.works if w.code == "XAY" and "bao che" in (w.element or ""))
    assert xb.quantity > xa.quantity and "không trừ theo ngưỡng" in xb.formula


def test_cross_checks_only_warn():
    assert {"be_tong_tren_san", "thep_tren_m3_be_tong"} <= set(load_ranges())
    works = [WorkItem(code="SAN", name="s", unit="m³", quantity=1.0), WorkItem(code="COT", name="c", unit="m³", quantity=50.0),
             WorkItem(code="COT_THEP", name="t", unit="tấn", quantity=0.1, steel_element="SAN")]
    msgs = cross_checks(works, slab_area_m2=10.0)
    assert any("KH01" in m and "ngoài khoảng" in m for m in msgs)
    assert not any("KH01" in m for m in cross_checks(works, None))          # không có m² sàn: không kiểm tỷ số sàn


def test_envelope_by_orientation():
    """Nhà chữ nhật 10 × 6 m, bắc = +y (north_deg = 90): tường y = 6000 có mặt ngoài quay về +y là hướng Bắc."""
    assert wall_orientation(0, 6000, 10000, 6000, 90.0, inside_sign=-1.0) == "B"     # tâm nhà bên phải đoạn (phía −y)
    env = envelope_by_orientation(walls(), [ReviewOpening(id="O1", wall="A", w=1000, h=2200)], 3300, 90.0)
    assert set(env) == {"B", "Đ", "N", "T"}
    assert env["N"]["length_m"] == pytest.approx(10.0) and env["B"]["length_m"] == pytest.approx(10.0)
    assert env["N"]["opening_m2"] == pytest.approx(2.2) and env["N"]["net_m2"] == pytest.approx(33.0 - 2.2)
    assert envelope_by_orientation(walls(), [], 3300, None) == {}
    res = compute_rough(RoughRequest(params=FULL.model_copy(update={"north_deg": 90.0}), plans=[plan("Tầng 2", False)]),
                        Catalog.from_csv(None))
    assert res.envelope_by_orientation["Tầng 2"]["Đ"]["length_m"] == pytest.approx(6.0)


def test_floor_area_check_against_building_area():
    """KH05: tầng gấp đôi diện tích xây dựng (nhân đôi sàn) bị cảnh báo; tầng trong khoảng thì không; thiếu số thì bỏ qua."""
    from optimat.rough.checks import floor_area_checks
    out = floor_area_checks({"Trệt": 60.0, "Tầng 2": 130.0}, 64.0)
    assert any("KH05" in s and "Tầng 2" in s for s in out) and not any("KH05" in s and "Trệt" in s for s in out)
    assert floor_area_checks({"Trệt": 60.0}, None) == []
    res = compute_rough(RoughRequest(params=FULL.model_copy(update={"building_area_m2": 1.0}),
                                     plans=[plan("Trệt", True)]), Catalog.from_csv(None))
    assert any("KH05" in s for s in res.warnings)


def test_export_for_optimizer():
    """JSON cho bộ tối ưu: vật liệu có nhóm, kg, lượng theo giai đoạn; dòng D không có số mà nằm trong missing."""
    import json
    from optimat.rough.boq import export_for_optimizer
    res = compute_rough(RoughRequest(params=FULL, plans=[plan("Trệt", True)]), Catalog.from_csv(None))
    out = export_for_optimizer(res)
    json.dumps(out, ensure_ascii=False)
    gn = next(m for m in out["materials"] if m["material_id"] == "GN01")
    assert gn["group_id"] == "phan_tho" and gn["weight_kg"] > 0 and gn["provisional"] and gn["by_stage"].get("tuong", 0) > 0
    assert all(m["status"] != "D" for m in out["materials"])
    d = [m for m in res.materials if m.status == "D"]
    assert len(out["missing"]) == len(d) and len(out["groups"]) == len(res.by_group)


def test_wall_system_by_class_fills_only_unmarked_walls():
    """Bản vẽ không ghi vật liệu tường: phương án theo lớp do người dùng chọn (ProjectParams.wall_systems_by_class) cho ra
    gạch, trạng thái C; tường đã có vật liệu từ bản vẽ giữ nguyên; mã phương án sai thì báo lỗi."""
    cat = Catalog.from_csv(None)
    bare = plan("Trệt", True)
    bare = bare.model_copy(update={"walls": [w.model_copy(update={"mat": None}) for w in bare.walls]})
    none = compute_rough(RoughRequest(params=FULL, plans=[bare]), cat)
    assert all(w.wall_system_id is None for w in none.works if w.code == "XAY") and not any(m.material_id == "GO01" for m in none.materials)
    p = FULL.model_copy(update={"wall_systems_by_class": {"220": "W-GO01-200", "110": "W-GO01-100"}})
    res = compute_rough(RoughRequest(params=p, plans=[bare]), cat)
    xay = [w for w in res.works if w.code == "XAY"]
    assert {w.wall_system_id for w in xay} == {"W-GO01-200", "W-GO01-100"} and all(w.status == "C" for w in xay)
    assert any("phương án tường: C" in i for w in xay for i in w.inputs)
    assert next(m for m in res.materials if m.material_id == "GO01").quantity > 0
    kept = compute_rough(RoughRequest(params=p, plans=[plan("Trệt", True)]), cat)          # bản vẽ ghi GN01: không đổi
    assert {w.wall_system_id for w in kept.works if w.code == "XAY"} <= {"W-GN01-220", "W-GN01-110"}
    with pytest.raises(ValueError):
        compute_rough(RoughRequest(params=FULL.model_copy(update={"wall_systems_by_class": {"220": "W-KHONG-CO"}}), plans=[bare]), cat)


def test_material_classes_tag_filter_and_totals():
    """Loại vật liệu thô (RAW_CLASSES): mọi dòng có loại (chưa có mã thì theo tên: cốt thép -> thep); chọn loại thì bảng vật
    liệu chỉ còn loại đó, công tác giữ nguyên; tổng theo loại có trong kết quả, BOQ và JSON; mã loại sai báo lỗi."""
    import json
    from optimat.rough.boq import boq_workbook, export_for_optimizer
    from optimat.rough.models import RAW_CLASSES
    cat = Catalog.from_csv(None)
    req = RoughRequest(params=FULL.model_copy(update={"concrete_supply": "site_mix"}), plans=[plan("Trệt", True), plan("Tầng 2", False)])
    full = compute_rough(req, cat)
    by = {m.material_id or m.name: m.raw_class for m in full.materials}
    assert all(c in RAW_CLASSES for c in by.values())
    assert by["GN01"] == "gach" and by["XM02"] == "xi_mang" and by["DA01"] == "da" and by["Cốt thép (chưa chia nhóm đường kính)"] == "thep"
    assert {g.group_id for g in full.by_class} >= {"gach", "xi_mang", "cat", "da", "thep"}
    pick = compute_rough(req.model_copy(update={"params": req.params.model_copy(update={"material_classes": ["gach", "xi_mang"]})}), cat)
    assert {m.raw_class for m in pick.materials} == {"gach", "xi_mang"} and len(pick.works) == len(full.works)
    assert any("Chỉ bóc loại vật liệu đã chọn" in w for w in pick.warnings)
    assert [g.group_id for g in pick.by_class] == ["xi_mang", "gach"]
    assert "Theo loại" in boq_workbook(pick).sheetnames
    out = export_for_optimizer(pick)
    json.dumps(out, ensure_ascii=False)
    assert {c["group_id"] for c in out["classes"]} == {"gach", "xi_mang"} and all(m["raw_class"] for m in out["materials"])
    with pytest.raises(ValueError):
        compute_rough(req.model_copy(update={"params": req.params.model_copy(update={"material_classes": ["kim_cuong"]})}), cat)
