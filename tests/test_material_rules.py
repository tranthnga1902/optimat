"""Kiểm thử bóc tách bằng quy tắc (ghi chú, hatch, layer, block -> vật liệu)."""
from pathlib import Path

import ezdxf
import pytest

from optimat.drawing.evaluate import evaluate, survey
from optimat.drawing.material_rules import CONFIDENCE, load_rules
from optimat.drawing.takeoff import takeoff_from_file

ROOT = Path(__file__).resolve().parents[1]


def _box_wall(msp, x0, y0, length, thick, layer="TUONG"):
    msp.add_line((x0, y0), (x0 + length, y0), dxfattribs={"layer": layer})
    msp.add_line((x0, y0 + thick), (x0 + length, y0 + thick), dxfattribs={"layer": layer})


def _make(tmp_path, build) -> str:
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    doc.layers.add("TUONG")
    doc.layers.add("GHICHU")
    build(doc, doc.modelspace())
    path = tmp_path / "t.dxf"
    doc.saveas(path)
    return str(path)


def test_rules_file_valid():
    rules = load_rules()
    assert len({r.rule_id for r in rules}) == len(rules) >= 20
    assert [r.priority for r in rules] == sorted((r.priority for r in rules), reverse=True)


def test_sample_design_materials(sample_dxf):
    """Ghi chú có số chiều dày quyết định vật liệu của mọi tường cùng chiều dày."""
    result = takeoff_from_file(sample_dxf, 3300)
    groups = {g.wall_type: g for g in result.groups}
    assert (groups["220"].design_material_id, groups["220"].design_wall_system_id) == ("GN01", "W-GN01-220")
    assert (groups["110"].design_material_id, groups["110"].design_wall_system_id) == ("AAC01", "W-AAC01-100")
    assert groups["220"].design_material_share == pytest.approx(1.0)
    assert all(w.material_source == "text" for w in result.walls)
    assert result.rule_hits == {"A-GN01-4": 4, "T02": 1}       # "gạch đặc" là tên gọi khác của GN01 trong danh mục
    assert result.unmatched == {}


def test_hatch_assigns_material(tmp_path):
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        h = msp.add_hatch(dxfattribs={"layer": "0"})
        h.set_pattern_fill("AR-B816")
        h.paths.add_polyline_path([(0, 0), (4000, 0), (4000, 220), (0, 220)], is_closed=True)
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    w = result.walls[0]
    assert (w.material_family, w.material_id, w.wall_system_id) == ("CMU_HOLLOW", "GK02", "W-GK02-190")
    assert result.walls[0].material_source == "hatch" and result.walls[0].material_rule == "H03"


def test_loose_hatch_still_assigns_material(tmp_path):
    """Hatch ANSI31 bị phá thành nét rời thẳng ra model (không trong block, như bản vẽ xuất qua phần mềm xem nhanh):
    trước đây mất tên mẫu nên quy tắc H01 không khớp được, tường không có vật liệu. Nay dựng lại một HatchItem
    "ANSI31" (synthetic) từ các nét rời, quy tắc H01 khớp và tường được xác nhận là khối xây."""
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        # nét xiên cùng phương, cách đều 40 mm phủ suốt chiều dài tường: mô phỏng hatch ANSI31 bị explode
        for off in range(0, 4000, 40):
            msp.add_line((off, 0), (off + 220, 220), dxfattribs={"layer": "0"})
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    w = result.walls[0]
    assert w.material_source == "hatch_doan" and w.material_rule == "H01"
    assert w.material_confidence < CONFIDENCE["hatch"]           # đoán: tin cậy thấp hơn hatch đọc được thẳng
    assert w.is_masonry is True and w.material_id is None        # H01 chỉ xác nhận khối xây, không cho biết loại gạch
    assert result.rule_hits == {"H01": 1} and "hatch" not in result.unmatched


