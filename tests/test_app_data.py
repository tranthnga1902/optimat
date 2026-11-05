"""API dữ liệu cho giao diện và kiểm soát dữ liệu (scripts/check_data.py, /api/data/check)."""
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


def test_admin_endpoints():
    offers = client.get("/api/data/offers").json()
    assert offers and {"material_id", "material_name", "data_kind"} <= set(offers[0])
    assert "loaded" in client.get("/api/models").json()


def test_real_catalog_has_no_structural_errors():
    """Danh mục, quy tắc, tên gọi khác, nguồn cung đi kèm không có lỗi tham chiếu; số liệu còn trống chỉ là cảnh báo."""
    rep = run_checks(Catalog.from_csv(), today=date(2026, 10, 13))
    assert rep["ok"], [f for f in rep["findings"] if f["level"] == "error"]
    s = rep["summary"]
    assert s["vat_lieu"] == 98 and s["phuong_an_tuong"] == 22 and s["theo_lop_tuong"]["330"]["phuong_an"] == 0
    items = {(f["area"], f["item"]) for f in rep["findings"]}
    assert ("phuong_an_tuong", "lớp 330") in items and ("phuong_an_tuong", "W-GK02-190") in items
    assert "# Kiểm soát dữ liệu" in to_markdown(rep)


def test_broken_references_are_errors():
    cat = Catalog.from_csv(ROOT / "data/sample/catalog")      # danh mục thật chưa có giá đại lý
    cat.supplier_materials = cat.supplier_materials.assign(material_id="MAT_CLAY_220")      # mã cũ
    cat.wall_systems = cat.wall_systems.copy()
    cat.wall_systems.loc[0, "mortar_material_id"] = "VU99"
    rep = run_checks(cat)
    errors = {(f["area"], f["message"][:20]) for f in rep["findings"] if f["level"] == "error"}
    assert not rep["ok"] and any(a == "nguon_cung" for a, _ in errors) and any(a == "phuong_an_tuong" for a, _ in errors)
    assert client.get("/api/data/check").status_code == 503


def test_data_check_requires_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.get("/api/data/check")
    assert response.status_code == 503
    assert "PostgreSQL" in response.json()["detail"]


def test_check_data_script_exit_codes(tmp_path):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    env.pop("DATABASE_URL", None)
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_data.py"), "--quiet", "--out-dir", str(tmp_path)],
                            capture_output=True, text=True, encoding="utf-8", env=env)
    assert result.returncode == 1 and "PostgreSQL" in result.stderr
    assert not (tmp_path / "data_check.md").exists()


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


def test_concept_images_upload_block_reset(tmp_path, monkeypatch):
    from optimat.api import main
    monkeypatch.setattr(main, "IMG_DIR", tmp_path / "hinh")
    monkeypatch.setattr(main.concept_samples, "block_svg", lambda n: "<svg/>" if n == "CUA DI" else None)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 20
    r = client.put("/api/concepts/images/cua_di-door", files={"file": ("a.png", png, "image/png")})
    assert r.status_code == 200 and r.json()["url"].startswith("/api/concepts/images/cua_di-door?v=")
    assert client.get("/api/concepts").json()["images"]["cua_di-door"] == r.json()["url"]
    g = client.get("/api/concepts/images/cua_di-door")
    assert g.content == png and "default-src 'none'" in g.headers["content-security-policy"]
    # đổi sang block: hình cũ khác định dạng bị thay
    assert client.put("/api/concepts/images/cua_di-door/block", json={"block": "CUA DI"}).status_code == 200
    assert [f.name for f in (tmp_path / "hinh").iterdir()] == ["cua_di-door.svg"]
    assert client.put("/api/concepts/images/cua_di-door/block", json={"block": "KHONG"}).status_code == 404
    # nội dung không khớp đuôi, khóa lạ, đuôi lạ đều bị chặn
    assert client.put("/api/concepts/images/x", files={"file": ("a.png", b"GIF89a", "image/png")}).status_code == 400
    assert client.put("/api/concepts/images/a.b", files={"file": ("a.png", png, "image/png")}).status_code == 400
    assert client.put("/api/concepts/images/X Y", files={"file": ("a.png", png, "image/png")}).status_code == 400
    assert client.put("/api/concepts/images/x", files={"file": ("a.exe", png, "image/png")}).status_code == 400
    assert client.delete("/api/concepts/images/cua_di-door").status_code == 200
    assert client.get("/api/concepts/images/cua_di-door").status_code == 404


def test_catalog_reference_comes_from_data():
    """Ô chọn trên giao diện không fix cứng: họ vật liệu, lớp tường, mác bê tông, vật liệu chống thấm lấy từ dữ liệu."""
    from optimat import config
    from optimat.rough.norms import variants_of
    ref = client.get("/api/catalog/reference").json()
    cat = Catalog.load()
    assert [f["id"] for f in ref["families"]] == list(cat.families.sort_values("sort_order").family_id)
    assert [c["id"] for c in ref["wall_classes"]] == list(config.WALL_THICKNESS_CLASSES)
    assert ref["concrete_grades"] == variants_of("BE_TONG_TRON")
    from optimat.rough.materials import mortar_material
    assert ref["mortar_grades"]
    assert all(mortar_material(cat, grade) for grade in ref["mortar_grades"])
    assert set(ref["plaster_thicknesses"]) == {v.split("/")[0] for v in variants_of("TRAT")}
    assert ref["screed_thicknesses"] == variants_of("CAN_NEN")
    assert [m["id"] for m in ref["waterproof_materials"]] == variants_of("CHONG_THAM")
    assert len(ref["vehicles"]) == len(cat.vehicles) and ref["data_kinds"] == ["ACTUAL", "SAMPLE", "SYNTHETIC"]
    rule = client.get("/api/admin/tables/material_rules").json()
    assert any(c["comment"] for c in rule["columns"])          # cách điền cột lấy từ lược đồ database
    tables = client.get("/api/admin/db").json()['rule_views']
    assert {t["name"] for t in tables if t["kind"] == "rule"} == {"material_rules", "material_notes", "drawing_concepts",
                                                                 "convention_clauses", "room_rules", "rough_norms"}
