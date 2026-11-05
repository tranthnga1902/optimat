"""J05c: vữa trát theo dày + họ vật liệu nền (AK.211/212; tường gạch rỗng +10% hao phí vữa, số đã nhân trong CSV).

Số liệu SYNTHETIC (diện tích tự đặt), định mức và cấp phối thật của data/rules, danh mục thật.
"""
import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewWall
from optimat.rough.materials import materials_for_works
from optimat.rough.models import WORKS, ProjectParams, WorkItem
from optimat.rough.takeoff import RoughRequest, compute_rough
from optimat.rough.walls import wall_works
from tests.test_rough_takeoff import FULL, plan

M75 = ProjectParams(plaster_mortar_grade="M75")      # VU02: 307 kg xi măng (XM01, tấn), 1,13 m³ cát (CA02) / m³ vữa


@pytest.fixture(scope="module")
def cat():
    return Catalog.from_csv(None)


def trat(qty, system, variant="15"):
    name, unit = WORKS["TRAT"]
    return WorkItem(code="TRAT", name=name, unit=unit, quantity=qty, variant=variant, wall_system_id=system)


def mortar(bill):
    return sum(i.quantity for i in bill.intermediates if i.kind == "vua" and i.quantity is not None)


def line(bill, key):
    return next(m for m in bill.materials if (m.material_id or m.name) == key)


@pytest.mark.parametrize("system, variant, m3", [("W-GN02-220", "15", 1.87), ("W-GN02-220", "20", 2.53),
                                                  ("W-GO01-200", "15", 1.87), ("W-GN01-220", "15", 1.7),
                                                  ("W-GN01-220", "20", 2.3)])
def test_plaster_mortar_by_substrate(cat, system, variant, m3):
    bill = materials_for_works([trat(100.0, system, variant)], M75, cat)
    assert mortar(bill) == pytest.approx(m3)
    assert line(bill, "XM01").quantity == pytest.approx(round(m3 * 307 / 1000, 3))     # tách một lần, không nhân 1,10 nữa
    assert line(bill, "CA02").quantity == pytest.approx(round(m3 * 1.13, 3))
    assert line(bill, "XM01").complete and all(u.waste_included for u in line(bill, "XM01").uses)


def test_two_substrates_kept_apart(cat):
    """Hai tường cùng dày khác nền: mỗi phần góp giữ hệ số của nó, không nhân 1,10 lên cả tổng."""
    bill = materials_for_works([trat(100.0, "W-GN01-220"), trat(100.0, "W-GN02-220")], M75, cat)
    assert mortar(bill) == pytest.approx(1.7 + 1.87)
    assert [u.quantity for u in line(bill, "CA02").uses] == pytest.approx([1.7 * 1.13, 1.87 * 1.13], abs=1e-4)


def test_negative_deduction_reverses_hollow_part(cat):
    bill = materials_for_works([trat(100.0, "W-GN02-220"), trat(-20.0, "W-GN02-220")], M75, cat)
    assert mortar(bill) == pytest.approx(80 * 0.0187)


@pytest.mark.parametrize("system, variant, why", [
    (None, "15", "chưa rõ"),                       # chưa có phương án tường
    ("W-KHONG-CO", "15", "chưa rõ"),               # phương án không có trong danh mục
    ("W-AAC02-150", "15", "AAC"),                  # AAC: AK.213–216, chưa tra trong J05c
    ("W-GK02-190", "15", "CMU_HOLLOW"),            # block bê tông rỗng là gạch không nung: không nhận +10% của gạch đất nung
    ("W-GN02-220", "25", "CLAY_HOLLOW"),           # dày không có cột trong bảng
    ("W-GN02-220", None, "chưa nhập"),            # chưa nhập dày trát
])
def test_unknown_or_out_of_scope_substrate_is_missing(cat, system, variant, why):
    bill = materials_for_works([trat(10.0, system, variant)], M75, cat)
    assert bill.intermediates == [] and len(bill.materials) == 1
    m = bill.materials[0]
    assert m.quantity is None and not m.complete and m.status == "D"
    assert any(why in r for r in m.missing)


