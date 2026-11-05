"""Đọc kết cấu chạy worker, giữ đầu vào và khả năng phản hồi API khác."""
import asyncio
import threading
from pathlib import Path

import httpx
import pytest

from optimat.api import main
from optimat.drawing.dwg_convert import DrawingError


def _health_without_io(monkeypatch):
    monkeypatch.setattr(main.MaterialPriceModel, "load", lambda: None)
    monkeypatch.setattr(main.dwg_convert, "is_available", lambda: False)
    monkeypatch.setattr(main, "get_database_url", lambda: None)


def test_structural_worker_allows_health_and_preserves_inputs(monkeypatch):
    _health_without_io(monkeypatch)
    entered, release = threading.Event(), threading.Event()
    drawing, seen = object(), {}
    parts = {"structural_beams": {}, "column_sections": None, "rebar": [], "notes": ["nguồn kết cấu"]}

    def read(path):
        seen["path"] = Path(path)
        seen["thread"] = threading.get_ident()
        assert seen["path"].read_bytes() == b"cad"
        return drawing

    def structural(drawings, project, scale):
        assert drawings == [drawing]
        assert project.slab_thickness_mm == 120
        assert scale == 0.5
        assert threading.get_ident() == seen["thread"]
        assert seen["path"].exists()
        entered.set()
        assert release.wait(3), "Yêu cầu health không được chờ đọc kết cấu hoàn tất"
        return project.model_copy(update={"lintel_height_mm": None, "foundations": []}), parts

    monkeypatch.setattr(main, "read_drawing", read)
    monkeypatch.setattr(main, "structural_parts", structural)

    async def exercise():
        event_loop_thread = threading.get_ident()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            upload = asyncio.create_task(client.post("/api/takeoff/structural", files={"file": ("ket_cau.dwg", b"cad")},
                data={"params": '{"slab_thickness_mm":120}', "structural_scale": "0.5"}))
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                assert seen["thread"] != event_loop_thread
                assert not upload.done()
                health = await asyncio.wait_for(client.get("/api/health"), timeout=1)
                assert health.status_code == 200
                assert health.json()["status"] == "ok"
                assert not release.is_set()
                release.set()
                result = await asyncio.wait_for(upload, timeout=2)
                assert result.status_code == 200
                assert result.json() == {**parts, "foundations": [], "lintel_height_mm": None, "file": "ket_cau.dwg"}
            finally:
                release.set()
                await asyncio.gather(upload, return_exceptions=True)

    asyncio.run(exercise())
    assert not seen["path"].exists()


def test_structural_omitted_params_and_scale_stay_optional(monkeypatch):
    seen = {}

    def read(path):
        seen["path"] = Path(path)
        return object()

    def structural(drawings, project, scale):
        assert project == main.ProjectParams()
        assert scale is None
        return project, {"members": [], "column_sections": None}

    monkeypatch.setattr(main, "read_drawing", read)
    monkeypatch.setattr(main, "structural_parts", structural)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            result = await client.post("/api/takeoff/structural", files={"file": ("ket_cau.dxf", b"cad")})
            assert result.status_code == 200
            assert result.json()["column_sections"] is None
            assert result.json()["lintel_height_mm"] is None
            assert result.json()["file"] == "ket_cau.dxf"

    asyncio.run(exercise())
    assert not seen["path"].exists()


def test_structural_drawing_error_keeps_422_and_cleans_tempfile(monkeypatch):
    paths = []

    def read(path):
        paths.append(Path(path))
        assert paths[-1].exists()
        raise DrawingError("Lỗi kết cấu kiểm thử")

    monkeypatch.setattr(main, "read_drawing", read)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            result = await client.post("/api/takeoff/structural", files={"file": ("hong.dwg", b"cad")})
            assert result.status_code == 422
            assert result.json()["detail"] == "Lỗi kết cấu kiểm thử"

    asyncio.run(exercise())
    assert paths and not paths[0].exists()


@pytest.mark.parametrize("filename,data", [
    ("ket_cau.pdf", {}), ("ket_cau.dxf", {"structural_scale": "0"}),
    ("ket_cau.dxf", {"structural_scale": "-1"}), ("ket_cau.dxf", {"params": "{"}),
    ("ket_cau.dxf", {"params": '{"slab_thickness_mm":"không phải số"}'}),
])
def test_structural_validation_stays_before_worker(monkeypatch, filename, data):
    def unexpected(*args):
        pytest.fail("Dữ liệu không hợp lệ không được chạy worker kết cấu")

    monkeypatch.setattr(main, "_takeoff_structural_payload", unexpected)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            result = await client.post("/api/takeoff/structural", files={"file": (filename, b"cad")}, data=data)
            assert result.status_code == 400

    asyncio.run(exercise())
