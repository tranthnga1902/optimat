"""S08: cầu thang, giằng tường, sê nô, mái; không cộng trùng lanh tô – dầm, giằng – tường, mái – sàn."""
import math
from pathlib import Path

import pandas as pd
import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.dxf_reader import Drawing, Segment, TextItem
from optimat.drawing.review import ReviewOpening, ReviewWall
from optimat.rough.beams import Beam
from optimat.rough.models import ProjectParams, RoofItem
from optimat.rough.secondary import LinearMember, deduct_ties, linear_works, normalize_ties, read_secondary, roof_kind
from optimat.rough.status import assign_status
from optimat.rough.stairs import Stair, stair_works
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough

ROOT = Path(__file__).resolve().parents[1]
WALL = ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
P = ProjectParams(beam_depth_mm=300, lintel_height_mm=200, lintel_bearing_mm=200, plaster_thickness_mm=15)


@pytest.fixture(scope="module")
def cat():
    return Catalog.from_csv(None)


def _one(res, code, plan="T1"):
    return next(w for w in res.works if w.code == code and w.plan == plan)


def _plan(**kw):
    return PlanInput(name="T1", height_mm=3300, walls=[WALL], **kw)


@pytest.mark.parametrize("kind", ["GIANG_TUONG", "SE_NO"])
@pytest.mark.parametrize("source, expected", [("structural", "A"), ("manual", "C"), ("inferred", "C")])
def test_linear_member_keeps_source_for_concrete_and_formwork(kind, source, expected):
    member = LinearMember(id="G1", kind=kind, x1=0, y1=0, x2=4000, y2=0,
                          b_mm=220, d_mm=150, source=source, z_bottom_mm=1000)
    works, _ = linear_works("T1", [member], tie_groups=normalize_ties([member], plan_context=True))
    quantities = [w.quantity for w in works]
    assign_status(works, ProjectParams(), {})
    concrete, formwork = works
    # Cao độ khai báo trong mặt bằng là phụ thuộc C kể cả source kết cấu.
    expected = "C" if kind == "GIANG_TUONG" else expected
    assert all(w.source == source and w.status == expected for w in works)
    assert concrete.quantity == pytest.approx(0.132)
    assert formwork.quantity == pytest.approx(1.2 if kind == "GIANG_TUONG" else 2.08)
    assert [w.quantity for w in works] == quantities
    assert any(f"({source})" in e for e in concrete.evidence)


@pytest.mark.parametrize("reverse", [False, True])
def test_linear_members_same_section_keep_separate_sources(reverse):
    members = [LinearMember(id="G1", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0,
                            b_mm=220, d_mm=150, source="structural", z_bottom_mm=1000),
               LinearMember(id="G2", kind="GIANG_TUONG", x1=4000, y1=0, x2=8000, y2=0,
                            b_mm=220, d_mm=150, source="manual", z_bottom_mm=1000)]
    ordered = members[::-1] if reverse else members
    works, _ = linear_works("T1", ordered, tie_groups=normalize_ties(ordered, plan_context=True))
    assign_status(works, ProjectParams(), {})
    concrete = [w for w in works if w.code == "GIANG_TUONG"]
    formwork = [w for w in works if w.code == "COP_PHA"]
    assert len(concrete) == len(formwork) == 2
    assert {w.source: w.status for w in concrete} == {"structural": "C", "manual": "C"}
    assert {w.source for w in formwork} == {"structural", "manual"}
    assert all(w.status == "C" for w in formwork)  # kế thừa yếu nhất của cùng cấu kiện/tầng
    assert sum(w.quantity for w in concrete) == pytest.approx(0.264)
    assert sum(w.quantity for w in formwork) == pytest.approx(2.4)
    assert all(len(w.evidence) == 1 and f"({w.source})" in w.evidence[0] for w in concrete)


def test_lintel_not_double_counted_with_beam(cat):
    """Cửa cao 2900: đỉnh lanh tô (2900 + 200) vượt đáy dầm (3300 − 300) -> dầm làm lanh tô, không lanh tô riêng."""
    beam = Beam(id="D1", x1=0, y1=0, x2=10000, y2=0, b_mm=220, d_mm=300, source="manual")
    p = P.model_copy(update={"slab_thickness_mm": 120})
    res = compute_rough(RoughRequest(params=p, plans=[_plan(openings=[ReviewOpening(id="O1", wall="W1", w=1000, h=2900)],
                                                            beams=[beam])]), cat)
    assert _one(res, "LANH_TO").quantity == 0 and _one(res, "DAM").quantity
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 1.0 * 2.9 * 0.22, abs=1e-3)
    assert any("tránh trùng dầm" in w for w in res.warnings)


