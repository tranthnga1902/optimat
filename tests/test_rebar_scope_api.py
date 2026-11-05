"""N02-b2: nguồn/mapping structural, metadata JSON; toàn bộ bản vẽ/đáp án ở đây SYNTHETIC."""
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from optimat.api import main
from optimat.drawing.dwg_convert import DrawingError
from optimat.drawing.dxf_reader import Drawing, TextItem
from optimat.rough import takeoff
from optimat.rough.models import ProjectParams
from optimat.rough.rebar import (RebarRow, RebarScope, RebarScopeAssignment, RebarSourceRef,
                                 collect_rebar_tables, table_manifest)
from optimat.rough.takeoff import RoughRequest, RoughResult

SOURCE_BYTES = b"SYNTHETIC original source, not a real CAD file"


def _drawing():
    headers = ["CẤU KIỆN", "SỐ HIỆU", "HÌNH DẠNG", "ĐƯỜNG KÍNH (mm)",
               "CHIỀU DÀI 1 THANH (mm)", "SỐ LƯỢNG", "KHỐI LƯỢNG (kg)"]
    texts = []
    for y in (1000, -5000):
        texts.append(TextItem("BẢNG THỐNG KÊ CỐT THÉP", 0, y, "TK", "unicode", 100))
        for row, values in enumerate([headers, ["D1", "1", "thẳng", "Ø16", "2000", "10", "31,60"], ["TỔNG"]]):
            yy = y - 500 if row == 0 else y - 700 - (row - 1) * 150
            texts += [TextItem(value, i * 1000, yy, "TK", "unicode", 100) for i, value in enumerate(values)]
    return Drawing([], texts, [], [], ["TK"], {}, 1.0, [])


def _metadata(data=SOURCE_BYTES, separate=False):
    source = RebarSourceRef.from_bytes(data)
    tables, _ = collect_rebar_tables(_drawing())
    manifest = table_manifest(tables, source=source)
    assignments = [RebarScopeAssignment(ref=m.ref, content_sha256=m.content_sha256,
                    scope=RebarScope(levels=(i + 1,) if separate else (1,), element_code="DAM", quantity_basis="total"),
                    evidence=["SYNTHETIC: tổng dầm tầng đã ghi"], confirmed_by="SYNTHETIC reviewer",
                    confirmed_at=datetime(2026, 11, 3, 12, tzinfo=timezone.utc)) for i, m in enumerate(manifest)]
    return source, manifest, assignments


@pytest.fixture
def worker_reader(monkeypatch):
    seen = {"reads": [], "collects": 0, "structural": []}
    original_collect = main.collect_rebar_tables

    def read(path):
        p = Path(path)
        seen["reads"].append((p, p.read_bytes()))
        return _drawing()

    def collect(drawing):
        seen["collects"] += 1
        return original_collect(drawing)

    def structural(drawings, project, scale, *, rebar_reads=None):
        seen["structural"].append(rebar_reads)
        assert len(drawings) == 1 and rebar_reads is not None
        rows, warnings = rebar_reads[0]
        return project, {"rebar": rows, "notes": warnings}

    monkeypatch.setattr(main, "read_drawing", read)
    monkeypatch.setattr(main, "collect_rebar_tables", collect)
    monkeypatch.setattr(main, "structural_parts", structural)
    return seen


def test_scope_worker_manifest_has_both_copies_reads_graph_and_tables_once(worker_reader):
    result = main._takeoff_structural_payload(SOURCE_BYTES, ".dxf", "first.dxf", ProjectParams(), None, [])
    source = result["rebar_sources"][0]
    assert source["revision_sha256"] == hashlib.sha256(SOURCE_BYTES).hexdigest()
    assert len(result["rebar_table_manifest"]) == 2 and len(result["rebar"]) == 2
    assert all(r["missing"] for r in result["rebar"]) and result["rebar_scope_assignments"] == []
    assert len(worker_reader["reads"]) == worker_reader["collects"] == len(worker_reader["structural"]) == 1
    assert not worker_reader["reads"][0][0].exists()


