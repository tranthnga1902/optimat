"""Kiểm thử với PostgreSQL thật. Bỏ qua nếu chưa đặt OPTIMAT_TEST_DATABASE_URL.

    $env:OPTIMAT_TEST_DATABASE_URL = "postgresql+psycopg://optimat:matkhau@localhost:5432/optimat_test"
CẢNH BÁO: bài kiểm thử xóa và tạo lại toàn bộ bảng trong cơ sở dữ liệu này. Dùng một database riêng.
"""
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("OPTIMAT_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="chưa đặt OPTIMAT_TEST_DATABASE_URL")


@pytest.fixture(scope="module")
def seeded_db(sample_prices):
    env = {**os.environ, "DATABASE_URL": URL}
    subprocess.run([sys.executable, str(ROOT / "scripts/init_db.py"), "--reset", "--prices", sample_prices],
                   check=True, env=env)
    return URL


def test_catalog_from_db_matches_csv(seeded_db):
    from optimat.catalog.repository import Catalog
    db, csv = Catalog.from_db(seeded_db), Catalog.from_csv()
    for name in ("materials", "suppliers", "vehicles"):
        a = getattr(db, name).sort_values(getattr(db, name).columns[0]).reset_index(drop=True)
        b = getattr(csv, name).sort_values(getattr(csv, name).columns[0]).reset_index(drop=True)
        pd.testing.assert_frame_equal(a[b.columns], b, check_dtype=False)
    assert len(db.supplier_materials) == len(csv.supplier_materials)


def test_optimize_same_result_from_db(seeded_db, sample_dxf, monkeypatch):
    from optimat.catalog.repository import Catalog
    from optimat.drawing.takeoff import takeoff_from_file
    from optimat.optimize.problem import optimize
    from optimat.schemas import Constraints
    groups = takeoff_from_file(sample_dxf, 3300).groups
    cons = Constraints(max_vehicle_ton=2.5)
    from_csv = optimize(groups, cons, Catalog.from_csv(), None, method="brute")
    monkeypatch.setenv("DATABASE_URL", seeded_db)
    from_db = optimize(groups, cons, Catalog.load(), None, method="brute")
    assert [(s.total_cost, s.supply_days, s.u_value) for s in from_db.solutions] == \
           [(s.total_cost, s.supply_days, s.u_value) for s in from_csv.solutions]


def test_train_from_db(seeded_db, tmp_path):
    from optimat.predict.train import load_prices_from_db, train_and_evaluate
    df = load_prices_from_db(seeded_db)
    assert len(df) == 1248
    report = train_and_evaluate(df, str(tmp_path), extra_models=False)
    assert report["rows"]["train"] > 0 and "XGBoost" in report["metrics_on_test"]


def test_all_tables_created(seeded_db):
    from sqlalchemy import inspect
    from optimat.db.models import Base
    from optimat.db.session import get_engine
    existing = set(inspect(get_engine(seeded_db)).get_table_names())
    assert set(Base.metadata.tables) <= existing and len(Base.metadata.tables) == 26


def test_rules_and_families_from_db(seeded_db, monkeypatch):
    """Quy tắc, định mức, họ vật liệu đọc từ PostgreSQL giống hệt bản CSV đã nạp."""
    from optimat.catalog.repository import Catalog
    from optimat.drawing import material_rules
    from optimat.rough import areas, norms
    csv = (material_rules.load_rules(str(material_rules.RULES_PATH)), areas.load_room_rules(str(areas.ROOM_RULES_PATH)),
           norms.load_norms(str(norms.NORMS_PATH)))
    monkeypatch.setenv("DATABASE_URL", seeded_db)
    for f in (material_rules.load_rules, areas.load_room_rules, norms.load_norms):
        f.cache_clear()
    try:
        assert (material_rules.load_rules(), areas.load_room_rules(), norms.load_norms()) == csv
    finally:
        for f in (material_rules.load_rules, areas.load_room_rules, norms.load_norms):
            f.cache_clear()
    db = Catalog.from_db(seeded_db)
    assert db.wall_families() == Catalog.from_csv().wall_families()


def test_project_flow_roundtrip(seeded_db, sample_dxf):
    """Người dùng -> dự án -> kết quả đo bóc -> lần chạy tối ưu: lưu và đọc lại được, kể cả cột JSON."""
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from optimat.catalog.repository import Catalog
    from optimat.db.models import MaterialGroup, OptimizationRun, Project, TakeoffResultRow, User
    from optimat.db.session import get_engine
    from optimat.drawing.takeoff import takeoff_from_file
    from optimat.optimize.problem import optimize
    from optimat.schemas import Constraints, TakeoffResult

    takeoff = takeoff_from_file(sample_dxf, 3300)
    result = optimize(takeoff.groups, Constraints(max_vehicle_ton=2.5), Catalog.from_db(seeded_db), None, "brute")
    with Session(get_engine(seeded_db)) as session:
        assert session.scalar(select(MaterialGroup.name).where(MaterialGroup.group_id == "phan_tho")) == \
            "Vật liệu thi công phần thô"
        user = User(email="thu@example.com", password_hash="chua-dat", role="user")
        session.add(user)
        session.flush()
        project = Project(user_id=user.user_id, name="Nhà phố 3 tầng", max_vehicle_ton=2.5,
                          excluded_materials=["CLAY_SOLID"])
        session.add(project)
        session.flush()
        row = TakeoffResultRow(project_id=project.project_id, result=takeoff.model_dump())
        session.add(row)
        session.flush()
        session.add(OptimizationRun(project_id=project.project_id, takeoff_id=row.takeoff_id, method="brute",
                                    solutions=[s.model_dump() for s in result.solutions]))
        session.commit()
        saved = session.scalar(select(TakeoffResultRow).where(TakeoffResultRow.project_id == project.project_id))
        assert TakeoffResult(**saved.result).groups[0].wall_type == "110"
        run = session.scalar(select(OptimizationRun).where(OptimizationRun.project_id == project.project_id))
        assert len(run.solutions) == len(result.solutions) and run.solutions[0]["choices"][0]["product_url"]
        assert session.get(Project, project.project_id).excluded_materials == ["CLAY_SOLID"]


def test_materials_sql_script_loads_and_reruns(seeded_db):
    """sql/03_materials.sql nạp 93 vật liệu, chạy lại không sinh dòng trùng."""
    from pathlib import Path

    from sqlalchemy import text

    from optimat.db.session import get_engine
    script = (Path(__file__).resolve().parents[1] / "sql/03_materials.sql").read_text(encoding="utf8")
    engine = get_engine(seeded_db)
    for _ in range(2):
        raw = engine.raw_connection()
        try:
            raw.cursor().execute(script)
            raw.commit()
        finally:
            raw.close()
    with engine.connect() as conn:
        count = lambda sql: conn.execute(text(sql)).scalar()
        assert count("SELECT count(*) FROM materials WHERE tier IS NOT NULL") == 93
        assert count("SELECT count(*) FROM materials WHERE tier = 1") == 16
        assert count("SELECT count(DISTINCT \"group\") FROM materials WHERE tier IS NOT NULL") == 5
        assert count("SELECT count(*) FROM wall_systems") == 20
        assert count("SELECT count(*) FROM material_relations") == 13
        assert count("SELECT round(qty_per_m2::numeric, 1) FROM v_wall_systems WHERE wall_system_id = 'W-GN01-220'") == 121


def _run_sql(engine, path):
    raw = engine.raw_connection()
    try:
        raw.cursor().execute(path.read_text(encoding="utf8"))
        raw.commit()
    finally:
        raw.close()


def test_upgrade_sql_fills_missing_and_reruns(seeded_db):
    """sql/04_upgrade.sql thêm lại bảng, cột, ràng buộc bị thiếu; chạy lại không lỗi; giữ nguyên dữ liệu."""
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    from optimat.db.session import get_engine
    engine = get_engine(seeded_db)
    with engine.begin() as conn:
        n_prices = conn.execute(text("SELECT count(*) FROM price_records")).scalar()
        conn.execute(text("DROP TABLE audit_logs; ALTER TABLE projects DROP COLUMN budget; "
                          "ALTER TABLE suppliers DROP COLUMN maps_url; "
                          "ALTER TABLE price_records DROP CONSTRAINT ck_price_records_positive"))
    for _ in range(2):
        _run_sql(engine, ROOT / "sql/04_upgrade.sql")
    with engine.connect() as conn:
        missing = conn.execute(text(
            "SELECT count(*) FROM information_schema.columns WHERE table_name IN ('audit_logs', 'projects', 'suppliers') "
            "AND column_name IN ('log_id', 'budget', 'maps_url')")).scalar()
        assert missing == 3
        assert conn.execute(text("SELECT count(*) FROM price_records")).scalar() == n_prices
        assert conn.execute(text("SELECT count(*) FROM pg_constraint WHERE conname = 'ck_price_records_positive'")).scalar() == 1
        conn.execute(text("SELECT * FROM v_price_training LIMIT 1"))
    # công bố giá không cần đại lý; giá đại lý thì phải có đại lý
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO price_records (date, material_id, province, quantity, unit, unit_price, price_level, "
                          "source, data_kind) VALUES ('2026-10-01', 'AAC01', 'Ha Noi', 1, 'm3', 1500000, 'BULLETIN', "
                          "'test', 'SAMPLE')"))
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("INSERT INTO price_records (date, material_id, province, quantity, unit, unit_price, price_level, "
                          "source, data_kind) VALUES ('2026-10-02', 'AAC01', 'Ha Noi', 1, 'm3', 1500000, 'DEALER', "
                          "'test', 'SAMPLE')"))
    # đại lý không công khai giá: được để trống giá
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO supplier_materials (supplier_id, material_id, collected_at, data_kind) "
                          "VALUES ('SUP_C', 'GN01', '2026-10-01', 'SAMPLE') ON CONFLICT DO NOTHING"))


