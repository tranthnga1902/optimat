"""Trang Kiểm tra bóc tách: công thức chốt ở máy chủ, sửa và bổ sung, các API của trang."""
import pytest
from fastapi.testclient import TestClient

from optimat.api.main import app
from optimat.drawing.dxf_reader import read_drawing
from optimat.drawing.review import ReviewPlan, compute_review
from optimat.drawing.takeoff import compute_takeoff
from optimat.drawing.viewer import view_payload
from optimat.schemas import OpeningDefaults


def _plan(sample_dxf):
    d = read_drawing(sample_dxf)
    payload = view_payload(d, compute_takeoff(d, 3300, openings=OpeningDefaults(door_width_mm=900, door_height_mm=2200, window_width_mm=1200, window_height_mm=1400)), "sample_floor.dxf")
    p = payload["plans"][0]
    walls = [{"id": w["id"], "cls": w["cls"], "role": w["role"], "x1": w["x1"], "y1": w["y1"], "x2": w["x2"],
              "y2": w["y2"], "mat": w["mat"], "masonry": w["masonry"]} for w in p["walls"]]
    openings = [{"id": f"O{i}", "wall": o["wall"], "kind": o["kind"], "w": o["w"], "h": o["h"]}
                for i, o in enumerate(p["openings"])]
    return {"file": "sample_floor.dxf", "plan": "Toàn bộ", "height_mm": 3300, "walls": walls, "openings": openings}


def test_review_without_edits_matches_takeoff(sample_dxf):
    r = compute_review(ReviewPlan(**_plan(sample_dxf)))
    g = {(x.wall_type, x.role): x for x in r.groups}
    assert g[("220", "envelope")].net_area_m2 == pytest.approx(105.64, abs=0.02)
    assert g[("110", "partition")].net_area_m2 == pytest.approx(4.56 * 3.3, abs=0.02)
    assert r.walls_removed == r.walls_added == 0


def test_review_edits_remove_add_and_height(sample_dxf):
    data = _plan(sample_dxf)
    data["walls"][-1]["keep"] = False                                     # loại một tường nhận nhầm
    data["walls"].append({"id": "M1", "cls": "110", "role": "partition", "x1": 0, "y1": 0, "x2": 3000, "y2": 0,
                          "src": "manual"})                              # vẽ thêm tường 3 m
    data["openings"].append({"id": "N1", "wall": "M1", "kind": "door", "w": 800, "h": 2200, "src": "manual"})
    data["height_mm"] = 3000
    r = compute_review(ReviewPlan(**data))
    assert r.walls_removed == 1 and r.walls_added == 1 and r.openings_added == 1
    added = [g for g in r.groups if g.wall_type == "110"]
    assert sum(g.length_m for g in added) >= 3.0
    with pytest.raises(ValueError):
        compute_review(ReviewPlan(**{**data, "height_mm": 0}))


def test_review_api(sample_dxf):
    client = TestClient(app)
    with open(sample_dxf, "rb") as f:
        view = client.post("/api/takeoff/view", files={"file": ("sample_floor.dxf", f, "application/dxf")})
    assert view.status_code == 200
    body = view.json()
    assert body["plans"] and body["materials"] and body["plans"][0]["walls"]
    conf = client.post("/api/takeoff/confirm", json=_plan(sample_dxf))
    assert conf.status_code == 200 and conf.json()["total_net_area_m2"] > 100
    bad = client.post("/api/takeoff/confirm", json={**_plan(sample_dxf), "height_mm": -1})
    assert bad.status_code == 422


def test_confirm_returns_bill_priced_by_catalog_code(sample_dxf):
    """Xác nhận xong có bảng vật liệu: mã nhận diện (GN01) là mã tra giá; vật liệu do người dùng chọn cũng vậy."""
    from optimat.catalog.repository import Catalog
    catalog = Catalog.load()
    # Fixture xác nhận đơn vị giá mẫu; production không được suy sale_unit khi nguồn thiếu.
    catalog.supplier_materials["sale_unit"] = catalog.supplier_materials.material_id.map(catalog.materials.set_index("material_id").unit)
    data = _plan(sample_dxf)
    for w in data["walls"]:
        if w["cls"] == "110":
            w["mat"] = "GK03"                                  # người dùng đổi tường ngăn sang block 100
    r = compute_review(ReviewPlan(**data), catalog)
    g = {x.wall_type: x for x in r.groups}
    assert (g["220"].design_material_id, g["220"].design_wall_system_id) == ("GN01", "W-GN01-220")
    assert (g["110"].design_material_id, g["110"].design_wall_system_id) == ("GK03", "W-GK03-100")
    main = {b.wall_type: b for b in r.bill if b.kind == "main"}
    assert main["110"].best_price == 4900 and main["110"].est_cost is not None
    assert r.bill_total is None and any("VU02" in m for m in r.bill_missing)     # vữa chưa có giá: không cộng bừa
    data["walls"][0]["mat"] = "MAT_CLAY_220"
    assert any("không có trong danh mục" in w for w in compute_review(ReviewPlan(**data), catalog).warnings)


def test_payload_materials_are_catalog_codes(sample_dxf):
    d = read_drawing(sample_dxf)
    payload = view_payload(d, compute_takeoff(d, 3300), "x.dxf")
    by = {m["id"]: m for m in payload["materials"]}
    assert by["GN01"]["systems"] == {"110": "W-GN01-110", "220": "W-GN01-220"}
    assert "AAC" in {f["id"] for f in payload["families"]} and not any(k.startswith("MAT_") for k in by)
    assert {w["mat"] for w in payload["plans"][0]["walls"]} == {"GN01", "AAC01"}
