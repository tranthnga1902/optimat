"""Kết nối PostgreSQL.

Đặt biến môi trường DATABASE_URL, ví dụ:
    postgresql+psycopg://optimat:matkhau@localhost:5432/optimat
Khi chưa đặt DATABASE_URL, hệ thống đọc danh mục từ các file CSV trong data/catalog (tiện cho kiểm thử).
"""
from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import Engine, create_engine


def get_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL") or None
    # Render cấp postgresql://... ; SQLAlchemy mặc định tìm psycopg2 (chưa cài), nên chỉ định psycopg 3
    for prefix in ("postgres://", "postgresql://"):
        if url and url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


@lru_cache(maxsize=4)
def _engine_for(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def read_rule_table(table: str, path, default_csv) -> "pd.DataFrame":
    """Bảng quy tắc dạng chuỗi (ô trống = ""), cùng dạng với file CSV sửa bằng Excel. path: đọc file đó;
    không có path thì đọc PostgreSQL khi có DATABASE_URL, ngược lại default_csv. Bảng trong database có cột id giữ thứ tự dòng."""
    import pandas as pd
    if not path and get_database_url():
        with get_engine().connect() as conn:
            df = pd.read_sql_query(f'SELECT * FROM "{table}" ORDER BY id', conn).drop(columns=["id"])
        for c in df.columns:   # số nguyên đọc về dạng 90.0 khi cột có ô trống: trả lại "90"
            df[c] = [("" if v is None or v != v else str(int(v)) if isinstance(v, float) and v.is_integer() else str(v))
                     for v in df[c]]
        return df
    return pd.read_csv(path or default_csv, dtype=str, keep_default_na=False)


def get_engine(url: str | None = None) -> Engine:
    url = url or get_database_url()
    if not url:
        raise RuntimeError("Chưa đặt biến môi trường DATABASE_URL.")
    return _engine_for(url)
