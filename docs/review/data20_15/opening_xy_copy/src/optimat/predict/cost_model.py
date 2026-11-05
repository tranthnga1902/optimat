"""Nạp mô hình đã huấn luyện (từ Colab) và dự đoán đơn giá vật liệu.

Máy cá nhân KHÔNG huấn luyện: chỉ cần hai file trong thư mục models/
    material_price_xgb.json, material_price_spec.json
Nếu chưa có mô hình, hệ thống vẫn chạy và dùng giá trong danh mục (price_source = "catalog").
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from .. import config
from .features import transform
from .train import MODEL_FILE, SPEC_FILE


class MaterialPriceModel:
    def __init__(self, model: XGBRegressor, spec: dict):
        self.model, self.spec = model, spec

    @classmethod
    def load(cls, folder: Path | str | None = None) -> "MaterialPriceModel | None":
        folder = Path(folder or config.MODELS_DIR)
        model_path, spec_path = folder / MODEL_FILE, folder / SPEC_FILE
        if not (model_path.exists() and spec_path.exists()):
            return None
        model = XGBRegressor()
        model.load_model(str(model_path))
        return cls(model, json.loads(spec_path.read_text(encoding="utf8")))

    def knows(self, material_id: str, supplier_id: str) -> bool:
        cats = self.spec["categories"]
        return material_id in cats["material_id"] and supplier_id in cats["supplier_id"]

    def predict(self, rows: pd.DataFrame) -> np.ndarray:
        """rows cần các cột: date, material_id, supplier_id, province, unit, quantity."""
        return np.exp(self.model.predict(transform(rows, self.spec)))
