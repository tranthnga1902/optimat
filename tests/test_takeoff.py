"""Đáp án đo tay cho data/sample/sample_floor.dxf (chiều cao tầng 3300 mm).

Tường 220 đo theo trục tim, góc chữ L kéo tới giao điểm trục tim: 2 x 4,78 + 2 x 11,78 = 33,12 m
(khớp data/ground_truth/walls.csv). Tường ngăn 110 đo tới mặt tường bao (ngã ba).
Tường 110: 4,56 m. Lỗ mở: D1 0,9 x 2,2 và S1 1,2 x 1,4 = 3,66 m2, đều nằm trên tường 220.
"""
import pytest

from optimat.drawing.encoding import normalize, tcvn3_to_unicode
from optimat.drawing.takeoff import takeoff_from_file


def test_wall_groups(sample_dxf, sample_openings):
    result = takeoff_from_file(sample_dxf, floor_height_mm=3300, openings=sample_openings)
    groups = {g.wall_type: g for g in result.groups}
    assert set(groups) == {"110", "220"}
    assert groups["220"].length_m == pytest.approx(33.12, abs=0.01)
    assert groups["110"].length_m == pytest.approx(4.56, abs=0.01)
    assert groups["220"].opening_area_m2 == pytest.approx(3.66, abs=0.01)
    assert groups["220"].net_area_m2 == pytest.approx(105.64, abs=0.02)
    assert groups["110"].net_area_m2 == pytest.approx(4.56 * 3.3, abs=0.02)
    assert groups["220"].role == "envelope" and groups["110"].role == "partition"
    assert result.openings_count == 2


def test_layer_roles(sample_dxf):
    result = takeoff_from_file(sample_dxf, floor_height_mm=3300)
    assert result.layer_classes["TUONG"] == "WALL"
    assert result.layer_classes["CUA"] == "OPENING"
    assert result.layer_classes["KICHTHUOC"] == "ANNOTATION"


def test_layer_override(sample_dxf):
    """Người dùng gỡ vai trò tường khỏi layer TUONG thì không còn tường nào được nhận diện."""
    result = takeoff_from_file(sample_dxf, 3300, layer_overrides={"TUONG": "IGNORE"})
    assert result.walls == [] and result.groups == []
    assert any("layer tường" in w for w in result.warnings)


def test_non_wall_layers_ignored(sample_dxf):
    result = takeoff_from_file(sample_dxf, floor_height_mm=3300)
    assert all(w.layer == "TUONG" for w in result.walls)
    assert len(result.walls) == 5


def test_encoding():
    assert tcvn3_to_unicode("T­êng g¹ch") == "Tường gạch"
    assert normalize("Tường Gạch Đặc") == "tuong gach dac"


def test_openings_recorded(sample_dxf, sample_openings):
    from optimat.drawing.dxf_reader import read_drawing
    from optimat.drawing.takeoff import compute_takeoff
    result = compute_takeoff(read_drawing(sample_dxf), 3300, openings=sample_openings)
    assert [o.name for o in result.openings] == ["D1", "S1"] and all(o.wall_id for o in result.openings)


def test_merge_plans_keeps_floor_groups(sample_dxf):
    """Agent đo cả nhà = gộp từng mặt bằng (không đo cả file: sẽ cộng mặt đứng, mặt cắt); file không có mặt bằng thì báo."""
    from optimat.drawing.takeoff import merge_plans
    from optimat.schemas import PlanTakeoff
    r = takeoff_from_file(sample_dxf, floor_height_mm=3300)
    plans = [PlanTakeoff(name=n, height_mm=3300, height_source="nhập tay", bbox=[0, 0, 1, 1], result=r) for n in ("T1", "T2")]
    merged = merge_plans(plans, 3300)
    assert len(merged.groups) == 2 * len(r.groups)
    assert sum(g.net_area_m2 for g in merged.groups) == pytest.approx(2 * sum(g.net_area_m2 for g in r.groups))
    assert merged.openings_count == 2 * r.openings_count
    assert all(w.startswith(("T1: ", "T2: ")) for w in merged.warnings)
    assert merge_plans([]).groups == [] and merge_plans([]).warnings
    # cùng một tầng vẽ nhiều hình (kích thước, vật dụng, bản chép "(2)"): chỉ tính một lần
    same = [PlanTakeoff(name=n, height_mm=3300, height_source="nhập tay", bbox=[0, 0, 1, 1], result=r)
            for n in ("MẶT BẰNG KÍCH THƯỚC LẦU 1", "MẶT BẰNG VẬT DỤNG LẦU 1", "MB TRỆT", "MB TRỆT (2)")]
    once = merge_plans(same, 3300)
    assert len(once.groups) == 2 * len(r.groups)
    assert sum("cùng tầng" in w for w in once.warnings) == 2


def test_block_openings_without_size_listed_not_subtracted(sample_dxf, sample_openings):
    """B7: block cửa không ghi kích thước và dự án chưa nhập vẫn có trong danh sách (gắn tường, rộng/cao trống)
    để trang kiểm tra nhập; không trừ. Có kích thước dự án thì trừ như cũ."""
    result = takeoff_from_file(sample_dxf, floor_height_mm=3300)
    ops = {o.name: o for o in result.openings}
    assert set(ops) == {"D1", "S1"}
    assert all(o.width_mm is None and o.height_mm is None and o.wall_id for o in ops.values())
    groups = {g.wall_type: g for g in result.groups}
    assert groups["220"].opening_area_m2 == 0 and result.openings_count == 0
    assert any("danh sách lỗ mở" in w and "D1" in w and "S1" in w for w in result.warnings)
    sized = takeoff_from_file(sample_dxf, floor_height_mm=3300, openings=sample_openings)
    assert {g.wall_type: g for g in sized.groups}["220"].net_area_m2 == pytest.approx(105.64, abs=0.02)