def test_lintel_kept_when_below_beam(cat):
    res = compute_rough(RoughRequest(params=P, plans=[_plan(openings=[ReviewOpening(id="O1", wall="W1", w=1000, h=2200)],
                                                            beams=[])]), cat)
    assert _one(res, "LANH_TO").quantity == pytest.approx(1.4 * 0.22 * 0.2, abs=1e-3)
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 2.2 * 0.22 - 1.4 * 0.22 * 0.2, abs=1e-3)


def test_tie_deducted_from_masonry(cat):
    tie = LinearMember(id="GT1", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0, b_mm=220, d_mm=150, z_bottom_mm=1000)
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=[tie])]), cat)
    assert _one(res, "GIANG_TUONG").quantity == pytest.approx(4 * 0.22 * 0.15, abs=1e-3)
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 4 * 0.15 * 0.22, abs=1e-3)
    form = next(w for w in res.works if w.formwork_of == "GIANG_TUONG")
    assert form.quantity == pytest.approx(2 * 0.15 * 4, abs=1e-3)
    assert any(t.code == "GIANG_TUONG" for t in res.formwork)


def test_tie_without_depth_left_blank(cat):
    tie = LinearMember(id="GT1", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0, b_mm=220)
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=[tie])]), cat)
    assert _one(res, "GIANG_TUONG").quantity is None and "cao giằng" in _one(res, "GIANG_TUONG").missing
    assert _one(res, "XAY").quantity is None and _one(res, "XAY").missing  # chưa đủ cơ sở trừ, giữ raw trong evidence


def test_overlapping_ties_deduct_masonry_once(cat):
    ties = [LinearMember(id=f"GT{i}", kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0,
                         b_mm=220, d_mm=150, z_bottom_mm=1000) for i in (1, 2)]
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=ties)]), cat)
    assert _one(res, "XAY").quantity == pytest.approx(10 * 3.0 * 0.22 - 4 * 0.15 * 0.22, abs=1e-3)
    assert _one(res, "GIANG_TUONG").quantity == pytest.approx(0.132)
    assert next(w for w in res.works if w.formwork_of == "GIANG_TUONG").quantity == pytest.approx(1.2)


def test_gutter_rectangular_with_warning(cat):
    sn = LinearMember(id="SN1", kind="SE_NO", x1=0, y1=0, x2=6000, y2=0, b_mm=600, d_mm=400)
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=[sn])]), cat)
    assert _one(res, "SE_NO").quantity == pytest.approx(6 * 0.6 * 0.4, abs=1e-3)
    assert any("chữ U" in w for w in res.warnings)


def test_concrete_roof_replaces_slab(cat):
    p = P.model_copy(update={"slab_thickness_mm": 120,
                             "roofs": [RoofItem(kind="be_tong", area_m2=50, thickness_mm=100, replaces_slab_of="T1")]})
    res = compute_rough(RoughRequest(params=p, plans=[_plan(beams=[])]), cat)
    mai = next(w for w in res.works if w.code == "MAI")
    assert mai.quantity == pytest.approx(5.0) and not any(w.code == "SAN" for w in res.works)
    assert not any(w.formwork_of == "SAN" for w in res.works) and any(t.code == "MAI" for t in res.formwork)


def test_frame_roof_not_supported(cat):
    res = compute_rough(RoughRequest(params=ProjectParams(roofs=[RoofItem(name="Mái tôn", kind="khung", area_m2=80)]),
                                     plans=[]), cat)
    mai = next(w for w in res.works if w.code == "MAI")
    assert mai.quantity is None and mai.basis == "not_supported" and "Not supported" in mai.missing[0]
    assert not any(u.work == "MAI" for m in res.materials for u in m.uses)
    assert roof_kind("CHI TIẾT VÌ KÈO MÁI") == "khung" and roof_kind("MẶT BẰNG KẾT CẤU SÀN MÁI") == "be_tong"