def test_exploded_hatch_in_block_matches_material_rule(tmp_path):
    """Hatch AR-B816 bị phá nằm trong block (bản vẽ xuất qua phần mềm xem nhanh): tên mẫu đã mất, chỉ còn nét rời.
    Dựng lại HatchItem đoán ANSI31 -> H01 (khối xây chung). Ghi chú có vật liệu vẫn thắng vì có target."""
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        blk = doc.blocks.new("HATCH_PHA")
        for off in range(0, 4000, 40):
            blk.add_line((off, 0), (off + 220, 220), dxfattribs={"layer": "0"})
        msp.add_blockref("HATCH_PHA", (0, 0))
        msp.add_text("Tường 220 xây gạch đặc", dxfattribs={"layer": "GHICHU"}).set_placement((90000, 90000))
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    w = result.walls[0]
    assert (w.material_id, w.material_source) == ("GN01", "text")
    assert "hatch" not in result.unmatched


def test_concrete_excluded(tmp_path):
    """Cặp nét có hatch bê tông là vách hoặc cột, không tính vào khối lượng xây."""
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        _box_wall(msp, 0, 3000, 4000, 220)
        h = msp.add_hatch(dxfattribs={"layer": "0"})
        h.set_pattern_fill("AR-CONC")
        h.paths.add_polyline_path([(0, 3000), (4000, 3000), (4000, 3220), (0, 3220)], is_closed=True)
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    assert len(result.walls) == 2 and sum(not w.is_masonry for w in result.walls) == 1
    assert result.groups[0].length_m == pytest.approx(4.0, abs=0.01)


def test_layer_rule_and_priority(tmp_path):
    """Layer gợi ý AAC nhưng ghi chú có chiều dày nói gạch đặc: ghi chú thắng vì ưu tiên cao hơn."""
    def build(doc, msp):
        doc.layers.add("TUONG_AAC")
        _box_wall(msp, 0, 0, 4000, 220, layer="TUONG_AAC")
        _box_wall(msp, 0, 3000, 4000, 110, layer="TUONG_AAC")
        msp.add_text("Tường 220 xây gạch đặc", dxfattribs={"layer": "GHICHU"}).set_placement((90000, 90000))
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    by = {w.thickness_class: w for w in result.walls}
    assert (by["220"].material_id, by["220"].material_source) == ("GN01", "text")
    assert (by["110"].material_id, by["110"].wall_system_id, by["110"].material_source) == ("AAC01", "W-AAC01-100", "layer")


def test_text_without_thickness_only_nearby(tmp_path):
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        _box_wall(msp, 0, 20000, 4000, 220)
        msp.add_text("xây gạch block", dxfattribs={"layer": "GHICHU"}).set_placement((2000, 500))
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    near = [w for w in result.walls if w.material_family == "CMU_HOLLOW|CMU_SOLID"]
    assert len(near) == 1 and max(near[0].y1, near[0].y2) < 1000
    # nhóm tách theo vật liệu: một nửa chiều dài có vật liệu, nửa kia thành nhóm chưa rõ vật liệu
    known = [g for g in result.groups if g.design_material_id]
    assert len(result.groups) == 2 and len(known) == 1 and known[0].design_material_share == pytest.approx(1.0)
    assert known[0].length_m == pytest.approx(sum(g.length_m for g in result.groups) / 2, rel=0.01)


def test_unmatched_signals_reported_not_guessed(tmp_path):
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        msp.add_text("Tường xây gạch ba banh", dxfattribs={"layer": "GHICHU"}).set_placement((100, 500))
        h = msp.add_hatch(dxfattribs={"layer": "0"})
        h.set_pattern_fill("HONEY")
        h.paths.add_polyline_path([(0, 0), (4000, 0), (4000, 220), (0, 220)], is_closed=True)
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    assert result.walls[0].material_id is None and result.walls[0].material_family is None
    assert result.groups[0].design_material_id is None
    assert result.unmatched["hatch"] == ["HONEY"]
    assert result.unmatched["text"] == ["Tường xây gạch ba banh"]


def test_evaluate_and_survey(sample_dxf):
    detail, summary = evaluate()
    assert len(detail) == 2 and bool(detail.material_ok.all())
    assert "test" not in set(summary.split)          # chưa có bản vẽ kiểm tra: không được báo số cho nhóm test
    tables = survey([sample_dxf])
    assert set(tables) >= {"layers", "hatches", "blocks", "texts"}
    assert "ANSI31" in set(tables["hatches"].gia_tri)


