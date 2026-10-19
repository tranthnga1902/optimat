"""API của OptiMat AI.

Chạy:  uvicorn optimat.api.main:app --reload --app-dir src
Tài liệu thử nghiệm tự sinh tại http://localhost:8000/docs
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, Field, model_validator

from fastapi.encoders import jsonable_encoder

from .admin_db import router as admin_router
from ..agent.llm import ParsedConstraints, llm_available, parse_constraints
from ..agent.orchestrator import run_agent
from ..agent.pipeline import run_pipeline
from ..catalog.pricing import BillLine, bill_of_materials
from .. import config
from ..catalog.repository import Catalog
from ..data_check import run_checks
from ..db.session import get_database_url
from ..drawing import concepts, dwg_convert
from ..drawing.dwg_convert import DrawingError
from ..drawing.dxf_reader import read_drawing
from ..drawing.encoding import normalize
from ..drawing.objects import list_objects
from ..drawing.review import ReviewPlan, ReviewResult, compute_review, save_review
from ..drawing.takeoff import takeoff_from_file, takeoff_plans, takeoff_plans_from_file
from ..drawing.viewer import build_review_html, material_options, view_payload
from ..optimize.problem import optimize
from ..predict.cost_model import MaterialPriceModel
from ..rough.models import ProjectParams
from ..rough.takeoff import RoughRequest, RoughResult, compute_rough, rough_from_drawing, save_rough
from ..schemas import Constraints, OpeningDefaults, OptimizeResult, PlanTakeoff, TakeoffResult, WallGroup

app = FastAPI(title="OptiMat AI", version="0.1.0")
app.include_router(admin_router)     # quản trị cơ sở dữ liệu (api/admin_db.py)
# Cho phép giao diện React chạy ở cổng khác gọi vào khi phát triển.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])


class OptimizeRequest(BaseModel):
    groups: list[WallGroup]
    constraints: Constraints = Constraints()
    method: str = "auto"


class BillRequest(BaseModel):
    groups: list[WallGroup]


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
                  layer_overrides: str | None = Form(None), project_id: int | None = Form(None)) -> TakeoffResult:
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
            return takeoff_from_file(str(path), height, overrides, openings)
        except DrawingError as exc:  # thiếu ODA File Converter, file hỏng, định dạng sai
            raise HTTPException(422, str(exc)) from exc


@app.get("/ui/takeoff", response_class=HTMLResponse)
def review_page() -> str:
    """Trang Kiểm tra bóc tách: bản vẽ bên trái, danh sách nhận dạng bên phải; sửa, bổ sung rồi xác nhận."""
    return build_review_html()


@app.post("/api/takeoff/view")
async def takeoff_view(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                       layer_overrides: str | None = Form(None), project_id: int | None = Form(None)) -> dict:
    """Dữ liệu cho trang Kiểm tra bóc tách: nét bản vẽ đã tách theo mặt bằng kèm kết quả nhận dạng."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    try:
        overrides = json.loads(layer_overrides) if layer_overrides else None
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "layer_overrides phải là chuỗi JSON hợp lệ.") from exc
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        try:
            drawing = read_drawing(str(path), overrides)
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
    height, openings = _project_inputs(project_id, floor_height_mm)
    plans = takeoff_plans(drawing, height, Catalog.load(), openings)
    return view_payload(drawing, plans, file.filename or path.name)


@app.post("/api/takeoff/confirm", response_model=ReviewResult)
def takeoff_confirm(plan: ReviewPlan) -> ReviewResult:
    """Chốt kết quả sau khi người dùng sửa, bổ sung: máy chủ tính lại khối lượng bằng một công thức duy nhất."""
    try:
        result = compute_review(plan)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        result.takeoff_id = save_review(result, plan)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return result


