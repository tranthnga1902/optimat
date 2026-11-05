"""Huấn luyện và đánh giá mô hình giá vật liệu.

Chạy được ở cả Google Colab (qua notebooks/train_xgboost_colab.ipynb) và máy cá nhân:
    python -m optimat.predict.train --data data/sample/prices_sample.csv --out models
    python -m optimat.predict.train --from-db --out models      (đọc bảng price_records trong PostgreSQL)

Kết quả ghi ra thư mục --out:
    material_price_xgb.json      mô hình XGBoost
    material_price_spec.json     cách mã hóa đặc trưng (bắt buộc đi kèm mô hình)
    material_price_metrics.json  bảng chỉ số của mọi mô hình trên tập kiểm tra
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from .features import CAT_COLS, NUM_COLS, REQUIRED_COLS, build_spec, transform

MODEL_FILE = "material_price_xgb.json"
SPEC_FILE = "material_price_spec.json"
METRICS_FILE = "material_price_metrics.json"


def load_prices_from_db(url: str | None = None) -> pd.DataFrame:
    """Đọc toàn bộ bảng price_records trong PostgreSQL."""
    from ..db.session import get_engine
    with get_engine(url).connect() as conn:
        return pd.read_sql_query('SELECT * FROM "price_records"', conn)


def load_prices(source: "str | pd.DataFrame") -> pd.DataFrame:
    """source: đường dẫn file CSV hoặc DataFrame (ví dụ lấy từ load_prices_from_db)."""
    df = source.copy() if isinstance(source, pd.DataFrame) else pd.read_csv(source)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột trong dữ liệu giá: {missing}")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=REQUIRED_COLS)
    df = df[df["unit_price"] > 0]
    return df.sort_values("date").reset_index(drop=True)


def time_split(df: pd.DataFrame, train: float = 0.70, val: float = 0.15):
    """Chia theo thời gian: huấn luyện trên các kỳ cũ, kiểm tra trên các kỳ mới nhất.

    Chia ngẫu nhiên sẽ cho điểm cao giả, vì giá cùng tháng của cùng vật liệu rất giống nhau.
    """
    dates = np.sort(df["date"].unique())
    a = dates[int(len(dates) * train)]
    b = dates[int(len(dates) * (train + val))]
    return df[df.date < a], df[(df.date >= a) & (df.date < b)], df[df.date >= b]


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    err = y_pred - y_true
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(np.mean(err ** 2))),
        "R2": float(r2_score(y_true, y_pred)),
        "MAPE_%": float(np.mean(np.abs(err) / y_true) * 100),
    }


def _with_num_features(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    x = transform(df, spec)
    out = df[CAT_COLS].astype(str).copy()
    for i, col in enumerate(NUM_COLS):
        out[col] = x[:, len(CAT_COLS) + i]
    return out


def train_and_evaluate(data: "str | pd.DataFrame", out_dir: str = "models", extra_models: bool = True) -> dict:
    df = load_prices(data)
    tr, va, te = time_split(df)
    if min(len(tr), len(va), len(te)) == 0:
        raise ValueError("Dữ liệu quá ít kỳ thời gian để chia train/validation/test.")
    spec = build_spec(tr)
    xtr, xva, xte = transform(tr, spec), transform(va, spec), transform(te, spec)
    ytr, yva = np.log(tr.unit_price.to_numpy()), np.log(va.unit_price.to_numpy())
    yte = te.unit_price.to_numpy()
    results: dict[str, dict] = {}

    # 1) XGBoost: mô hình chính
    xgb = XGBRegressor(n_estimators=800, learning_rate=0.05, max_depth=6, subsample=0.9,
                       colsample_bytree=0.9, early_stopping_rounds=50, random_state=42)
    xgb.fit(xtr, ytr, eval_set=[(xva, yva)], verbose=False)
    results["XGBoost"] = evaluate(yte, np.exp(xgb.predict(xte)))

    # 2) Đối chứng "tra bảng": lấy giá gần nhất đã biết của đúng cặp vật liệu, nhà cung cấp.
    #    Đây là mốc quan trọng nhất: nếu XGBoost không hơn tra bảng thì chưa cần học máy.
    known = pd.concat([tr, va]).sort_values("date").groupby(["material_id", "supplier_id"]).unit_price.last()
    fallback = pd.concat([tr, va]).groupby("material_id").unit_price.median()
    keys = list(zip(te.material_id, te.supplier_id))
    lookup = np.array([known.get(k, fallback.get(k[0], np.nan)) for k in keys], dtype=float)
    mask = ~np.isnan(lookup)
    results["Tra bảng giá gần nhất"] = evaluate(yte[mask], lookup[mask])

    # 3) Hồi quy tuyến tính (Ridge) trên one-hot
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
                             ("num", StandardScaler(), NUM_COLS)])
    ridge = make_pipeline(pre, Ridge(alpha=1.0))
    ridge.fit(_with_num_features(pd.concat([tr, va]), spec), np.concatenate([ytr, yva]))
    results["Hồi quy tuyến tính"] = evaluate(yte, np.exp(ridge.predict(_with_num_features(te, spec))))

    # 4) LightGBM, CatBoost: chỉ chạy khi đã cài (Colab: pip install lightgbm catboost)
    if extra_models:
        try:
            from lightgbm import LGBMRegressor
            lgbm = LGBMRegressor(n_estimators=600, learning_rate=0.05, random_state=42, verbose=-1)
            lgbm.fit(xtr, ytr, eval_set=[(xva, yva)], categorical_feature=list(range(len(CAT_COLS))))
            results["LightGBM"] = evaluate(yte, np.exp(lgbm.predict(xte)))
        except ImportError:
            pass
        try:
            from catboost import CatBoostRegressor
            cb = CatBoostRegressor(iterations=800, learning_rate=0.05, random_seed=42, verbose=False)
            cb.fit(_with_num_features(tr, spec), ytr, cat_features=CAT_COLS,
                   eval_set=(_with_num_features(va, spec), yva), early_stopping_rounds=50)
            results["CatBoost"] = evaluate(yte, np.exp(cb.predict(_with_num_features(te, spec))))
        except ImportError:
            pass

    kinds = sorted(df["data_kind"].astype(str).unique().tolist()) if "data_kind" in df.columns else ["UNKNOWN"]
    report = {
        "rows": {"train": len(tr), "validation": len(va), "test": len(te)},
        "test_period": [str(te.date.min().date()), str(te.date.max().date())],
        "data_kinds": kinds,
        "contains_synthetic": "SYNTHETIC" in kinds,
        "note": ("Dữ liệu có phần MÔ PHỎNG: các chỉ số chỉ dùng để kiểm tra mã chạy đúng, "
                 "KHÔNG dùng để báo cáo độ chính xác.") if "SYNTHETIC" in kinds else "",
        "metrics_on_test": results,
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    xgb.save_model(str(out / MODEL_FILE))
    (out / SPEC_FILE).write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf8")
    (out / METRICS_FILE).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình giá vật liệu")
    parser.add_argument("--data", help="file CSV lịch sử giá")
    parser.add_argument("--from-db", action="store_true", help="đọc bảng price_records trong PostgreSQL (cần DATABASE_URL)")
    parser.add_argument("--out", default="models")
    args = parser.parse_args()
    if not args.data and not args.from_db:
        parser.error("cần --data <file.csv> hoặc --from-db")
    report = train_and_evaluate(load_prices_from_db() if args.from_db else args.data, args.out)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
