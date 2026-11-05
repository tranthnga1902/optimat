"""API của OptiMat AI.

Chạy:  uvicorn optimat.api.main:app --reload --app-dir src
Tài liệu thử nghiệm tự sinh tại http://localhost:8000/docs
"""
from __future__ import annotations

import json
import re
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Literal, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import SQLAlchemyError

from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder

from .admin_db import router as admin_router
from .admin_ops import router as admin_ops_router
from .auth import require_admin, current_user, router as auth_router
from .mapping import router as mapping_router
from .material_advisor import router as material_advisor_router
from .project_analysis import router as project_analysis_router
from .project_files import router as project_files_router
from ..agent.llm import ParsedConstraints, llm_available, parse_constraints
from ..agent.orchestrator import run_agent
from ..agent.pipeline import run_pipeline
from ..catalog.pricing import BillLine, bill_of_materials
from .. import config
from ..catalog.repository import Catalog
from ..data_check import DATA_KINDS, run_checks
from ..db.session import get_database_url
from ..drawing import concept_samples, concepts, dwg_convert
from ..drawing.dwg_convert import DrawingError
from ..drawing.dxf_reader import read_drawing
from ..drawing.encoding import normalize
from ..drawing.ingest import convert_with_log, ingest_file
from ..drawing.objects import list_objects
from ..drawing.review import ReviewPlan, ReviewResult, compute_review, save_review
from ..drawing.takeoff import takeoff_from_file, takeoff_plans, takeoff_plans_from_file
from ..drawing.viewer import add_cad_layers, material_options, view_payload
from ..drawing.view_progress import line_preview
from ..optimize.problem import optimize
from ..predict.cost_model import MaterialPriceModel
from ..rough.models import RAW_CLASSES, STEEL_ELEMENTS, ProjectParams
from ..rough.norms import variants_of
from ..rough.rebar import (RebarScopeAssignment, RebarSourceRef, collect_rebar_tables,
                          resolve_rebar_tables, table_manifest)
from ..rough.takeoff import RoughRequest, RoughResult, compute_rough, rough_from_drawing, save_rough, structural_parts
from ..schemas import Constraints, OpeningDefaults, OptimizeResult, PlanTakeoff, TakeoffResult, WallGroup

app = FastAPI(title="OptiMat AI", version="0.1.0")
app.include_router(admin_router)     # quản trị cơ sở dữ liệu (api/admin_db.py)
app.include_router(auth_router)      # đăng nhập, phân quyền (api/auth.py)
app.include_router(admin_ops_router) # tổng quan, người dùng, dự án (api/admin_ops.py)
app.include_router(mapping_router)   # hồ sơ chuẩn hóa kiến trúc–kết cấu (api/mapping.py)
app.include_router(project_files_router)
app.include_router(project_analysis_router)
app.include_router(material_advisor_router)
# Cho phép giao diện React chạy ở cổng khác gọi vào khi phát triển.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])


class OptimizeRequest(BaseModel):
    groups: list[WallGroup]
    constraints: Constraints = Constraints()
    method: str = "auto"
    project_id: int | None = Field(default=None, gt=0)
    takeoff_id: int | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def _saved_context(self):
        if (self.project_id is None) != (self.takeoff_id is None):
            raise ValueError('Lưu tối ưu cần cả dự án và kết quả bóc tách.')
        return self


class BillRequest(BaseModel):
    groups: list[WallGroup]
    actual_only: bool = True


class ParseRequest(BaseModel):
    message: str
    use_llm: bool = True


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "price_model_loaded": MaterialPriceModel.load() is not None,
            "dwg_converter_available": dwg_convert.is_available(),
            "catalog_source": "postgresql" if get_database_url() else "csv"}


def _project_inputs(project_id: int | None, floor_height_mm: float | None) -> tuple[float | None, OpeningDefaults | None]:
    """Chiều cao tầng và kích thước cửa của dự án (bảng projects); floor_height_mm gửi kèm thắng chiều cao của dự án.
    Không gắn dự án hoặc không có PostgreSQL thì không có kích thước cửa."""
    if project_id is None or not get_database_url():
        return floor_height_mm, None
    from sqlalchemy.orm import Session

    from ..db.models import Project
    from ..db.session import get_engine
    with Session(get_engine()) as session:
        p = session.get(Project, project_id)
        if p is None:
            raise HTTPException(404, f"Không có dự án {project_id}.")
        return (floor_height_mm or p.floor_height_mm,
                OpeningDefaults(door_width_mm=p.door_width_mm, door_height_mm=p.door_height_mm,
                                window_width_mm=p.window_width_mm, window_height_mm=p.window_height_mm))