@app.post("/api/takeoff/rough/auto")
async def takeoff_rough_auto(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                             params: str | None = Form(None), layer_overrides: str | None = Form(None),
                             project_id: int | None = Form(None)) -> dict:
    """Bóc phần thô từ nhận dạng tự động. params: chuỗi JSON thông số công trình (ProjectParams), trống được.
    Trả {"request": đầu vào đã dựng (tường, cửa, cột, tên phòng từng mặt bằng) để sửa, "result": bảng phần thô}."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    try:
        overrides = json.loads(layer_overrides) if layer_overrides else None
        project = ProjectParams(**json.loads(params)) if params else ProjectParams()
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(400, f"params hoặc layer_overrides không hợp lệ: {exc}") from exc
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        try:
            drawing = read_drawing(str(path), overrides)
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
    catalog = Catalog.load()
    height, openings = _project_inputs(project_id, floor_height_mm)
    req = rough_from_drawing(drawing, project, height, catalog, file.filename or path.name, openings)
    try:
        result = compute_rough(req, catalog)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"request": jsonable_encoder(req), "result": jsonable_encoder(result)}


@app.post("/api/takeoff/rough", response_model=RoughResult)
def takeoff_rough(req: RoughRequest) -> RoughResult:
    """Chốt bảng phần thô từ dữ liệu đã sửa (mọi mặt bằng + thông số công trình); lưu takeoff_results khi có dự án."""
    try:
        result = compute_rough(req)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        result.takeoff_id = save_rough(result, req)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    return result


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


@app.post("/api/price/bill", response_model=list[BillLine])
def price_bill(req: BillRequest) -> list[BillLine]:
    """Bảng vật liệu theo thiết kế (gạch + vữa) và giá đang có, cho các nhóm tường đã chốt."""
    return bill_of_materials(req.groups, Catalog.load())


@app.post("/api/takeoff/plans", response_model=list[PlanTakeoff])
async def takeoff_plans_api(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                        layer_overrides: str | None = Form(None), project_id: int | None = Form(None)) -> list[PlanTakeoff]:
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
            return takeoff_plans_from_file(str(path), height, overrides, openings)
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc


@app.post("/api/constraints/parse", response_model=ParsedConstraints)
def parse(req: ParseRequest) -> ParsedConstraints:
    return parse_constraints(req.message, req.use_llm)


@app.post("/api/optimize", response_model=OptimizeResult)
def run_optimize(req: OptimizeRequest) -> OptimizeResult:
    try:
        return optimize(req.groups, req.constraints, Catalog.load(), MaterialPriceModel.load(), req.method)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/agent/run")
async def agent_run(file: UploadFile = File(...), message: str = Form(""), floor_height_mm: float | None = Form(None),
                    use_llm: bool = Form(True), rough_params: str | None = Form(None)) -> dict:
    """Chạy trọn luồng: đo bóc -> vật liệu theo thiết kế và giá -> (phần thô) -> ràng buộc -> tối ưu -> giải thích.
    Có mô hình ngôn ngữ thì agent gọi công cụ; không có (hoặc use_llm=false) thì chạy luồng cố định.
    rough_params: chuỗi JSON thông số công trình; có thì luồng cố định bóc thêm phần thô."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    try:
        rough = ProjectParams(**json.loads(rough_params)) if rough_params else None
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(400, f"rough_params không hợp lệ: {exc}") from exc
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        try:
            if use_llm and llm_available():
                out = run_agent(str(path), message, floor_height_mm, rough_params=rough)
            else:
                state = run_pipeline(str(path), message=message or None, floor_height_mm=floor_height_mm, use_llm=False,
                                     rough_params=rough)
                out = {"mode": "pipeline", "answer": state["explanation"], "takeoff": state["takeoff"],
                       "result": state["result"], "constraints": state["constraints"], "bill": state["bill"],
                       "questions": state["questions"], "rough": state.get("rough")}
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
    return jsonable_encoder(out)


# ------------------------------------------------------------------ giao diện chung và quản trị dữ liệu
APP_HTML = Path(__file__).resolve().parents[1] / "web" / "app.html"


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse("/app")


@app.get("/app", response_class=HTMLResponse)
def app_page() -> str:
    """Giao diện chung (theo mockup): người dùng (bóc tách, vật liệu và giá, tối ưu, trợ lý) và quản trị (kiểm soát dữ liệu)."""
    return APP_HTML.read_text(encoding="utf8")


@app.get("/api/data/check")
def data_check() -> dict:
    """Kiểm soát dữ liệu: lỗi cấu trúc, số liệu còn trống, dữ liệu mẫu, giá cũ, đáp án đo tay. Chỉ đọc."""
    return run_checks()


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
            "signals": [asdict(s) for s in concepts.load_signals()]}


@app.post("/api/concepts")
def concept_create(body: ConceptIn) -> dict:
    """Thêm ký hiệu vào cuối bảng (ưu tiên thấp nhất trong cùng loại tín hiệu)."""
    from ..db.models import DrawingConcept
    with _concept_session() as session:
        if session.query(DrawingConcept).filter_by(ma=body.ma).first():
            raise HTTPException(409, f"Mã {body.ma} đã có.")
        row = DrawingConcept(**body.model_dump())
        session.add(row)
        session.commit()
        return _concept_changed(row)


@app.put("/api/concepts/{ma}")
def concept_update(ma: str, body: ConceptIn) -> dict:
    """Sửa một ký hiệu, giữ nguyên vị trí ưu tiên."""
    from ..db.models import DrawingConcept
    with _concept_session() as session:
        row = session.query(DrawingConcept).filter_by(ma=ma).first()
        if row is None:
            raise HTTPException(404, f"Không có ký hiệu {ma}.")
        if body.ma != row.ma and session.query(DrawingConcept).filter_by(ma=body.ma).first():
            raise HTTPException(409, f"Mã {body.ma} đã có.")
        for k, v in body.model_dump().items():
            setattr(row, k, v)
        session.commit()
        return _concept_changed(row)


@app.delete("/api/concepts/{ma}")
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
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        try:
            drawing = read_drawing(str(path))
        except DrawingError as exc:
            raise HTTPException(422, str(exc)) from exc
    rows = list(list_objects(drawing, file.filename or path.name))
    unknown = sorted(n for n, c in drawing.layer_classes.items() if c.value == "UNKNOWN")
    return jsonable_encoder({"rows": rows, "unknown_layers": unknown})


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
