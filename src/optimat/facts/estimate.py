"""KD07: dự toán XLSX/XLS đính kèm (tùy chọn) → mã công tác, để đối chiếu với khối lượng hệ thống tính.

Dòng dự toán chỉ dùng ĐỐI CHIẾU, không làm nguồn số của bảng tiên lượng. Quy tắc data/rules/cong_tac_du_toan.csv khớp
trước, còn lại AI gắn mã (danh mục WORKS + OUT); khối lượng luôn lấy từ ô Excel của dòng đó, không lấy từ AI.
"""
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .. import config
from ..rough.models import WORKS
from . import ai
from .verify import norm

RULE_FILE = config.DATA_DIR / "rules" / "cong_tac_du_toan.csv"
OUT = "OUT"
INSTRUCTIONS = ("Đây là tên công tác trong bảng dự toán/tiên lượng nhà ở. Gắn mã công tác phần thô tương ứng; công tác "
                "hoàn thiện, điện nước, thiết bị, vận chuyển… gắn OUT. excerpt là toàn bộ tên công tác.")


@lru_cache(maxsize=2)
def load_rules(path: str | None = None) -> tuple[tuple[str, re.Pattern, str], ...]:
    rows = pd.read_csv(Path(path or RULE_FILE), dtype=str, keep_default_na=False).to_dict("records")
    bad = [r["ma"] for r in rows if r["ma_cong_tac"] not in WORKS and r["ma_cong_tac"] != OUT]
    if bad:
        raise ValueError(f"cong_tac_du_toan.csv: mã công tác không hợp lệ ở {', '.join(bad)}.")
    return tuple((r["ma"], re.compile(r["mau"]), r["ma_cong_tac"]) for r in rows)


def unit_of(text) -> str:
    """Đơn vị Excel về cách viết của WORKS (m3 -> m³, m2 -> m², T -> tấn)."""
    u = norm(str(text or "")).replace(" ", "")
    return {"m3": "m³", "m2": "m²", "t": "tấn", "tan": "tấn", "kg": "kg", "m": "m"}.get(u, str(text or "").strip())


def _number(text):
    if text in (None, ""):
        return None
    try:
        return float(str(text).replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def map_rows(candidates: list[dict], source_file: str, allow_ai: bool) -> dict:
    """candidates: kết quả spreadsheet_candidates()['candidates']. Thêm work_code + cách gắn cho từng dòng."""
    rows, rest = [], []
    for i, c in enumerate(candidates):
        name = c["fields"].get("work") or ""
        row = {**c, "row_ref": f"r{i}", "work_code": None, "work_method": None, "work_rule": None,
               "quantity_value": _number(c["fields"].get("quantity"))}
        hit = next(((ma, code) for ma, pat, code in load_rules() if pat.search(norm(name))), None)
        if hit:
            row.update(work_code=hit[1], work_method="rule", work_rule=hit[0])
        elif name:
            rest.append({"ref": row["row_ref"], "text": name})
        rows.append(row)
    labels = {**{k: v[0] for k, v in WORKS.items()}, OUT: "Ngoài phần thô (hoàn thiện, điện nước, thiết bị…)"}
    accepted, rejected, meta = ai.label("du_toan", INSTRUCTIONS, rest, labels, allow_ai, source_file)
    by_ref = {r["row_ref"]: r for r in rows}
    for p in accepted:
        by_ref[p["ref"]].update(work_code=p["label"], work_method="ai_label")
    totals = defaultdict(float)
    for r in rows:
        if r["work_code"] not in (None, OUT) and r["quantity_value"] is not None:
            totals[(r["work_code"], unit_of(r["fields"].get("unit")))] += r["quantity_value"]
    return {"rows": rows, "rejected": rejected, "ai": meta,
            "totals": [{"code": k[0], "unit": k[1], "quantity": round(v, 3)} for k, v in sorted(totals.items())],
            "notice": "Dòng dự toán chỉ để đối chiếu; chưa xác định dòng tổng/phần con nên có thể cộng trùng, cần xem lại."}


def compare(estimate_totals: list[dict], rough_totals: list[dict]) -> list[dict]:
    """Đối chiếu tổng theo mã công tác (cùng đơn vị). rough_totals: RoughResult.totals."""
    system = {(t["code"], t["unit"]): t for t in rough_totals}
    out = []
    for e in estimate_totals:
        s = system.get((e["code"], e["unit"]))
        q = s.get("quantity") if s else None
        out.append({**e, "system_quantity": q,
                    "diff_pct": round((q - e["quantity"]) / e["quantity"] * 100, 1) if q is not None and e["quantity"] else None,
                    "note": "" if s else "hệ thống không có dòng cùng mã và đơn vị"})
    return out