@app.post("/api/takeoff", response_model=TakeoffResult)
async def takeoff(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                  layer_overrides: str | None = Form(None), project_id: int | None = Form(None),
                  length_rule: str = Form("tim")) -> TakeoffResult:
    """Nhận .dxf hoặc .dwg. layer_overrides: chuỗi JSON dạng {"tên layer": "WALL"} để ghi đè vai trò layer."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    try:
        overrides = json.loads(layer_overrides) if layer_overrides else None
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "layer_overrides phải là chuỗi JSON hợp lệ.") from exc
    height, openings = _project_inputs(project_id, floor_height_mm)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        try:
            return takeoff_from_file(str(path), height, overrides, openings, length_rule)
        except ValueError as exc:  # quy tắc chiều dài sai
            raise HTTPException(422, str(exc)) from exc
        except DrawingError as exc:  # thiếu ODA File Converter, file hỏng, định dạng sai
            raise HTTPException(422, str(exc)) from exc


def _takeoff_view_payload(data: bytes, suffix: str, file_name: str, overrides: dict | None,
                          project_id: int | None, floor_height_mm: float | None) -> dict:
    """Đọc, đo và dựng nền CAD trong worker để không chặn các yêu cầu khác."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(data)
        try:
            drawing = read_drawing(str(path), overrides)
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
        height, openings = _project_inputs(project_id, floor_height_mm)
        plans = takeoff_plans(drawing, height, Catalog.load(), openings)
        return view_payload(drawing, plans, file_name or path.name)


def _takeoff_view_events(data: bytes, suffix: str, file_name: str, overrides: dict | None,
                         project_id: int | None, floor_height_mm: float | None):
    """Một lần đọc file, trả nét trước khi đo bóc và dựng nền CAD đầy đủ."""
    def packet(kind: str, **fields):
        return json.dumps(jsonable_encoder({"type": kind, **fields}), ensure_ascii=False, allow_nan=False) + "\n"

    try:
        yield packet("status", stage="reading", message="Đang đọc nét bản vẽ và quy đổi đơn vị…")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"upload{suffix}"
            path.write_bytes(data)
            drawing = read_drawing(str(path), overrides)
            yield packet("preview", preview=line_preview(drawing))
            yield packet("status", stage="recognizing", message="Đã có nét bản vẽ. Đang nhận diện mặt bằng, tường và lỗ mở…")
            height, openings = _project_inputs(project_id, floor_height_mm)
            plans = takeoff_plans(drawing, height, Catalog.load(), openings)
            payload = view_payload(drawing, plans, file_name or path.name, cad=False)
            yield packet("recognized", data=payload)
            yield packet("status", stage="rendering", message="Đã nhận diện hình học. Đang dựng nền CAD đầy đủ…")
            add_cad_layers(drawing, payload, plans)
            yield packet("complete", data=payload)
    except Exception as exc:
        message = str(exc.detail) if isinstance(exc, HTTPException) else str(exc)
        yield packet("error", message="Chưa đọc xong bản vẽ: " + message)


