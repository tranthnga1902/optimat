"""Tiếp nhận hồ sơ CAD (S02): kiểm tra file, phiên bản, chuyển DWG, kiểm kê đối tượng và cảnh báo."""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from optimat.api.main import app
from optimat.drawing import dwg_convert, ingest
from optimat.drawing.ingest import UploadRejected, check_upload, ingest_file, store_upload

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data/sample/ingest"
client = TestClient(app)


@pytest.fixture(scope="module")
def samples() -> dict:
    if not (SAMPLES / "expected.json").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/make_ingest_samples.py")], check=True)
    return json.loads((SAMPLES / "expected.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def fonts_present(monkeypatch):
    """Font cài trên máy khác nhau: mặc định coi mọi font đều có để kết quả không phụ thuộc máy chạy test."""
    monkeypatch.setattr(ingest.fonts_mod.font_manager, "has_font", lambda name: True)


@pytest.fixture
def no_converter(monkeypatch):
    monkeypatch.delenv("ODA_CONVERTER_PATH", raising=False)
    monkeypatch.setattr(dwg_convert.shutil, "which", lambda name: None)
    monkeypatch.setattr(dwg_convert.glob, "glob", lambda pattern: [])


def raw_count(path: Path) -> tuple[Counter, Counter, int]:
    """Đếm độc lập, không qua ezdxf: đọc cặp mã nhóm của DXF văn bản.
    Trả về (số entity modelspace theo loại, theo layer) trong mục ENTITIES và số bản ghi bảng LAYER.
    Bỏ thành phần con (VERTEX, SEQEND, ATTRIB) và entity paperspace (mã 67 = 1); entity không có mã 8 nằm ở layer "0"."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    pairs = [(lines[i].strip(), lines[i + 1].strip()) for i in range(0, len(lines) - 1, 2)]
    types, layers, n_layer = Counter(), Counter(), 0
    section = table = None
    entity = None                              # [loại, {mã: giá trị đầu tiên}] của entity đang đọc

    def close():
        if entity and entity[0] not in ("VERTEX", "SEQEND", "ATTRIB") and entity[1].get("67") != "1":
            types[entity[0]] += 1
            layers[entity[1].get("8", "0")] += 1
    for code, value in pairs:
        if code == "2" and section == "?":
            section = value
            continue
        if code == "0" and section == "ENTITIES":
            close()
            entity = [value, {}] if value != "ENDSEC" else None
        elif section == "ENTITIES" and entity:
            entity[1].setdefault(code, value)
        if code == "0" and value == "SECTION":
            section = "?"
        elif code == "0" and value == "ENDSEC":
            section = None
        elif section == "TABLES" and code == "0" and value == "TABLE":
            table = "?"
        elif section == "TABLES" and code == "2" and table == "?":
            table = value
        elif section == "TABLES" and table == "LAYER" and code == "0" and value == "LAYER":
            n_layer += 1
    return types, layers, n_layer


@pytest.mark.parametrize("name", ["01_hop_le_mm.dxf", "02_thieu_don_vi.dxf", "06_xref.dxf", "07_nhieu_layout.dxf",
                                  "08_font_vni_spline.dxf", "14_block_long_sau.dxf"])
def test_counts_match_independent_count(samples, name):
    path = SAMPLES / name
    res = ingest_file(name, path.read_bytes())
    types, layers, n_layer = raw_count(path)
    assert res["entity_counts"] == dict(types)
    assert res["entity_total"] == sum(types.values())
    assert {ly["name"]: ly["entities"] for ly in res["layers"] if ly["entities"]} == dict(layers)
    assert sum(ly["in_table"] for ly in res["layers"]) == n_layer


def test_counts_on_project_sample(sample_dxf):
    res = ingest_file("sample_floor.dxf", Path(sample_dxf).read_bytes())
    types, layers, _ = raw_count(Path(sample_dxf))
    assert res["entity_counts"] == dict(types) and res["status"] == "ok" and res["warnings"] == []
    assert res["bbox_mm"]["size"] == [5000.0, 12800.0]


def test_samples_match_expected(samples, no_converter):
    for name, exp in samples.items():
        res = ingest_file(name, (SAMPLES / name).read_bytes())
        assert (res["status"], sorted({w["code"] for w in res["warnings"]})) == (exp["status"], exp["codes"]), name
        assert res["takeoff_allowed"] == (exp["status"] == "ok"), name


def test_units_normalised_to_mm(samples):
    mm = ingest_file("a.dxf", (SAMPLES / "01_hop_le_mm.dxf").read_bytes())
    m = ingest_file("b.dxf", (SAMPLES / "03_don_vi_met.dxf").read_bytes())
    assert m["units"]["scale_to_mm"] == 1000 and m["units"]["insunits"] == 6
    assert m["bbox_mm"]["size"][0] == pytest.approx(mm["bbox_mm"]["size"][0], abs=1)


def test_headerless_dxf_is_not_meters(tmp_path):
    """ezdxf tự điền $INSUNITS = 6 (mét) khi file không có HEADER: phải coi là chưa khai báo, không nhân 1000."""
    from optimat.drawing.dxf_reader import read_dxf
    dxf = "\n".join(["0", "SECTION", "2", "ENTITIES", "0", "LINE", "8", "TUONG", "10", "0", "20", "0", "30", "0",
                     "11", "6000", "21", "0", "31", "0", "0", "ENDSEC", "0", "EOF", ""])
    res = ingest_file("r12.dxf", dxf.encode())
    assert res["units"]["insunits"] == 0 and res["bbox_mm"]["size"] == [6000.0, 0.0]
    assert "NO_UNITS" in {w["code"] for w in res["warnings"]}
    (tmp_path / "r12.dxf").write_text(dxf)
    assert read_dxf(str(tmp_path / "r12.dxf")).unit_scale == 1.0


def test_entities_carry_source(samples):
    data = (SAMPLES / "06_xref.dxf").read_bytes()
    res = ingest_file("06_xref.dxf", data)
    e = res["entities"][0]
    assert e["file"] == "06_xref.dxf" and e["sha256"] == res["file"]["sha256"] and e["handle"] and e["layout"] == "Model"
    assert any(x["type"] == "INSERT" and x["block"] == "NEN_XREF" for x in res["entities"])
    xref = next(b for b in res["blocks"] if b["name"] == "NEN_XREF")
    assert xref["is_xref"] and xref["xref_path"].endswith("nen.dwg")


def test_dwg_failure_gives_no_fake_takeoff(tmp_path, monkeypatch):
    """ODA chạy nhưng báo lỗi: kiểm kê rỗng, có log lỗi, API đo bóc trả 422 chứ không trả khối lượng."""
    fake = tmp_path / "ODAFileConverter 25.12.0" / "ODAFileConverter.exe"
    fake.parent.mkdir()
    fake.write_bytes(b"")
    monkeypatch.setenv("ODA_CONVERTER_PATH", str(fake))
    monkeypatch.setattr(dwg_convert.subprocess, "run",
                        lambda args, **kw: type("R", (), {"returncode": 1, "stdout": "", "stderr": "bad file"})())
    data = (SAMPLES / "11_dwg_hong.dwg").read_bytes()
    res = ingest_file("nha.dwg", data)
    assert res["status"] == "failed" and not res["takeoff_allowed"]
    assert res["entities"] == [] and res["entity_total"] == 0 and res["layers"] == []
    log = res["conversion"]
    assert not log["ok"] and "bad file" in log["error"] and log["converter_version"] == "25.12.0"
    assert res["file"]["dwg_version"] == "2018"
    r = client.post("/api/takeoff", files={"file": ("nha.dwg", data)})
    assert r.status_code == 422


def test_dwg_success_logs_versions(tmp_path, monkeypatch, sample_dxf):
    import shutil
    fake = tmp_path / "ODAFileConverter"
    fake.write_bytes(b"")
    monkeypatch.setenv("ODA_CONVERTER_PATH", str(fake))

    def fake_run(args, **kwargs):
        for f in Path(args[1]).glob("*.dwg"):
            shutil.copy(sample_dxf, Path(args[2]) / (f.stem + ".dxf"))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(dwg_convert.subprocess, "run", fake_run)
    res = ingest_file("nha.dwg", b"AC1027" + b"\0" * 32)
    assert res["status"] == "ok" and res["conversion"]["ok"] and res["file"]["dwg_version"] == "2013"
    assert res["entity_total"] == 10 and res["acad_release"] == "R2010"


@pytest.mark.parametrize("name, data, mime, msg", [
    ("nha.pdf", b"%PDF", None, "định dạng .pdf"),
    ("nha", b"0\nSECTION\n", None, "không có đuôi"),
    ("nha.dxf", b"", None, "rỗng"),
    ("nha.dxf", b"%PDF-1.7", None, "không phải file .dxf"),
    ("nha.dwg", b"0\nSECTION\n", None, "nội dung là DXF"),
    ("nha.dxf", b"0\nSECTION\n", "application/pdf", "MIME"),
])
def test_upload_rejected(name, data, mime, msg):
    with pytest.raises(UploadRejected, match=msg):
        check_upload(name, data, mime)


def test_upload_size_limit():
    with pytest.raises(UploadRejected, match="vượt giới hạn"):
        check_upload("nha.dxf", b"0\nSECTION\n" + b" " * 2048, max_mb=0.001)
    assert check_upload("nha.dxf", b"999\nchu thich\n0\nSECTION\n", "text/plain; charset=utf-8")["ext"] == ".dxf"


def test_store_versions_by_name_and_hash(tmp_path):
    a, b = b"0\nSECTION\n1", b"0\nSECTION\n2"
    v1 = store_upload(check_upload("nha.dxf", a), a, tmp_path)
    again = store_upload(check_upload("nha.dxf", a), a, tmp_path)
    v2 = store_upload(check_upload("nha.dxf", b), b, tmp_path)
    other = store_upload(check_upload("khac.dxf", a), a, tmp_path)
    assert (v1["version"], again["version"], v2["version"], other["version"]) == (1, 1, 2, 1)
    assert again["duplicate"] and not v2["duplicate"]
    assert (tmp_path / v1["stored_as"]).read_bytes() == a and len(list(tmp_path.glob("*.dxf"))) == 2
    assert len((tmp_path / "manifest.jsonl").read_text(encoding="utf-8").splitlines()) == 3


def test_api_ingest_many_files(samples, no_converter, monkeypatch, tmp_path):
    from optimat import config
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path)
    names = ["01_hop_le_mm.dxf", "11_dwg_hong.dwg", "12_pdf_doi_ten.dxf"]
    r = client.post("/api/ingest", files=[("files", (n, (SAMPLES / n).read_bytes())) for n in names])
    assert r.status_code == 200
    assert [x["status"] for x in r.json()] == ["ok", "failed", "rejected"]
    assert len(list(tmp_path.glob("*.dxf"))) == 1 and len(list(tmp_path.glob("*.dwg"))) == 1


def test_headerless_text_insunits_keeps_unitless(samples, tmp_path):
    """Chữ "$INSUNITS" nằm trong TEXT (không có HEADER) không được coi là khai báo đơn vị."""
    from optimat.drawing.dxf_reader import read_dxf
    path = SAMPLES / "15_khong_header_chu_insunits.dxf"
    res = ingest_file(path.name, path.read_bytes())
    assert res["units"]["insunits"] == 0 and res["units"]["scale_to_mm"] == 1.0
    assert "NO_UNITS" in {w["code"] for w in res["warnings"]}
    assert read_dxf(str(path)).unit_scale == 1.0


def test_raw_count_paperspace_and_missing_layer(tmp_path):
    """Entity paperspace (67 = 1) nằm trong mục ENTITIES không tính vào modelspace; entity thiếu mã 8 thuộc layer 0."""
    tags = ["0", "SECTION", "2", "ENTITIES",
            "0", "LINE", "10", "0", "20", "0", "30", "0", "11", "1000", "21", "0", "31", "0",
            "0", "LINE", "67", "1", "8", "KHUNG", "10", "0", "20", "0", "30", "0", "11", "420", "21", "0", "31", "0",
            "0", "ENDSEC", "0", "EOF", ""]
    path = tmp_path / "ps.dxf"
    path.write_text("\n".join(tags), encoding="ascii")
    types, layers, _ = raw_count(path)
    assert types == Counter({"LINE": 1}) and layers == Counter({"0": 1})
    res = ingest_file("ps.dxf", path.read_bytes())
    assert res["entity_counts"] == {"LINE": 1}
    assert {ly["name"]: ly["entities"] for ly in res["layers"] if ly["entities"]} == {"0": 1}


def test_binary_dxf_inventory(samples):
    """DXF nhị phân cho đúng bản kiểm kê của bản văn bản cùng nội dung (đếm thô trên bản văn bản)."""
    text, binary = SAMPLES / "01_hop_le_mm.dxf", SAMPLES / "13_nhi_phan.dxf"
    assert binary.read_bytes().startswith(b"AutoCAD Binary DXF")
    res = ingest_file(binary.name, binary.read_bytes())
    types, layers, n_layer = raw_count(text)
    assert res["entity_counts"] == dict(types) and res["units"]["insunits"] == 4
    assert {ly["name"]: ly["entities"] for ly in res["layers"] if ly["entities"]} == dict(layers)
    assert sum(ly["in_table"] for ly in res["layers"]) == n_layer


def test_declared_font_absent_on_server(samples, monkeypatch):
    monkeypatch.setattr(ingest.fonts_mod.font_manager, "has_font", lambda name: name.lower() != "txt")
    res = ingest_file("a.dxf", (SAMPLES / "01_hop_le_mm.dxf").read_bytes())
    w = [w for w in res["warnings"] if w["code"] == "FONT_NOT_FOUND"]
    assert len(w) == 1 and "txt" in w[0]["message"] and res["status"] == "ok"


def test_unreadable_entity_is_reported(samples, monkeypatch):
    real = ingest.bbox.extents

    def broken(entities, **kw):
        if any(e.dxftype() == "HATCH" for e in entities):
            raise ValueError("hình học hỏng")
        return real(entities, **kw)
    monkeypatch.setattr(ingest.bbox, "extents", broken)
    res = ingest_file("a.dxf", (SAMPLES / "01_hop_le_mm.dxf").read_bytes())
    w = [w for w in res["warnings"] if w["code"] == "UNREADABLE_ENTITY"]
    assert w and "HATCH ×1" in w[0]["message"] and res["entity_counts"]["HATCH"] == 1


def test_manifest_concurrent_versions_unique(tmp_path):
    """Nhiều luồng lưu cùng tên, nội dung khác nhau cùng lúc: mỗi bản một số phiên bản riêng."""
    import threading
    barrier = threading.Barrier(8)
    out = []

    def worker(i):
        data = b"0\nSECTION\n" + str(i).encode()
        info = check_upload("nha.dxf", data)
        barrier.wait()
        out.append(store_upload(info, data, tmp_path)["version"])
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(out) == list(range(1, 9))


@pytest.mark.parametrize("route, extra", [
    ("/api/takeoff", {}), ("/api/takeoff/view", {}), ("/api/takeoff/rough/auto", {}),
    ("/api/agent/run", {"use_llm": "false"}),
])
def test_dwg_failure_all_takeoff_routes(samples, no_converter, route, extra):
    """DWG không chuyển được: mọi API đo bóc trả 422, không trả kết quả rỗng giả làm thành công."""
    r = client.post(route, files={"file": ("nha.dwg", (SAMPLES / "11_dwg_hong.dwg").read_bytes())}, data=extra)
    assert r.status_code == 422


def test_api_rejects_too_many_files(monkeypatch):
    from optimat import config
    monkeypatch.setattr(config, "MAX_UPLOAD_FILES", 1)
    r = client.post("/api/ingest", files=[("files", ("a.dxf", b"0\nSECTION\n")), ("files", ("b.dxf", b"0\nSECTION\n"))])
    assert r.status_code == 400 and "tối đa 1 file" in r.json()["detail"]
