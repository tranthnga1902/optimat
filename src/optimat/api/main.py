"""API của OptiMat AI.

Chạy:  uvicorn optimat.api.main:app --reload --app-dir src
Tài liệu thử nghiệm tự sinh tại http://localhost:8000/docs
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from fastapi.encoders import jsonable_encoder

from ..agent.llm import ParsedConstraints, llm_available, parse_constraints
from ..agent.orchestrator import run_agent
from ..agent.pipeline import run_pipeline
from ..catalog.pricing import BillLine, bill_of_materials
from .. import config
from ..catalog.repository import Catalog
from ..data_check import run_checks
from ..db.session import get_database_url
from ..drawing import dwg_convert
from ..drawing.dwg_convert import DrawingError
from ..drawing.dxf_reader import read_drawing
from ..drawing.review import ReviewPlan, ReviewResult, compute_review, save_review
from ..drawing.takeoff import takeoff_from_file, takeoff_plans, takeoff_plans_from_file
from ..drawing.viewer import build_review_html, material_options, view_payload
from ..optimize.problem import optimize
from ..predict.cost_model import MaterialPriceModel
from ..schemas import Constraints, OptimizeResult, PlanTakeoff, TakeoffResult, WallGroup

app = FastAPI(title="OptiMat AI", version="0.1.0")
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


@app.post("/api/takeoff", response_model=TakeoffResult)
async def takeoff(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                  layer_overrides: str | None = Form(None)) -> TakeoffResult:
    """Nhận .dxf hoặc .dwg. layer_overrides: chuỗi JSON dạng {"tên layer": "WALL"} để ghi đè vai trò layer."""
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
            return takeoff_from_file(str(path), floor_height_mm, overrides)
        except DrawingError as exc:  # thiếu ODA File Converter, file hỏng, định dạng sai
            raise HTTPException(422, str(exc)) from exc


@app.get("/ui/takeoff", response_class=HTMLResponse)
def review_page() -> str:
    """Trang Kiểm tra bóc tách: bản vẽ bên trái, danh sách nhận dạng bên phải; sửa, bổ sung rồi xác nhận."""
    return build_review_html()


@app.post("/api/takeoff/view")
async def takeoff_view(file: UploadFile = File(...), floor_height_mm: float | None = Form(None),
                       layer_overrides: str | None = Form(None)) -> dict:
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
    plans = takeoff_plans(drawing, floor_height_mm, Catalog.load())
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
                        layer_overrides: str | None = Form(None)) -> list[PlanTakeoff]:
    """File có nhiều mặt bằng: tách theo tiêu đề "MẶT BẰNG TẦNG ..." và đo bóc từng mặt bằng.
    Chiều cao tầng suy từ cao độ sàn trên bản vẽ khi không nhập. Danh sách rỗng: file không có mặt bằng kiến trúc."""
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
            return takeoff_plans_from_file(str(path), floor_height_mm, overrides)
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
                    use_llm: bool = Form(True)) -> dict:
    """Chạy trọn luồng: đo bóc -> vật liệu theo thiết kế và giá -> ràng buộc -> tối ưu -> giải thích.
    Có mô hình ngôn ngữ thì agent gọi công cụ; không có (hoặc use_llm=false) thì chạy luồng cố định."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".dxf", ".dwg"):
        raise HTTPException(400, "Chỉ nhận file .dxf hoặc .dwg.")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(await file.read())
        try:
            if use_llm and llm_available():
                out = run_agent(str(path), message, floor_height_mm)
            else:
                state = run_pipeline(str(path), message=message or None, floor_height_mm=floor_height_mm, use_llm=False)
                out = {"mode": "pipeline", "answer": state["explanation"], "takeoff": state["takeoff"],
                       "result": state["result"], "constraints": state["constraints"], "bill": state["bill"],
                       "questions": state["questions"]}
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
