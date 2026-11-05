"""KD04 tiêu đề cột bảng thống kê thép, KD05 tiêu đề tờ/mặt bằng tầng và ký hiệu cấu kiện chưa có quy tắc.

Chỉ lấy mục quy tắc CSV chưa khớp → AI gắn nhãn danh mục đóng → kiểm chứng → hàng chờ duyệt. Đề xuất chưa duyệt
KHÔNG đổi kết quả tính; duyệt xong thành dòng CSV (bang_thep, loai_ban_ve + tieu_de_mat_bang, ky_hieu_cau_kien).
"""
import re
from collections import Counter

from ..drawing import sheets
from ..drawing.encoding import normalize
from ..drawing.registry import SYMBOL_LIKE, floors_of, match_symbol, symbol_key
from ..rough import rebar
from . import Fact, FactReport, ai
from .verify import norm

HEADER_LABELS = {
    "cau_kien": "Tên/ký hiệu cấu kiện", "so_hieu": "Số hiệu thanh thép", "hinh_dang": "Hình dạng thanh",
    "duong_kinh": "Đường kính thép (Ø)", "chieu_dai": "Chiều dài cắt 1 thanh", "sl_1ck": "Số thanh trong 1 cấu kiện",
    "so_ck": "Số cấu kiện", "tong_thanh": "Tổng số thanh", "khoi_luong": "Khối lượng / trọng lượng (kg)",
}
TITLE_HINT = re.compile(r"^(mat bang|mb|chi tiet|ct|mat cat|mc|mat dung|md|mat tien|mat ben|bang thong ke|thong ke"
                        r"|bo tri|trien khai|so do|ket cau|kien truc|tang|lau|tret)\b")
ROLE_LABELS = {"COLUMN": "Cột", "BEAM": "Dầm, đà kiềng, giằng móng", "FOUNDATION": "Móng", "SLAB": "Ô sàn",
               "LINTEL": "Lanh tô", "WALL_TIE": "Giằng tường", "GUTTER": "Sê nô", "STAIR": "Bản thang, cầu thang"}


def _merge(report: FactReport, other: FactReport, task: str) -> None:
    report.facts += other.facts
    report.rejected += other.rejected
    report.ai[task] = other.ai


def rebar_header_items(drawing) -> list[dict]:
    """Ô chữ dưới tiêu đề bảng thép không đọc được tiêu đề cột: ô không phải số, chưa khớp bang_thep.csv."""
    out, seen = [], set()
    for title in (t for t in drawing.texts if rebar.TITLE_RE.search(normalize(t.text))):
        rows, warnings = rebar.read_table(drawing, title)
        if rows or not any("không thấy dòng tiêu đề cột" in w for w in warnings):
            continue
        h = title.height or 1.0
        for i, t in enumerate(drawing.texts):
            if not (t.y < title.y and title.y - t.y < 12 * h and abs(t.x - title.x) < 60 * h):
                continue
            key = normalize(t.text).strip()
            if (not key or key in seen or rebar._num(t.text) is not None or len(key) > 40
                    or rebar._header([t])):
                continue
            seen.add(key)
            out.append({"ref": f"t{i}", "text": t.text.strip()})
    return out


def title_items(drawing, need_plan: bool) -> list[dict]:
    """Tiêu đề hình vẽ chưa nhận loại (loai_ban_ve.csv). need_plan: file chưa tách được mặt bằng tầng nào."""
    out, seen = [], set()
    for i, t in enumerate(drawing.texts):
        key = re.sub(r"\s+", " ", normalize(t.text)).strip()
        if not (4 <= len(key) <= 80) or key in seen or not TITLE_HINT.search(key):
            continue
        if sheets.sheet_type_of(t.text) and not need_plan:
            continue
        seen.add(key)
        out.append({"ref": f"t{i}", "text": t.text.strip()})
    return out


def symbol_items(drawing, limit: int = 80) -> list[dict]:
    """Ký hiệu dạng chữ+số chưa khớp ky_hieu_cau_kien.csv, gặp ≥ 2 lần (bớt nhãn trục, ghi chú lẻ)."""
    counts, first = Counter(), {}
    for i, t in enumerate(drawing.texts):
        key = symbol_key(t.text)
        if SYMBOL_LIKE.fullmatch(key) and match_symbol(t.text) is None and not floors_of(t.text):
            prefix = re.sub(r"\d.*", "", key)
            counts[prefix] += 1
            first.setdefault(prefix, (i, t.text.strip()))
    return [{"ref": f"t{first[p][0]}", "text": first[p][1]} for p, n in counts.most_common(limit) if n >= 2]


def _sheet_labels() -> dict[str, str]:
    return {st.ma: st.ten for st in sheets.load_sheet_types()}


def label_drawing(drawing, source_file: str, allow_ai: bool, need_plan: bool = False) -> FactReport:
    report = FactReport()
    jobs = [
        ("tieu_de_bang", rebar_header_items(drawing), HEADER_LABELS,
         "Đây là ô tiêu đề cột của bảng thống kê cốt thép. Gắn nhãn vai trò cột; excerpt là toàn bộ chữ của ô."),
        ("loai_ban_ve", title_items(drawing, need_plan), _sheet_labels(),
         "Đây là tiêu đề hình vẽ trong hồ sơ thiết kế. Gắn loại hình vẽ; excerpt là toàn bộ tiêu đề (bỏ phần tỷ lệ)."),
        ("ky_hieu", symbol_items(drawing), ROLE_LABELS,
         "Đây là ký hiệu cấu kiện trên bản vẽ kết cấu (chữ + số). Chỉ gắn khi chắc là ký hiệu cấu kiện; "
         "bỏ qua tên trục, mã cửa, số phòng. excerpt là chính ký hiệu."),
    ]
    for task, items, labels, instructions in jobs:
        accepted, rejected, meta = ai.label(task, instructions, items, labels, allow_ai, source_file)
        part = FactReport(rejected=rejected, ai=meta)
        part.facts = [Fact(field=p["label"], task=task, source_file=source_file, ref=p["ref"], excerpt=p["excerpt"],
                           method="ai_label", note="Đề xuất chờ duyệt; chưa dùng để tính.") for p in accepted]
        _merge(report, part, task)
    return report