@pytest.mark.parametrize("separate,expected", [(False, 1), (True, 2)])
def test_scope_worker_mapping_same_or_independent_levels(worker_reader, separate, expected):
    source, _, assignments = _metadata(separate=separate)
    result = main._takeoff_structural_payload(SOURCE_BYTES, ".dxf", "renamed.dxf", ProjectParams(), None, assignments)
    assert len(result["rebar_table_manifest"]) == 2 and len(result["rebar"]) == expected
    assert sum(r["kg"] for r in result["rebar"]) == pytest.approx(31.6 * expected)
    assert all(not r["missing"] and r["scope_source"] == "confirmed" for r in result["rebar"])
    assert result["rebar_sources"][0]["revision_sha256"] == source.revision_sha256
    assert result["rebar_scope_assignments"][0]["confirmed_by"] == "SYNTHETIC reviewer"


@pytest.mark.parametrize("bad", ["revision", "table", "content", "group"])
def test_scope_worker_bad_mapping_422_atomic_and_cleanup(worker_reader, bad):
    _, _, assignments = _metadata()
    data = SOURCE_BYTES
    if bad == "revision":
        data += b" revision 2"
    elif bad == "table":
        assignments[1].ref.table_id = "unknown-table"
    elif bad == "content":
        assignments[1].content_sha256 = "0" * 64
    else:
        assignments[1].scope.element_code = "COT"
    before = [a.model_dump_json() for a in assignments]
    with pytest.raises(HTTPException) as exc:
        main._takeoff_structural_payload(data, ".dxf", "same-name.dxf", ProjectParams(), None, assignments)
    assert exc.value.status_code == 422 and exc.value.detail
    assert not worker_reader["structural"] and [a.model_dump_json() for a in assignments] == before
    assert all(not path.exists() for path, _ in worker_reader["reads"])


def test_scope_worker_dwg_hash_is_original_and_existing_conversion_trace_survives(monkeypatch, worker_reader):
    paths = []
    trace = {"converter": "SYNTHETIC converter", "converter_version": "1", "ok": True,
             "error": None, "seconds": 0.01, "target_version": "ACAD2018"}

    def convert(path, out_dir):
        paths.append(Path(path))
        assert paths[-1].read_bytes() == SOURCE_BYTES
        target = Path(out_dir) / "converted.dxf"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"SYNTHETIC converted DXF, not original bytes")
        return str(target), trace.copy()

    monkeypatch.setattr(main, "convert_with_log", convert)
    result = main._takeoff_structural_payload(SOURCE_BYTES, ".dwg", "drawing.dwg", ProjectParams(), None, [])
    source = result["rebar_sources"][0]
    assert source["revision_sha256"] == hashlib.sha256(SOURCE_BYTES).hexdigest()
    assert source["revision_sha256"] != hashlib.sha256(worker_reader["reads"][0][1]).hexdigest()
    assert result["rebar_conversion"] == {source["source_id"]: trace}
    assert len(paths) == len(worker_reader["reads"]) == worker_reader["collects"] == 1
    assert not paths[0].exists() and not worker_reader["reads"][0][0].exists()


def test_scope_worker_dwg_conversion_error_422_and_cleanup(monkeypatch, worker_reader):
    paths = []

    def convert(path, out_dir):
        paths.append(Path(path))
        return None, {"ok": False, "error": "SYNTHETIC conversion failure"}

    monkeypatch.setattr(main, "convert_with_log", convert)
    with pytest.raises(HTTPException) as exc:
        main._takeoff_structural_payload(SOURCE_BYTES, ".dwg", "bad.dwg", ProjectParams(), None, [])
    assert exc.value.status_code == 422 and "conversion failure" in exc.value.detail
    assert paths and not paths[0].exists() and not worker_reader["reads"] and not worker_reader["structural"]


def test_scope_worker_read_error_keeps_422_and_cleanup(monkeypatch):
    paths = []

    def read(path):
        paths.append(Path(path))
        raise DrawingError("SYNTHETIC drawing failure")

    monkeypatch.setattr(main, "read_drawing", read)
    with pytest.raises(HTTPException) as exc:
        main._takeoff_structural_payload(SOURCE_BYTES, ".dxf", "bad.dxf", ProjectParams(), None, [])
    assert exc.value.status_code == 422 and paths and not paths[0].exists()


