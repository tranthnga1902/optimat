"""Ký hiệu có dấu nối: dùng vocabulary hiện có, không suy mặt cắt thành cấu kiện."""
import pytest
from optimat.rough.rebar import element_code


@pytest.mark.parametrize("value,expected", [
    ("C1", "COT"), ("C-1", "COT"), ("C-2", "COT"), ("C-1A", "COT"),
    ("D-2", "DAM"), ("MC1-1", None), ("MC 1-1", None), ("C1-C2", None),
    ("C-2-B", None),
])
def test_element_token_preserves_internal_hyphen(value, expected):
    assert element_code(value) == expected
