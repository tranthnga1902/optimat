"""API hồ sơ chuẩn hóa kiến trúc–kết cấu (S03): dựng hồ sơ từ một hay nhiều file, người dùng xác nhận mapping.

/api/mapping/view     tải file lên (kiến trúc, kết cấu) -> Registry
/api/mapping/confirm  Registry + quyết định của người dùng -> Registry đã chấm lại (không đọc lại bản vẽ)
/api/mapping/schema   lược đồ JSON của hồ sơ chuẩn hóa
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..drawing.dwg_convert import DrawingError
from ..drawing.dxf_reader import read_drawing
from ..drawing.registry import Decision, Registry, apply_decisions, build_registry

router = APIRouter()


class ConfirmRequest(BaseModel):
    registry: Registry
    decisions: dict[str, Decision]


@router.post("/api/mapping/view", response_model=Registry)
async def mapping_view(files: list[UploadFile] = File(...), layer_overrides: str | None = Form(None),
                       symbol_overrides: str | None = Form(None)) -> Registry:
    """files: một hay nhiều bản vẽ cùng hồ sơ. layer_overrides: JSON {tên file: {layer: vai trò}};
    symbol_overrides: JSON {ký hiệu: BEAM | COLUMN | FOUNDATION} cho ký hiệu chưa có quy tắc."""
    try:
        layers = json.loads(layer_overrides) if layer_overrides else {}
        symbols = json.loads(symbol_overrides) if symbol_overrides else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "layer_overrides, symbol_overrides phải là JSON hợp lệ.") from exc
    if not isinstance(layers, dict) or not isinstance(symbols, dict):
        raise HTTPException(400, "layer_overrides, symbol_overrides phải là đối tượng JSON.")
    bad = sorted({v for v in symbols.values() if v not in ("BEAM", "COLUMN", "FOUNDATION")})
    if bad:
        raise HTTPException(400, f"Vai trò ký hiệu không hợp lệ: {', '.join(map(str, bad))} (BEAM, COLUMN, FOUNDATION).")
    sources = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(files):
            suffix = Path(f.filename or "").suffix.lower()
            if suffix not in (".dxf", ".dwg"):
                raise HTTPException(400, f"{f.filename}: chỉ nhận file .dxf hoặc .dwg.")
            path = Path(tmp) / f"upload{i}{suffix}"
            path.write_bytes(await f.read())
            try:
                sources.append((f.filename or path.name, read_drawing(str(path), layers.get(f.filename or ""))))
            except DrawingError as exc:
                raise HTTPException(422, f"{f.filename}: {exc}") from exc
    return build_registry(sources, symbols)


@router.post("/api/mapping/confirm", response_model=Registry)
def mapping_confirm(req: ConfirmRequest) -> Registry:
    try:
        return apply_decisions(req.registry, req.decisions)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/api/mapping/schema")
def mapping_schema() -> dict:
    return Registry.model_json_schema()