def test_stair_with_landing_beam():
    s = Stair(steps=22, flight_width_mm=1000, tread_mm=250, landing_area_m2=2.0, beam_length_mm=2400,
              beam_width_mm=220, beam_depth_mm=300)
    works, _ = stair_works("T1", [s], 3300, ProjectParams(stair_slab_thickness_mm=120))
    riser, slope = 3.3 / 22, math.hypot(22 * 0.25, 3.3)
    assert works[0].quantity == pytest.approx(slope * 0.12 + 22 * 0.25 * riser / 2 + 0.24 + 2.4 * 0.22 * 0.3, abs=1e-3)
    assert works[1].quantity == pytest.approx(slope + 2.0 + 22 * riser + (0.6 + 0.22) * 2.4, abs=1e-3)


def test_stair_con_not_supported():
    works, _ = stair_works("T1", [Stair(kind="con", steps=20, flight_width_mm=1000, tread_mm=250)], 3300,
                           ProjectParams(stair_slab_thickness_mm=120))
    assert len(works) == 1 and works[0].quantity is None and works[0].basis == "not_supported"
    works, _ = stair_works("T1", [Stair(steps=20, flight_width_mm=1000, tread_mm=250, beam_length_mm=2000)], 3300,
                           ProjectParams(stair_slab_thickness_mm=120))
    assert works[0].quantity is None and "tiết diện dầm thang" in works[0].missing


def test_read_secondary_from_structural_plan():
    segs = [Segment(0, 0, 6000, 0, "KC"), Segment(0, 220, 6000, 220, "KC")]
    texts = [TextItem("MẶT BẰNG DẦM SÀN LẦU 1", 3000, -2000, "T", "unicode", 600),
             TextItem("GT1", 3000, 400, "T", "unicode", 300),
             TextItem("GT1 220x150", 20000, -3000, "T", "unicode", 300),
             TextItem("LT1 220x200", 20000, -4000, "T", "unicode", 300),
             TextItem("CHI TIẾT VÌ KÈO", 30000, -9000, "T", "unicode", 600)]
    d = Drawing(segments=segs, texts=texts, blocks=[], hatches=[], layers=["KC"], layer_classes={}, unit_scale=1.0, warnings=[])
    members, lintel_h, warnings = read_secondary(d)
    assert len(members) == 1 and members[0].kind == "GIANG_TUONG" and (members[0].b_mm, members[0].d_mm) == (220, 150)
    assert members[0].length_mm == pytest.approx(6000) and lintel_h == {"lt1": 200}
    assert any("chưa trừ khỏi khối xây" in w for w in warnings) and any("Not supported" in w for w in warnings)


def test_support_matrix_backed_by_tests():
    """Nhóm 'supported' phải có ít nhất một test chuẩn và một case âm tính, và các test đó tồn tại."""
    m = pd.read_csv(ROOT / "data/rules/ho_tro_cau_kien.csv", dtype=str, keep_default_na=False)
    assert set(m.trang_thai) <= {"supported", "conditional", "not_supported"}
    for row in m[m.trang_thai == "supported"].itertuples():
        refs = [r.strip() for r in row.kiem_thu.split(";") if r.strip()]
        assert len(refs) >= 2, row.cau_kien
        for ref in refs:
            f, name = ref.split("::")
            assert f"def {name}(" in (ROOT / f).read_text(encoding="utf-8"), ref


# N03: các ca toán có cao độ/ngữ cảnh được khai báo tường minh; legacy có ca riêng.
def _tie(id="G1", **kw):
    data = dict(id=id, kind="GIANG_TUONG", x1=0, y1=0, x2=4000, y2=0,
                b_mm=220, d_mm=150, z_bottom_mm=1000, z_evidence="SYNTHETIC, đã xác nhận đáy +1000 so đáy T1")
    data.update(kw)
    return LinearMember(**data)


def _compute_ties(cat, ties, **kw):
    return compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=ties, **kw)]), cat)


@pytest.mark.parametrize("reverse", [False, True])
def test_n03_partial_overlap_uses_same_union_for_all_quantities(cat, reverse):
    ties = [_tie("G1"), _tie("G2", x1=6000, x2=2000), _tie("G3")]
    res = _compute_ties(cat, ties[::-1] if reverse else ties)
    assert _one(res, "GIANG_TUONG").quantity == pytest.approx(0.198)
    assert next(w for w in res.works if w.formwork_of == "GIANG_TUONG").quantity == pytest.approx(1.8)
    assert _one(res, "XAY").quantity == pytest.approx(6.402)
    assert all(any(m.id in ev for ev in _one(res, "GIANG_TUONG").evidence) for m in ties)
    assert _one(res, "GIANG_TUONG").status == "C"
    assert any("cao độ" in i and "C" in i for i in _one(res, "GIANG_TUONG").inputs)


