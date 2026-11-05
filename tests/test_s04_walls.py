"""S04: bộ mặt bằng quy ước tự dựng có đáp án tính tay (tường thẳng, giao góc, cửa sát góc, cửa trùng, không có cao độ).

Mỗi tường vẽ bằng hai nét mặt trên layer TUONG (QU-08), cửa là block D…/S… trên layer CUA (QU-14).
Đáp án đo theo trục tim (góc L kéo tới giao trục tim, tường ngăn tới mặt tường bao); "thong_thuy" trừ phần nằm
trong tường giao ở mỗi đầu. Sai số cho phép chốt trước khi chạy: 0,5% chiều dài và diện tích mỗi nhóm tường.
"""
import ezdxf
import pytest

from optimat.drawing.review import ReviewOpening, ReviewPlan, ReviewWall, compute_review
from optimat.drawing.takeoff import takeoff_from_file
from optimat.schemas import OpeningDefaults

TOL = 0.005
OPEN = OpeningDefaults(door_width_mm=900, door_height_mm=2200, window_width_mm=1200, window_height_mm=1400)


def _wall(msp, x1, y1, x2, y2, t, gaps=()):
    """Hai nét mặt song song trục tim (x1, y1)–(x2, y2), cách nhau t; gaps: các khoảng (từ, tới) dọc trục bị ngắt."""
    import math
    L = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy * t / 2, ux * t / 2
    cuts = [0.0] + [v for g in gaps for v in g] + [L]
    for a, b in zip(cuts[::2], cuts[1::2]):
        for s in (1, -1):
            msp.add_line((x1 + ux * a + s * nx, y1 + uy * a + s * ny), (x1 + ux * b + s * nx, y1 + uy * b + s * ny),
                         dxfattribs={"layer": "TUONG"})


def _doc():
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    for name in ("TUONG", "CUA"):
        doc.layers.add(name)
    for name in ("D1", "S1"):
        doc.blocks.new(name).add_line((0, 0), (900, 0))
    return doc


def _box(msp, W, L, T):
    """Nhà chữ nhật phủ bì W x L, tường bao dày T: tim = 2(W - T) + 2(L - T)."""
    msp.add_lwpolyline([(0, 0), (W, 0), (W, L), (0, L)], close=True, dxfattribs={"layer": "TUONG"})
    msp.add_lwpolyline([(T, T), (W - T, T), (W - T, L - T), (T, L - T)], close=True, dxfattribs={"layer": "TUONG"})


def _save(doc, tmp_path, name):
    path = tmp_path / f"{name}.dxf"
    doc.saveas(path)
    return str(path)


def _groups(result):
    return {g.wall_type: g for g in result.groups}


def _close(got, want):
    assert got == pytest.approx(want, rel=TOL, abs=0.01)


def test_straight_wall(tmp_path):
    doc = _doc()
    _wall(doc.modelspace(), 0, 0, 6000, 0, 220)
    r = takeoff_from_file(_save(doc, tmp_path, "thang"), 3000)
    g = _groups(r)["220"]
    _close(g.length_m, 6.0)
    _close(g.gross_area_m2, 18.0)
    assert g.opening_area_m2 == 0
    # không giao tường nào: thông thủy bằng tim
    _close(_groups(takeoff_from_file(_save(doc, tmp_path, "thang"), 3000, length_rule="thong_thuy"))["220"].length_m, 6.0)


def test_l_corner_centerline_and_net(tmp_path):
    doc = _doc()
    msp = doc.modelspace()
    # tường ngang trục y=110 từ x=0 tới 5000, tường đứng trục x=110 từ y=220 tới 4000: góc L
    _wall(msp, 0, 110, 5000, 110, 220)
    _wall(msp, 110, 220, 110, 4000, 220)
    path = _save(doc, tmp_path, "goc")
    tim = _groups(takeoff_from_file(path, 3000))["220"]
    _close(tim.length_m, (5000 - 110) / 1000 + (4000 - 110) / 1000)       # cả hai kéo tới giao trục tim (110, 110)
    net = _groups(takeoff_from_file(path, 3000, length_rule="thong_thuy"))["220"]
    _close(net.length_m, tim.length_m - 2 * 0.110)                          # mỗi tường bớt nửa dày tường kia ở góc


