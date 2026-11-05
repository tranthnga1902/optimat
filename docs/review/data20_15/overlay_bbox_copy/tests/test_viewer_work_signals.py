from optimat.drawing.dxf_reader import Drawing, TextItem
from optimat.drawing.viewer import view_payload
from optimat.schemas import TakeoffResult
from types import SimpleNamespace


def drawing(titles):
    return Drawing(segments=[], texts=[TextItem(t, 0, 0, "0", "unicode") for t in titles],
                   blocks=[], hatches=[], layers=[], layer_classes={}, unit_scale=1, warnings=[])


def test_structural_only_signals_merge_titles_without_quantities(monkeypatch):
    import optimat.drawing.viewer as viewer
    monkeypatch.setattr(viewer, "rough_parts", lambda _: {"BEAM": ["layer KC_DAM"]})
    monkeypatch.setattr(viewer, "add_cad_layers", lambda *_: (_ for _ in ()).throw(AssertionError("no render")))
    titles = ["MẶT BẰNG MÓNG", "CHI TIẾT CỘT", "CHI TIẾT SÀN", "CHI TIẾT CẦU THANG",
              "CHI TIẾT LANH TÔ", "BẢNG THỐNG KÊ THÉP DẦM", "CHI TIẾT CỘT", "MẶT ĐỨNG"]
    payload = view_payload(drawing(titles), [], "SYNTHETIC", cad=False)
    signals = payload["drawing_work_signals"]
    assert payload["plans"] == []
    assert set(signals) == {"FOUNDATION", "BEAM", "COLUMN", "SLAB", "STAIR", "LINTEL", "REBAR"}
    assert signals["BEAM"][0] == "layer KC_DAM"
    assert signals["COLUMN"].count("tiêu đề CHI TIẾT CỘT") == 1
    assert all(isinstance(source, str) for sources in signals.values() for source in sources)
    assert not any("MẶT ĐỨNG" in source for sources in signals.values() for source in sources)


def test_no_signals_is_empty_and_legacy_result_has_no_optional_field():
    d = drawing([])
    assert view_payload(d, [], "SYNTHETIC", cad=False)["drawing_work_signals"] == {}
    result = TakeoffResult(walls=[], groups=[], openings_count=0)
    assert "drawing_work_signals" not in view_payload(d, result, "SYNTHETIC", cad=False)


def test_empty_detected_plans_keep_structural_signals_at_document_scope(monkeypatch):
    import optimat.drawing.viewer as viewer
    monkeypatch.setattr(viewer, "plans_data", lambda *_: {"plans": [{"name": "T1"}] * 4})
    monkeypatch.setattr(viewer, "convention_summary", lambda *_: {})
    plans = [SimpleNamespace(result=SimpleNamespace(walls=[], openings=[])) for _ in range(4)]
    payload = view_payload(drawing(["CHI TIẾT CỘT"]), plans, "SYNTHETIC", cad=False)
    assert payload["drawing_work_signals"] == {"COLUMN": ["tiêu đề CHI TIẾT CỘT"]}
    assert all("drawing_work_signals" not in p for p in payload["plans"])
    assert "drawing_work_signals" not in view_payload(drawing(["MẶT ĐỨNG"]), plans, "SYNTHETIC", cad=False)
    plans[0].result.walls = [object()]
    assert "drawing_work_signals" not in view_payload(drawing(["CHI TIẾT CỘT"]), plans, "SYNTHETIC", cad=False)
    plans[0].result.walls = []
    plans[0].result.openings = [object()]
    assert "drawing_work_signals" not in view_payload(drawing(["CHI TIẾT CỘT"]), plans, "SYNTHETIC", cad=False)


def test_one_failed_render_keeps_recognition_and_other_views(monkeypatch):
    import optimat.drawing.viewer as viewer
    class Renderer:
        def __init__(self, *_):
            self.calls = 0

        def view(self, *_):
            self.calls += 1
            if self.calls in (1, 3):
                raise ValueError("synthetic render failure")
            return SimpleNamespace(svg="<g/>", display_bbox=None)

    monkeypatch.setattr(viewer, "DrawingRenderer", Renderer)
    d = drawing([])
    d.doc = object()
    def plan(name):
        return {"origin": [0, 1], "display_bbox": [0, 0, 1, 1], "bbox_mm": [0, 0, 1, 1],
                "plan": {"name": name}, "walls": [{"id": name}], "warnings": []}
    payload = {"plans": [plan("T1"), plan("T2")], "source_hash": "untouched"}
    viewer.add_cad_layers(d, payload, None)
    first, second = payload["plans"]
    assert first["cad_missing"] and first["warnings"] and "cad" not in first
    assert first["walls"] == [{"id": "T1"}]
    assert second["cad"] == "<g/>" and not second["warnings"]
    assert payload["overview"]["cad_missing"] and payload["overview"]["warnings"]
    assert payload["source_hash"] == "untouched"
