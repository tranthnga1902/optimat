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
    assert sand.quantity_with_waste == pytest.approx(sand.quantity * 1.02, abs=1e-3)
    assert "hao hụt thi công (%)" in line(bill, "GN01").missing           # gạch chưa có hao hụt: không cộng, có báo
    assert bill.intermediates[0].material_id == "VU02" and bill.intermediates[0].quantity == pytest.approx(2.9)


def test_masonry_mortar_grade_from_params(cat):
    bill = materials_for_works([work("XAY", 10.0, wall_system_id="W-GN01-220")],
                               ProjectParams(masonry_mortar_grade="M50"), cat)
    assert line(bill, "XM01").quantity == pytest.approx(10 * 0.29 * 226 / 1000, abs=1e-3)


def test_masonry_without_wall_system_is_blank(cat):
    bill = materials_for_works([work("XAY", 5.0)], ProjectParams(), cat)
    assert all(m.quantity is None and not m.complete for m in bill.materials)


def test_concrete_ready_mix_and_site_mix(cat):
    w = [work("COT", 2.0), work("SAN", 8.0)]
    ready = materials_for_works(w, ProjectParams(concrete_supply="ready_mix", concrete_grade="M250"), cat)
    assert line(ready, "BT03").quantity == pytest.approx(10.0) and line(ready, "BT03").complete
    site = materials_for_works(w, ProjectParams(concrete_supply="site_mix", concrete_grade="M250"), cat)
    cement = line(site, "XM02")
    assert cement.quantity is None and not cement.complete and any("chưa tra" in m for m in cement.missing)
    none = materials_for_works(w, ProjectParams(), cat)
    assert any("mác bê tông" in m for m in none.materials[0].missing)


def test_plaster_uses_norm_and_mortar_mix(cat):
    norms = (Norm("TRAT", "15", "@VUA", "Vữa trát", 0.017, "m³ / m²", "BẢNG-THỬ", "", ""),)
    bill = materials_for_works([work("TRAT", 100.0, variant="15")], ProjectParams(plaster_mortar_grade="M75"), cat, norms)
    assert line(bill, "XM01").quantity == pytest.approx(1.7 * 307 / 1000, abs=1e-3)
    blank = materials_for_works([work("TRAT", 100.0, variant="15")], ProjectParams(plaster_mortar_grade="M75"), cat)
    assert line(blank, "XM01").quantity is None and any("chưa tra" in m for m in line(blank, "XM01").missing)


def test_steel_and_tie_wire_without_code(cat):
    bill = materials_for_works([work("COT_THEP", 1.5, steel_element="COT")], ProjectParams(), cat)
    steel = next(m for m in bill.materials if m.name.startswith("Cốt thép"))
    assert steel.quantity == pytest.approx(1.5) and steel.material_id is None
    wire = next(m for m in bill.materials if m.name == "Dây thép buộc")
    assert wire.quantity is None and "danh mục chưa có mã vật liệu" in wire.missing


def test_missing_work_quantity_warns(cat):
    bill = materials_for_works([work("SAN", None, missing=["chiều dày sàn"])], ProjectParams(concrete_supply="ready_mix",
                                                                                            concrete_grade="M250"), cat)
    assert line(bill, "BT03").quantity is None and any("chiều dày sàn" in w for w in bill.warnings)


def test_norms_csv_valid_and_no_unsourced_numbers(cat):
    norms = load_norms()
    known = set(cat.materials.material_id)
    for n in norms:
        assert n.material_id in (None, "@VUA") or n.material_id in known, n
        assert n.qty is None or n.norm_code, f"Định mức có số mà không có số hiệu bảng: {n}"
