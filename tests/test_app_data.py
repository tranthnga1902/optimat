"""Giao diện chung (/app) và kiểm soát dữ liệu (scripts/check_data.py, /api/data/check)."""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from optimat.api.main import app
from optimat.catalog.repository import Catalog
from optimat.data_check import run_checks, to_markdown

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_app_page_and_admin_endpoints():
    assert client.get("/", follow_redirects=False).headers["location"] == "/app"
    page = client.get("/app").text
    assert "OptiMat AI" in page and "/api/data/check" in page and "/ui/takeoff" in page
    offers = client.get("/api/data/offers").json()
    assert offers and {"material_id", "material_name", "data_kind"} <= set(offers[0])
    assert "loaded" in client.get("/api/models").json()


def test_real_catalog_has_no_structural_errors():
    """Danh mục, quy tắc, tên gọi khác, nguồn cung đi kèm không có lỗi tham chiếu; số liệu còn trống chỉ là cảnh báo."""
    rep = run_checks(Catalog.from_csv(), today=date(2026, 10, 13))
    assert rep["ok"], [f for f in rep["findings"] if f["level"] == "error"]
    s = rep["summary"]
    assert s["vat_lieu"] == 93 and s["phuong_an_tuong"] == 20 and s["theo_lop_tuong"]["330"]["phuong_an"] == 0
    items = {(f["area"], f["item"]) for f in rep["findings"]}
    assert ("phuong_an_tuong", "lớp 330") in items and ("phuong_an_tuong", "W-GK02-190") in items
    assert "# Kiểm soát dữ liệu" in to_markdown(rep)


def test_broken_references_are_errors():
    cat = Catalog.from_csv()
    cat.supplier_materials = cat.supplier_materials.assign(material_id="MAT_CLAY_220")      # mã cũ
    cat.wall_systems = cat.wall_systems.copy()
    cat.wall_systems.loc[0, "mortar_material_id"] = "VU99"
    rep = run_checks(cat)
    errors = {(f["area"], f["message"][:20]) for f in rep["findings"] if f["level"] == "error"}
    assert not rep["ok"] and any(a == "nguon_cung" for a, _ in errors) and any(a == "phuong_an_tuong" for a, _ in errors)
    assert client.get("/api/data/check").json()["counts"]["error"] == 0


def test_check_data_script_exit_codes(tmp_path):
    ok = subprocess.run([sys.executable, str(ROOT / "scripts/check_data.py"), "--quiet", "--out-dir", str(tmp_path)],
                        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert ok.returncode == 0 and "lỗi" in ok.stdout and (tmp_path / "data_check.md").exists()
    strict = subprocess.run([sys.executable, str(ROOT / "scripts/check_data.py"), "--quiet", "--strict", "--out-dir", str(tmp_path)], capture_output=True)
    assert strict.returncode == 1                       # còn cảnh báo (số liệu trống, giá mẫu) thì chưa được chốt báo cáo


def test_concepts_admin_csv_mode(sample_dxf, monkeypatch):
    """Trang quản trị Ký hiệu nhận diện: không có database thì xem được, không sửa được; thử nhận diện trên bản vẽ."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    d = client.get("/api/concepts").json()
    assert d["source"] == "csv" and not d["editable"] and {"door", "IGNORE"} <= set(d["block_roles"])
    assert any(s["ma"] == "B08" and s["khai_niem"] == "Cao độ" for s in d["signals"])
    ok = {"ma": "L99", "khai_niem": "Cầu thang", "qu": "QU-17", "tin_hieu": "layer", "mau": "CẦU_THANG", "vai_tro": "IGNORE"}
    assert client.post("/api/concepts", json=ok).status_code == 409                      # chưa có PostgreSQL
    assert client.post("/api/concepts", json={**ok, "vai_tro": "door"}).status_code == 422  # door chỉ dành cho block
    assert client.post("/api/concepts", json={**ok, "qu": "QU-99"}).status_code == 422
    csv_text = client.get("/api/concepts/csv").text
    assert csv_text.lstrip("﻿").startswith("ma,khai_niem,qu,tin_hieu,mau,vai_tro") and "COS-MB" in csv_text
    with open(sample_dxf, "rb") as fh:
        r = client.post("/api/concepts/try", files={"file": ("mau.dxf", fh)}).json()
    assert sum(o["loai"] == "tuong" for o in r["rows"]) == 5 and isinstance(r["unknown_layers"], list)
    assert "viewConcepts" in client.get("/app").text
