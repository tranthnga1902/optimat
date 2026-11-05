"""QA15 SYNTHETIC: kiểm cả hai chiều, không CAD/DB/HTTP."""
import pytest
from pydantic import ValidationError
from optimat.drawing.review import ReviewOpening


@pytest.mark.parametrize("field", ["w", "h"])
@pytest.mark.parametrize("value", ["bad", "", "900", -1, 0, float("nan"), float("inf"), -float("inf")])
def test_invalid_dimension_crossproduct(field, value):
    values = {"id": "SYN-O", "wall": "SYN-W", "w": 900, "h": 2000}
    values[field] = value
    with pytest.raises(ValidationError):
        ReviewOpening(**values)


@pytest.mark.parametrize("field", ["w", "h"])
def test_null_is_preserved_with_identity(field):
    values = {"id": "SYN-O", "wall": "SYN-W", "w": 900, "h": 2000, "keep": False}
    values[field] = None
    result = ReviewOpening(**values)
    assert getattr(result, field) is None
    assert (result.id, result.wall, result.keep) == ("SYN-O", "SYN-W", False)
