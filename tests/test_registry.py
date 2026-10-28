"""S03 hồ sơ chuẩn hóa: 15 bản vẽ con chuẩn (SYNTHETIC, đáp án viết tay), xác nhận của người dùng, API, bản vẽ build."""
import json
import sys
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from optimat.api.main import app
from optimat.drawing.dxf_reader import read_drawing
from optimat.drawing.registry import Decision, Registry, apply_decisions, build_registry, floors_of
from optimat.drawing.sheets import sheet_type_of

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from make_s03_fixtures import build, load_cases  # noqa: E402

CASES = load_cases()
SCHEMA = ROOT / "docs/schema/ho_so_chuan_hoa.schema.json"


def _registry(case, tmp_path) -> Registry:
    path = tmp_path / f"{case['name']}.dxf"
    build(case).saveas(path)
    return build_registry([(path.name, read_drawing(str(path)))], case.get("symbol_overrides"))


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_ground_truth_case(case, tmp_path):
    reg = _registry(case, tmp_path)
    exp = case["expect"]
    comps = {c.id: c for c in reg.components}
    for cid, want in exp["components"].items():
        assert cid in comps, f"thiếu cấu kiện {cid}"
        c = comps[cid]
        got = {"occurrences": len(c.occurrences), "details": len(c.details), "size": c.size, "rules": c.rules,
               "confidence": c.confidence, "needs_confirmation": c.needs_confirmation,
               "floors": sorted({f for o in c.occurrences for f in o.floors}),
               "drawn_width_mm": c.occurrences[0].drawn_width_mm if c.occurrences else None,
               "axis": c.occurrences[0].axis if c.occurrences else None}
        assert {k: got[k] for k in want} == want, cid
    for cid in exp.get("absent", []):
        assert cid not in comps
    assert sorted(i.kind for i in reg.issues) == sorted(exp["issues"])
    assert sorted(u.text for u in reg.unmatched if u.kind != "layer") == sorted(exp["unmatched"])
    # nghiệm thu: mọi cấu kiện nhận trên mặt bằng có file + handle nguồn
    for c in reg.components:
        for o in c.occurrences:
            assert o.evidence.file == f"{case['name']}.dxf" and o.evidence.handle and o.evidence.rule


def test_ground_truth_set_size():
    assert 10 <= len(CASES) <= 15 and len({c["name"] for c in CASES}) == len(CASES)


def test_floors_and_sheet_types():
    assert floors_of("MẶT BẰNG DẦM SÀN LẦU 2-3-4-SÂN THƯỢNG") == ["T3", "T4", "T5", "ST"]
    assert floors_of("MẶT BẰNG SÀN LẦU 2-LẦU 5") == ["T3", "T4", "T5", "T6"]
    assert floors_of("MẶT BẰNG TẦNG TRỆT (-0.45)") == ["T1"] and floors_of("MẶT BẰNG DẦM LẦU 1 TL 1/50") == ["T2"]
    assert floors_of("MẶT BẰNG MÓNG - ĐÀ KIỀNG") == ["MONG"] and floors_of("MẶT BẰNG KẾT CẤU") == []
    assert sheet_type_of("BẢNG THỐNG KÊ THÉP DẦM").ma == "BV15" and sheet_type_of("THỐNG KÊ CỘT").ma == "BV15"
    assert sheet_type_of("BẢNG THỐNG KÊ CỘT").ma == "BV07"


def test_decisions_never_fill_missing_values(tmp_path):
    reg = _registry(next(c for c in CASES if c["name"] == "c02_thieu_chi_tiet"), tmp_path)
    confirmed = apply_decisions(reg, {"BEAM:d2": Decision(status="xac_nhan")})
    d2 = confirmed.components[0]
    assert d2.size == {"b_mm": None, "d_mm": None} and d2.confidence == "trung_binh" and not d2.needs_confirmation
    typed = apply_decisions(reg, {"BEAM:d2": Decision(size={"b_mm": 200, "d_mm": 350})}).components[0]
    assert typed.size == {"b_mm": 200, "d_mm": 350} and typed.confidence == "cao"
    assert typed.size_sources[-1].source == "nguoi_dung" and typed.size_sources[-1].evidence.rule == "NGUOI_DUNG"
    assert reg.components[0].size["d_mm"] is None              # hồ sơ gốc không bị sửa
    with pytest.raises(ValueError):
        apply_decisions(reg, {"BEAM:d2": Decision(size={"d_mm": 0})})
    with pytest.raises(ValueError):
        apply_decisions(reg, {"BEAM:x9": Decision()})


def test_user_resolves_conflict(tmp_path):
    reg = _registry(next(c for c in CASES if c["name"] == "c03_xung_dot_chu"), tmp_path)
    fixed = apply_decisions(reg, {"BEAM:d3": Decision(size={"d_mm": 400})})       # chỉ nhập cao: rộng 200 giữ từ chữ ghi
    assert fixed.components[0].size == {"b_mm": 200, "d_mm": 400} and fixed.issues == []
    dropped = apply_decisions(reg, {"BEAM:d3": Decision(status="loai_bo")})
    assert dropped.components[0].status == "loai_bo" and not dropped.components[0].needs_confirmation


def test_schema_file_in_sync():
    assert json.loads(SCHEMA.read_text(encoding="utf-8")) == Registry.model_json_schema(), \
        "lược đồ lệch mã: python scripts/make_s03_fixtures.py --schema"


def test_mapping_api(tmp_path):
    case = CASES[0]
    path = tmp_path / "c01.dxf"
    build(case).saveas(path)
    client = TestClient(app)
    with open(path, "rb") as f:
        r = client.post("/api/mapping/view", files=[("files", ("c01.dxf", f.read()))],
                        data={"symbol_overrides": json.dumps({"DS1": "BEAM"})})
    assert r.status_code == 200, r.text
    reg = r.json()
    assert [c["id"] for c in reg["components"]] == ["BEAM:d1"]
    r = client.post("/api/mapping/confirm", json={"registry": reg, "decisions": {"BEAM:d1": {"status": "xac_nhan"}}})
    assert r.status_code == 200 and r.json()["components"][0]["status"] == "xac_nhan"
    bad = client.post("/api/mapping/view", files=[("files", ("c01.dxf", b""))], data={"symbol_overrides": '{"X1": "WALL"}'})
    assert bad.status_code == 400
    assert client.post("/api/mapping/confirm", json={"registry": reg, "decisions": {"BEAM:z": {}}}).status_code == 422


def test_ket_cau_build_drawing():
    path = ROOT / "data/drawings/build/ket_cau.dxf"
    if not path.exists():
        pytest.skip("không có ket_cau.dxf")
    reg = build_registry([(path.name, read_drawing(str(path)))])
    comps = {c.id: c for c in reg.components}
    assert all(o.evidence.handle for c in reg.components for o in c.occurrences)
    # ghi nhận 21/10/2026 (S03): chi tiết D7a, D8 không có ký hiệu trên mặt bằng; D6 không có tiết diện
    assert {i.component for i in reg.issues if i.kind == "chi_tiet_khong_dung"} == {"BEAM:d7a", "BEAM:d8"}
    assert comps["BEAM:d6"].size == {"b_mm": None, "d_mm": None} and comps["BEAM:d6"].needs_confirmation
    assert comps["FOUNDATION:m1"].size["height_mm"] == 700 and len(comps["FOUNDATION:m1"].occurrences) == 4
    assert Counter(i.kind for i in reg.issues)["da_tang"] == 2
