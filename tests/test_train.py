import pandas as pd

from optimat.predict.cost_model import MaterialPriceModel
from optimat.predict.train import train_and_evaluate


def test_train_and_load(sample_prices, tmp_path):
    report = train_and_evaluate(sample_prices, str(tmp_path), extra_models=False)
    assert report["contains_synthetic"] is True
    assert {"XGBoost", "Tra bảng giá gần nhất", "Hồi quy tuyến tính"} <= set(report["metrics_on_test"])
    model = MaterialPriceModel.load(tmp_path)
    assert model is not None and model.knows("AAC01", "SUP_A")
    rows = pd.DataFrame([{"date": "2026-10-08", "material_id": "AAC01", "supplier_id": "SUP_A",
                          "province": "Ha Noi", "unit": "m³", "quantity": 12}])
    price = float(model.predict(rows)[0])
    assert 1.2e6 < price < 2.4e6


def test_quantity_outside_trained_range(sample_prices, tmp_path):
    """Khối lượng nhỏ hơn mọi mức đã học không được làm giá nhảy sang vùng của đơn vị khác."""
    train_and_evaluate(sample_prices, str(tmp_path), extra_models=False)
    model = MaterialPriceModel.load(tmp_path)
    base = {"date": "2026-10-01", "material_id": "GK03", "supplier_id": "SUP_C", "province": "Ha Noi", "unit": "viên"}
    small, edge = model.predict(pd.DataFrame([{**base, "quantity": 50}, {**base, "quantity": 200}]))
    assert abs(small - edge) / edge < 0.05


def test_missing_model_returns_none(tmp_path):
    assert MaterialPriceModel.load(tmp_path) is None
