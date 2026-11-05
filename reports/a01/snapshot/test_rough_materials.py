"""Phần thô bước 1: công tác -> vật liệu mua về (định mức phương án tường, cấp phối vữa, bê tông, định mức CSV)."""
import pytest

from optimat.catalog.repository import Catalog
from optimat.rough.materials import materials_for_works, mortar_material, ready_mix_material
from optimat.rough.models import WORKS, ProjectParams, WorkItem
from optimat.rough.norms import Norm, load_norms


@pytest.fixture(scope="module")
def cat():
    return Catalog.from_csv(None)           # danh mục thật, không đè số mẫu


def work(code, qty, **kw):
    name, unit = WORKS[code]
    return WorkItem(code=code, name=name, unit=unit, quantity=qty, **kw)


def line(bill, key):
    return next(m for m in bill.materials if (m.material_id or m.name) == key)


def test_catalog_has_mix_relations(cat):
    assert {"VU01", "VU02"} <= set(cat.relations[cat.relations.relation_type == "COMPOSED_OF"].material_id)
    assert mortar_material(cat, "M75") == "VU02" and mortar_material(cat, "M50") == "VU01" and mortar_material(cat, None) is None
    assert ready_mix_material(cat, "M250") == "BT03" and ready_mix_material(cat, "M400") is None


def test_masonry_bricks_and_mortar_split(cat):
    bill = materials_for_works([work("XAY", 10.0, wall_system_id="W-GN01-220")], ProjectParams(), cat)
    assert line(bill, "GN01").quantity == pytest.approx(5500)              # 550 viên/m³ (AE.222)
    assert line(bill, "XM01").quantity == pytest.approx(10 * 0.29 * 307 / 1000, abs=1e-3)   # tấn
    sand = line(bill, "CA02")
    assert sand.quantity == pytest.approx(10 * 0.29 * 1.13, abs=1e-3) and sand.waste_pct == 2.0
    # định mức AE.222 đã gồm hao hụt thi công (TT 38 PL II): không cộng thêm 2% của cát, không báo thiếu hao hụt gạch
    assert sand.quantity_with_waste == sand.quantity
    assert "hao hụt thi công (%)" not in line(bill, "GN01").missing and all(u.waste_included for u in line(bill, "GN01").uses)
    assert bill.intermediates[0].material_id == "VU02" and bill.intermediates[0].quantity == pytest.approx(2.9)


def test_masonry_mortar_grade_from_params(cat):
    bill = materials_for_works([work("XAY", 10.0, wall_system_id="W-GN01-220")],
                               ProjectParams(masonry_mortar_grade="M50"), cat)
    assert line(bill, "XM01").quantity == pytest.approx(10 * 0.29 * 224 / 1000, abs=1e-3)   # cấp phối M50 PCB30: TT 38/2026 PL VII 12.10133


def test_masonry_without_wall_system_is_blank(cat):
    bill = materials_for_works([work("XAY", 5.0)], ProjectParams(), cat)
    assert all(m.quantity is None and not m.complete for m in bill.materials)


def test_concrete_ready_mix_and_site_mix(cat):
    w = [work("COT", 2.0), work("SAN", 8.0)]
    ready = materials_for_works(w, ProjectParams(concrete_supply="ready_mix", concrete_grade="M250"), cat)
    assert line(ready, "BT03").quantity == pytest.approx(10.0) and line(ready, "BT03").complete
    assert "hao hụt thi công (%)" in line(ready, "BT03").missing           # thương phẩm: m³ kết cấu, chưa qua định mức 1,025
    site = materials_for_works(w, ProjectParams(concrete_supply="site_mix", concrete_grade="M250"), cat)
    cement = line(site, "XM02")   # TT 38/2026 PL VII 11.12323: 310 kg / m³ vữa × 1,025 m³ vữa / m³ kết cấu, đổi ra tấn
    assert cement.quantity == pytest.approx(10 * 310 * 1.025 / 1000, abs=1e-3) and cement.complete
    assert line(site, "DA01").quantity == pytest.approx(10 * 0.817 * 1.025, abs=1e-3)
    none = materials_for_works(w, ProjectParams(), cat)
    assert any("mác bê tông" in m for m in none.materials[0].missing)