def test_confirm_saves_to_project(seeded_db, sample_dxf, monkeypatch):
    """Xác nhận trên trang kiểm tra có gắn dự án: kết quả chốt kèm bảng vật liệu được lưu vào takeoff_results."""
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session

    from optimat.api.main import app
    from optimat.db.models import Project, TakeoffResultRow, User
    from optimat.db.session import get_engine
    from optimat.drawing.dxf_reader import read_drawing
    from optimat.drawing.takeoff import compute_takeoff
    from optimat.drawing.viewer import view_payload
    with Session(get_engine(seeded_db)) as session:
        user = User(email="luu@example.com", password_hash="chua-dat", role="user")
        session.add(user)
        session.flush()
        project = Project(user_id=user.user_id, name="Nhà thử lưu")
        session.add(project)
        session.commit()
        pid = project.project_id
    monkeypatch.setenv("DATABASE_URL", seeded_db)
    d = read_drawing(sample_dxf)
    p = view_payload(d, compute_takeoff(d, 3300), "s.dxf")["plans"][0]
    plan = {"project_id": pid, "file": "s.dxf", "plan": "Toàn bộ", "height_mm": 3300,
            "walls": [{k: w[k] for k in ("id", "cls", "role", "x1", "y1", "x2", "y2", "mat", "masonry")} for w in p["walls"]]}
    client = TestClient(app)
    body = client.post("/api/takeoff/confirm", json=plan).json()
    assert body["takeoff_id"] and body["bill"]
    with Session(get_engine(seeded_db)) as session:
        row = session.get(TakeoffResultRow, body["takeoff_id"])
        assert row.project_id == pid and row.confirmed_at and row.result["input"]["walls"]
    assert client.post("/api/takeoff/confirm", json={**plan, "project_id": 999999}).status_code == 404


