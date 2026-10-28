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