def test_n03_disjoint_elevations_remain_two_ties(cat):
    res = _compute_ties(cat, [_tie(), _tie("G2", z_bottom_mm=2000)])
    assert sum(w.quantity for w in res.works if w.code == "GIANG_TUONG") == pytest.approx(0.264)
    assert sum(w.quantity for w in res.works if w.formwork_of == "GIANG_TUONG") == pytest.approx(2.4)
    assert _one(res, "XAY").quantity == pytest.approx(6.336)


@pytest.mark.parametrize("second", [dict(z_bottom_mm=None), dict(z_bottom_mm=1050),
                                     dict(b_mm=200), dict(d_mm=200), dict(source="structural")])
def test_n03_ambiguous_intersection_is_not_a_complete_total(cat, second):
    res = _compute_ties(cat, [_tie(), _tie("G2", **second)])
    assert _one(res, "XAY").quantity is None and _one(res, "XAY").status == "D"
    assert all(w.quantity is None and w.missing for w in res.works if w.code == "GIANG_TUONG")
    assert any("6.6" in ev for ev in _one(res, "XAY").evidence)
    assert any("G2" in ev for ev in _one(res, "XAY").evidence)


@pytest.mark.parametrize("z", [float("nan"), float("inf"), float("-inf")])
def test_n03_elevation_must_be_finite(z):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        _tie(z_bottom_mm=z)


def test_n03_legacy_without_z_or_context_is_explicitly_incomplete(cat):
    members = [_tie(z_bottom_mm=None), _tie("G2", z_bottom_mm=None)]
    res = _compute_ties(cat, members)
    assert _one(res, "XAY").quantity is None and _one(res, "GIANG_TUONG").quantity is None
    works, warnings = linear_works("tên tầng bất kỳ", [_tie()])
    assert all(w.quantity is None and w.status == "D" for w in works)
    assert any("pending K03" in w for w in warnings)


@pytest.mark.parametrize("z", [-1, 2900])
def test_n03_outside_vertical_wall_bounds_does_not_clamp_net(cat, z):
    res = _compute_ties(cat, [_tie(z_bottom_mm=z)])
    assert _one(res, "XAY").quantity is None
    assert any("vượt đáy/đỉnh" in r for r in _one(res, "XAY").missing)


@pytest.mark.parametrize("openings,columns,blocked", [(None, {}, True), ([], None, True), ([], {}, False)])
def test_n03_unknown_inputs_are_not_known_empty(cat, openings, columns, blocked):
    from optimat.rough.models import WorkItem
    w = WorkItem(code="XAY", name="xây", unit="m³", quantity=6.6, plan="T1",
                 element="tường 220 bao che", wall_system_id=None)
    ties = [_tie()]
    deduct_ties([w], "T1", [WALL], {}, ties, cat, tie_groups=normalize_ties(ties, plan_context=True),
                wall_height_mm=3000, openings=openings, column_len_in_walls=columns)
    assert (w.quantity is None) == blocked
    if not blocked:
        assert w.quantity == pytest.approx(6.468)


def test_n03_opening_gate_flows_through_totals_materials_and_boq(cat):
    from optimat.rough.boq import boq_workbook, export_for_optimizer
    res = _compute_ties(cat, [_tie()], openings=[ReviewOpening(id="O1", wall="W1", w=1000, h=2000)])
    xay = _one(res, "XAY")
    assert xay.quantity is None and xay.status == "D" and any("lỗ mở" in m for m in xay.missing)
    assert any("trước trừ giằng" in ev for ev in xay.evidence)
    total = next(t for t in res.totals if t.code == "XAY")
    assert total.quantity is None and not total.complete and total.status == "D"
    brick = next(m for m in res.materials if m.material_id == "GN01")
    assert brick.quantity is None and not brick.complete and brick.status == "D"
    out = export_for_optimizer(res)
    assert not any(m["material_id"] == "GN01" for m in out["materials"])
    assert any(m["material_id"] == "GN01" and m["known_part"] is None for m in out["missing"])
    ws = boq_workbook(res)["Theo tầng"]
    rows = list(ws.values); headers = rows[0]
    row = next(dict(zip(headers, r)) for r in rows[1:] if r[headers.index("Công tác")] == xay.name)
    assert row["Khối lượng"] is None and "D" in row["Trạng thái (A đọc / B suy / C tạm tính / D thiếu)"]
    assert "lỗ mở" in row["missing_reason"]


