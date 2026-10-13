"""Đáp án đo tay cho data/sample/sample_floor.dxf (chiều cao tầng 3300 mm).

Tường 220 đo theo trục tim, góc chữ L kéo tới giao điểm trục tim: 2 x 4,78 + 2 x 11,78 = 33,12 m
(khớp data/ground_truth/walls.csv). Tường ngăn 110 đo tới mặt tường bao (ngã ba).
Tường 110: 4,56 m. Lỗ mở: D1 0,9 x 2,2 và S1 1,2 x 1,4 = 3,66 m2, đều nằm trên tường 220.
"""
import pytest

from optimat.drawing.encoding import normalize, tcvn3_to_unicode
from optimat.drawing.takeoff import takeoff_from_file


def test_wall_groups(sample_dxf):
    result = takeoff_from_file(sample_dxf, floor_height_mm=3300)
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
