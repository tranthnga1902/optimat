"""KD07: gom thông số còn thiếu của mọi công tác thành MỘT danh sách câu hỏi cho người dùng (không điền mặc định, B7)."""
from pydantic import BaseModel, Field


class MissingInput(BaseModel):
    input: str                                      # thông số thiếu, đúng chữ của WorkItem.missing
    works: list[str] = Field(default_factory=list)  # mã công tác bị trống vì thiếu thông số này
    plans: list[str] = Field(default_factory=list)  # mặt bằng liên quan
    count: int = 0                                  # số dòng công tác bị ảnh hưởng: hỏi thông số nào trước


def missing_inputs(works) -> list[MissingInput]:
    found: dict[str, MissingInput] = {}
    for work in works:
        for reason in dict.fromkeys(m.strip() for m in work.missing if m.strip()):
            item = found.setdefault(reason, MissingInput(input=reason))
            item.count += 1
            if work.code not in item.works:
                item.works.append(work.code)
            if work.plan and work.plan not in item.plans:
                item.plans.append(work.plan)
    return sorted(found.values(), key=lambda m: (-m.count, m.input))
