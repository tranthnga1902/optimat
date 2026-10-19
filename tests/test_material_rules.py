"""Kiểm thử bóc tách bằng quy tắc (ghi chú, hatch, layer, block -> vật liệu)."""
from pathlib import Path

import ezdxf
import pytest

from optimat.drawing.evaluate import evaluate, survey
from optimat.drawing.material_rules import load_rules
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
    assert result.groups[0].design_material_share == pytest.approx(0.5)


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
    bill = {(b.wall_type, b.kind): b for b in bill_of_materials(groups, Catalog.load())}
    brick = bill[("220", "main")]
    assert (brick.material_id, brick.unit) == ("GN01", "viên")
    assert brick.quantity == pytest.approx(105.64 * 121.0, rel=1e-3)        # hao hụt chưa có nguồn: không cộng
    assert brick.best_price == 1350 and {o.supplier_id for o in brick.offers} == {"SUP_A", "SUP_B", "SUP_C"}
    assert "hao hụt thi công (%)" in brick.missing
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
