"""S9: khái niệm đọc bản vẽ theo Quy ước v1.0 (data/rules/quy_uoc.csv, data/rules/concepts.csv)."""
import pytest

from optimat.drawing import concepts
from optimat.drawing.dxf_reader import Drawing, Segment, TextItem
from optimat.drawing.plans import find_plans


def test_definitions_load():
    clauses = concepts.load_clauses()
    assert [c.ma for c in clauses] == [f"QU-{i:02d}" for i in range(1, 24)]
    assert concepts.clause("QU-09").muc == "B" and concepts.clause("QU-08").muc == "K"
    assert {s.qu for s in concepts.load_signals()} <= {c.ma for c in clauses}


def test_block_signals():
    assert concepts.match_block("D1").vai_tro == "door" and concepts.match_block("cd12").vai_tro == "door"
    assert concepts.match_block("CS2").vai_tro == "window" and concepts.match_block("W").vai_tro == "window"
    assert concepts.match_block("DOOR1") is None and concepts.match_block("BAN_AN") is None
    # kích thước cửa là thông số dự án (bảng projects), quy tắc không ghi số mặc định
    assert all(s.rong_mm is None and s.cao_mm is None for s in concepts.block_signals())
    # block không phải cửa (cột, cao độ, nội thất) khớp ký hiệu nhưng không thành lỗ mở
    assert concepts.match_block_signal("COS-MB").khai_niem == "Cao độ" and concepts.match_block("COS-MB") is None
    assert concepts.match_block_signal("SOFA4150").vai_tro == "IGNORE" and concepts.match_block("SOFA4150") is None
    assert concepts.match_block("CUA_CHINH_").vai_tro == "door"


def test_layer_signals_from_build():
    role = lambda n: concepts.match_layer(n).vai_tro
    assert role("column") == role("cot") == role("4hach") == "IGNORE"
    assert role("hachtuong") == "WALL"            # ký hiệu tường đứng trước "hach"
    # layer tường của nha_pho (OK_NET_MANH, NET_THAY có cặp nét tường): không gán ký hiệu, để hình học tự nhận
    assert concepts.match_layer("ok net manh") is None and concepts.match_layer("net thay") is None


def test_bad_role_rejected(tmp_path):
    f = tmp_path / "c.csv"
    f.write_text("ma,khai_niem,qu,tin_hieu,mau,vai_tro,rong_mm,cao_mm,ghi_chu\nL01,Tường,QU-08,layer,tuong,TUONG,,,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="L01"):
        concepts.load_signals(str(f))


def _plan_box(x0, title):
    # khung một mặt bằng nhỏ: bốn nét quanh (x0..x0+8000, 0..6000) và tiêu đề ngay dưới
    segs = [Segment(x0, 0, x0 + 8000, 0, "TUONG"), Segment(x0 + 8000, 0, x0 + 8000, 6000, "TUONG"),
            Segment(x0 + 8000, 6000, x0, 6000, "TUONG"), Segment(x0, 6000, x0, 0, "TUONG")]
    return segs, TextItem(title, x0 + 4000, -800, "CHU", "unicode", height=400)


def test_duplicate_plan_titles_renamed():
    a, ta = _plan_box(0, "MẶT BẰNG TẦNG 3")
    b, tb = _plan_box(20000, "MẶT BẰNG TẦNG 3")
    d = Drawing(segments=a + b, texts=[ta, tb], blocks=[], hatches=[], layers=["TUONG", "CHU"], layer_classes={},
                unit_scale=1.0, warnings=[])
    plans = find_plans(d)
    assert [p.name for p in plans] == ["MẶT BẰNG TẦNG 3", "MẶT BẰNG TẦNG 3 (2)"]
    assert plans[1].title == "MẶT BẰNG TẦNG 3" and plans[0].title == ""


BUILD = __import__("pathlib").Path(__file__).resolve().parents[1] / "data" / "drawings" / "build"


@pytest.mark.skipif(not (BUILD / "nha_pho.dxf").exists() or not (BUILD / "ket_cau.dxf").exists(), reason="cần bản vẽ build")
def test_analyze_build_drawings():
    from optimat.drawing.concept_view import build_concept_html
    from optimat.drawing.convention_check import analyze
    r = analyze(str(BUILD / "nha_pho.dxf"))
    by = {c.ma: c for c in r.checks}
    assert len(r.checks) == 23 and r.trong_quy_uoc is False
    assert by["QU-05"].trang_thai == "vi_pham" and "(2)" in by["QU-05"].bang_chung[0]   # hai tiêu đề "tầng 3"
    assert by["QU-08"].trang_thai == "vi_pham"            # tường trên layer không theo tên: đoán bằng hình học
    assert all(w.nguon == "hinh_hoc" for p in r.plans for w in p.walls)
    assert "QU-05" in build_concept_html(r)
    k = analyze(str(BUILD / "ket_cau.dxf"))
    assert k.trong_quy_uoc is None and not k.plans        # file kết cấu: không áp dụng, không kết luận "trong quy ước"


def test_review_payload_has_conventions(sample_dxf):
    # S9.8: trang kiểm tra nhận kết quả đối chiếu quy ước cùng dữ liệu bản vẽ, tab Cảnh báo hiển thị vi phạm
    from optimat.drawing.dxf_reader import read_drawing
    from optimat.drawing.takeoff import takeoff_plans
    from optimat.drawing.viewer import build_review_html, view_payload
    d = read_drawing(sample_dxf)
    conv = view_payload(d, takeoff_plans(d, 3300), "mau.dxf", cad=False)["conventions"]
    assert "error" not in conv and len(conv["checks"]) == 23
    assert {c["trang_thai"] for c in conv["checks"]} <= {"dat", "vi_pham", "chua_kiem", "khong_ap_dung"}
    assert "function convHtml" in build_review_html()
