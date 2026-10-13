"""Sinh dữ liệu giá MÔ PHỎNG để kiểm tra mã chạy đúng trước khi có dữ liệu thật.

    python scripts/make_sample_data.py

Mọi dòng được gắn data_kind = SYNTHETIC. Không dùng file này để báo cáo độ chính xác:
mô hình học trên dữ liệu mô phỏng chỉ học lại công thức đã dùng để sinh dữ liệu.
Dữ liệu thật (công bố giá Sở Xây dựng, giá thu thập từ web) phải có đúng các cột này.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(42)

offers = pd.read_csv(ROOT / "data/catalog/supplier_materials.csv")
suppliers = pd.read_csv(ROOT / "data/catalog/suppliers.csv").set_index("supplier_id")
months = pd.date_range("2024-11-01", "2026-10-01", freq="MS")
qty_tiers = {"viên": [200, 1000, 5000, 20000], "m³": [2, 8, 25, 80]}
units = pd.read_csv(ROOT / "data/catalog/materials.csv").set_index("material_id").unit

rows = []
for _, offer in offers.iterrows():
    drift = np.cumsum(rng.normal(0.003, 0.012, len(months)))      # biến động riêng của từng nhà cung cấp
    for i, month in enumerate(months):
        season = 0.02 * np.sin(2 * np.pi * (month.month - 3) / 12)
        for qty in qty_tiers[units[offer.material_id]]:
            discount = 0.03 * np.log10(qty / qty_tiers[units[offer.material_id]][0])
            price = offer.base_price * np.exp(drift[i] - drift[-1]) * (1 + season) * (1 - discount)
            price *= 1 + rng.normal(0, 0.012)
            rows.append({
                "date": month.strftime("%Y-%m-%d"), "material_id": offer.material_id,
                "supplier_id": offer.supplier_id, "province": suppliers.province[offer.supplier_id],
                "quantity": qty, "unit": units[offer.material_id], "unit_price": round(float(price), 0),
                "vat_included": "UNKNOWN", "transport_included": "NO",
                "source": "scripts/make_sample_data.py", "data_kind": "SYNTHETIC",
            })

out = ROOT / "data/sample/prices_sample.csv"
pd.DataFrame(rows).to_csv(out, index=False)
print(f"Đã ghi {len(rows)} dòng mô phỏng vào {out}")