def test_rule_targets_exist_in_catalog():
    """Mọi họ, mã vật liệu trong bộ quy tắc phải có trong danh mục, nếu không bóc tách ra mã không tra được giá."""
    from optimat.catalog.repository import Catalog
    cat = Catalog.load()
    known = set(cat.wall_families()) | set(cat.materials.material_id)
    assert {t for r in load_rules() for t in r.target} <= known


def test_ambiguous_family_left_for_user(tmp_path):
    """"Gạch block" có hai phương án tường 220 trong danh mục (GK01, GK02): không chọn thay người dùng."""
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        msp.add_text("xây gạch block", dxfattribs={"layer": "GHICHU"}).set_placement((2000, 500))
    w = takeoff_from_file(_make(tmp_path, build), 3300).walls[0]
    assert w.material_id is None and w.wall_system_id is None
    assert w.material_candidates == ["W-GK01-220", "W-GK02-190"]


def test_alias_falls_back_to_family_thickness(tmp_path):
    """"Gạch siêu nhẹ" là tên gọi của AAC01 (dày 100) nhưng ghi cho tường 220: phương án đúng là AAC03."""
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        msp.add_text("Tường 220 xây gạch siêu nhẹ", dxfattribs={"layer": "GHICHU"}).set_placement((2000, 500))
    w = takeoff_from_file(_make(tmp_path, build), 3300).walls[0]
    assert (w.material_id, w.wall_system_id) == ("AAC03", "W-AAC03-200")


def test_bill_of_materials_prices_by_catalog_code(sample_dxf, sample_openings):
    """Mã vật liệu nhận diện được tra thẳng ra giá trong danh mục; thiếu số liệu thì để trống và báo."""
    from optimat.catalog.pricing import bill_of_materials
    from optimat.catalog.repository import Catalog
    groups = takeoff_from_file(sample_dxf, 3300, openings=sample_openings).groups
    catalog = Catalog.load()
    # Fixture giá mẫu xác nhận đơn vị danh mục; mã thật không được suy khi sale_unit thiếu.
    catalog.supplier_materials["sale_unit"] = catalog.supplier_materials.material_id.map(catalog.materials.set_index("material_id").unit)
    bill = {(b.wall_type, b.kind): b for b in bill_of_materials(groups, catalog)}
    brick = bill[("220", "main")]
    assert (brick.material_id, brick.unit) == ("GN01", "viên")
    assert brick.quantity == pytest.approx(105.64 * 121.0, rel=1e-3)        # hao hụt chưa có nguồn: không cộng
    assert brick.best_price == 1350 and {o.supplier_id for o in brick.offers} == {"SUP_A", "SUP_B", "SUP_C"}
    assert brick.waste_included and "hao hụt thi công (%)" not in brick.missing
    mortar = bill[("220", "mortar")]
    assert mortar.material_id == "VU02" and mortar.quantity == pytest.approx(105.64 * 0.29 * 0.22, rel=1e-3)
    assert mortar.best_price is None and "giá" in mortar.missing


def test_text_rules_match_whole_words():
    # Sprint 1, câu 10: quy tắc chữ / layer so nguyên từ, không so chuỗi con
    from optimat.drawing.material_rules import _best, load_rules
    rules = load_rules()
    assert _best(rules, "text", "tuong xay gach dat nung 220").rule_id == "T09"
    assert _best(rules, "text", "dung gach be tong khi chung ap").target == ("AAC",)
    assert _best(rules, "text", "kaac bao") is None             # "aac" nằm giữa từ khác: không khớp


def test_abbreviation_expanded_before_matching(tmp_path):
    """Viết tắt trên bản vẽ (data/rules/viet_tat.csv): "gạch kg nung" -> "gach khong nung" khớp T07; "gach bt" -> T04."""
    from optimat.drawing.encoding import expand_abbreviations, load_abbreviations
    abbr = load_abbreviations()
    assert abbr and abbr == sorted(abbr, key=lambda x: -len(x[0]))            # mẫu dài xét trước
    assert expand_abbreviations("tuong 220 xay gach kg nung") == "tuong 220 xay gach khong nung"
    assert expand_abbreviations("san btct day 120") == "san be tong cot thep day 120"
    assert expand_abbreviations("xay gach bt") == "xay gach be tong"            # "gach bt" (VT08) thắng "bt" (VT01)
    assert expand_abbreviations("bt1 vua xm") == "bt1 vua xi mang"              # so nguyên từ: "bt1" giữ nguyên

    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        msp.add_text("Tường 220 xây gạch kg nung", dxfattribs={"layer": "GHICHU"}).set_placement((90000, 90000))
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    assert result.walls[0].material_rule == "T07" and result.unmatched == {}