def test_n03_only_affected_wall_group_is_incomplete(cat):
    wall2 = WALL.model_copy(update={"id": "W2", "cls": "110", "role": "partition", "y1": 10000, "y2": 10000})
    req = RoughRequest(params=P, plans=[PlanInput(name="T1", height_mm=3300, beams=[], walls=[WALL, wall2],
        members=[_tie()], openings=[ReviewOpening(id="O1", wall="W1", w=1000, h=2000)])])
    res = compute_rough(req, cat)
    xay = [w for w in res.works if w.code == "XAY"]
    assert next(w for w in xay if "220" in w.element).quantity is None
    assert next(w for w in xay if "110" in w.element).quantity is not None


def test_n03_grouped_wall_keeps_raw_without_reverse_allocation(cat):
    wall2 = WALL.model_copy(update={"id": "W2", "y1": 10000, "y2": 10000})
    res = compute_rough(RoughRequest(params=P, plans=[PlanInput(name="T1", height_mm=3300, beams=[],
        walls=[WALL, wall2], members=[_tie()],
        openings=[ReviewOpening(id="O1", wall="W1", w=1000, h=2000)])]), cat)
    xay = _one(res, "XAY")
    assert xay.quantity is None and any("W1" in r for r in xay.missing)
    assert not any("W2" in r for r in xay.missing)
    assert any("XAY trước trừ" in ev for ev in xay.evidence)


def test_n03_structural_members_never_deduct_without_plan_context(cat):
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[])], members=[_tie(source="structural")]), cat)
    assert _one(res, "XAY").quantity == pytest.approx(6.6)
    tie = next(w for w in res.works if w.code == "GIANG_TUONG")
    assert tie.quantity is None and tie.status == "D" and any("pending K03" in m for m in tie.missing)


@pytest.mark.parametrize("changes", [dict(x2=4000, y2=1000), dict(x2=0), dict(b_mm=None), dict(d_mm=None)])
def test_n03_unsupported_geometry_keeps_missing(cat, changes):
    res = _compute_ties(cat, [_tie(**changes)])
    assert _one(res, "GIANG_TUONG").quantity is None and _one(res, "GIANG_TUONG").status == "D"


def test_n03_keep_false_and_gutter_do_not_deduct(cat):
    res = _compute_ties(cat, [_tie(keep=False), _tie("SN1", kind="SE_NO", z_bottom_mm=None)])
    assert not any(w.code == "GIANG_TUONG" for w in res.works)
    assert _one(res, "XAY").quantity == pytest.approx(6.6)


def test_n03_parallel_offset_tie_is_not_merged_by_clip_tolerance(cat):
    res = _compute_ties(cat, [_tie(), _tie("G2", y1=50, y2=50)])
    assert len([w for w in res.works if w.code == "GIANG_TUONG"]) == 2
    assert _one(res, "XAY").quantity is None
    assert all(w.quantity is None and w.status == "D" and w.missing
               for w in res.works if w.code == "GIANG_TUONG" or w.formwork_of == "GIANG_TUONG")


def test_n03_column_gate_marks_affected_group(cat):
    from optimat.rough.columns import Column
    res = _compute_ties(cat, [_tie()], columns=[Column(id="C1", x=2000, y=0, b_mm=220, h_mm=220)])
    assert _one(res, "XAY").quantity is None and any("đã trừ cột" in m for m in _one(res, "XAY").missing)



def test_n03_confirmed_union_reaches_materials_boq_and_optimizer(cat):
    from optimat.rough.boq import boq_workbook, export_for_optimizer
    res = _compute_ties(cat, [_tie(), _tie("G2")])
    brick = next(m for m in res.materials if m.material_id == "GN01")
    assert brick.quantity == pytest.approx(6.468 * 550) and brick.complete and brick.status == "C"
    material = next(m for m in export_for_optimizer(res)["materials"] if m["material_id"] == "GN01")
    assert material["quantity"] == pytest.approx(6.468 * 550) and material["provisional"]
    rows = list(boq_workbook(res)["Theo tầng"].values); header = rows[0]
    row = next(dict(zip(header, r)) for r in rows[1:] if r[header.index("Công tác")] == _one(res, "XAY").name)
    assert row["Khối lượng"] == pytest.approx(6.468) and "C" in row["Trạng thái (A đọc / B suy / C tạm tính / D thiếu)"]