@pytest.mark.parametrize("raw", ["{", "{}", "null", '[{"confirmed_by":""}]'])
def test_scope_api_invalid_mapping_rejected_before_worker(monkeypatch, raw):
    def unexpected(*args, **kwargs):
        pytest.fail("Mapping không hợp lệ không được chạy worker")

    monkeypatch.setattr(main, "_takeoff_structural_payload", unexpected)
    with TestClient(main.app) as client:
        r = client.post("/api/takeoff/structural", files={"file": ("source.dxf", SOURCE_BYTES)},
                        data={"rebar_scope_assignments": raw})
    assert r.status_code == 422 and "rebar_scope_assignments" in r.json()["detail"]


@pytest.mark.parametrize("separate,expected", [(False, 1), (True, 2)])
def test_scope_api_reupload_manifest_then_apply_same_or_different_scope(worker_reader, separate, expected):
    with TestClient(main.app) as client:
        first = client.post("/api/takeoff/structural", files={"file": ("one.dxf", SOURCE_BYTES)},
                            data={"rebar_scope_assignments": "[]"})
        assert first.status_code == 200
        _, _, assignments = _metadata(separate=separate)
        result = client.post("/api/takeoff/structural", files={"file": ("renamed.dxf", SOURCE_BYTES)},
                             data={"rebar_scope_assignments": json.dumps([a.model_dump(mode="json") for a in assignments])})
    assert result.status_code == 200 and len(result.json()["rebar"]) == expected
    assert len(result.json()["rebar_table_manifest"]) == 2
    assert result.json()["rebar_sources"] == first.json()["rebar_sources"]
    assert len(worker_reader["reads"]) == worker_reader["collects"] == 2


def test_scope_api_changed_bytes_same_filename_rejects_old_mapping(worker_reader):
    _, _, assignments = _metadata()
    with TestClient(main.app) as client:
        r = client.post("/api/takeoff/structural", files={"file": ("same.dxf", SOURCE_BYTES + b"new revision")},
                        data={"rebar_scope_assignments": json.dumps([a.model_dump(mode="json") for a in assignments])})
    assert r.status_code == 422 and "revision" in r.json()["detail"] and not worker_reader["structural"]


def test_scope_api_group_conflict_is_422_without_half_apply(worker_reader):
    _, _, assignments = _metadata()
    assignments[1].scope.element_code = "COT"
    with TestClient(main.app) as client:
        r = client.post("/api/takeoff/structural", files={"file": ("source.dxf", SOURCE_BYTES)},
                        data={"rebar_scope_assignments": json.dumps([a.model_dump(mode="json") for a in assignments])})
    assert r.status_code == 422 and "COT" in r.json()["detail"] and "DAM" in r.json()["detail"]
    assert not worker_reader["structural"]


def _payload(resolved=False):
    source, manifest, assignments = _metadata()
    row = RebarRow(table="SYNTHETIC", row=1, element="D1", element_code="DAM", kg=31.6,
                   missing=[] if resolved else ["phạm vi chưa xác nhận"], evidence="SYNTHETIC raw evidence",
                   scope=assignments[0].scope, scope_source="confirmed", table_id=manifest[0].ref.table_id,
                   source_id=source.source_id, revision_sha256=source.revision_sha256)
    return {"plans": [], "rebar": [row.model_dump(mode="json") for _ in range(1 if resolved else 2)],
            "rebar_sources": [source.model_dump(mode="json")],
            "rebar_table_manifest": [m.model_dump(mode="json") for m in manifest],
            "rebar_scope_assignments": [a.model_dump(mode="json") for a in assignments],
            "rebar_conversion": {source.source_id: {"ok": True, "converter": "SYNTHETIC"}}}


@pytest.mark.parametrize("resolved", [False, True])
def test_scope_model_metadata_and_rows_roundtrip_are_inert(resolved):
    payload = _payload(resolved)
    request = RoughRequest(**payload)
    copied = RoughRequest.model_validate_json(request.model_dump_json())
    assert [r.model_dump(mode="json") for r in copied.rebar] == payload["rebar"]
    assert copied.rebar_scope_assignments[0].scope.levels == (1,)
    assert copied.rebar_scope_assignments[0].confirmed_at.utcoffset() is not None
    assert copied.rebar_table_manifest[0].model_dump(mode="json") == payload["rebar_table_manifest"][0]
    assert copied.rebar_conversion == payload["rebar_conversion"]
    assert any("gửi lại đúng file" in note for note in copied.notes) and len(copied.notes) == 1