def test_rough_saves_to_project(seeded_db, sample_dxf, monkeypatch):
    """Bảng phần thô chốt có gắn dự án: lưu vào takeoff_results với kind = rough, không cần bảng mới."""
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session

    from optimat.api.main import app
    from optimat.catalog.repository import Catalog
    from optimat.db.models import Project, TakeoffResultRow, User
    from optimat.db.session import get_engine
    from optimat.drawing.dxf_reader import read_drawing
    from optimat.rough.takeoff import rough_from_drawing
    with Session(get_engine(seeded_db)) as session:
        user = User(email="phantho@example.com", password_hash="chua-dat", role="user")
        session.add(user)
        session.flush()
        project = Project(user_id=user.user_id, name="Nhà thử phần thô")
        session.add(project)
        session.commit()
        pid = project.project_id
    monkeypatch.setenv("DATABASE_URL", seeded_db)
    req = rough_from_drawing(read_drawing(sample_dxf), floor_height_mm=3300, catalog=Catalog.from_db(seeded_db))
    req.project_id = pid
    client = TestClient(app)
    body = client.post("/api/takeoff/rough", json=req.model_dump(mode="json")).json()
    assert body["takeoff_id"] and body["totals"]
    with Session(get_engine(seeded_db)) as session:
        row = session.get(TakeoffResultRow, body["takeoff_id"])
        assert row.result["kind"] == "rough" and row.result["input"]["plans"]
    assert client.post("/api/takeoff/rough", json={**req.model_dump(mode="json"), "project_id": 999999}).status_code == 404