@app.post("/api/takeoff/view", response_model=dict, responses={
    200: {"content": {"application/x-ndjson": {"schema": {"type": "string"}}}},
})
async def takeoff_view(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                       layer_overrides: str | None = Form(None), project_id: int | None = Form(None),
                       progressive: bool = Form(False)):
    """Dữ liệu cho trang Kiểm tra bóc tách: nét bản vẽ đã tách theo mặt bằng kèm kết quả nhận dạng."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    try:
        overrides = json.loads(layer_overrides) if layer_overrides else None
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "layer_overrides phải là chuỗi JSON hợp lệ.") from exc
    data = await file.read()
    if progressive is True:
        return StreamingResponse(_takeoff_view_events(data, suffix, file.filename or "", overrides, project_id, floor_height_mm),
                                 media_type="application/x-ndjson", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})
    return await run_in_threadpool(_takeoff_view_payload, data, suffix, file.filename or "", overrides,
                                   project_id, floor_height_mm)


@app.post("/api/takeoff/confirm", response_model=ReviewResult)
def takeoff_confirm(plan: ReviewPlan) -> ReviewResult:
    """Chốt kết quả sau khi người dùng sửa, bổ sung: máy chủ tính lại khối lượng bằng một công thức duy nhất."""
    try:
        from ..db.analysis20 import capture_catalog
        catalog=Catalog.load()
        snapshot=capture_catalog(catalog) if plan.project_id is not None and get_database_url() else None
        result = compute_review(plan,catalog)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        result.takeoff_id = save_review(result, plan, snapshot)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return result


@app.post("/api/takeoff/rough/auto")
async def takeoff_rough_auto(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                             params: str | None = Form(None), layer_overrides: str | None = Form(None),
                             project_id: int | None = Form(None), structural_file: UploadFile | None = File(None),
                             structural_scale: float | None = Form(None)) -> dict:
    """Bóc phần thô từ nhận dạng tự động. params: chuỗi JSON thông số công trình (ProjectParams), trống được.
    structural_file: bản vẽ kết cấu (mặt bằng móng, dầm) nếu tách file; structural_scale: hệ số đổi số đo trên mặt bằng
    kết cấu ra mm thật (mặt bằng vẽ phóng to 2 lần: 0.5); trống: tự suy từ đường kích thước.
    Trả {"request": đầu vào đã dựng (tường, cửa, cột, tên phòng từng mặt bằng) để sửa, "result": bảng phần thô}."""
    suffix = Path(file.filename or "").suffix.lower()
    s_suffix = Path(structural_file.filename or "").suffix.lower() if structural_file else ""
    if suffix not in (".dxf", ".dwg") or (structural_file and s_suffix not in (".dxf", ".dwg")):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    if structural_scale is not None and not structural_scale > 0:
        raise HTTPException(400, "structural_scale phải lớn hơn 0.")
    try:
        overrides = json.loads(layer_overrides) if layer_overrides else None
        project = ProjectParams(**json.loads(params)) if params else ProjectParams()
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(400, f"params hoặc layer_overrides không hợp lệ: {exc}") from exc
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        structural = None
        try:
            drawing = read_drawing(str(path), overrides)
            if structural_file:
                s_path = Path(tmp) / f"structural{s_suffix}"
                s_path.write_bytes(await structural_file.read())
                structural = read_drawing(str(s_path))
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
    catalog = Catalog.load()
    height, openings = _project_inputs(project_id, floor_height_mm)
    req = rough_from_drawing(drawing, project, height, catalog, file.filename or path.name, openings, structural,
                             structural_scale)
    try:
        result = compute_rough(req, catalog)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"request": jsonable_encoder(req), "result": jsonable_encoder(result)}


def _takeoff_structural_payload(data: bytes, suffix: str, file_name: str | None,
                                project: ProjectParams, structural_scale: float | None,
                                rebar_scope_assignments: list[RebarScopeAssignment] | None = None) -> dict:
    """Đọc kết cấu trong worker, giữ file tạm tới khi dựng đủ đầu vào phần thô."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"structural{suffix}"
        path.write_bytes(data)
        conversion = None
        try:
            read_path = str(path)
            if rebar_scope_assignments is not None and suffix == ".dwg":
                read_path, conversion = convert_with_log(str(path), str(Path(tmp) / "converted"))
                if read_path is None:
                    raise DrawingError(conversion.get("error") or "Chuyển DWG thất bại.")
            drawing = read_drawing(read_path)
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
        metadata = {}
        if rebar_scope_assignments is None:
            project, parts = structural_parts([drawing], project, structural_scale)
        else:
            source = RebarSourceRef.from_bytes(data)
            try:
                tables, warnings = collect_rebar_tables(drawing)
                manifest = table_manifest(tables, source=source)
                rows, resolved_warnings = resolve_rebar_tables(tables, source=source,
                                                              assignments=rebar_scope_assignments)
                project, parts = structural_parts([drawing], project, structural_scale,
                                                  rebar_reads=[(rows, warnings + resolved_warnings)])
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
            metadata = {"rebar_sources": [source], "rebar_table_manifest": manifest,
                        "rebar_scope_assignments": rebar_scope_assignments,
                        "rebar_conversion": {source.source_id: conversion} if conversion is not None else {}}
        return jsonable_encoder({**parts, "foundations": project.foundations, "lintel_height_mm": project.lintel_height_mm,
                                 "file": file_name, **metadata})


@app.post("/api/takeoff/structural")
async def takeoff_structural(file: UploadFile = File(...), params: str | None = Form(None),
                             structural_scale: float | None = Form(None),
                             rebar_scope_assignments: str | None = Form(None)) -> dict:
    """Đọc bản vẽ kết cấu tách file (dầm, cột, móng, bảng thép) cho trang kiểm tra: trả các trường để ghép vào RoughRequest
    rồi gửi /api/takeoff/rough. params: thông số đang nhập (móng, cao lanh tô chỉ bổ sung khi còn trống)."""
    if Path(file.filename or "").suffix.lower() not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    if structural_scale is not None and not structural_scale > 0:
        raise HTTPException(400, "structural_scale phải lớn hơn 0.")
    try:
        project = ProjectParams(**json.loads(params)) if params else ProjectParams()
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(400, f"params không hợp lệ: {exc}") from exc
    assignments = None
    if rebar_scope_assignments is not None:
        try:
            raw = json.loads(rebar_scope_assignments)
            if not isinstance(raw, list):
                raise ValueError("rebar_scope_assignments phải là danh sách JSON.")
            assignments = [RebarScopeAssignment.model_validate(item) for item in raw]
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise HTTPException(422, f"rebar_scope_assignments không hợp lệ: {exc}") from exc
    data = await file.read()
    args = (data, Path(file.filename or "").suffix.lower(), file.filename, project, structural_scale)
    if assignments is None:
        return await run_in_threadpool(_takeoff_structural_payload, *args)
    return await run_in_threadpool(_takeoff_structural_payload, *args, assignments)