def test_existing_wall_system_with_blank_family_is_missing(cat):
    """Phương án có trong danh mục nhưng vật liệu chính chưa có họ: khác ca phương án không tồn tại, vẫn thiếu nền."""
    from dataclasses import replace
    blank = replace(cat, materials=cat.materials.assign(family=cat.materials.family.where(cat.materials.material_id != "GN02")))
    bill = materials_for_works([trat(10.0, "W-GN02-220")], M75, blank)
    assert bill.intermediates == [] and len(bill.materials) == 1
    m = bill.materials[0]
    assert m.quantity is None and not m.complete and any("chưa rõ" in r for r in m.missing)


def test_plaster_without_area_on_valid_substrate(cat):
    """Nền hợp lệ nhưng chưa có diện tích trát: vật liệu trống, không 0, vữa trung gian chưa hoàn chỉnh."""
    bill = materials_for_works([trat(None, "W-GN02-220")], M75, cat)
    assert all(m.quantity is None and not m.complete for m in bill.materials)
    assert {m.material_id for m in bill.materials} == {"XM01", "CA02"}
    assert [(i.quantity, i.complete) for i in bill.intermediates] == [(None, False)]


def test_plaster_without_grade_keeps_mortar_quantity(cat):
    bill = materials_for_works([trat(100.0, "W-GN02-220")], ProjectParams(), cat)
    assert mortar(bill) == pytest.approx(1.87)
    assert all(not m.complete and any("mác vữa" in r for r in m.missing) for m in bill.materials)


def test_screed_unchanged(cat):
    name, unit = WORKS["CAN_NEN"]
    bill = materials_for_works([WorkItem(code="CAN_NEN", name=name, unit=unit, quantity=10.0, variant="30")],
                               ProjectParams(screed_mortar_grade="M75"), cat)
    assert mortar(bill) == pytest.approx(0.35)


def test_wall_works_carry_wall_system_to_plaster(cat):
    walls = [ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN02"),
             ReviewWall(id="W2", cls="110", role="partition", x1=0, y1=2000, x2=5000, y2=2000)]
    works, _ = wall_works("Tầng 1", 3300, walls, [], ProjectParams(plaster_thickness_mm=15), cat)
    tr = {w.element: w for w in works if w.code == "TRAT"}
    assert tr["tường 220 bao che, mặt ngoài"].wall_system_id == "W-GN02-220"
    assert tr["tường 220 bao che, mặt trong"].wall_system_id == "W-GN02-220"
    assert tr["tường 110 ngăn, hai mặt"].wall_system_id is None and tr["tường 110 ngăn, hai mặt"].variant == "15"
    bill = materials_for_works([w for w in works if w.code == "TRAT"], M75, cat)
    outer = next(u for u in line(bill, "CA02").uses)
    assert outer.quantity == pytest.approx(tr["tường 220 bao che, mặt ngoài"].quantity * 0.0187 * 1.13, abs=1e-4)
    assert any(m.quantity is None and any("chưa rõ" in r for r in m.missing) for m in bill.materials)   # tường 110 chưa có nền


def test_plaster_substrate_from_user_class_choice_is_c():
    """Phương án theo lớp do người dùng chọn (wall_systems_by_class): dòng trát mang bằng chứng đó, trạng thái C."""
    bare = plan("Trệt", True)
    bare = bare.model_copy(update={"walls": [w.model_copy(update={"mat": None}) for w in bare.walls]})
    p = FULL.model_copy(update={"wall_systems_by_class": {"220": "W-GO01-200", "110": "W-GO01-100"}})
    res = compute_rough(RoughRequest(params=p, plans=[bare]), Catalog.from_csv(None))
    tr = [w for w in res.works if w.code == "TRAT"]
    assert tr and all(w.wall_system_id in ("W-GO01-200", "W-GO01-100") and w.status == "C" for w in tr)
    assert all(any("phương án tường: C" in i for i in w.inputs) for w in tr)
