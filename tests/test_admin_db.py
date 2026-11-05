"""Quản trị cơ sở dữ liệu (api/admin_db.py): xem 28 bảng, sửa 6 bảng quy tắc khi có PostgreSQL."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from optimat.api.main import app

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("OPTIMAT_TEST_DATABASE_URL")
client = TestClient(app)


def test_overview_and_rows_from_csv(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    d = client.get("/api/admin/db").json()
    tables = {t["name"]: t for c in d["clusters"] for t in c["tables"]}
    assert d["source"] == "csv" and not d["connected"] and len(tables) == 20
    assert d['expected_table_count'] == 20 and d['physical_table_count'] is None
    assert not any(t["editable"] for t in tables.values())          # không có database: chỉ xem
    revisions = {"project_document_revisions", "project_profile_revisions"}
    assert 'document_revisions' in tables
    for name in sorted(revisions):
        response = client.get(f"/api/admin/tables/{name}")
        assert response.status_code == 200
        fallback = response.json()
        # Có model trong metadata không có nghĩa DB đã áp schema hoặc đã có dữ liệu.
        assert fallback["name"] == name and fallback["source"] == "csv"
        assert fallback["rows"] == [] and fallback["total"] == 0 and fallback["editable"] is False
    t = client.get("/api/admin/tables/material_notes").json()
    assert t["total"] > 150 and t["rows"][0]["id"] == 1 and "pattern" in t["rows"][0]
    assert client.post("/api/admin/tables/material_notes", json={"pattern": "x"}).status_code == 409
    assert client.get("/api/admin/tables/khong_co").status_code == 404
    sup = client.get("/api/admin/tables/suppliers").json()
    assert sup["key"] == ["supplier_id"] and not sup["editable"]
    assert client.put("/api/admin/tables/suppliers/SUP_A", json={"name": "x"}).status_code == 409
    dealers = client.get("/api/data/suppliers").json()                # trang Đại lý: đọc được, không sửa được
    assert not dealers["editable"] and {"supplier_id", "lat", "note"} <= set(dealers["rows"][0])


@pytest.mark.skipif(not URL, reason="chưa đặt OPTIMAT_TEST_DATABASE_URL")
def test_edit_rule_tables_in_postgresql(monkeypatch, login_admin):
    subprocess.run([sys.executable, str(ROOT / "scripts/init_db.py"), "--reset"], check=True, cwd=ROOT,
                   env={**os.environ, "DATABASE_URL": URL}, capture_output=True)
    monkeypatch.setenv("DATABASE_URL", URL)
    login_admin(client, URL)
    from optimat.drawing.material_notes import load_note_rules, match_note
    assert client.get("/api/admin/db").json()["connected"]
    # mã vật liệu không có trong danh mục, bảng danh mục: bị từ chối
    bad = client.post("/api/admin/tables/material_notes", json={"rule_id": "T999", "pattern": "gach the", "material_id": "XX99"})
    assert bad.status_code == 422 and "XX99" in bad.json()["detail"]
    assert client.post("/api/admin/tables/materials", json={"material_id": "Z1"}).status_code == 403
    # thêm -> bộ đọc ghi chú dùng ngay; sửa; xóa; mỗi lần ghi audit_logs
    load_note_rules.cache_clear()
    row = client.post("/api/admin/tables/material_notes",
                      json={"rule_id": "T999", "pattern": "gach the", "material_id": "GN01", "nguon": "de_xuat"}).json()["row"]
    assert "GN01" in {r.material_id for r in match_note("tuong xay gach the 220")}
    assert client.put(f"/api/admin/tables/material_notes/{row['id']}", json={"pattern": "gach the do"}).json()["row"]["pattern"] == "gach the do"
    assert client.delete(f"/api/admin/tables/material_notes/{row['id']}").status_code == 200
    from sqlalchemy import create_engine, text
    with create_engine(URL).connect() as conn:
        actions = conn.execute(text("SELECT action FROM audit_logs WHERE action LIKE 'admin_%' ORDER BY log_id")).scalars().all()
    assert actions[-3:] == ["admin_insert", "admin_update", "admin_delete"]
    csv_text = client.get("/api/admin/tables/material_notes/csv").text
    assert csv_text.splitlines()[0] == "rule_id,pattern,material_id,ten,nguon,kiem_chung,ghi_chu"


@pytest.mark.skipif(not URL, reason="chưa đặt OPTIMAT_TEST_DATABASE_URL")
def test_manage_dealers_in_postgresql(monkeypatch, login_admin):
    subprocess.run([sys.executable, str(ROOT / "scripts/init_db.py"), "--reset"], check=True, cwd=ROOT,
                   env={**os.environ, "DATABASE_URL": URL}, capture_output=True)
    monkeypatch.setenv("DATABASE_URL", URL)
    login_admin(client, URL)
    from optimat.catalog.repository import default_catalog
    tables = {t["name"]: t for c in client.get("/api/admin/db").json()["clusters"] for t in c["tables"]}
    assert tables["suppliers"]["editable"] and tables["supplier_materials"]["editable"]
    # thêm đại lý (mã nhập tay), tọa độ sai bị ràng buộc chặn
    new = {"supplier_id": "SUP_T", "name": "Đại lý thử", "province": "Ha Noi", "lat": "21.0", "lon": "105.8",
           "lead_time_days": "1", "data_kind": "SAMPLE", "delivers": "có"}
    assert client.post("/api/admin/tables/suppliers", json={**new, "lat": "200"}).status_code == 422
    row = client.post("/api/admin/tables/suppliers", json=new).json()["row"]
    assert row["supplier_id"] == "SUP_T" and row["delivers"] is True
    assert "SUP_T" in set(default_catalog().suppliers.supplier_id)       # danh mục đọc lại ngay
    # sửa không đổi được mã; thêm giá; xóa đại lý xóa luôn giá
    upd = client.put("/api/admin/tables/suppliers/SUP_T", json={"supplier_id": "SUP_X", "name": "Đổi tên"}).json()["row"]
    assert upd["supplier_id"] == "SUP_T" and upd["name"] == "Đổi tên"
    price = client.post("/api/admin/tables/supplier_materials",
                        json={"supplier_id": "SUP_T", "material_id": "GN01", "base_price": "1200", "price_level": "DEALER",
                              "price_date": "2026-10-01", "collected_at": "2026-10-01", "data_kind": "SAMPLE"}).json()["row"]
    assert price["price_date"] == "2026-10-01"
    assert client.delete("/api/admin/tables/suppliers/SUP_T").status_code == 200
    assert client.put(f"/api/admin/tables/supplier_materials/{price['id']}", json={"note": "x"}).status_code == 404
    assert client.get("/api/admin/tables/suppliers/csv").text.startswith("supplier_id,name,province")
