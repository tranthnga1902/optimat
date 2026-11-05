"""Đọc bản vẽ kết cấu cho phần thô: loại bản vẽ theo tiêu đề, móng đếm theo ký hiệu, dầm đo theo cặp nét."""
from pathlib import Path

import pytest

from optimat.catalog.repository import Catalog
from optimat.drawing.dxf_reader import Drawing, Segment, TextItem, read_drawing
from optimat.drawing.dimensions import Dim, _number, view_scale
from optimat.drawing.sheets import find_views, load_sheet_types, sheet_inventory, sheet_type_of
from optimat.rough.models import ProjectParams
from optimat.rough.structural import element_of, floor_count, read_structural
from optimat.rough.takeoff import RoughRequest, compute_rough, rough_from_drawing

BUILD = Path(__file__).resolve().parents[1] / "data/drawings/build"


@pytest.mark.parametrize("title,code", [
    ("MẶT BẰNG MÓNG - ĐÀ KIỀNG", "BV04"), ("MÓNG M1", "BV05"), ("MẶT BẰNG ĐỊNH VỊ CỘT TẦNG 1", "BV06"),
    ("MẶT BẰNG ĐÒNH VÒ CỔ CỘT. TL 1/50", "BV06"), ("CHI TIẾT CỘT ĐIỂN HÌNH", "BV07"), ("MẶT BẰNG DẦM SÀN LẦU 1", "BV08"),
    ("DẦM D7a", "BV09"), ("ĐÀ KIỀNG ĐK2 300X500", "BV09"), ("MẶT BẰNG SÀN MÁI", "BV10"), ("CHI TIẾT THÉP SÀN", "BV11"),
    ("CẦU THANG TRỆT TL 1/20", "BV12"), ("MẶT BẰNG KẾT CẤU MÁI", "BV13"), ("CHI TIẾT LANH TÔ", "BV14"),
    ("MẶT ĐỨNG CHÍNH", "BV02"), ("MẶT CẮT A-A", "BV03"), ("MẶT BẰNG TẦNG 1", "BV01"),
])
def test_sheet_types(title, code):
    assert sheet_type_of(title).ma == code


def test_sheet_types_not_titles():
    assert sheet_type_of("MẶT BẰNG ĐIỆN TẦNG 1") is None          # điện nước không phải bản vẽ phần thô
    assert sheet_type_of("4. ĐÀ SÀN") is None and sheet_type_of("MC 1-1") is None


def test_element_labels_and_floor_count():
    assert element_of("ĐK1")[0] == "BEAM" and element_of("D7a")[0] == "BEAM" and element_of("Dct")[0] == "BEAM"
    assert element_of("M2")[0] == "FOUNDATION" and element_of("C5")[0] == "COLUMN"
    assert element_of("D") is None and element_of("TL1/20") is None
    assert floor_count("MẶT BẰNG DẦM SÀN LẦU 1") == 1
    assert floor_count("MẶT BẰNG DẦM SÀN LẦU 2-3-4-SÂN THƯỢNG") == 4
    assert floor_count("MẶT BẰNG SÀN LẦU 2-LẦU 5") == 4


def _t(text, x, y, h=300):
    return TextItem(text, x, y, "TEXT", "unicode", h)


def _beam_plan() -> Drawing:
    """Mặt bằng dầm giả: dầm ngang dài 8 m rộng 200 (hai ký hiệu D1, D2), đà kiềng ghi tiết diện ở hình chi tiết,
    mặt bằng móng có 3 móng M1 và 1 móng M2."""
    segs = [Segment(0, 0, 8000, 0, "DAM"), Segment(0, 200, 8000, 200, "DAM"),
            Segment(0, -20000, 6000, -20000, "DAM"), Segment(0, -19700, 6000, -19700, "DAM")]
    texts = [_t("MẶT BẰNG DẦM SÀN LẦU 2-3-4", 4000, -2000, 600), _t("D1", 2000, 400), _t("D2", 6000, 400),
             _t("MẶT BẰNG MÓNG", 3000, -22000, 600), _t("ĐK2", 3000, -19500),
             _t("M1", 500, -19000), _t("M1", 3000, -19000), _t("M1", 5500, -19000), _t("M2", 5500, -18500),
             _t("ĐÀ KIỀNG ĐK2 300X500", 30000, -22000, 500)]
    return Drawing(segments=segs, texts=texts, blocks=[], hatches=[], layers=["DAM"], layer_classes={}, unit_scale=1.0,
                   warnings=[])