def test_house_with_partition_and_corner_door(tmp_path):
    """Nhà 5 x 12 m, tường bao 220, tường ngăn 110 chữ T; cửa đi sát góc dưới trái, cửa sổ giữa tường phải."""
    doc = _doc()
    msp = doc.modelspace()
    _box(msp, 5000, 12000, 220)
    _wall(msp, 220, 6055, 4780, 6055, 110)
    msp.add_blockref("D1", (600, 110), dxfattribs={"layer": "CUA"})       # mép cửa cách mặt trong tường trái 380 mm
    msp.add_blockref("S1", (4890, 9000), dxfattribs={"layer": "CUA"})
    r = takeoff_from_file(_save(doc, tmp_path, "nha"), 3300, openings=OPEN)
    g = _groups(r)
    _close(g["220"].length_m, 2 * 4.78 + 2 * 11.78)
    _close(g["110"].length_m, 4.56)
    _close(g["220"].opening_area_m2, 0.9 * 2.2 + 1.2 * 1.4)
    _close(g["220"].net_area_m2, 33.12 * 3.3 - 3.66)
    assert g["110"].opening_area_m2 == 0
    door = next(o for o in r.openings if o.name == "D1")
    host = next(w for w in r.walls if w.wall_id == door.wall_id)
    assert abs(host.y1 - host.y2) < 1 and host.y1 == pytest.approx(110, abs=1)   # trừ vào tường ngang, không vào tường góc
    # thông thủy: tường ngăn 110 đã đo tới mặt tường bao nên giữ nguyên; tường bao bớt 4 góc x 2 x 110
    n = _groups(takeoff_from_file(_save(doc, tmp_path, "nha"), 3300, openings=OPEN, length_rule="thong_thuy"))
    _close(n["110"].length_m, 4.56)
    _close(n["220"].length_m, 33.12 - 8 * 0.110)


def test_duplicate_door_block_subtracted_once(tmp_path):
    doc = _doc()
    msp = doc.modelspace()
    _box(msp, 5000, 12000, 220)
    for _ in range(2):                                                     # chép đè cùng một block hai lần
        msp.add_blockref("D1", (2500, 110), dxfattribs={"layer": "CUA"})
    r = takeoff_from_file(_save(doc, tmp_path, "trung"), 3300, openings=OPEN)
    _close(_groups(r)["220"].opening_area_m2, 0.9 * 2.2)
    assert r.openings_count == 1
    assert any("trùng" in w for w in r.warnings)


def test_gap_door_with_arc_and_block_subtracted_once(tmp_path):
    """Cửa có cả khe tường, cung cánh cửa và block: chỉ một lỗ mở, nguồn ghi đủ dấu hiệu."""
    doc = _doc()
    msp = doc.modelspace()
    _wall(msp, 0, 0, 6000, 0, 220, gaps=[(2000, 2900)])
    msp.add_arc((2000, 110), 900, 0, 90, dxfattribs={"layer": "CUA"})
    msp.add_blockref("D1", (2450, 0), dxfattribs={"layer": "CUA"})
    r = takeoff_from_file(_save(doc, tmp_path, "khe"), 3000, openings=OPEN)
    g = _groups(r)["220"]
    _close(g.length_m, 6.0)
    _close(g.opening_area_m2, 0.9 * 2.2)
    assert r.openings_count == 1
    assert all(o.wall_id for o in r.openings) and r.openings[0].evidence


