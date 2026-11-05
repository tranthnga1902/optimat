"""Tạo đặc trưng cho mô hình giá vật liệu.

QUAN TRỌNG: file này được dùng ở CẢ HAI nơi, Colab lúc huấn luyện và máy cá nhân
lúc dự đoán. Không sao chép logic ra chỗ khác; nếu hai nơi tạo đặc trưng khác nhau
thì mô hình vẫn chạy nhưng cho kết quả sai.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CAT_COLS = ["material_id", "supplier_id", "province"]
NUM_COLS = ["t_month", "month", "log_qty_rel"]
FEATURE_NAMES = CAT_COLS + NUM_COLS
REQUIRED_COLS = ["date", "material_id", "supplier_id", "province", "unit", "quantity", "unit_price"]
EPOCH_YEAR = 2024


def build_spec(df: pd.DataFrame) -> dict:
    """Ghi lại danh sách giá trị của từng cột phân loại để mã hóa nhất quán về sau."""
    return {
        "feature_names": FEATURE_NAMES,
        "categories": {c: sorted(df[c].astype(str).unique().tolist()) for c in CAT_COLS},
        # Khối lượng tính theo đơn vị khác nhau (viên, m3) không so sánh trực tiếp được. Nếu đưa thẳng
        # vào mô hình, cây quyết định sẽ dùng ngưỡng khối lượng để đoán đơn vị và dự đoán sai khi gặp
        # khối lượng nằm ngoài dải đã học. Vì vậy chuẩn hóa theo khối lượng trung vị của từng đơn vị.
        "qty_ref": {str(u): float(q) for u, q in df.groupby("unit")["quantity"].median().items()},
        "target": "log(unit_price)",
        "epoch_year": EPOCH_YEAR,
    }


def transform(df: pd.DataFrame, spec: dict) -> np.ndarray:
    """Đưa bảng dữ liệu về ma trận số. Giá trị phân loại chưa gặp khi huấn luyện -> -1."""
    out = np.zeros((len(df), len(FEATURE_NAMES)), dtype=float)
    for k, col in enumerate(CAT_COLS):
        index = {v: i for i, v in enumerate(spec["categories"][col])}
        out[:, k] = df[col].astype(str).map(index).fillna(-1).to_numpy()
    date = pd.to_datetime(df["date"])
    n = len(CAT_COLS)
    out[:, n] = ((date.dt.year - spec.get("epoch_year", EPOCH_YEAR)) * 12 + date.dt.month).to_numpy()
    out[:, n + 1] = date.dt.month.to_numpy()
    ref = df["unit"].astype(str).map(spec["qty_ref"]).fillna(1.0).to_numpy(dtype=float)
    out[:, n + 2] = np.log(df["quantity"].astype(float).to_numpy() / ref)
    return out