def test_strip_footing_uses_explicit_length_and_leaves_section_pending():
    d = _beam_plan()
    d.texts.append(_t("lanh tô", 90000, 0, 1914))
    d.texts.extend([_t("BM-5", 1000, -19000), _t("MẶT CẮT MÓNG BĂNG BM-5", 31000, -32000),
                    _t("bm-5: l=12590mm; sl=01", 31000, -32100)])
    def footing():
        return next(f for f in read_structural(d).foundations if f.name == "BM-5")
    f = footing()
    assert (f.kind, f.count, f.gross_length_mm, f.length_mm, f.width_mm, f.height_mm) == ("bang", 1, 12590, None, None, None)
    d.texts.append(_t("bm-5: l=11000mm; sl=01", 31000, -32200))
    assert footing().gross_length_mm is None
    d.texts = [t for t in d.texts if t.text not in ("BM-5", "bm-5: l=11000mm; sl=01")]
    f = footing()
    assert not f.positions and f.gross_length_mm == 12590 and f.length_mm is None


def test_read_structural_beams_and_foundations():
    st = read_structural(_beam_plan())
    beams = st.beams["MẶT BẰNG DẦM SÀN LẦU 2-3-4"]
    assert [(b.id, round(b.length_mm), b.b_mm, b.d_mm) for b in beams] == [("D1", 4000, 200, None), ("D2", 4000, 200, None)]
    (dk,) = st.beams["MẶT BẰNG MÓNG"]
    assert (dk.id, round(dk.length_mm), dk.b_mm, dk.d_mm) == ("ĐK2", 6000, 300, 500)     # tiết diện ghi bằng chữ thắng
    assert [(f.name, f.count) for f in st.foundations] == [("M1", 3), ("M2", 1)]
    assert any("chưa có cao dầm D1, D2" in w for w in st.warnings)
    have = {s["ma"] for s in st.sheets if s["co"]}
    assert have == {"BV04", "BV08", "BV09"} and len(st.sheets) == len(load_sheet_types())


def test_structural_scale_and_rough_bill():
    st = read_structural(_beam_plan(), scale=0.5)
    assert round(st.beams["MẶT BẰNG DẦM SÀN LẦU 2-3-4"][0].length_mm) == 2000
    req = rough_from_drawing(_beam_plan(), ProjectParams(slab_thickness_mm=100, beam_depth_mm=400))
    assert req.structural_floors["MẶT BẰNG DẦM SÀN LẦU 2-3-4"] == 3
    assert [(f.name, f.count) for f in req.params.foundations] == [("M1", 3), ("M2", 1)]
    res = compute_rough(RoughRequest(**req.model_dump()), Catalog.from_csv(None))
    dam = [w for w in res.works if w.code == "DAM"]
    # dầm sàn: 3 tầng × 8 m × 0,2 × (0,4 − 0,1); đà kiềng không có sàn bên trên: 6 m × 0,3 × 0,5
    assert sum(w.quantity for w in dam) == pytest.approx(3 * 8 * 0.2 * 0.3 + 6 * 0.3 * 0.5, abs=1e-3)
    assert next(t for t in res.totals if t.code == "MONG").quantity is None      # kích thước móng chưa có: để trống
    assert any(w.startswith("Chưa có loại bản vẽ") for w in res.warnings)


def _with_details() -> tuple[Drawing, list[Dim]]:
    """Thêm chi tiết móng M1 (TL 1/20: nét gấp 5) và mặt cắt dầm D1; mặt bằng dầm vẽ gấp 2 (số hiển thị = nửa số đo)."""
    d = _beam_plan()
    d.segments += [Segment(48000, -21000, 52000, -21000, "0"), Segment(52000, -21000, 52000, -17000, "0"),
                   Segment(52000, -17000, 48000, -17000, "0"), Segment(48000, -17000, 48000, -21000, "0")]
    d.texts += [_t("MÓNG M1", 50000, -22000, 600), _t("MC 1-1", 50000, -35000), _t("DẦM D1", 80000, -22000, 600),
                _t("MC 2-2", 80000, -30000)]
    dims = [Dim(4000, -1000, 4000, 8000, False),                                        # mặt bằng dầm: tỷ lệ 0,5
            Dim(50000, -21300, 1350, 6750, False), Dim(47500, -19000, 1700, 8500, True),  # mặt bằng móng M1
            Dim(48000, -30000, 700, 3500, True), Dim(48500, -33000, 100, 500, True), Dim(48600, -33500, 50, 250, True),
            Dim(80000, -29000, 220, 1100, False), Dim(79000, -27000, 400, 2000, True), Dim(79500, -25000, 100, 500, True)]
    return d, dims


