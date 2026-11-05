"""Kiểm tra thứ tự bản tin, hủy đọc và phản hồi HTTP của bản vẽ mẫu."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from optimat.api import main
from optimat.drawing.dwg_convert import DrawingError
from optimat.drawing.view_progress import line_preview
from fastapi.testclient import TestClient


def test_missing_detect_class_keeps_material_available(monkeypatch):
    catalog = main.Catalog.load()
    view = catalog.wall_view().copy()
    material_id = next(m["id"] for m in main.material_options(catalog) if m["systems"])
    view.loc[view.material_id == material_id, "detect_class"] = float("nan")
    monkeypatch.setattr(catalog, "wall_view", lambda: view)
    option = next(m for m in main.material_options(catalog) if m["id"] == material_id)
    assert option["systems"] == {} and option["ready"] == {}


def test_progressive_http_sample_reaches_complete(sample_dxf):
    client = TestClient(main.app)
    with open(sample_dxf, "rb") as drawing:
        response = client.post("/api/takeoff/view", data={"progressive": "true"},
                               files={"file": ("sample_floor.dxf", drawing, "application/dxf")})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [event["type"] for event in events] == [
        "status", "preview", "status", "recognized", "status", "complete",
    ]
    result = events[-1]["data"]
    assert result["plans"][0]["walls"] and result["materials"]
    for material in result["materials"]:
        assert all(cls.isdigit() for cls in material["systems"])
        assert material["systems"].keys() == material["ready"].keys()


def segment(x=0, kind="line"):
    return SimpleNamespace(x1=x, y1=10, x2=x+10, y2=0, kind=kind)


def test_preview_coordinates_and_limit():
    drawing = SimpleNamespace(segments=[segment(x) for x in range(5)] + [segment(1000, "hatch")])
    preview = line_preview(drawing, limit=2)
    assert preview["origin"] == [0, 10]
    assert preview["size"] == [14, 10]
    assert preview["segments"] == [[0, 0, 10, 10], [3, 0, 13, 10]]
    assert preview["total"] == 5 and preview["shown"] == 2
    assert line_preview(SimpleNamespace(segments=[]))["segments"] == []


def prepare(monkeypatch, tmp_path, fail=False):
    monkeypatch.setattr(main.tempfile, "tempdir", str(tmp_path))
    state = {"reads": 0, "recognized": False, "rendered": False}
    drawing = SimpleNamespace(segments=[segment()])
    def read(path, overrides):
        state["path"] = Path(path)
        assert state["path"].read_bytes() == b"DXF"
        state["reads"] += 1
        return drawing
    def recognize(*args):
        state["recognized"] = True
        if fail: raise DrawingError("Lỗi nhận diện kiểm thử")
        return []
    def render(drawing, payload, plans):
        state["rendered"] = True
        payload["overview"] = {"cad": "<svg/>"}
    monkeypatch.setattr(main, "read_drawing", read)
    monkeypatch.setattr(main, "takeoff_plans", recognize)
    monkeypatch.setattr(main, "_project_inputs", lambda *_: (3400, None))
    monkeypatch.setattr(main.Catalog, "load", lambda: object())
    monkeypatch.setattr(main, "view_payload", lambda *_args, **kw: {"file": "Mẫu.dxf", "plans": []} if kw["cad"] is False else pytest.fail("CAD dựng ở bước riêng"))
    monkeypatch.setattr(main, "add_cad_layers", render)
    return state, main._takeoff_view_events(b"DXF", ".dxf", "Mẫu.dxf", None, None, None)


def test_preview_is_yielded_before_recognition_and_renderer(monkeypatch, tmp_path):
    state, events = prepare(monkeypatch, tmp_path)
    assert json.loads(next(events))["stage"] == "reading"
    preview = json.loads(next(events))
    assert preview["type"] == "preview", preview
    assert not state["recognized"] and not state["rendered"]
    assert json.loads(next(events))["stage"] == "recognizing"
    recognized = json.loads(next(events))
    assert recognized["type"] == "recognized" and not state["rendered"]
    remaining = [json.loads(packet) for packet in events]
    assert remaining[-1]["type"] == "complete" and remaining[-1]["data"]["overview"]["cad"] == "<svg/>"
    assert state["reads"] == 1 and not state["path"].exists()


def test_error_after_preview_keeps_stream_incomplete_and_cleans_file(monkeypatch, tmp_path):
    state, events = prepare(monkeypatch, tmp_path, fail=True)
    packets = [json.loads(packet) for packet in events]
    assert any(p["type"] == "preview" for p in packets)
    assert packets[-1]["type"] == "error"
    assert "Lỗi nhận diện" in packets[-1]["message"]
    assert not any(p["type"] == "complete" for p in packets)
    assert not state["path"].exists()


def test_cancel_after_preview_cleans_tempfile_without_recognizing(monkeypatch, tmp_path):
    state, events = prepare(monkeypatch, tmp_path)
    next(events); next(events)
    events.close()
    assert not state["path"].exists() and not state["recognized"]