def test_takeoff_reads_project_params(seeded_db, tmp_path, monkeypatch):
    """API đo bóc có project_id: chiều cao tầng và kích thước cửa lấy từ bảng projects; chiều cao gửi kèm thắng."""
    import ezdxf
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session

    from optimat.api.main import app
    from optimat.db.models import Project, User
    from optimat.db.session import get_engine
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    doc.blocks.new("D5").add_line((0, 0), (900, 0))          # block cửa không ghi kích thước
    msp = doc.modelspace()
    msp.add_line((0, 0), (6000, 0), dxfattribs={"layer": "TUONG"})
    msp.add_line((0, 220), (6000, 220), dxfattribs={"layer": "TUONG"})
    msp.add_blockref("D5", (3000, 110), dxfattribs={"layer": "CUA"})
    path = tmp_path / "cua.dxf"
    doc.saveas(path)
    with Session(get_engine(seeded_db)) as session:
        user = User(email="cua@example.com", password_hash="chua-dat", role="user")
        session.add(user)
        session.flush()
        project = Project(user_id=user.user_id, name="Nhà thử cửa", floor_height_mm=3000,
                          door_width_mm=800, door_height_mm=2100)
        session.add(project)
        session.commit()
        pid = project.project_id
    monkeypatch.setenv("DATABASE_URL", seeded_db)
    client = TestClient(app)

    def post(**data):
        with open(path, "rb") as f:
            return client.post("/api/takeoff", files={"file": ("cua.dxf", f, "application/dxf")}, data=data)
    body = post(project_id=str(pid)).json()
    assert body["floor_height_mm"] == 3000
    assert [(o["name"], o["width_mm"], o["height_mm"]) for o in body["openings"]] == [("D5", 800, 2100)]
    assert body["groups"][0]["opening_area_m2"] == pytest.approx(0.8 * 2.1, abs=0.01)
    assert post(project_id=str(pid), floor_height_mm="3300").json()["floor_height_mm"] == 3300
    plain = post(floor_height_mm="3300").json()                # không gắn dự án: không trừ, có cảnh báo
    assert plain["openings"] == [] and any("chưa có kích thước" in w for w in plain["warnings"])
    assert post(project_id="999999").status_code == 404


def test_concepts_admin_crud(seeded_db, monkeypatch):
    """Quản trị sửa bảng drawing_concepts: thêm, sửa, xóa; nhận diện dùng ngay ký hiệu mới (không cần khởi động lại)."""
    from fastapi.testclient import TestClient

    from optimat.api.main import app
    from optimat.drawing import concepts
    monkeypatch.setenv("DATABASE_URL", seeded_db)
    concepts.load_signals.cache_clear()
    client = TestClient(app)
    body = {"ma": "l99", "khai_niem": "Cầu thang", "qu": "QU-17", "tin_hieu": "layer", "mau": "CẦU_THANG", "vai_tro": "IGNORE"}
    row = client.post("/api/concepts", json=body).json()
    assert row["ma"] == "L99" and row["mau"] == "cau thang"
    assert client.get("/api/concepts").json()["editable"] and concepts.match_layer("cau thang 2").ma == "L99"
    assert client.post("/api/concepts", json=body).status_code == 409
    assert client.put("/api/concepts/L99", json={**body, "vai_tro": "ANNOTATION"}).json()["vai_tro"] == "ANNOTATION"
    assert concepts.match_layer("cau thang").vai_tro == "ANNOTATION"
    assert client.delete("/api/concepts/L99").status_code == 200 and concepts.match_layer("cau thang") is None
    assert client.delete("/api/concepts/L99").status_code == 404
    monkeypatch.delenv("DATABASE_URL")
    concepts.load_signals.cache_clear()
