"""Quản trị cơ sở dữ liệu (api/admin_db.py): xem 26 bảng, sửa 6 bảng quy tắc khi có PostgreSQL."""
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
    assert d["source"] == "csv" and not d["connected"] and len(tables) == 26
    assert not any(t["editable"] for t in tables.values())          # không có database: chỉ xem
    t = client.get("/api/admin/tables/material_notes").json()
    assert t["total"] > 150 and t["rows"][0]["id"] == 1 and "pattern" in t["rows"][0]
    assert client.post("/api/admin/tables/material_notes", json={"pattern": "x"}).status_code == 409
    assert client.get("/api/admin/tables/khong_co").status_code == 404


@pytest.mark.skipif(not URL, reason="chưa đặt OPTIMAT_TEST_DATABASE_URL")
def test_edit_rule_tables_in_postgresql(monkeypatch):
    subprocess.run([sys.executable, str(ROOT / "scripts/init_db.py"), "--reset"], check=True, cwd=ROOT,
                   env={**os.environ, "DATABASE_URL": URL}, capture_output=True)
    monkeypatch.setenv("DATABASE_URL", URL)
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
        actions = conn.execute(text("SELECT action FROM audit_logs ORDER BY log_id")).scalars().all()
    assert actions[-3:] == ["admin_insert", "admin_update", "admin_delete"]
    csv_text = client.get("/api/admin/tables/material_notes/csv").text
    assert csv_text.splitlines()[0] == "rule_id,pattern,material_id,ten,nguon,kiem_chung,ghi_chu"