def test_multiline_note_grouped(tmp_path):
    """Ghi chú xếp hai dòng TEXT: "TƯỜNG 220 XÂY" / "GẠCH BÊ TÔNG KHÍ". Từng dòng không khớp quy tắc có vật liệu,
    đoạn ghép khớp T01 và có số 220 -> áp cho tường 220."""
    def build(doc, msp):
        _box_wall(msp, 0, 0, 4000, 220)
        msp.add_text("TƯỜNG 220 XÂY", dxfattribs={"layer": "GHICHU", "height": 150}).set_placement((90000, 90000))
        msp.add_text("GẠCH BÊ TÔNG KHÍ", dxfattribs={"layer": "GHICHU", "height": 150}).set_placement((90000, 89750))
    result = takeoff_from_file(_make(tmp_path, build), 3300)
    w = result.walls[0]
    assert (w.material_rule, w.material_source, w.material_id) == ("T01", "text", "AAC03")
    assert result.unmatched == {}                      # dòng lẻ "TƯỜNG 220 XÂY" không bị báo chưa có quy tắc nữa


def test_text_blocks_do_not_merge_distant_or_different_size():
    from optimat.drawing.dxf_reader import TextItem
    from optimat.drawing.text_blocks import group_text_lines
    T = lambda s, x, y, h=150: TextItem(s, x, y, "GHICHU", "unicode", h)
    assert [b.text for b in group_text_lines([T("a", 0, 1000), T("b", 0, 750), T("c", 0, 500)])] == ["a b c"]
    assert group_text_lines([T("a", 0, 1000), T("b", 0, 0)]) == []                  # cách quá xa
    assert group_text_lines([T("a", 0, 1000), T("b", 0, 750, h=300)]) == []         # khác cỡ chữ
    assert group_text_lines([T("a", 0, 1000), T("b", 2000, 750)]) == []             # không cùng mép trái
    assert group_text_lines([T("a", 0, 1000, h=0), T("b", 0, 750, h=0)]) == []      # không có cỡ chữ: không ghép


def test_all_rules_cached_per_catalog():
    """all_rules(catalog) chỉ tính một lần cho mỗi danh mục; đổi danh mục hoặc clear_rule_cache thì tính lại."""
    from optimat.catalog.repository import Catalog
    from optimat.drawing import material_rules as mr
    mr.clear_rule_cache()
    cat = Catalog.load()
    calls = []
    orig = mr.alias_rules
    mr.alias_rules = lambda c: calls.append(1) or orig(c)
    try:
        a = mr.all_rules(cat)
        assert mr.all_rules(cat) is a and len(calls) == 1
        assert mr.all_rules(Catalog.load()) is not a and len(calls) == 2        # danh mục khác
        mr.clear_rule_cache()
        mr.all_rules(cat)
        assert len(calls) == 3
    finally:
        mr.alias_rules = orig
        mr.clear_rule_cache()


def test_hatch_must_cover_half_the_wall():
    # bộ 46: ô tô đặc của một cột nằm ở giữa tường dài 7,7 m không làm cả bức tường thành vách bê tông
    from types import SimpleNamespace
    from optimat.drawing.material_rules import _hatch_share
    wall = SimpleNamespace(x1=0, y1=0, x2=7700, y2=0)
    column = [[(3700, -110), (3920, -110), (3920, 110), (3700, 110)]]
    assert _hatch_share(wall, column) < 0.5
    whole = [[(-50, -110), (7750, -110), (7750, 110), (-50, 110)]]
    assert _hatch_share(wall, whole) == 1.0
    assert _hatch_share(wall, [[(9000, 0), (9100, 0), (9100, 100)]]) == 0.0      # ngoài khung, không thử điểm