def test_n03_all_raw_ids_survive_union_evidence_beyond_label_limit(cat):
    ties = [_tie(f"G{i}") for i in range(8)]
    res = _compute_ties(cat, ties)
    concrete = _one(res, "GIANG_TUONG")
    assert concrete.quantity == pytest.approx(0.132) and len(concrete.evidence) == 8
    for m in ties:
        assert any(ev.startswith(m.id + " ") for ev in concrete.evidence)
        assert any(ev.startswith(m.id + " ") for ev in _one(res, "XAY").evidence)


def test_n03_other_plan_keeps_own_elevation_and_quantity(cat):
    res = compute_rough(RoughRequest(params=P, plans=[_plan(beams=[], members=[_tie(), _tie("G2")]),
        PlanInput(name="T2", height_mm=3300, walls=[WALL], beams=[], members=[_tie()])]), cat)
    assert _one(res, "GIANG_TUONG", "T1").quantity == pytest.approx(0.132)
    assert _one(res, "GIANG_TUONG", "T2").quantity == pytest.approx(0.132)
    assert _one(res, "XAY", "T1").quantity == _one(res, "XAY", "T2").quantity == pytest.approx(6.468)


@pytest.mark.parametrize("second", [dict(y1=100, y2=100),
                                     dict(x1=4050, x2=4050, y1=-500, y2=500)])
def test_n03_review_xy_sections_overlap_even_when_axes_do_not_cross(cat, second):
    members = [_tie(), _tie("G2", **second)]
    groups = normalize_ties(members, plan_context=True)
    assert len(groups) == 2 and all(g.missing for g in groups)
    works, _ = linear_works("T1", members, tie_groups=groups)
    assert all(w.quantity is None and w.status == "D" and w.missing for w in works)
    assert all(any(ev.startswith(m.id + " ") for w in works for ev in w.evidence) for m in members)
    res = _compute_ties(cat, members)
    total = next(t for t in res.totals if t.code == "GIANG_TUONG")
    assert total.quantity is None and not total.complete and total.status == "D"
    assert all(m.status == "D" and not m.complete for m in res.materials
               if any(u.work == "GIANG_TUONG" for u in m.uses))


@pytest.mark.parametrize("second", [dict(y1=400, y2=400), dict(y1=220, y2=220),
                                     dict(y1=100, y2=100, z_bottom_mm=2000)])
def test_n03_review_disjoint_sections_are_not_merged_or_marked_missing(second):
    members = [_tie(), _tie("G2", **second)]
    groups = normalize_ties(members, plan_context=True)
    assert len(groups) == 2 and not any(g.missing for g in groups)
    works, _ = linear_works("T1", members, tie_groups=groups)
    assert sum(w.quantity for w in works if w.code == "GIANG_TUONG") == pytest.approx(0.264)
    assert sum(w.quantity for w in works if w.formwork_of == "GIANG_TUONG") == pytest.approx(2.4)
    assert all(w.status == "C" and not w.missing for w in works)


@pytest.mark.parametrize("width,concrete,net", [(100, 0.060, 6.540), (220, 0.132, 6.468), (300, 0.180, 6.468)])
def test_n03_review_masonry_uses_actual_intersection_width(cat, width, concrete, net):
    from optimat.rough.boq import boq_workbook
    res = _compute_ties(cat, [_tie(b_mm=width)])
    xay, tie = _one(res, "XAY"), _one(res, "GIANG_TUONG")
    assert xay.quantity == pytest.approx(net) and xay.status == "C" and not xay.missing
    assert tie.quantity == pytest.approx(concrete) and tie.status == "C" and not tie.missing
    cp = next(w for w in res.works if w.formwork_of == "GIANG_TUONG")
    if width > 220:
        assert cp.quantity is None and cp.status == "D" and any("đáy không được tường đỡ đầy" in m for m in cp.missing)
        assert any("cốp pha đáy" in warning for warning in res.warnings)
        total = next(t for t in res.formwork if t.code == "GIANG_TUONG")
        assert total.quantity is None and not total.complete and total.status == "D"
        rows = list(boq_workbook(res)["Theo tầng"].values); header = rows[0]
        row = next(dict(zip(header, r)) for r in rows[1:] if r[header.index("Công tác")] == cp.name and "giằng" in str(r[header.index("Chi tiết")]))
        assert row["Khối lượng"] is None and "cốp pha đáy" in row["missing_reason"]
    else:
        assert cp.quantity == pytest.approx(1.2) and not cp.missing
    brick = next(m for m in res.materials if m.material_id == "GN01")
    assert brick.quantity == pytest.approx(net * 550) and brick.complete