def test_read_details_footing_and_beam_section():
    d, dims = _with_details()
    st = read_structural(d, dims=dims)
    (d1, d2) = st.beams["MẶT BẰNG DẦM SÀN LẦU 2-3-4"]
    assert (d1.id, round(d1.length_mm), d1.b_mm, d1.d_mm) == ("D1", 2000, 220, 400)    # tỷ lệ 0,5 tự suy; mặt cắt MC 2-2
    assert d2.d_mm is None                                                              # D2 không có mặt cắt: để trống
    m1 = next(f for f in st.foundations if f.name == "M1")
    assert (m1.count, m1.length_mm, m1.width_mm, m1.height_mm, m1.lean_thickness_mm) == (3, 1350, 1700, 700, 100)
    m2 = next(f for f in st.foundations if f.name == "M2")
    assert m2.length_mm is None and any("M2" in w and "không có chi tiết móng" in w for w in st.warnings)


def test_rough_bill_uses_detail_sizes():
    d, dims = _with_details()
    st = read_structural(d, dims=dims)
    req = RoughRequest(plans=[], params=ProjectParams(slab_thickness_mm=100, foundations=st.foundations),
                       structural_beams=st.beams)
    res = compute_rough(req, Catalog.from_csv(None))
    mong = next(w for w in res.works if w.code == "MONG" and "M1" in w.element)
    assert mong.quantity == pytest.approx(3 * 1.35 * 1.7 * 0.7, abs=1e-3)
    lot = next(w for w in res.works if w.code == "BE_TONG_LOT" and "M1" in w.element)
    assert lot.quantity == pytest.approx(3 * 1.35 * 1.7 * 0.1, abs=1e-3)


def test_dimension_text_parsing():
    assert _number("1350") == 1350 and _number(r"{\fSymbol|b0;f}6a200") is None and _number("2x100") is None
    assert view_scale([Dim(0, 0, 4000, 8000, False), Dim(0, 0, 2700, 5400, False)]) == 0.5


def test_ket_cau_build_drawing():
    path = BUILD / "ket_cau.dxf"
    if not path.exists():
        pytest.skip("không có ket_cau.dxf")
    d = read_drawing(str(path))
    have = {s["ma"] for s in sheet_inventory(find_views(d, bbox_for=())) if s["co"]}
    assert {"BV04", "BV05", "BV06", "BV07", "BV08", "BV09", "BV10", "BV12"} <= have
    st = read_structural(d)
    # đếm trên bản vẽ 21/10/2026: mặt bằng móng có 4 M1, 6 M2, 2 M3, 2 M4
    assert [(f.name, f.count) for f in st.foundations] == [("M1", 4), ("M2", 6), ("M3", 2), ("M4", 2)]
    assert "MẶT BẰNG DẦM MÁI" in st.beams and "MẶT BẰNG ĐÀ KIỀNG" in st.beams
    # đọc từ chi tiết 21/10/2026: mặt bằng vẽ TL 1/50 (tỷ lệ 0,5 tự suy), dầm rộng 200; D1 200×350 (MC 3-3…7-7)
    sizes = {f.name: (f.length_mm, f.width_mm, f.height_mm, f.lean_thickness_mm) for f in st.foundations}
    assert sizes["M1"] == (1350, 1700, 700, 100) and sizes["M2"] == (1300, 1700, 700, 100)
    d1 = [b for b in st.beams["MẶT BẰNG DẦM SÀN LẦU 1"] if b.id == "D1"]
    assert d1 and all((b.b_mm, b.d_mm) == (200, 350) for b in d1)


def test_unlabeled_beam_pairs_same_width():
    # bộ 46: ký hiệu ghi một lần cho mỗi loại dầm; cặp nét cùng bề rộng không ký hiệu vẫn là dầm (vẽ phóng to 2 lần)
    from optimat.rough.structural import _unlabeled_beams
    lines = [("h", 0, 0, 8000), ("h", 400, 0, 8000),                      # dầm có ký hiệu, rộng 400 trên bản vẽ
             ("v", 1000, 400, 7600), ("v", 1400, 400, 7600),              # dầm ngang không ký hiệu
             ("v", 5000, 400, 1000), ("v", 5400, 400, 1000),              # cạnh cột 600 = 300 mm: bỏ
             ("v", 7000, 400, 7600), ("v", 7600, 400, 7600)]              # rộng 600 khác bề rộng dầm: bỏ
    labeled = [(0, "h", 200, 0, 8000, 400, ("h", 200, 0, 8000))]
    beams = _unlabeled_beams(lines, labeled, 0.5)
    assert [(b.id, b.b_mm, b.x1, b.y1, b.x2, b.y2) for b in beams] == [("D?", 200, 600, 200, 600, 3800)]