@app.post("/api/takeoff/rough", response_model=RoughResult)
def takeoff_rough(req: RoughRequest) -> RoughResult:
    """Chốt bảng phần thô từ dữ liệu đã sửa (mọi mặt bằng + thông số công trình); lưu takeoff_results khi có dự án."""
    try:
        from ..db.analysis20 import capture_catalog
        catalog=Catalog.load()
        snapshot=capture_catalog(catalog) if req.project_id is not None and get_database_url() else None
        result = compute_rough(req,catalog)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        result.takeoff_id = save_rough(result, req, snapshot)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return result


@app.post("/api/takeoff/rough/excel")
def takeoff_rough_excel(req: RoughRequest) -> Response:
    """BOQ phần thô ra Excel (tổng, theo tầng, theo cấu kiện, cốt thép, vật liệu, cảnh báo, phạm vi hỗ trợ); không lưu."""
    from ..rough.boq import boq_bytes
    try:
        result = compute_rough(req)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return Response(boq_bytes(result, req), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="boq_phan_tho.xlsx"'})


@app.post("/api/takeoff/rough/optimizer")
def takeoff_rough_optimizer(req: RoughRequest) -> dict:
    """Vật liệu thô theo nhóm cho bộ tối ưu (JSON: nhóm, kg, giai đoạn, trạng thái; dòng D vào missing); không lưu."""
    from ..rough.boq import export_for_optimizer
    try:
        return export_for_optimizer(compute_rough(req))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/catalog/wall-materials")
def wall_materials() -> dict:
    """Vật liệu tường và phương án tường trong danh mục: mã dùng chung cho bóc tách, tối ưu và tra giá.
    ready = đủ số liệu để tối ưu; missing = thông số còn trống."""
    catalog = Catalog.load()
    view = catalog.wall_view()
    systems = [{"wall_system_id": r.wall_system_id, "material_id": r.material_id, "family": r.family,
                "detect_class": r.detect_class, "ready": bool(r.ready), "missing": list(r.missing), "data_kind": r.data_kind}
               for r in view.itertuples()]
    return {"materials": material_options(catalog), "wall_systems": systems}


@app.get("/api/catalog/reference")
def catalog_reference() -> dict:
    """Danh sách tra cứu cho các ô chọn trên giao diện (không fix cứng ở web): họ vật liệu, loại xe (bảng material_families,
    vehicles), mác bê tông và vật liệu chống thấm (biến thể trong rough_norms); lớp tường theo dải chiều dày bộ nhận dạng dùng."""
    catalog = Catalog.load()
    fam = catalog.families.sort_values("sort_order")
    veh = catalog.vehicles.sort_values("payload_ton")
    return {
        "families": [{"id": r.family_id, "name": r.name, "is_wall": str(r.is_wall).lower() in ("true", "1")} for r in fam.itertuples()],
        "vehicles": [{"id": r.vehicle_id, "name": r.name, "payload_ton": float(r.payload_ton)} for r in veh.itertuples()],
        "wall_classes": [{"id": k, "min_mm": lo, "max_mm": hi} for k, (lo, hi) in config.WALL_THICKNESS_CLASSES.items()],
        "concrete_grades": variants_of("BE_TONG_TRON"),
        "mortar_grades": sorted({"M" + match.group(1)
            for row in catalog.materials.itertuples()
            if row.unit == "m³" and "MORTAR" in str(row.usage_role)
            if (match := re.search(r"mác\s*(\d+)\b", row.name, re.IGNORECASE))}, key=lambda g: int(g[1:])),
        "plaster_thicknesses": sorted({v.split("/")[0] for v in variants_of("TRAT")}, key=float),
        "screed_thicknesses": variants_of("CAN_NEN"),
        "waterproof_materials": [{"id": m, "name": catalog.material_name(m) or m} for m in variants_of("CHONG_THAM")],
        "steel_elements": [{"code": k, "name": v} for k, v in STEEL_ELEMENTS.items()],
        "raw_classes": [{"code": k, "name": v} for k, v in RAW_CLASSES.items()],
        "data_kinds": list(DATA_KINDS),
    }


@app.post("/api/price/bill", response_model=list[BillLine])
def price_bill(req: BillRequest) -> list[BillLine]:
    """Bảng vật liệu theo thiết kế (gạch + vữa) và giá đang có, cho các nhóm tường đã chốt."""
    return bill_of_materials(req.groups, Catalog.load(), actual_only=req.actual_only)


@app.post("/api/takeoff/plans", response_model=list[PlanTakeoff])
async def takeoff_plans_api(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                        layer_overrides: str | None = Form(None), project_id: int | None = Form(None),
                        length_rule: str = Form("tim")) -> list[PlanTakeoff]:
    """File có nhiều mặt bằng: tách theo tiêu đề "MẶT BẰNG TẦNG ..." và đo bóc từng mặt bằng.
    Chiều cao tầng suy từ cao độ sàn trên bản vẽ khi không nhập. Danh sách rỗng: file không có mặt bằng kiến trúc."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    try:
        overrides = json.loads(layer_overrides) if layer_overrides else None
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "layer_overrides phải là chuỗi JSON hợp lệ.") from exc
    height, openings = _project_inputs(project_id, floor_height_mm)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        try:
            return takeoff_plans_from_file(str(path), height, overrides, openings, length_rule)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc


@app.post("/api/constraints/parse", response_model=ParsedConstraints)
def parse(req: ParseRequest) -> ParsedConstraints:
    return parse_constraints(req.message, req.use_llm)


@app.post("/api/optimize", response_model=OptimizeResult)
def run_optimize(req: OptimizeRequest, user: dict | None = Depends(current_user)) -> OptimizeResult:
    try:
        if req.project_id is not None:
            from .project_files import _user, _project
            from ..db.session import get_engine
            from ..db.models import TakeoffResultRow
            from sqlalchemy.orm import Session
            uid=_user(user)
            with Session(get_engine()) as db:
                _project(db,req.project_id,uid)
                saved=db.get(TakeoffResultRow,req.takeoff_id)
                if saved is None or saved.project_id != req.project_id:
                    raise HTTPException(404,'Không có kết quả bóc tách trong dự án.')
                from ..db.optimization20 import assert_groups_match
                assert_groups_match(saved.result,req.groups)
        model = None if req.constraints.procurement_mode else MaterialPriceModel.load()
        catalog=Catalog.load()
        result=optimize(req.groups, req.constraints, catalog, model, req.method)
        if req.project_id is not None:
            from ..db.optimization20 import save_optimization
            result.run_id=save_optimization(req,result,catalog,model)
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/agent/run")
async def agent_run(file: UploadFile = File(...), message: str = Form(""), floor_height_mm: float | None = Form(None),
                    use_llm: bool = Form(True), rough_params: str | None = Form(None),
                    structural_file: UploadFile | None = File(None)) -> dict:
    """Chạy trọn luồng: đo bóc -> vật liệu theo thiết kế và giá -> phần thô -> ràng buộc -> tối ưu -> giải thích.
    Có mô hình ngôn ngữ thì agent gọi công cụ; không có (hoặc use_llm=false) thì chạy luồng cố định.
    rough_params: chuỗi JSON thông số công trình (trống: phần cần thông số để trống kèm cảnh báo).
    structural_file: bản vẽ kết cấu nếu tách file (móng, dầm, cột)."""
    suffix = Path(file.filename or "").suffix.lower()
    s_suffix = Path(structural_file.filename or "").suffix.lower() if structural_file else ""
    if suffix not in (".dxf", ".dwg") or (structural_file and s_suffix not in (".dxf", ".dwg")):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    try:
        rough = ProjectParams(**json.loads(rough_params)) if rough_params else None
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(400, f"rough_params không hợp lệ: {exc}") from exc
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        structural = []
        if structural_file:
            s_path = Path(tmp) / f"structural{s_suffix}"
            s_path.write_bytes(await structural_file.read())
            structural = [str(s_path)]
        try:
            if use_llm and llm_available():
                out = run_agent(str(path), message, floor_height_mm, rough_params=rough, structural_paths=structural)
            else:
                state = run_pipeline(str(path), message=message or None, floor_height_mm=floor_height_mm, use_llm=False,
                                     rough_params=rough, structural_paths=structural)
                out = {"mode": "pipeline", "answer": state["explanation"], "takeoff": state["takeoff"],
                       "result": state["result"], "constraints": state["constraints"], "bill": state["bill"],
                       "questions": state["questions"], "rough": state.get("rough")}
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
    # Bản vẽ vừa tải trong agent chưa qua phân phạm vi và duyệt vật liệu của dự án.
    out["procurement_ready"] = False
    out["answer"] = ("Kịch bản sơ bộ từ bản vẽ tự nhận diện. Để lập nhu cầu mua, hãy duyệt mặt bằng, "
                     "vật liệu và tính phần thô của dự án.\n" + out["answer"])
    return jsonable_encoder(out)


# ------------------------------------------------------------------ tiếp nhận hồ sơ CAD (S02)


@app.post("/api/ingest")
async def ingest(files: list[UploadFile] = File(...), store: bool = Form(True)) -> list[dict]:
    """Nhận nhiều .dxf/.dwg: kiểm tra, lưu theo hash kèm phiên bản, chuyển DWG, trả bản kiểm kê từng file.
    File sai được trả status "rejected"/"failed" kèm cảnh báo, không làm hỏng cả lô."""
    if len(files) > config.MAX_UPLOAD_FILES:
        raise HTTPException(400, f"Mỗi lần gửi tối đa {config.MAX_UPLOAD_FILES} file.")
    limit = int(config.MAX_UPLOAD_MB * 1024 * 1024)
    out = []
    for f in files:
        data = await f.read(limit + 1)    # đọc dư 1 byte để biết file vượt giới hạn mà không nạp hết vào bộ nhớ
        out.append(await run_in_threadpool(ingest_file, f.filename or "", data, f.content_type,
                                           config.UPLOAD_DIR if store else None))
    return out


# ------------------------------------------------------------------ quản trị dữ liệu
# giao diện web là frontend/ (Next.js); máy chủ này chỉ phục vụ API
@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/api/data/check")
def data_check() -> dict:
    """Kiểm soát dữ liệu: lỗi cấu trúc, số liệu còn trống, dữ liệu mẫu, giá cũ, đáp án đo tay. Chỉ đọc."""
    if not get_database_url():
        raise HTTPException(503, "Kiểm soát dữ liệu cần kết nối PostgreSQL (DATABASE_URL).")
    try:
        return run_checks()
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Không kết nối hoặc đọc được PostgreSQL.") from exc


@app.get("/api/data/offers")
def data_offers() -> list[dict]:
    """Bảng giá đại lý trong danh mục kèm thông tin nhà cung cấp và loại dữ liệu, cho trang quản trị."""
    cat = Catalog.load()
    names = cat.materials.set_index("material_id").name
    rows = cat.offers(cat.supplier_materials.material_id.unique().tolist())
    keep = [c for c in ("supplier_id", "name", "material_id", "base_price", "sale_unit", "price_level", "price_date",
                        "data_kind", "product_url", "maps_url", "province") if c in rows.columns]
    rows = rows[keep].assign(material_name=rows.material_id.map(names))
    return jsonable_encoder(rows.astype(object).where(rows.notna(), None).to_dict("records"))


@app.get("/api/data/suppliers")
def data_suppliers() -> dict:
    """Danh bạ đại lý cho trang Đại lý (bản đồ, danh sách, chi tiết). Sửa qua /api/admin/tables/suppliers khi có PostgreSQL."""
    s = Catalog.load().suppliers
    return {"editable": bool(get_database_url()),
            "rows": jsonable_encoder(s.astype(object).where(s.notna(), None).to_dict("records"))}


@app.get("/api/models")
def models_info() -> dict:
    """Mô hình giá đang có trong thư mục models/ và bảng chỉ số trên tập kiểm tra (nếu đã huấn luyện)."""
    path = config.ROOT / "models" / "material_price_metrics.json"
    metrics = json.loads(path.read_text(encoding="utf8")) if path.exists() else None
    return {"loaded": MaterialPriceModel.load() is not None, "metrics": metrics,
            "nsga": {"pop_size": config.NSGA_POP_SIZE, "generations": config.NSGA_GENERATIONS},
            "llm_provider": config.LLM_PROVIDER, "llm_model": config.OPENAI_MODEL, "llm_available": llm_available()}


# ------------------------------------------------------------------ quản trị: ký hiệu nhận diện bản vẽ (drawing_concepts)
class ConceptIn(BaseModel):
    """Một ký hiệu nhận dạng; layer: mẫu là chuỗi con của tên layer (tự bỏ dấu, chữ thường); block: tiền tố tên block."""
    ma: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9_-]+$")
    khai_niem: str = Field(min_length=1, max_length=64)
    qu: str = Field(min_length=1, max_length=16)
    tin_hieu: Literal["layer", "block"]
    mau: str = Field(min_length=1, max_length=128)
    vai_tro: str
    rong_mm: Optional[float] = Field(None, gt=0)
    cao_mm: Optional[float] = Field(None, gt=0)
    ghi_chu: str = ""

    @model_validator(mode="after")
    def _check(self) -> "ConceptIn":
        allowed = concepts.LAYER_ROLES if self.tin_hieu == "layer" else concepts.BLOCK_ROLES
        if self.vai_tro not in allowed:
            raise ValueError(f"Vai trò của {self.tin_hieu} phải là {' | '.join(allowed)}.")
        if self.qu not in {c.ma for c in concepts.load_clauses()}:
            raise ValueError(f"Không có điều khoản {self.qu} trong quy ước.")
        self.ma, self.mau = self.ma.strip().upper(), self.mau.strip()
        if self.tin_hieu == "layer":     # match_layer so với tên đã bỏ dấu, chữ thường, _ và - đổi thành dấu cách
            self.mau = normalize(self.mau).replace("_", " ").replace("-", " ")
        return self


def _concept_session():
    if not get_database_url():
        raise HTTPException(409, "Chưa kết nối PostgreSQL (DATABASE_URL): chỉ xem được. Không có database thì sửa "
                                 "data/rules/concepts.csv bằng Excel.")
    from sqlalchemy.orm import Session

    from ..db.session import get_engine
    return Session(get_engine())


def _concept_changed(row) -> dict:
    concepts.load_signals.cache_clear()     # lần đọc bản vẽ sau dùng ngay ký hiệu mới
    return {c: getattr(row, c) for c in ConceptIn.model_fields}


@app.get("/api/concepts")
def concepts_list() -> dict:
    """Ký hiệu nhận dạng theo thứ tự ưu tiên (dòng khớp đầu tiên thắng) kèm danh sách vai trò, điều khoản cho biểu mẫu."""
    return {"source": "postgresql" if get_database_url() else "csv", "editable": bool(get_database_url()),
            "layer_roles": concepts.LAYER_ROLES, "block_roles": concepts.BLOCK_ROLES,
            "clauses": [{"ma": c.ma, "nhom": c.nhom} for c in concepts.load_clauses()],
            "signals": [asdict(s) for s in concepts.load_signals()], "conflicts": concepts.conflicts(),
            "rough_roles": concepts.ROUGH_ROLES, "images": _concept_images()}


@app.post("/api/concepts", dependencies=[Depends(require_admin)])
def concept_create(body: ConceptIn) -> dict:
    """Thêm ký hiệu vào cuối bảng (ưu tiên thấp nhất trong cùng loại tín hiệu)."""
    from ..db.models import DrawingConcept
    with _concept_session() as session:
        if session.query(DrawingConcept).filter_by(ma=body.ma).first():
            raise HTTPException(409, f"Mã {body.ma} đã có.")
        if bad := concepts.new_conflicts(body.model_dump()):
            raise HTTPException(409, "Ký hiệu " + "; ".join(bad) + ".")
        row = DrawingConcept(**body.model_dump())
        session.add(row)
        session.commit()
        return _concept_changed(row)


@app.put("/api/concepts/{ma}", dependencies=[Depends(require_admin)])
def concept_update(ma: str, body: ConceptIn) -> dict:
    """Sửa một ký hiệu, giữ nguyên vị trí ưu tiên."""
    from ..db.models import DrawingConcept
    with _concept_session() as session:
        row = session.query(DrawingConcept).filter_by(ma=ma).first()
        if row is None:
            raise HTTPException(404, f"Không có ký hiệu {ma}.")
        if body.ma != row.ma and session.query(DrawingConcept).filter_by(ma=body.ma).first():
            raise HTTPException(409, f"Mã {body.ma} đã có.")
        if bad := concepts.new_conflicts({**body.model_dump(), "ma": ma}):   # so ở vị trí cũ của ký hiệu đang sửa
            raise HTTPException(409, "Ký hiệu " + "; ".join(bad) + ".")
        for k, v in body.model_dump().items():
            setattr(row, k, v)
        session.commit()
        return _concept_changed(row)


@app.delete("/api/concepts/{ma}", dependencies=[Depends(require_admin)])
def concept_delete(ma: str) -> dict:
    from ..db.models import DrawingConcept
    with _concept_session() as session:
        row = session.query(DrawingConcept).filter_by(ma=ma).first()
        if row is None:
            raise HTTPException(404, f"Không có ký hiệu {ma}.")
        session.delete(row)
        session.commit()
        concepts.load_signals.cache_clear()
        return {"deleted": ma}


# hình minh họa người dùng đặt cho từng đối tượng (thẻ trên trang): file trong data/rules/hinh_ky_hieu, tên = khóa thẻ
IMG_DIR = config.DATA_DIR / "rules" / "hinh_ky_hieu"
IMG_TYPES = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
IMG_MAX_BYTES = 2 * 1024 * 1024


def _image_key(key: str) -> str:
    import re
    if not re.fullmatch(r"[a-z0-9_-]{1,80}", key):
        raise HTTPException(400, "Khóa hình chỉ gồm chữ thường không dấu, số, _ và -.")
    return key


def _image_file(key: str) -> Optional[Path]:
    return next((IMG_DIR / f"{key}{ext}" for ext in IMG_TYPES if (IMG_DIR / f"{key}{ext}").exists()), None)


def _concept_images() -> dict:
    """Khóa thẻ → đường dẫn hình (kèm thời điểm sửa để trình duyệt không dùng bản cũ)."""
    if not IMG_DIR.exists():
        return {}
    return {f.stem: f"/api/concepts/images/{f.stem}?v={int(f.stat().st_mtime)}" for f in IMG_DIR.iterdir() if f.suffix in IMG_TYPES}


def _save_image(key: str, ext: str, data: bytes) -> dict:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    for old in IMG_TYPES:                       # mỗi thẻ một hình: bỏ hình cũ khác định dạng
        (IMG_DIR / f"{key}{old}").unlink(missing_ok=True)
    (IMG_DIR / f"{key}{ext}").write_bytes(data)
    return {"key": key, "url": _concept_images()[key]}


@app.get("/api/concepts/images/{key}")
def concept_image(key: str) -> FileResponse:
    path = _image_file(_image_key(key))
    if path is None:
        raise HTTPException(404, f"Chưa có hình {key}.")
    # SVG tải lên có thể chứa mã: cấm chạy mã khi mở trực tiếp; trang hiển thị bằng <img> nên không chạy mã
    return FileResponse(path, media_type=IMG_TYPES[path.suffix],
                        headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
                                 "X-Content-Type-Options": "nosniff"})


@app.put("/api/concepts/images/{key}", dependencies=[Depends(require_admin)])
async def concept_image_upload(key: str, file: UploadFile = File(...)) -> dict:
    """Tải hình minh họa (SVG, PNG, JPG, WEBP, tối đa 2 MB) cho một thẻ ký hiệu."""
    key = _image_key(key)
    ext = Path(file.filename or "").suffix.lower().replace(".jpeg", ".jpg")
    if ext not in IMG_TYPES:
        raise HTTPException(400, "Chỉ nhận hình .svg, .png, .jpg, .webp.")
    data = await file.read(IMG_MAX_BYTES + 1)
    if len(data) > IMG_MAX_BYTES:
        raise HTTPException(413, "Hình lớn hơn 2 MB.")
    ok = {".png": data.startswith(b"\x89PNG"), ".jpg": data.startswith(b"\xff\xd8"),
          ".webp": data[:4] == b"RIFF" and data[8:12] == b"WEBP", ".svg": b"<svg" in data[:4096]}[ext]
    if not ok:
        raise HTTPException(400, f"Nội dung file không phải hình {ext}.")
    return _save_image(key, ext, data)


class ImageFromBlock(BaseModel):
    block: str = Field(min_length=1, max_length=128)


@app.put("/api/concepts/images/{key}/block", dependencies=[Depends(require_admin)])
def concept_image_from_block(key: str, body: ImageFromBlock) -> dict:
    """Dùng hình một block trong bản vẽ mẫu (data/drawings) làm hình minh họa của thẻ."""
    key = _image_key(key)
    svg = concept_samples.block_svg(body.block)
    if svg is None:
        raise HTTPException(404, f"Không có block {body.block} trong bản vẽ mẫu.")
    return _save_image(key, ".svg", svg.encode("utf8"))


@app.delete("/api/concepts/images/{key}", dependencies=[Depends(require_admin)])
def concept_image_delete(key: str) -> dict:
    """Bỏ hình đã đặt, thẻ quay về hình tự động."""
    path = _image_file(_image_key(key))
    if path is None:
        raise HTTPException(404, f"Chưa có hình {key}.")
    path.unlink()
    return {"deleted": key}


@app.get("/api/concepts/samples")
def concepts_samples() -> dict:
    """Hình mẫu từng ký hiệu (block vẽ lại từ bản vẽ mẫu) và tên block/layer thật khớp; lần đầu đọc bản vẽ mẫu ~20–40 s."""
    return concept_samples.samples()


@app.get("/api/concepts/csv", response_class=PlainTextResponse)
def concepts_csv() -> PlainTextResponse:
    """Bảng ký hiệu hiện hành dạng concepts.csv: chép đè data/rules/concepts.csv để init_db.py --reload-rules
    không làm mất các sửa đổi trên trang quản trị."""
    import csv
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, list(ConceptIn.model_fields), lineterminator="\n")
    w.writeheader()
    for s in concepts.load_signals():
        w.writerow({k: ("" if v is None else f"{v:g}" if isinstance(v, float) else v) for k, v in asdict(s).items()})
    return PlainTextResponse("﻿" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": 'attachment; filename="concepts.csv"'})


@app.post("/api/concepts/try")
async def concepts_try(file: UploadFile = File(...)) -> dict:
    """Chạy nhận diện với bảng ký hiệu hiện hành trên một bản vẽ: danh sách từng đối tượng và layer chưa có ký hiệu."""
    from hashlib import sha256
    from ..drawing.layer_inventory import layer_inventory

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        payload = await file.read()
        digest = sha256(payload).hexdigest()
        path.write_bytes(payload)
        del payload
        try:
            drawing = read_drawing(str(path))
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
    rows = list(list_objects(drawing, file.filename or path.name))
    unknown = sorted(n for n, c in drawing.layer_classes.items() if c.value == "UNKNOWN")
    return jsonable_encoder({"rows": rows, "unknown_layers": unknown,
                             "source": {"filename": file.filename, "sha256": digest},
                             "layers": layer_inventory(drawing)})


class GroundTruthPlan(BaseModel):
    version: int = 1
    file: str
    plan: str
    height_mm: float
    saved_at: str = ""
    walls: list[dict]
    removed: list[dict] = []
    openings: list[dict] = []


@app.post("/api/ground-truth")
def save_ground_truth(gt: GroundTruthPlan) -> dict:
    """Lưu mặt bằng đã sửa đúng làm đáp án nhận diện (data/ground_truth/plans), dùng cho scripts/evaluate_recognition.py."""
    import re
    import unicodedata

    from ..drawing import recognition_eval
    GT_PLANS_DIR = recognition_eval.GT_PLANS_DIR

    def slug(text: str) -> str:
        t = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")
        return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")[:80] or "ban_ve"
    GT_PLANS_DIR.mkdir(parents=True, exist_ok=True)
    path = GT_PLANS_DIR / f"{slug(Path(gt.file).stem)}_{slug(gt.plan)}.gt.json"
    path.write_text(json.dumps(gt.model_dump(), ensure_ascii=False, indent=1), encoding="utf8")
    shown = path.relative_to(config.ROOT) if path.is_relative_to(config.ROOT) else path
    return {"path": str(shown), "walls": len(gt.walls), "removed": len(gt.removed)}
