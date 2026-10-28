"""scripts/compare_estimate.py: gom khối lượng hệ thống theo mã công tác + cấu kiện, so với dự toán."""
import importlib.util
from pathlib import Path

import pandas as pd

from optimat.rough.models import WorkItem

_spec = importlib.util.spec_from_file_location("compare_estimate",
                                               Path(__file__).resolve().parents[1] / "scripts/compare_estimate.py")
ce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ce)


def test_compare_groups_and_flags_incomplete():
    est = pd.DataFrame([
        {"ma_dinh_muc": "AE.63124", "ma_cong_tac": "XAY", "cau_kien": None, "khoi_luong": 100.0},
        {"ma_dinh_muc": "AE.63224", "ma_cong_tac": "XAY", "cau_kien": None, "khoi_luong": 50.0},
        {"ma_dinh_muc": "AF.81132", "ma_cong_tac": "COP_PHA", "cau_kien": "COT", "khoi_luong": 20.0},
        {"ma_dinh_muc": "AF.12313", "ma_cong_tac": "DAM", "cau_kien": None, "khoi_luong": 10.0},
        {"ma_dinh_muc": "AK.84414", "ma_cong_tac": None, "cau_kien": None, "khoi_luong": 999.0},   # ngoài phạm vi
    ])
    works = [WorkItem(code="XAY", name="x", unit="m³", quantity=120.0), WorkItem(code="XAY", name="x", unit="m³", quantity=15.0),
             WorkItem(code="COP_PHA", name="c", unit="m²", quantity=18.0, formwork_of="COT"),
             WorkItem(code="COP_PHA", name="c", unit="m²", quantity=5.0, formwork_of="DAM"),
             WorkItem(code="DAM", name="d", unit="m³", quantity=None, missing=["cao dầm"])]
    t = ce.compare(est, works).set_index(["ma_cong_tac", "cau_kien"])
    assert len(t) == 3
    assert (t.loc[("XAY", ""), "du_toan"], t.loc[("XAY", ""), "he_thong"], t.loc[("XAY", ""), "lech_pct"]) == (150.0, 135.0, -10.0)
    assert t.loc[("COP_PHA", "COT"), "he_thong"] == 18.0                       # cốp pha dầm không lẫn vào cột
    assert t.loc[("DAM", ""), "trang_thai"] == "thiếu" and pd.isna(t.loc[("DAM", ""), "lech_pct"])
