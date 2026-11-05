"""KD06: hàng chờ duyệt đề xuất AI. Duyệt = thêm một dòng quy tắc CSV, lần sau quy tắc khớp, không gọi AI nữa.

Hàng chờ: data/ai_de_xuat/queue.jsonl (mỗi dòng một đề xuất, trạng thái cho_duyet | da_duyet | tu_choi).
Mẫu quy tắc sinh từ trích đoạn đã chuẩn hóa (bỏ dấu, chữ thường), số thay bằng \\d+ để dùng lại cho bản vẽ khác.
"""
import csv
import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from .. import config
from .verify import norm

_LOCK = threading.Lock()
NUMBER = r"\d+(?:[.,]\d+)?"
RULES = config.DATA_DIR / "rules"
TARGETS = {   # task -> file quy tắc CSV nhận dòng mới khi duyệt
    "thong_so": "ghi_chu_thong_so.csv", "tieu_de_bang": "bang_thep.csv", "loai_ban_ve": "loai_ban_ve.csv",
    "ky_hieu": "ky_hieu_cau_kien.csv", "du_toan": "cong_tac_du_toan.csv",
}


def queue_path() -> Path:
    return Path(os.environ.get("OPTIMAT_AI_QUEUE") or config.DATA_DIR / "ai_de_xuat" / "queue.jsonl")


def pattern_of(excerpt: str) -> str:
    """Trích đoạn -> biểu thức chính quy trên chữ đã chuẩn hóa; số -> \\d+ (khớp cùng cách ghi, khác số)."""
    parts = re.split(NUMBER, norm(excerpt))
    return NUMBER.join(re.escape(p).replace(r"\ ", r"\s*") for p in parts)


def _id(task: str, label: str, excerpt: str) -> str:
    return hashlib.sha256(f"{task}|{label}|{pattern_of(excerpt)}".encode()).hexdigest()[:16]


def _read() -> list[dict]:
    try:
        lines = queue_path().read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _write(items: list[dict]) -> None:
    path = queue_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf-8")
    os.replace(tmp, path)


def enqueue(task: str, proposals: list[dict], source_file: str = "") -> None:
    """Thêm đề xuất mới (đã đạt kiểm chứng); trùng mẫu đã có thì chỉ tăng số lần gặp."""
    if not proposals:
        return
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        try:
            items = _read()
            index = {i["id"]: i for i in items}
            for p in proposals:
                pid = _id(task, p["label"], p["excerpt"])
                if pid in index:
                    index[pid]["seen"] = index[pid].get("seen", 1) + 1
                    continue
                item = {"id": pid, "task": task, "label": p["label"], "excerpt": p["excerpt"], "text": p.get("text", ""),
                        "pattern": pattern_of(p["excerpt"]), "source_file": source_file, "status": "cho_duyet",
                        "seen": 1, "created_at": now}
                items.append(item)
                index[pid] = item
            _write(items)
        except OSError:
            pass   # không ghi được hàng chờ thì bỏ qua; kết quả phân tích không phụ thuộc hàng chờ


def pending(task: str | None = None) -> list[dict]:
    return [i for i in _read() if i["status"] == "cho_duyet" and (task is None or i["task"] == task)]


def _append_csv(name: str, row: dict) -> None:
    path = RULES / name
    if not path.exists():
        header, prefix = list(row), ""
    else:
        raw = path.read_bytes()
        with path.open(encoding="utf-8-sig", newline="") as f:
            header = next(csv.reader(f))
        prefix = "" if raw.endswith(b"\n") else "\n"
    with path.open("a", encoding="utf-8", newline="") as f:
        f.write(prefix)
        if not path.stat().st_size:
            csv.writer(f).writerow(header)
        csv.writer(f).writerow([row.get(c, "") for c in header])


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _next_code(rows: list[dict], prefix: str) -> str:
    nums = [int(m.group(1)) for r in rows if (m := re.fullmatch(prefix + r"(\d+)", r.get("ma", "")))]
    return f"{prefix}{max(nums, default=0) + 1:02d}"


def rule_rows(item: dict, reviewer: str) -> list[tuple[str, dict]]:
    """Các dòng quy tắc CSV cho một đề xuất đã duyệt."""
    task, label, pattern = item["task"], item["label"], item["pattern"]
    note = f"AI đề xuất, {reviewer} duyệt {datetime.now().date().isoformat()}: \"{item['excerpt']}\""
    name = TARGETS[task]
    if task == "thong_so":
        return [(name, {"ma": _next_code(_rows(RULES / name), "TS"), "mau": pattern, "truong": label, "ghi_chu": note})]
    if task == "tieu_de_bang":
        return [(name, {"nhom": "cot_bang", "khoa": label, "mau": f"^{pattern}$", "ghi_chu": note})]
    if task == "loai_ban_ve":
        base = next(r for r in _rows(RULES / name) if r["ma"] == label)
        out = [(name, {**base, "mau": f"^{pattern}", "loai_tru": "", "ghi_chu": note})]
        if label == "BV01":   # mặt bằng kiến trúc: bộ tách mặt bằng tầng (plans.py) cũng nhận tiêu đề này
            plans_file = "tieu_de_mat_bang.csv"
            out.append((plans_file, {"ma": _next_code(_rows(RULES / plans_file), "MB"), "mau": f"^{pattern}",
                                     "ghi_chu": note}))
        return out
    if task == "ky_hieu":
        from .labels import ROLE_LABELS   # import muộn: labels -> ai -> review
        rows = _rows(RULES / name)
        m = re.match(r"[a-z]+", re.sub(r"\s+", "", norm(item["excerpt"])))
        if not m:
            raise ValueError("Ký hiệu không có phần chữ để lập mẫu.")
        letters = m.group(0)
        return [(name, {"ma": _next_code(rows, "K"), "mau": rf"{re.escape(letters)}\d+[a-z]?", "vai_tro": label,
                        "ten": ROLE_LABELS.get(label, label).lower(), "ghi_chu": note})]
    if task == "du_toan":
        return [(name, {"ma": _next_code(_rows(RULES / name), "DT"), "mau": pattern, "ma_cong_tac": label,
                        "ghi_chu": note})]
    raise ValueError(f"Không có tệp quy tắc cho loại đề xuất {task}.")


def _clear_rule_caches() -> None:
    from ..drawing import plans, registry, sheets
    from ..rough import rebar, structural
    from . import estimate, params
    for fn in (sheets.load_sheet_types, registry._element_rules, rebar.load_rules, plans.extra_plan_titles,
               params.load_rules, estimate.load_rules, getattr(structural, "load_element_rules", None)):
        if hasattr(fn, "cache_clear"):
            fn.cache_clear()


def decide(proposal_id: str, approve: bool, reviewer: str) -> dict:
    with _LOCK:
        items = _read()
        item = next((i for i in items if i["id"] == proposal_id), None)
        if item is None:
            raise KeyError("Không tìm thấy đề xuất.")
        if item["status"] != "cho_duyet":
            raise ValueError("Đề xuất đã được xử lý.")
        if approve:
            rows = rule_rows(item, reviewer)
            for _, row in rows:
                re.compile(row.get("mau", ""))   # mẫu lỗi thì dừng trước khi ghi tệp nào
            for name, row in rows:
                _append_csv(name, row)
            item["rules"] = [{"file": name, **row} for name, row in rows]
        item["status"] = "da_duyet" if approve else "tu_choi"
        item["reviewed_by"], item["reviewed_at"] = reviewer, datetime.now(timezone.utc).isoformat()
        _write(items)
    if approve:
        _clear_rule_caches()
    return item
