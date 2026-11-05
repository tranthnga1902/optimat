"""Router độc lập cho tư vấn client snapshot; phiên ràng buộc không xác minh hồ sơ."""
from __future__ import annotations

import os
import secrets
import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError

from optimat import config
from optimat.agent.llm import LLMUnavailable, llm_available
from optimat.agent.material_advisor import MaterialRequest, advise_materials
from optimat.api.auth import require_user
from optimat.catalog.repository import Catalog
from optimat.db.session import get_database_url

router = APIRouter(prefix="/api/assistant", tags=["Trợ lý vật liệu"])
COOKIE = "optimat_material_advisor"
_sessions: dict[str, dict] = {}
_lock = threading.Lock()
TTL = 600
MAX_CALLS = 6


def _allow(request: Request, user):
    origin = request.headers.get("origin")
    if origin not in {"http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:3001"}:
        raise HTTPException(403, "Nguồn yêu cầu trợ lý chưa được cho phép.")
    if not get_database_url():
        if os.environ.get("OPTIMAT_ASSISTANT_LOCAL_DEMO") != "1" or not request.client or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            raise HTTPException(403, "Trợ lý cục bộ chưa được mở cho phiên demo này.")
    elif not user:
        raise HTTPException(401, "Cần đăng nhập để dùng trợ lý.")


def _validate(payload: MaterialRequest):
    try:
        return payload.context()
    except ValueError as exc:
        raise HTTPException(422, "Ngữ cảnh hoặc phiên bản vật tư không hợp lệ; hãy tải lại bản đang xem.") from exc


@router.post("/material-session")
def material_session(payload: MaterialRequest, request: Request, response: Response, user=Depends(require_user)):
    _allow(request, user)
    context = _validate(payload)
    now = time.monotonic()
    with _lock:
        for token in list(_sessions):
            if _sessions[token]["expires"] <= now:
                del _sessions[token]
        if len(_sessions) >= 128:
            raise HTTPException(429, "Đang có nhiều phiên trợ lý; hãy thử lại sau.")
        token = secrets.token_urlsafe(32)
        _sessions[token] = {"hash": payload.contextHash, "binding": context.binding.model_dump(),
                            "uid": user["user_id"] if user else None, "expires": now + TTL, "calls": 0, "busy": False}
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", secure=request.url.scheme == "https", max_age=TTL, path="/api/assistant")
    return {"contextHash": payload.contextHash, "binding": context.binding.model_dump(), "provenance": "client_snapshot",
            "warning": "Phiên chỉ ràng buộc nội dung do trình duyệt cung cấp; chưa xác minh quyền sở hữu hoặc nguồn bản vẽ."}


@router.post("/materials")
def materials(payload: MaterialRequest, request: Request, user=Depends(require_user)):
    _allow(request, user)
    context = _validate(payload)
    token = request.cookies.get(COOKIE, "")
    uid = user["user_id"] if user else None
    with _lock:
        session = _sessions.get(token)
        if not session or session["expires"] <= time.monotonic() or session["uid"] != uid:
            raise HTTPException(401, "Phiên trợ lý đã hết hiệu lực; hãy mở lại từ bản đang xem.")
        if session["hash"] != payload.contextHash or session["binding"] != context.binding.model_dump():
            raise HTTPException(409, "Bản công tác/vật tư đã đổi; hãy mở lại trợ lý từ bản hiện hành.")
        if session["busy"] or session["calls"] >= MAX_CALLS:
            raise HTTPException(429, "Đang xử lý hoặc đã hết lượt của phiên trợ lý.")
        if config.LLM_PROVIDER != "openai" or not llm_available():
            raise HTTPException(503, "Trợ lý chưa được cấu hình trên máy chủ. Không gửi khóa API qua hội thoại.")
        session["busy"] = True
        session["calls"] += 1
    try:
        return advise_materials(payload, Catalog.load())
    except LLMUnavailable as exc:
        raise HTTPException(503, "Chưa kết nối được trợ lý. Hãy thử lại sau; bản khối lượng vẫn được giữ nguyên.") from exc
    except ValueError as exc:
        raise HTTPException(502, "Trợ lý chưa trả lời hợp lệ; chưa có đề xuất được áp dụng.") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Chưa đọc được danh mục để tư vấn; hãy thử lại sau.") from exc
    finally:
        with _lock:
            session["busy"] = False