def test_gap_door_without_height_listed_not_subtracted(tmp_path):
    """Dự án chưa nhập cao cửa (B7): cửa nhận từ khe vẫn vào danh sách (rộng theo khe, cao trống), không trừ;
    trang kiểm tra nhập cao thì trừ. Lanh tô chỉ cần rộng lỗ nên vẫn tính."""
    from optimat.catalog.repository import Catalog
    from optimat.rough.models import ProjectParams
    from optimat.rough.walls import review_input_from_takeoff, wall_works
    doc = _doc()
    msp = doc.modelspace()
    _wall(msp, 0, 0, 6000, 0, 220, gaps=[(2000, 2900)])
    msp.add_arc((2000, 110), 900, 0, 90, dxfattribs={"layer": "CUA"})
    r = takeoff_from_file(_save(doc, tmp_path, "khe_khong_cao"), 3000)
    assert [(o.width_mm, o.height_mm, bool(o.wall_id)) for o in r.openings] == [(900, None, True)]
    assert r.openings_count == 0 and _groups(r)["220"].opening_area_m2 == 0
    assert any("chưa có kích thước" in w for w in r.warnings)
    walls, ops, systems = review_input_from_takeoff(r)
    params = ProjectParams(lintel_height_mm=200, lintel_bearing_mm=200, beam_depth_mm=0)
    works, warns = wall_works("T1", 3000, walls, ops, params, Catalog.load(), systems)
    lintel = next(w for w in works if w.code == "LANH_TO")
    _close(lintel.quantity, (0.9 + 0.4) * 0.22 * 0.2)
    assert next(w for w in works if w.code == "XAY").quantity is None          # B7: chưa có cao cửa -> khối xây chưa đủ căn cứ
    assert any("thiếu cao" in m for w in works if w.code == "XAY" for m in w.missing)
    ops[0].h = 2200    # người dùng nhập cao trên trang kiểm tra -> trừ lỗ
    xay = lambda ws: next(w for w in ws if w.code == "XAY").quantity
    with_hole = xay(wall_works("T1", 3000, walls, ops, params, Catalog.load(), systems)[0])
    no_hole = xay(wall_works("T1", 3000, walls, [o.model_copy(update={"keep": False}) for o in ops], params,
                             Catalog.load(), systems)[0])
    _close(no_hole - with_hole, 0.9 * 2.2 * 0.22 + (0.9 + 0.4) * 0.22 * 0.2)   # lỗ + lanh tô của lỗ đó


def test_no_height_no_area(tmp_path):
    doc = _doc()
    _box(doc.modelspace(), 5000, 12000, 220)
    r = takeoff_from_file(_save(doc, tmp_path, "khong_cao"), None, openings=OPEN)
    assert r.groups == [] and r.floor_height_mm is None and len(r.walls) == 4
    assert any("chiều cao tầng" in w for w in r.warnings)


def test_wall_150_class(tmp_path):
    doc = _doc()
    _wall(doc.modelspace(), 0, 0, 4000, 0, 150)
    _close(_groups(takeoff_from_file(_save(doc, tmp_path, "t150"), 3000))["150"].length_m, 4.0)


def test_bad_length_rule(tmp_path):
    doc = _doc()
    _wall(doc.modelspace(), 0, 0, 4000, 0, 220)
    with pytest.raises(ValueError):
        takeoff_from_file(_save(doc, tmp_path, "sai"), 3000, length_rule="phu_bi")


def test_review_opening_larger_than_wall_capped():
    plan = ReviewPlan(file="x", plan="p", height_mm=3000,
                      walls=[ReviewWall(id="W1", cls="220", x1=0, y1=0, x2=1000, y2=0)],
                      openings=[ReviewOpening(id="O1", wall="W1", w=1200, h=2200),
                                ReviewOpening(id="O2", wall="W1", w=900, h=2200)])
    r = compute_review(plan)
    g = r.groups[0]
    assert g.opening_area_m2 <= g.gross_area_m2 and g.net_area_m2 == 0
    assert any("lớn hơn diện tích tường" in w for w in r.warnings)


def test_review_net_rule():
    walls = [ReviewWall(id="A", cls="220", x1=110, y1=110, x2=5000, y2=110),
             ReviewWall(id="B", cls="220", x1=110, y1=110, x2=110, y2=4000)]
    tim = compute_review(ReviewPlan(file="x", plan="p", height_mm=3000, walls=walls)).groups[0]
    net = compute_review(ReviewPlan(file="x", plan="p", height_mm=3000, walls=walls, length_rule="thong_thuy")).groups[0]
    _close(net.length_m, tim.length_m - 0.22)


# ---------------------------------------------------------------- các trường hợp Codex review chỉ ra

def test_different_name_blocks_same_place_subtracted_once(tmp_path):
    doc = _doc()
    msp = doc.modelspace()
    _box(msp, 5000, 12000, 220)
    doc.blocks.new("CUA_DI").add_line((0, 0), (900, 0))
    msp.add_blockref("D1", (2500, 110), dxfattribs={"layer": "CUA"})
    msp.add_blockref("D1", (2580, 110), dxfattribs={"layer": "CUA"})       # chép lệch 80 mm
    msp.add_blockref("CUA_DI", (2500, 110), dxfattribs={"layer": "CUA", })
    r = takeoff_from_file(_save(doc, tmp_path, "khac_ten"), 3300, openings=OPEN)
    attached = [o for o in r.openings if o.wall_id]
    _close(_groups(r)["220"].opening_area_m2, 0.9 * 2.2)
    assert r.openings_count == len(attached) == 1 and "block D1" in attached[0].evidence


