"""Mở CAD không chặn yêu cầu khác; giữ hợp đồng dữ liệu và dọn file tạm."""
import asyncio
import threading
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException

from optimat.api import main
from optimat.drawing.dwg_convert import DrawingError


def _health_without_io(monkeypatch):
    monkeypatch.setattr(main.MaterialPriceModel, "load", lambda: None)
    monkeypatch.setattr(main.dwg_convert, "is_available", lambda: False)
    monkeypatch.setattr(main, "get_database_url", lambda: None)


def test_view_worker_allows_health_and_preserves_inputs(monkeypatch):
    _health_without_io(monkeypatch)
    entered, release = threading.Event(), threading.Event()
    seen = {}
    drawing, catalog, plans, openings = object(), object(), object(), object()

    def read(path, overrides):
        seen["path"] = Path(path)
        seen["thread"] = threading.get_ident()
        assert seen["path"].read_bytes() == b"cad"
        assert overrides == {"A-WALL": "WALL"}
        return drawing

    def project_inputs(project_id, floor_height_mm):
        assert (project_id, floor_height_mm) == (12, 3500)
        assert threading.get_ident() == seen["thread"]
        return 3500, openings

    def takeoff(found_drawing, height, found_catalog, found_openings):
        assert (found_drawing, height, found_catalog, found_openings) == (drawing, 3500, catalog, openings)
        entered.set()
        assert release.wait(3), "Yêu cầu health không được chờ CAD hoàn tất"
        return plans

    def payload(found_drawing, found_plans, filename):
        assert (found_drawing, found_plans, filename) == (drawing, plans, "nha.dxf")
        assert seen["path"].exists(), "File tạm phải còn trong lúc dựng nền CAD"
        return {"file": filename, "plans": [{"name": "Tầng 1"}]}

    monkeypatch.setattr(main, "read_drawing", read)
    monkeypatch.setattr(main, "_project_inputs", project_inputs)
    monkeypatch.setattr(main.Catalog, "load", lambda: catalog)
    monkeypatch.setattr(main, "takeoff_plans", takeoff)
    monkeypatch.setattr(main, "view_payload", payload)

    async def exercise():
        event_loop_thread = threading.get_ident()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            upload = asyncio.create_task(client.post("/api/takeoff/view", files={"file": ("nha.dxf", b"cad")},
                data={"project_id": "12", "floor_height_mm": "3500", "layer_overrides": '{"A-WALL":"WALL"}'}))
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
                assert result.json() == {"file": "nha.dxf", "plans": [{"name": "Tầng 1"}]}
            finally:
                release.set()
                await asyncio.gather(upload, return_exceptions=True)

    asyncio.run(exercise())
    assert not seen["path"].exists()


def test_view_drawing_error_keeps_422_and_cleans_tempfile(monkeypatch):
    _health_without_io(monkeypatch)
    paths = []

    def read(path, overrides):
        paths.append(Path(path))
        assert paths[-1].exists()
        raise DrawingError("Lỗi CAD kiểm thử")

    monkeypatch.setattr(main, "read_drawing", read)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            result = await client.post("/api/takeoff/view", files={"file": ("hong.dwg", b"cad")})
            assert result.status_code == 422
            assert result.json()["detail"] == "Lỗi CAD kiểm thử"
            assert (await client.get("/api/health")).status_code == 200

    asyncio.run(exercise())
    assert paths and not paths[0].exists()


@pytest.mark.parametrize("filename,overrides", [("nha.pdf", "{}"), ("nha.dxf", "{")])
def test_view_validation_stays_before_worker(monkeypatch, filename, overrides):
    def unexpected(*args):
        pytest.fail("Dữ liệu không hợp lệ không được chạy worker CAD")

    monkeypatch.setattr(main, "_takeoff_view_payload", unexpected)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            result = await client.post("/api/takeoff/view", files={"file": (filename, b"cad")},
                                       data={"layer_overrides": overrides})
            assert result.status_code == 400

    asyncio.run(exercise())


def test_view_project_error_keeps_status_and_cleans_tempfile(monkeypatch):
    paths = []

    def read(path, overrides):
        paths.append(Path(path))
        return object()

    def missing_project(project_id, height):
        raise HTTPException(404, f"Không có dự án {project_id}.")

    monkeypatch.setattr(main, "read_drawing", read)
    monkeypatch.setattr(main, "_project_inputs", missing_project)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
            result = await client.post("/api/takeoff/view", files={"file": ("nha.dxf", b"cad")}, data={"project_id": "12"})
            assert result.status_code == 404
            assert result.json()["detail"] == "Không có dự án 12."

    asyncio.run(exercise())
    assert paths and not paths[0].exists()
