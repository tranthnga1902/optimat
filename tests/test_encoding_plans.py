"""Bảng mã VNI, VH và tách mặt bằng trên bản vẽ ngoài bộ build cũ (28/10/2026, bộ công trình 18 bản vẽ)."""
from optimat.drawing.dxf_reader import Drawing, Segment, TextItem
from optimat.drawing.encoding import detect_encoding, to_unicode, vh_to_unicode, vni_to_unicode
from optimat.drawing.plans import (_frame_lines, _is_plan_title, find_plans, floor_order, has_only_views,
                                   level_chain)


def _drawing(segments=(), texts=()) -> Drawing:
    return Drawing(list(segments), list(texts), [], [], [], {}, 1.0, [])


def _t(text, x=0.0, y=0.0, h=400.0):
    return TextItem(text, x, y, "0", "unicode", h)


def test_vni_windows():
    # chữ thật trên [filethietke.vn]nhà_dân.dwg
    assert vni_to_unicode("MAËT BAÈNG TREÄT + LÖÛNG") == "MẶT BẰNG TRỆT + LỬNG"
    assert vni_to_unicode("49L ÑÖÔØNG QUOÁC HÖÔNG") == "49L ĐƯỜNG QUỐC HƯƠNG"
    assert vni_to_unicode("NGUYEÃN VAÊN HAÄU") == "NGUYỄN VĂN HẬU"
    assert to_unicode("MAËT CAÉT A-A") == ("MẶT CẮT A-A", "vni")


def test_vh():
    # chữ thật trên Mau_nha_25x5.dwg (font VHArial, VHAvan)
    assert vh_to_unicode("MÀÛT BÀÒNG TÁÖNG 1 TL 1/100") == "MẶT BẰNG TẦNG 1 TL 1/100"
    assert vh_to_unicode("MÀÛT ÂÆÏNG CHÊNH") == "MẶT ĐỨNG CHÍNH"
    assert vh_to_unicode("âæåüc thäúng chiãöu VÆÎA Cæía NHIÃÛT") == "được thống chiều VỮA Cửa NHIỆT"
    assert to_unicode("TÁÖNG 2") == ("TẦNG 2", "vh")
    assert detect_encoding("VHARIAL.TTF") == "vh"


def test_short_text_uses_style_hint():
    # một mình không đủ dấu hiệu; kiểu chữ có nhiều chữ VNI thì theo kiểu chữ
    assert to_unicode("LEÂ THÒ KIM LOAN") == ("LEÂ THÒ KIM LOAN", "unicode")
    assert to_unicode("LEÂ THÒ KIM LOAN", None, "vni") == ("LÊ THỊ KIM LOAN", "vni")
    assert to_unicode("A-A", None, "vni") == ("A-A", "unicode")


def test_unicode_and_tcvn3_unchanged():
    assert to_unicode("Tường gạch 220, mặt bằng tầng 1") == ("Tường gạch 220, mặt bằng tầng 1", "unicode")
    assert to_unicode("Hoà Bình") == ("Hoà Bình", "unicode")
    assert to_unicode("T\xadêng g¹ch") == ("Tường gạch", "tcvn3")
    # font TCVN3 nhưng nội dung VNI (bản vẽ đổi font): theo nội dung
    assert to_unicode("OÁNG CAÁP NÖÔÙC TÖØ BOÀN", ".vntime.ttf") == ("ỐNG CẤP NƯỚC TỪ BỒN", "vni")


def test_san_thuong_is_floor_plan():
    assert _is_plan_title("MẶT BẰNG SÂN THƯỢNG TL 1:50")
    assert not _is_plan_title("MẶT BẰNG KẾT CẤU SÀN TẦNG 2")
    assert not _is_plan_title("MẶT BẰNG CẦU THANG")


def test_floor_order():
    assert floor_order("MẶT BẰNG TRỆT") == 0
    assert floor_order("mặt bằng tầng 1") == 0
    assert floor_order("MẶT BẰNG LẦU 3 TL 1:50") == 3
    assert floor_order("mặt bằng tầng 3 (+6.60)") == 2
    assert floor_order("MẶT BẰNG SÂN THƯỢNG") == -2
    assert floor_order("MẶT BẰNG LỬNG") is None


def test_level_chain_skips_finish_levels():
    texts = [_t(v) for v in ["±0.000", "±0.000", "+3.700", "+3.700", "+3.650", "+7.000", "+7.000", "-0.050", "-0.050"]]
    assert level_chain(_drawing(texts=texts)) == [0.0, 3.7, 7.0]
    assert level_chain(_drawing(texts=[_t("+3.700"), _t("+3.700")])) == []      # không có ±0.000


def test_long_wall_with_broken_partner_is_not_frame():
    # mặt tường dọc nhà ống dài 22 m, mặt kia bị cửa cắt thành 4 đoạn: là tường, không phải viền khung
    wall = [Segment(0, 0, 22000, 0, "T")] + [Segment(x, 200, x + 4000, 200, "T") for x in (0, 5500, 11000, 16500)]
    frame = [Segment(0, -5000, 0, 30000, "K")]
    lines = _frame_lines(_drawing(wall + frame))
    assert ("v", 0, -5000, 30000) in lines
    assert not any(k == "h" and c == 0 for k, c, *_ in lines)


def test_plan_window_not_cut_by_own_long_wall():
    # nhà 22 m × 4 m vẽ phía trên tiêu đề; trước đây khung tìm dừng ở mặt tường dưới (coi là viền khung)
    segs = []
    for y in (1000, 1200, 5000, 5200):      # hai tường dọc, mỗi tường hai mặt (mặt trong đứt ở cửa)
        if y in (1200, 5000):
            segs += [Segment(x, y, x + 5000, y, "T") for x in (0, 6000, 12000, 17000)]
        else:
            segs.append(Segment(0, y, 22000, y, "T"))
    segs += [Segment(x, 1000, x, 5200, "T") for x in (0, 22000, 11000)]
    plans = find_plans(_drawing(segs, [_t("MẶT BẰNG LẦU 1", 11000, 0)]))
    assert len(plans) == 1
    x0, y0, x1, y1 = plans[0].bbox
    assert y1 >= 5200 and x1 - x0 >= 22000


def test_views_only_file_has_no_plan():
    assert has_only_views(_drawing(texts=[_t("MẶT CẮT A-A"), _t("CHI TIẾT CẦU THANG")]))
    assert not has_only_views(_drawing(texts=[_t("MẶT BẰNG TẦNG 1"), _t("MẶT CẮT A-A")]))
    assert not has_only_views(_drawing(texts=[_t("Tường 220")]))