def test_corner_block_on_perpendicular_wall_not_merged_with_gap(tmp_path):
    """Khe cửa (có cung) ở tường ngang sát góc và block cửa riêng ở tường đứng sát góc: hai lỗ, trừ cả hai."""
    doc = _doc()
    msp = doc.modelspace()
    _wall(msp, 0, 110, 5000, 110, 220, gaps=[(500, 1400)])
    _wall(msp, 110, 220, 110, 4000, 220)
    msp.add_arc((500, 110), 900, 0, 90, dxfattribs={"layer": "CUA"})
    msp.add_blockref("D1", (110, 500), dxfattribs={"layer": "CUA"})
    r = takeoff_from_file(_save(doc, tmp_path, "goc_vuong"), 3000, openings=OPEN)
    _close(_groups(r)["220"].opening_area_m2, 2 * 0.9 * 2.2)
    assert r.openings_count == 2 and len({o.wall_id for o in r.openings}) == 2


def test_far_block_listed_but_not_counted(tmp_path):
    doc = _doc()
    msp = doc.modelspace()
    _wall(msp, 0, 0, 6000, 0, 220)
    msp.add_blockref("D1", (3000, 3000), dxfattribs={"layer": "CUA"})
    r = takeoff_from_file(_save(doc, tmp_path, "xa"), 3000, openings=OPEN)
    assert r.openings_count == 0 and len(r.openings) == 1 and r.openings[0].wall_id is None
    assert _groups(r)["220"].opening_area_m2 == 0


def test_net_length_oblique_45():
    from optimat.drawing.walls import net_lengths
    import math
    # tường xiên 45° dừng ở trục tim tường ngang dày 220: bớt 110 / sin 45° ≈ 155,6 mm
    n = net_lengths([("A", 0, 0, 6000, 0, 220), ("B", 1000, 0, 1000 + 3000, 3000, 220)])
    _close(n["B"] / 1000, (3000 * math.sqrt(2) - 110 * math.sqrt(2)) / 1000)


def test_groups_split_by_material():
    walls = [ReviewWall(id="A", cls="220", role="envelope", x1=0, y1=0, x2=4000, y2=0, mat="GN01"),
             ReviewWall(id="B", cls="220", role="envelope", x1=0, y1=3000, x2=4000, y2=3000, mat="AAC01")]
    r = compute_review(ReviewPlan(file="x", plan="p", height_mm=3000, walls=walls))
    assert len(r.groups) == 2 and {g.design_material_id for g in r.groups} == {"GN01", "AAC01"}
    assert all(g.design_material_share == 1.0 for g in r.groups)


@pytest.mark.parametrize("rule", ["tim", "thong_thuy"])
def test_auto_takeoff_matches_confirmed(tmp_path, rule):
    """Cùng mặt bằng: số tự động (compute_takeoff) và số chốt (compute_review) khớp với cả hai quy tắc chiều dài."""
    from optimat.rough.walls import review_input_from_takeoff
    doc = _doc()
    msp = doc.modelspace()
    _box(msp, 5000, 12000, 220)
    _wall(msp, 220, 6055, 4780, 6055, 110)
    msp.add_blockref("D1", (2500, 110), dxfattribs={"layer": "CUA"})
    msp.add_blockref("S1", (4890, 9000), dxfattribs={"layer": "CUA"})
    auto = takeoff_from_file(_save(doc, tmp_path, "khop"), 3300, openings=OPEN, length_rule=rule)
    walls, openings, _ = review_input_from_takeoff(auto)
    chot = compute_review(ReviewPlan(file="x", plan="p", height_mm=3300, walls=walls, openings=openings, length_rule=rule))
    key = lambda g: (g.wall_type, g.role, g.design_material_id or "")  # noqa: E731
    a, c = {key(g): g for g in auto.groups}, {key(g): g for g in chot.groups}
    assert set(a) == set(c)
    for k in a:
        _close(c[k].length_m, a[k].length_m)
        _close(c[k].net_area_m2, a[k].net_area_m2)
    assert chot.length_rule == rule
