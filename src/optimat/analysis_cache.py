"""KD01: cache kết quả phân tích hồ sơ theo hash, để lần chạy lại cùng tệp không đọc lại DXF (~20 s) và vẽ lại nền CAD (~30 s).

Khóa = SHA-256 của: tệp đã chọn (file/revision/sha256/vai trò), tên tệp, hồ sơ thông số, dấu vân tay mã + quy tắc + danh mục.
Đổi bất kỳ thứ gì trong đó thì khóa đổi, tính lại. Kết quả lưu JSON ở OPTIMAT_CACHE_DIR (mặc định data/cache/analysis);
OPTIMAT_ANALYSIS_CACHE=0 tắt cache. Cache hỏng hoặc không ghi được thì bỏ qua, luôn tính lại được.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path

from . import config

PACKAGE_DIR = Path(__file__).resolve().parent
DB_RULE_TABLES = ("material_rules", "room_rules", "rough_norms", "material_notes")


def enabled() -> bool:
    return os.environ.get("OPTIMAT_ANALYSIS_CACHE", "1") != "0"


def cache_dir() -> Path:
    return Path(os.environ.get("OPTIMAT_CACHE_DIR") or config.DATA_DIR / "cache" / "analysis")


def _hash_files(digest, folder: Path, pattern: str) -> None:
    if not folder.is_dir():
        return
    for path in sorted(folder.rglob(pattern)):
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(path.relative_to(folder).as_posix().encode())
            digest.update(path.read_bytes())


@lru_cache(maxsize=1)
def _code_fingerprint() -> str:
    """Mã nguồn chỉ đổi khi khởi động lại tiến trình nên băm một lần."""
    digest = hashlib.sha256()
    _hash_files(digest, PACKAGE_DIR, "*.py")
    return digest.hexdigest()


def data_fingerprint() -> str:
    """Quy tắc và danh mục: file CSV (luôn băm, vì nhiều CSV quy tắc đọc thẳng file) + bảng PostgreSQL khi có DATABASE_URL."""
    digest = hashlib.sha256(_code_fingerprint().encode())
    _hash_files(digest, config.DATA_DIR / "rules", "*")
    _hash_files(digest, config.CATALOG_DIR, "*")
    overlay = os.environ.get("OPTIMAT_CATALOG_OVERLAY")
    if overlay:
        _hash_files(digest, Path(overlay), "*")
    from .db.session import get_database_url
    if get_database_url():
        import pandas as pd

        from .catalog.repository import Catalog
        from .db.session import read_rule_table
        catalog = Catalog.load()
        frames = [getattr(catalog, name) for name in catalog.__dataclass_fields__ if name != "price_records"]
        frames += [read_rule_table(table, None, None) for table in DB_RULE_TABLES]
        for df in frames:
            digest.update(json.dumps(list(map(str, df.columns))).encode())
            digest.update(pd.util.hash_pandas_object(df.astype(str), index=False).values.tobytes())
    return digest.hexdigest()


def make_key(files: list[dict], names: dict, profile_payload) -> str:
    body = {"files": files, "names": {str(k): v for k, v in sorted(names.items())},
            "profile": profile_payload, "data": data_fingerprint()}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def load(key: str) -> list[dict] | None:
    path = cache_dir() / f"{key}.json"
    try:
        events = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(events, list) or not events or events[-1].get("type") != "complete":
        return None
    return events


def save(key: str, events: list[dict]) -> None:
    # shortcut: không tự dọn cache (~30 MB/lần phân tích có nền CAD), xóa tay data/cache/analysis; thêm giới hạn dung lượng khi chạy máy chủ chung

    folder = cache_dir()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, allow_nan=False)
        os.replace(tmp, folder / f"{key}.json")   # ghi nguyên tử: không để lại file nửa chừng
    except (OSError, ValueError):
        try:
            os.unlink(tmp)
        except (OSError, UnboundLocalError):
            pass