def test_scale_picked_by_beam_width_when_view_mixes_scales():
    # dầm mái bộ 46: khung có hình chi tiết 1:20 (nhiều kích thước) cạnh mặt bằng 1:50 vẽ phóng to 2 lần
    from optimat.drawing.sheets import View
    from optimat.rough.structural import _scale_by_beam_width
    segs = [Segment(0, 0, 8000, 0, "D"), Segment(0, 400, 8000, 400, "D")]
    d = Drawing(segs, [TextItem("DM1", 4000, 600, "0", "unicode", 250)], [], [], [], {}, 1.0, [])
    view = View(title="MẶT BẰNG DẦM MÁI", ma="BV08", ten="Mặt bằng dầm", nhom="", x=4000, y=-2000, bbox=(-1000, -1000, 9000, 3000))
    dims = [Dim(x=1, y=1, value=200, measured=1000, vertical=False)] * 5 + [Dim(x=1, y=1, value=500, measured=1000, vertical=False)] * 2
    assert _scale_by_beam_width(d, view, dims, {"dk1": (200, 300)}) == 0.5
    assert _scale_by_beam_width(d, view, dims[:5], {"dk1": (200, 300)}) is None       # một tỷ lệ: theo trung vị


def _schedule_drawing():
    # bảng THỐNG KÊ CỘT kiểu bộ 46: hàng mã cột + SL, mỗi hàng một đoạn cao độ, ô có đường kích thước mặt cắt
    t = lambda s, x, y: TextItem(s, x, y, "0", "unicode", 250)
    texts = [t("THỐNG KÊ CỘT", 0, 0), t("C1", -7000, 600), t("SL: 02", -5000, 600), t("C2", 0, 600), t("SL: 06", 2000, 600),
             t("Từ+0.050", -14000, 4300), t("Đến +3.650", -14000, 3700),
             t("Từ+3.650", -14000, 9300), t("Đến +6.950", -14000, 8700)]
    dims = [Dim(-7000, 4000, 200, 2000, False), Dim(-6000, 4000, 300, 3000, True), Dim(-7000, 4100, 50, 500, False),
            Dim(0, 4000, 300, 3000, False), Dim(1000, 4000, 250, 2500, True),
            Dim(-7000, 9000, 200, 2000, False), Dim(-6000, 9000, 250, 2500, True)]       # C2 đoạn trên: không có hình
    return Drawing([], texts, [], [], [], {}, 1.0, []), dims


def test_column_schedule_reads_grid():
    from optimat.rough.structural import read_column_schedule
    d, dims = _schedule_drawing()
    spans, warnings = read_column_schedule(d, dims)
    got = {(s.code, s.count, s.z_from_mm, s.z_to_mm, s.b_mm, s.h_mm) for s in spans}
    assert got == {("C1", 2, 50, 3650, 200, 300), ("C2", 6, 50, 3650, 300, 250), ("C1", 2, 3650, 6950, 200, 250)}
    assert any("C2" in w and "tiết diện" in w for w in warnings)                  # ô trống không đoán


def test_column_schedule_without_mapping_keeps_local_column_pending():
    from optimat.rough.structural import ColumnSpan
    from optimat.rough.columns import Column
    from optimat.drawing.review import ReviewWall
    from optimat.rough.takeoff import PlanInput
    walls = [ReviewWall(id="A", cls="220", role="envelope", x1=0, y1=0, x2=6000, y2=0, mat="GN01")]
    plan = PlanInput(name="Tầng 2", height_mm=3300, walls=walls, columns=[Column(id="K1", x=0, y=0, b_mm=220, h_mm=220)])
    span = ColumnSpan(code="C1", count=4, z_from_mm=0, z_to_mm=3300, b_mm=200, h_mm=300)
    res = compute_rough(RoughRequest(params=ProjectParams(slab_thickness_mm=100), plans=[plan], column_schedule=[span]),
                        Catalog.from_csv(None))
    cot = [w for w in res.works if w.code == "COT"]
    assert len(cot) == 2
    scheduled = next(w for w in cot if w.plan == "bảng thống kê cột")
    assert scheduled.quantity == pytest.approx(4 * 0.2 * 0.3 * 3.3)
    local = next(w for w in cot if w.plan == "Tầng 2")
    assert local.quantity is None and local.missing and local.status == "D"
    assert not next(t for t in res.totals if t.code == "COT").complete