def test_plaster_uses_norm_and_mortar_mix(cat):
    # J05c: khóa định mức trát = dày/họ vật liệu nền của phương án tường (tests/test_rough_plaster.py)
    norms = (Norm("TRAT", "15/CLAY_SOLID", "@VUA", "Vữa trát", 0.017, "m³ / m²", "BẢNG-THỬ", "", ""),)
    w = [work("TRAT", 100.0, variant="15", wall_system_id="W-GN01-220")]
    bill = materials_for_works(w, ProjectParams(plaster_mortar_grade="M75"), cat, norms)
    assert line(bill, "XM01").quantity == pytest.approx(1.7 * 307 / 1000, abs=1e-3)
    csv = materials_for_works(w, ProjectParams(plaster_mortar_grade="M75"), cat)
    assert line(csv, "XM01").quantity == line(bill, "XM01").quantity    # CSV: AK.211/212 0,017 m³ / m² nền gạch đặc
    blank = materials_for_works([work("TRAT", 100.0, variant="15")], ProjectParams(plaster_mortar_grade="M75"), cat)
    assert blank.materials[0].quantity is None and not blank.materials[0].complete      # chưa có phương án: thiếu nền


def test_steel_and_tie_wire(cat):
    bill = materials_for_works([work("COT_THEP", 1.5, steel_element="COT")], ProjectParams(), cat)
    steel = next(m for m in bill.materials if m.name.startswith("Cốt thép"))
    assert steel.quantity == pytest.approx(1.5) and steel.material_id is None
    wire = line(bill, "TH10")    # AF.61xxx 7,85–16,07 kg / tấn tùy đường kính: chưa chia đường kính -> khoảng, tạm tính C
    assert wire.quantity == pytest.approx(1.5 * (7.85 + 16.07) / 2, abs=1e-3)
    assert wire.quantity_min == pytest.approx(1.5 * 7.85, abs=1e-3) and wire.quantity_max == pytest.approx(1.5 * 16.07, abs=1e-3)


def test_missing_work_quantity_warns(cat):
    bill = materials_for_works([work("SAN", None, missing=["chiều dày sàn"])], ProjectParams(concrete_supply="ready_mix",
                                                                                            concrete_grade="M250"), cat)
    assert line(bill, "BT03").quantity is None and any("chiều dày sàn" in w for w in bill.warnings)


def test_norms_csv_valid_and_no_unsourced_numbers(cat):
    norms = load_norms()
    known = set(cat.materials.material_id)
    for n in norms:
        assert n.material_id in (None, "@VUA") or n.material_id in known, n
        # Quy ước B7 mở rộng theo đặc tả 30/10/2026 (1A, 3B): số không có số hiệu bảng TT 38 phải là hệ số tham khảo
        # ghi đủ mức xác nhận, nguồn và ngày tra (vật liệu tính từ đó là tạm tính C)
        assert n.value is None or n.norm_code or (n.confirmation and n.source and n.checked_on), \
            f"Định mức có số mà không có số hiệu bảng và thiếu mức xác nhận / nguồn / ngày tra: {n}"
        assert n.qty_min is None or n.qty_max is None or n.qty_min <= n.qty_max


def test_formwork_materials_by_type_and_element(cat):
    """Ván khuôn gỗ (formwork_type = go): gỗ (CP03) và đinh (CP06) theo định mức AF.81 đúng cấu kiện, không cộng thêm hao
    hụt; chưa chọn loại hoặc ván ép (chưa có định mức) thì vật liệu cốp pha trống kèm lý do."""
    w = [work("COP_PHA", 100.0, formwork_of="COT"), work("COP_PHA", 200.0, formwork_of="SAN")]
    go = materials_for_works(w, ProjectParams(formwork_type="go"), cat)
    wood = line(go, "CP03")
    assert wood.quantity == pytest.approx((0.794 + 0.149 + 0.496) + 2 * (0.794 + 0.112 + 0.668), abs=1e-3)   # AF.81130, AF.81150
    assert line(go, "CP06").quantity == pytest.approx(15.0 + 2 * 8.05, abs=1e-3)
    assert "hao hụt thi công (%)" not in wood.missing and wood.quantity_with_waste == wood.quantity
    none = materials_for_works(w, ProjectParams(), cat)
    assert any("loại ván khuôn" in m for x in none.materials for m in x.missing)
    plywood = materials_for_works(w, ProjectParams(formwork_type="van_ep"), cat)
    assert line(plywood, "CP01").quantity is None