def test_scope_model_old_request_needs_no_metadata():
    payload = {"plans": [], "rebar": [{"table": "old", "row": 1, "kg": 31.6, "missing": ["old reason"]}]}
    request = RoughRequest(**payload)
    copied = RoughRequest.model_validate_json(request.model_dump_json())
    assert copied.rebar[0].kg == 31.6 and copied.rebar[0].missing == ["old reason"]
    assert not copied.rebar_sources and not copied.rebar_scope_assignments and not copied.rebar_table_manifest
    assert not copied.notes and copied.rebar_conversion == {}


@pytest.mark.parametrize("resolved", [False, True])
def test_scope_api_json_only_map_never_resolves_or_deduplicates(monkeypatch, resolved):
    captured = []

    def compute(request, catalog=None):
        captured.append(request.model_dump(mode="json"))
        return RoughResult(works=[], warnings=list(request.notes))

    def forbidden(*args, **kwargs):
        pytest.fail("JSON-only không được resolve mapping hay dedup bảng")

    monkeypatch.setattr(main, "compute_rough", compute)
    monkeypatch.setattr(main, "save_rough", lambda *args: None)
    monkeypatch.setattr(main, "resolve_rebar_tables", forbidden)
    payload = _payload(resolved)
    with TestClient(main.app) as client:
        response = client.post("/api/takeoff/rough", json=payload)
    assert response.status_code == 200
    assert captured[0]["rebar"] == payload["rebar"]
    assert captured[0]["rebar_scope_assignments"] == payload["rebar_scope_assignments"]
    assert any("gửi lại đúng file" in warning for warning in response.json()["warnings"])


def _stub_non_rebar_parts(monkeypatch):
    monkeypatch.setattr(takeoff, "read_secondary", lambda *args: ([], {}, []))
    monkeypatch.setattr(takeoff, "read_structural", lambda *args: SimpleNamespace(
        beams={}, column_sections={}, column_schedule=[], warnings=[], sheets=[], foundations=[]))


def test_scope_parts_pre_read_is_used_without_reading_rebar_twice(monkeypatch):
    _stub_non_rebar_parts(monkeypatch)

    def forbidden(*args):
        pytest.fail("rebar_reads đã cung cấp thì không gọi reader nữa")

    monkeypatch.setattr(takeoff, "read_rebar_schedules", forbidden)
    a, b = RebarRow(table="A", row=1, kg=31.6), RebarRow(table="B", row=1, kg=31.6)
    _, parts = takeoff.structural_parts([object(), object()], rebar_reads=[([a], ["A source"]), ([b], ["B source"])])
    assert parts["rebar"] == [a, b] and parts["notes"] == ["A source", "B source"]
    with pytest.raises(ValueError, match="rebar_reads"):
        takeoff.structural_parts([object()], rebar_reads=[])


def test_scope_parts_old_caller_keeps_one_reader_call(monkeypatch):
    _stub_non_rebar_parts(monkeypatch)
    calls = []
    monkeypatch.setattr(takeoff, "read_rebar_schedules", lambda d: (calls.append(d) or [], []))
    drawing = object()
    _, parts = takeoff.structural_parts([drawing])
    assert calls == [drawing] and parts["rebar"] == []


def test_scope_model_save_input_keeps_metadata_without_database(monkeypatch):
    import sqlalchemy.orm
    from optimat.db import session as db_session
    saved = []
    details = []

    class FakeSession:
        def __init__(self, engine):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args):
            return object()

        def add(self, row):
            row.takeoff_id = 123
            saved.append(row.result)

        def commit(self):
            pass

        def flush(self):
            pass

        def connection(self):
            return self

    monkeypatch.setattr(db_session, "get_database_url", lambda: "SYNTHETIC_NO_DB_CONNECTION")
    monkeypatch.setattr(db_session, "get_engine", lambda: object())
    monkeypatch.setattr(sqlalchemy.orm, "Session", FakeSession)
    from optimat.db import analysis20
    monkeypatch.setattr(analysis20,'store_details',lambda conn,analysis_id,**kwargs: details.append(analysis_id))
    payload = _payload(True)
    request = RoughRequest(project_id=1, **payload)
    assert takeoff.save_rough(RoughResult(works=[]), request) == 123
    assert saved[0]["input"] == request.model_dump(mode="json")
    assert details == [123]
