"""KD06: API hàng chờ duyệt đề xuất AI. Chỉ quản trị viên; duyệt = thêm dòng quy tắc CSV (facts/review.py)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from ..facts import review
from .auth import require_admin

router = APIRouter()


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approve: bool


@router.get("/api/admin/ai-proposals")
def list_proposals(task: str | None = None, user: dict | None = Depends(require_admin)) -> dict:
    return {"items": review.pending(task), "targets": review.TARGETS,
            "notice": "Đề xuất đã qua kiểm chứng (nhãn trong danh mục, trích đoạn có thật trong nguồn) nhưng chưa dùng để "
                      "tính. Duyệt sẽ thêm một dòng quy tắc CSV; đồng bộ CSV vào PostgreSQL theo quy trình dữ liệu."}


@router.post("/api/admin/ai-proposals/{proposal_id}")
def decide(proposal_id: str, body: Decision, user: dict | None = Depends(require_admin)) -> dict:
    reviewer = (user or {}).get("email") or "admin"
    try:
        return review.decide(proposal_id, body.approve, reviewer)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except (ValueError, StopIteration) as exc:
        raise HTTPException(409, f"Không duyệt được: {exc}") from exc
