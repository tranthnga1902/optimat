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
    return os.environ.get("DATABASE_URL") or None


@lru_cache(maxsize=4)
def _engine_for(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def get_engine(url: str | None = None) -> Engine:
    url = url or get_database_url()
    if not url:
        raise RuntimeError("Chưa đặt biến môi trường DATABASE_URL.")
    return _engine_for(url)
