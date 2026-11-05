"""Liên kết phần góp vật tư với dòng công tác trong đúng snapshot; dữ liệu hình học thử."""
import pytest

from optimat.catalog.repository import Catalog
from optimat.rough.materials import materials_for_works
from optimat.rough.models import MaterialUse, ProjectParams
from optimat.rough.structural_column_instances import StructuralColumnInstance, instance_column_works


@pytest.fixture(scope="module")
def catalog():
    return Catalog.from_csv()


def segment(key, axis, slab):
    return StructuralColumnInstance(instance_id=key, code="C2", grid_x=axis, grid_y="A", floor_key="T2",
        file="fixture.dxf", sheet="S1", b_mm=250, h_mm=400, z_from_mm=3000, z_to_mm=6000,
        top_slab_thickness_mm=slab, top_slab_source="Vùng sàn của cột thử" if slab else None,
        evidence=["Hồ sơ tổng hợp cho kiểm thử"])


@pytest.mark.parametrize("supply,material_ids", [
    ("ready_mix", {"BT03"}), ("site_mix", {"XM02", "CA01", "DA01"}), (None, {None})
])
def test_contributions_use_final_row_indices_for_each_segment(catalog, supply, material_ids):
    works = instance_column_works([segment("first", "1", None), segment("second", "2", 100)])
    # Cả hai có cùng mã công tác/tầng. Đổi thứ tự như khi producer hoàn tất sắp xếp snapshot.
    works = [works[i] for i in (3, 0, 2, 1)]
    params = ProjectParams(concrete_supply=supply, concrete_grade="M250")
    bill = materials_for_works(works, params, catalog)
    concrete = [m for m in bill.materials if any(u.work == "COT" for u in m.uses)]
    assert {m.material_id for m in concrete} == material_ids
    for m in concrete:
        assert [(u.model_dump().get("rowIndex"), u.work, u.plan) for u in m.uses] == [
            (1, "COT", "T2"), (2, "COT", "T2")]
        assert m.uses[0].quantity is None and m.uses[1].quantity > 0
        assert not m.complete and m.est_cost is None
        assert all(u.waste_included == (supply == "site_mix") for u in m.uses)
    if supply == "ready_mix":
        assert concrete[0].uses[1].quantity == pytest.approx(0.29)
    if supply == "site_mix":
        assert all(m.quantity_with_waste == m.quantity for m in concrete)
    cp = [u for m in bill.materials for u in m.uses if u.work == "COP_PHA"]
    assert [(u.model_dump().get("rowIndex"), u.quantity) for u in cp] == [(0, None), (3, None)]


def test_grade_is_not_taken_from_unrelated_evidence_and_legacy_use_opens(catalog):
    col = segment("one", "1", 100)
    col.evidence.append("Ghi chú B20 (M250) của cấu kiện khác")
    works = instance_column_works([col])
    bill = materials_for_works(works, ProjectParams(concrete_supply="ready_mix"), catalog)
    assert not any(m.material_id == "BT03" for m in bill.materials)
    demand = next(m for m in bill.materials if m.uses[0].work == "COT")
    assert demand.quantity == pytest.approx(0.29) and "mác bê tông" in demand.missing
    assert MaterialUse.model_validate({"work": "COT", "plan": "T2"}).model_dump().get("rowIndex") is None
