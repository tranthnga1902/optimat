"""B01: diện tích SYNTHETIC, đối chiếu vật tư theo CSV hiện có; không duyệt định mức mới.

Kỳ vọng tính riêng từ bảng 100 m²: DAM gỗ 1,940 m³/đinh 14,29 kg;
MONG 1,339 m³/15 kg; CAU_THANG 1,775 m³/11,45 kg. Kiểm đầu ra
đã làm tròn 3 chữ số, không dùng loader để tính số kỳ vọng.
"""
import pytest

from optimat.catalog.repository import Catalog
from optimat.rough.materials import materials_for_works
from optimat.rough.models import ProjectParams, WorkItem
from optimat.rough.norms import NORMS_PATH, load_norms


@pytest.fixture(scope="module")
def catalog():
    return Catalog.from_csv(None)


@pytest.fixture(scope="module")
def csv_norms():
    return load_norms(str(NORMS_PATH))  # Đường dẫn rõ ràng: không đọc DB.


def formwork(element, area):
    return WorkItem(code="COP_PHA", name="Cốp pha SYNTHETIC", unit="m²",
                    quantity=area, formwork_of=element, status="C", source="manual")


def bill_for(catalog, csv_norms, works):
    return materials_for_works(works, ProjectParams(formwork_type="go"), catalog, csv_norms)


def assert_materials(bill, wood, nails):
    rows = {m.material_id: m for m in bill.materials}
    assert set(rows) == {"CP03", "CP06"}
    for material_id, expected, unit in (("CP03", wood, "m³"), ("CP06", nails, "kg")):
        row = rows[material_id]
        assert row.unit == unit and row.quantity == pytest.approx(expected, abs=1e-9)
        assert row.complete and row.quantity_with_waste == row.quantity
        assert all(u.waste_included for u in row.uses)
        assert "hao hụt thi công (%)" not in row.missing


@pytest.mark.parametrize("element,area,wood,nails", [
    ("DAM", 10, 0.194, 1.429),
    ("MONG", 100, 1.339, 15.0),
    ("CAU_THANG", 100, 1.775, 11.45),
])
def test_wood_formwork_materials_follow_element(catalog, csv_norms, element, area, wood, nails):
    assert_materials(bill_for(catalog, csv_norms, [formwork(element, area)]), wood, nails)


@pytest.mark.parametrize("element,area,wood,nails", [
    ("DAM", -10, -0.194, -1.429),
    ("MONG", -100, -1.339, -15.0),
    ("CAU_THANG", -100, -1.775, -11.45),
])
def test_negative_formwork_reverses_materials(catalog, csv_norms, element, area, wood, nails):
    assert_materials(bill_for(catalog, csv_norms, [formwork(element, area)]), wood, nails)


def test_deduction_reduces_positive_beam_formwork(catalog, csv_norms):
    works = [formwork("DAM", 10), formwork("DAM", -2)]
    assert_materials(bill_for(catalog, csv_norms, works), 0.155, 1.143)


def test_different_elements_keep_their_own_norms_when_summed(catalog, csv_norms):
    works = [formwork("DAM", 10), formwork("MONG", 100), formwork("CAU_THANG", 100)]
    assert_materials(bill_for(catalog, csv_norms, works), 3.308, 27.879)


def test_unknown_wood_element_stays_missing(catalog, csv_norms):
    bill = bill_for(catalog, csv_norms, [formwork("KHONG_CO", 10)])
    assert len(bill.materials) == 1
    row = bill.materials[0]
    assert row.material_id is None and row.quantity is None and not row.complete and row.status == "D"
    assert any("định mức ván khuôn" in reason and "KHONG_CO" in reason for reason in row.missing)


@pytest.mark.parametrize("element", ["DAM", "MONG", "CAU_THANG"])
def test_missing_formwork_area_does_not_become_zero(catalog, csv_norms, element):
    bill = bill_for(catalog, csv_norms, [formwork(element, None)])
    assert {m.material_id for m in bill.materials} == {"CP03", "CP06"}
    assert all(m.quantity is None and m.quantity_with_waste is None and not m.complete and m.status == "D"
               for m in bill.materials)
    assert any("chưa có khối lượng" in warning for warning in bill.warnings)
