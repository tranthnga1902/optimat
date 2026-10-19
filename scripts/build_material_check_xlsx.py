"""Sinh file Excel đối chiếu định nghĩa vật liệu với bản vẽ: docs/du-lieu/OptiMat AI - Doi chieu vat lieu ban ve.xlsx

    python scripts/build_material_check_xlsx.py [bản vẽ ...]      # mặc định: mọi .dxf trong data/drawings/build

Sheet "Định nghĩa": quy tắc vật liệu đang chạy (data/rules/material_rules.csv + tên gọi khác của danh mục).
Sheet "Đối chiếu": tín hiệu vật liệu tìm thấy trên bản vẽ (chữ, hatch, layer, block) và kết quả hệ thống gán; người kiểm tra
chọn vật liệu đúng ở cột vàng, cột "Kết quả" tự so. Sheet "Tổng hợp": tỷ lệ đúng theo bản vẽ (công thức).
Sinh lại sau khi sửa quy tắc; phần người kiểm tra đã nhập ở file cũ không được giữ, nên lưu file cũ với tên khác trước.
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

from optimat.catalog.repository import default_catalog  # noqa: E402
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.drawing.encoding import normalize  # noqa: E402
from optimat.drawing.layer_classifier import LayerClass  # noqa: E402
from optimat.drawing.material_notes import load_note_rules, match_note  # noqa: E402
from optimat.drawing.material_rules import MATERIAL_HINTS, _best, all_rules, rule_label  # noqa: E402
from optimat.drawing.plans import find_plans  # noqa: E402
from optimat.drawing.takeoff import takeoff_plans  # noqa: E402

OUT = ROOT / "docs" / "du-lieu" / "OptiMat AI - Doi chieu vat lieu ban ve.xlsx"
OUTSIDE = "Ngoài mặt bằng (ghi chú chung, khung tên)"
NOT_MATERIAL = "KHONG_PHAI_VAT_LIEU"
FONT, BOLD = Font(name="Arial", size=10), Font(name="Arial", size=10, bold=True)
HEAD = PatternFill("solid", fgColor="DDE4EA")
INPUT = PatternFill("solid", fgColor="FFFF00")
SIGNAL_VI = {"text": "Chữ ghi chú", "hatch": "Mẫu hatch", "layer": "Tên layer", "block": "Tên block"}


# Danh mục vật liệu phần thô – móng và thân (39 mục, file Danh-muc-vat-lieu-phan-tho.pdf): STT -> (tên, đơn vị, cách xác định
# khối lượng, mã danh mục tương ứng). Mục không có mã là vật liệu chưa có trong danh mục.
PHAN_THO = {
    1: ("Xi măng PCB30 / PCB40", "tấn", "Định mức, từ m³ bê tông + m³ vữa", ["XM01", "XM02"]),
    2: ("Cát vàng", "m³", "Định mức, từ m³ bê tông", ["CA01"]),
    3: ("Cát đen (cát xây)", "m³", "Định mức, từ m³ vữa xây – trát – cán nền", ["CA02"]),
    4: ("Cát san lấp, cát đệm", "m³", "Bóc trực tiếp", ["CA03"]),
    5: ("Đá 1×2", "m³", "Định mức, từ m³ bê tông", ["DA01"]),
    6: ("Đá 4×6", "m³", "Bóc trực tiếp (bê tông lót)", ["DA03"]),
    7: ("Đá mi / đá bụi", "m³", "Bóc trực tiếp (đệm nền)", ["DA04"]),
    8: ("Bê tông thương phẩm M250/M300/M350", "m³", "Bóc trực tiếp", ["BT03", "BT04"]),
    9: ("Thép tròn trơn D ≤ 10 (CB240-T)", "tấn", "Bảng thống kê thép", ["TH01"]),
    10: ("Thép vằn D ≤ 18 (CB300-V / CB400-V)", "tấn", "Bảng thống kê thép", ["TH02", "TH07"]),
    11: ("Thép vằn D > 18 (CB400-V)", "tấn", "Bảng thống kê thép", ["TH03", "TH08"]),
    12: ("Thép hình (I, H, U, V, hộp)", "tấn", "Bản vẽ kết cấu thép", ["TH04", "TH09"]),
    13: ("Xà gồ C / Z mạ kẽm", "md, kg", "Chi tiết mái", ["TH05"]),
    14: ("Bu lông, ốc vít liên kết", "bộ, kg", "Chi tiết liên kết", ["LK01"]),
    15: ("Que hàn", "kg", "Định mức theo md đường hàn", ["LK02"]),
    16: ("Sơn chống gỉ", "m², kg", "m² bề mặt thép", ["LK03"]),
    17: ("Dây thép buộc 1 ly", "kg", "1–2% khối lượng cốt thép", ["TH10"]),
    18: ("Gạch tuynel (2 lỗ / 4 lỗ / 6 lỗ / đặc)", "viên", "Định mức, từ m³ tường", ["GN01", "GN02", "GN03"]),
    19: ("Gạch không nung / block bê tông", "viên", "Định mức, từ m³ tường", ["GK01", "GK02", "GK03", "GK04"]),
    20: ("Gạch AAC", "viên, m³", "Định mức, từ m³ tường", ["AAC01", "AAC02", "AAC03"]),
    21: ("Màng khò nóng (bitum)", "m²", "Bóc trực tiếp", ["CT01"]),
    22: ("Màng tự dính", "m²", "Bóc trực tiếp", ["CT04"]),
    23: ("Chống thấm gốc xi măng 2 thành phần", "kg", "m² × định mức hãng", ["CT02"]),
    24: ("Chống thấm gốc PU / Polyurea", "kg", "m² × định mức hãng", ["CT03"]),
    25: ("Băng cản nước (waterstop)", "md", "Chiều dài mạch ngừng", ["CT05"]),
    26: ("Thanh trương nở", "md", "Chiều dài mạch ngừng, cổ ống", ["CT06"]),
    27: ("Phụ gia bê tông (dẻo, chống thấm, đông cứng nhanh)", "lít, kg", "m³ bê tông, theo chỉ dẫn KT", ["PG01"]),
    28: ("Phụ gia kết nối (Sika Latex)", "lít", "m² bề mặt", ["PG02"]),
    29: ("Vữa rót không co ngót (grout)", "bao", "Chi tiết chân cột, khe hở", ["VU05"]),
    30: ("Vữa trộn sẵn (nếu dùng thay vữa tại chỗ)", "bao, tấn", "m³ vữa", ["VU03"]),
    31: ("Con kê bê tông (15/20/25/30mm)", "viên", "Tỷ lệ theo m² cốp pha, m² sàn", ["PK04"]),
    32: ("Lưới mắt cáo mạ kẽm", "md, m²", "Giáp ranh tường – cột", ["PK01"]),
    33: ("Lưới thủy tinh chống nứt", "m²", "Tuyến ngầm, mạch nối", ["PK05"]),
    34: ("Ván cốp pha phủ phim", "m², tấm", "m² cốp pha ÷ số lần luân chuyển", ["CP01"]),
    35: ("Cốp pha thép định hình", "m²", "Theo biện pháp thi công", ["CP02"]),
    36: ("Gỗ xẻ, ván khuôn", "m³", "Chi tiết dị hình, cầu thang", ["CP03"]),
    37: ("Cây chống thép, giàn giáo", "cây, bộ", "Biện pháp thi công", ["CP04"]),
    38: ("Ty ren, cùm, bu lông cốp pha", "bộ, kg", "Biện pháp thi công", ["CP05"]),
    39: ("Đinh các loại", "kg", "Định mức", ["CP06"]),
}
# Mục PDF ghi rõ không bóc được từ bản vẽ (ghi chú 3: vật tư luân chuyển)
NOT_FROM_DRAWING = {34, 35, 37, 38, 39}
# Phạm vi: phần thô móng và thân (Quy ước v1.0 mục A1: không gồm mái, hoàn thiện, cách nhiệt). Vật liệu tường hoàn thiện
# (vách cemboard, thạch cao) vẫn giữ vì là phương án tường của bộ tối ưu. Mục 13 (xà gồ) là chi tiết mái: bỏ.
OUT_OF_SCOPE = {"TH05", "TH06", "GN04", "GN05", "MA01", "MA02", "MA03", "MA04", "MA05", "MA06", "MA07",
                "CN01", "CN02", "CN03", "CN04", "CN05", "CN06"}
OUT_OF_SCOPE_PT = {13}
TARGET = 0.9                     # mục tiêu: ít nhất 90% vật liệu phần thô đã chốt cách xác định
ROLE_VI = {"WALL_ENVELOPE": "tường bao", "WALL_PARTITION": "tường ngăn", "WALL_ACCESSORY": "phụ kiện tường", "FOUNDATION": "móng",
           "FLOOR": "sàn, nền", "FRAME": "khung (cột, dầm)", "ROOF": "mái", "MORTAR": "vữa", "CONCRETE": "bê tông",
           "WATERPROOF": "chống thấm"}
COVER_RULE, COVER_KEY, COVER_NONE, COVER_OUT = ("Có quy tắc tự động", "Có từ khóa, chưa nối vào quy tắc",
                                                "Chưa có định nghĩa", "Không đọc từ bản vẽ")


def where(plans, x, y) -> str:
    for p in plans:
        x0, y0, x1, y1 = p.bbox
        if x0 <= x <= x1 and y0 <= y <= y1:
            return p.name
    return OUTSIDE


def signals(path: Path, rules, texts_out: list) -> list[dict]:
    """Tín hiệu vật liệu trên một bản vẽ, gộp theo (loại, nội dung, mặt bằng), kèm quy tắc hệ thống khớp.
    texts_out: nhận mọi chữ đã chuẩn hóa của bản vẽ (sheet Vật liệu đếm từ khóa trên đó)."""
    d = read_drawing(str(path))
    texts_out += [normalize(t.text) for t in d.texts]
    plans = find_plans(d)
    rows: dict[tuple, Counter] = defaultdict(Counter)
    raw: dict[tuple, str] = {}

    def add(kind, value, norm, plan):
        key = (kind, norm, plan)
        rows[key]["n"] += 1
        raw.setdefault(key, value)

    for t in d.texts:
        norm = normalize(t.text).strip()
        if _best(rules, "text", norm) or match_note(t.text) or any(h in norm for h in MATERIAL_HINTS):
            add("text", t.text.strip()[:120], norm, where(plans, t.x, t.y))
    for h in d.hatches:
        p = h.polygons[0][0] if h.polygons and h.polygons[0] else (0, 0)
        add("hatch", h.pattern, h.pattern.upper(), where(plans, *p))
    wall_layers = {l for pt in takeoff_plans(d) for l in pt.result.wall_layers}
    for layer in d.layers:
        norm = normalize(layer).replace("_", " ").replace("-", " ")
        if layer in wall_layers or _best(rules, "layer", norm):
            add("layer", layer, norm, "Cả file")
    for b in d.blocks:
        if d.layer_classes.get(b.layer) == LayerClass.OPENING or _best(rules, "block", b.name):
            add("block", b.name, b.name.upper(), where(plans, b.x, b.y))

    out = []
    for (kind, norm, plan), c in sorted(rows.items(), key=lambda kv: (kv[0][0] != "text", kv[0][0], kv[0][2], kv[0][1])):
        r = _best(rules, kind, norm)
        nr = match_note(norm) if kind == "text" else []     # ghi chú vật liệu phần thô (material_notes.csv)
        ids = ([r.rule_id] if r else []) + [x.rule_id for x in nr]
        res = ([rule_label(r)] if r else []) + [x.material_id for x in nr]
        why = ([r.note] if r else []) + [f"ghi chú vật liệu: {x.ten}" for x in nr]
        out.append({"file": path.name, "plan": plan, "kind": SIGNAL_VI[kind], "value": raw[(kind, norm, plan)],
                    "norm": norm, "n": c["n"], "rule": ", ".join(ids), "result": "|".join(res),
                    "note": "; ".join(why) or ("có từ gợi ý vật liệu nhưng chưa có quy tắc" if kind == "text" else "chưa có quy tắc")})
    return out


def _channel(mid: str, role: str, pt: list[int]) -> str:
    if pt and all(n in NOT_FROM_DRAWING for n in pt):
        return "Không: vật tư luân chuyển, tính theo biện pháp thi công"
    if "WALL_ENVELOPE" in role or "WALL_PARTITION" in role:
        return "Ghi chú chữ, hatch mặt cắt tường, tên layer (QU-10, QU-20)"
    if mid in ("TH01", "TH02", "TH03", "TH07", "TH08") or (pt and pt[0] in (9, 10, 11)):
        return "Bảng thống kê thép, ghi chú cấu kiện (QU-22, QU-23)"
    if pt and pt[0] in (12, 13, 14, 15, 16):
        return "Bản vẽ kết cấu thép, chi tiết liên kết"
    if pt and pt[0] in (17, 31, 36):
        return "Không trực tiếp: suy từ khối lượng cốt thép / cốp pha"
    return "Ghi chú chữ, chỉ dẫn kỹ thuật (mác, chủng loại; QU-20)"


def _count(keys: list[str], texts: list[str]) -> tuple[int, int, str]:
    """(số chữ khớp nguyên từ, số chữ khớp theo chuỗi con như hệ thống đang so, ví dụ chữ khớp nhầm)."""
    pats = [re.compile(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])") for k in keys if k]
    whole = [t for t in texts if any(p.search(t) for p in pats)]
    sub = [t for t in texts if any(k and k in t for k in keys)]
    wrong = next((t for t in sub if t not in whole), "")
    return len(whole), len(sub), wrong.strip()[:60]


def material_sheet(wb, catalog, rules, texts: list[str]) -> int:
    """Sheet Vật liệu: mỗi vật liệu phần thô (mã danh mục + mục phần thô chưa có mã) một dòng định nghĩa nhận dạng."""
    m, al = catalog.materials, catalog.aliases
    notes = load_note_rules()
    groups = {}
    gfile = ROOT / "data" / "catalog" / "material_groups.csv"
    if gfile.exists():
        import csv
        with open(gfile, encoding="utf-8") as f:
            groups = {r["group_id"]: r["name"] for r in csv.DictReader(f)}
    fam_name = dict(zip(catalog.families.family_id, catalog.families.name))
    pt_of: dict[str, list[int]] = defaultdict(list)
    for n, (*_, ids) in PHAN_THO.items():
        for i in ids:
            pt_of[i].append(n)
    ws = wb.create_sheet("Vật liệu", 2)
    header(ws, ["Mã", "Mục phần thô (STT)", "Tên vật liệu", "Nhóm", "Họ vật liệu tường", "Dùng cho", "Đơn vị",
                "Cách xác định khối lượng", "Đọc từ bản vẽ qua", "Từ khóa trong danh mục (tên gọi khác)",
                "Mẫu ghi chú (material_notes.csv)", "Ký hiệu hatch", "Quy tắc hệ thống", "Chữ khớp trên bản vẽ build",
                "Mức phủ", "Ghi chú", "Duyệt", "Ý kiến người duyệt"],
           [9, 11, 34, 22, 20, 22, 8, 30, 34, 44, 40, 18, 22, 12, 24, 48, 11, 26])
    rows = []
    for r in m.itertuples():
        mid, fam = r.material_id, (r.family if isinstance(r.family, str) else "")
        if mid in OUT_OF_SCOPE:
            continue
        role = str(r.usage_role or "")
        pt = pt_of.get(mid, [])
        method = "; ".join(PHAN_THO[n][2] for n in pt) or ("Định mức, từ m³ tường" if fam else "")
        keys = [normalize(a).strip() for a in al[al.material_id == mid].alias]
        rule_ids = [x.rule_id for x in rules if mid in x.target or (fam and fam in x.target)]
        rule_ids += [n.rule_id for n in notes if n.material_id == mid]
        hatch = ", ".join(x.pattern for x in rules if x.signal == "hatch" and fam and fam in x.target)
        if mid.startswith("BT"):
            hatch = ", ".join(x.pattern for x in rules if x.signal == "hatch" and x.element == "CONCRETE")
        rows.append([mid, ", ".join(map(str, pt)), r.name, groups.get(r.group, r.group), fam_name.get(fam, ""),
                     ", ".join(ROLE_VI.get(x.strip(), x.strip()) for x in role.split(";") if x.strip()), r.unit, method,
                     _channel(mid, role, pt), "; ".join(keys), rule_ids, hatch, keys])
    known = set(m.material_id)
    for n, (name, unit, method, ids) in PHAN_THO.items():
        if not ids and n not in OUT_OF_SCOPE_PT:
            mid = f"PT-{n:02d}"
            rows.append([mid, str(n), name, "Chưa có trong danh mục", "", "", unit, method, _channel(mid, "", [n]), "",
                         [x.rule_id for x in notes if x.material_id == mid], "", []])
    pt_ids = {f"PT-{n:02d}" for n in PHAN_THO}
    for mid in dict.fromkeys(x.material_id for x in notes if x.material_id not in known and x.material_id not in pt_ids):
        rule = next(x for x in notes if x.material_id == mid)
        rows.append([mid, "", rule.ten, "Chưa có trong danh mục (gặp trên bản vẽ build)", "", "", "", "Bóc trực tiếp",
                     _channel(mid, "", []), "", [x.rule_id for x in notes if x.material_id == mid], "", []])
    by_id = {x.rule_id: x for x in notes}
    for row in rows:
        mid, rule_ids, keys = row[0], row[10], row[12]
        pats = [by_id[i].pattern for i in rule_ids if i in by_id]
        allkeys = keys + pats
        whole, sub, wrong = _count(allkeys, texts) if allkeys else (0, 0, "")
        if row[8].startswith("Không:"):
            cover = COVER_OUT
        elif rule_ids:
            cover = COVER_RULE
        elif allkeys:
            cover = COVER_KEY
        else:
            cover = COVER_NONE
        note = []
        if mid in ("BT03", "BT04"):
            note.append("Mục 8 có M350: danh mục chưa có bê tông M350")
        if mid == "TH04":
            note.append("Mục 12 còn thép hình I, H, U, V: danh mục mới có thép hộp (xem PT-12)")
        if mid in ("TH03", "TH08"):
            note.append("Danh mục chia Φ14–Φ25, danh mục phần thô chia D ≤ 18 / D > 18")
        if sub > whole and not pats:
            note.append(f"Quy tắc tường so chuỗi con: khớp nhầm {sub - whole} chữ, ví dụ \"{wrong}\"")
        wall_ids = [i for i in rule_ids if i not in by_id]
        rule_txt = ", ".join(wall_ids[:4] + ([f"{len(pats)} mẫu ghi chú N…"] if pats else []))
        ws.append(row[:10] + ["; ".join(pats), row[11], rule_txt, whole, cover, "; ".join(note), None, None])
    last = ws.max_row
    for r in ws.iter_rows(min_row=2, max_row=last):
        for c in r:
            c.font = FONT
            c.alignment = Alignment(wrap_text=True, vertical="top")
        r[16].fill = r[17].fill = INPUT
    dv = DataValidation(type="list", formula1='"Đồng ý,Sửa,Bỏ"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"Q2:Q{last}")
    ws.auto_filter.ref = f"A1:R{last}"
    return last


def header(ws, cols, widths):
    ws.append(cols)
    for i, w in enumerate(widths, start=1):
        c = ws.cell(row=ws.max_row, column=i)
        c.font, c.fill, c.alignment = BOLD, HEAD, Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions[c.column_letter].width = w
    ws.freeze_panes = f"A{ws.max_row + 1}"     # địa chỉ chữ: ws.cell() sẽ tạo dòng trống và đẩy dữ liệu xuống


def main() -> None:
    files = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "data" / "drawings" / "build").glob("*.dxf"))
    catalog = default_catalog()
    rules = all_rules(catalog)
    families = catalog.families.sort_values("sort_order")
    wb = Workbook()

    # ---------------------------------------------------------------- Hướng dẫn
    g = wb.active
    g.title = "Hướng dẫn"
    for line in [
        "ĐỐI CHIẾU ĐỊNH NGHĨA VẬT LIỆU VỚI BẢN VẼ (OptiMat AI)",
        "",
        "Mục đích: kiểm tra hệ thống đọc đúng vật liệu từ bản vẽ hay chưa, và tìm tín hiệu còn thiếu quy tắc.",
        "1. Sheet \"Định nghĩa\": các quy tắc hệ thống đang dùng. Mẫu so trên chữ đã bỏ dấu, chữ thường (cột \"Nội dung đã chuẩn hóa\").",
        "2. Sheet \"Đối chiếu\": mỗi dòng là một tín hiệu tìm thấy trên bản vẽ và vật liệu hệ thống gán.",
        "   Người kiểm tra chỉ nhập ở 2 cột nền VÀNG: \"Vật liệu đúng\" (chọn trong danh sách) và \"Ghi chú người kiểm tra\".",
        f"   Chọn {NOT_MATERIAL} khi tín hiệu không nói gì về vật liệu (ví dụ chữ \"tường bao\").",
        "   Cột \"Kết quả\" tự tính: Đúng / Sai / Thiếu quy tắc / Chưa kiểm.",
        "   Đúng khi vật liệu đúng nằm trong kết quả hệ thống (kết quả có thể là nhiều họ, ví dụ CLAY_SOLID|CLAY_HOLLOW).",
        "3. Sheet \"Vật liệu\": định nghĩa nhận dạng vật liệu PHẦN THÔ (móng và thân; bỏ mái, cách nhiệt, hoàn thiện theo Quy ước A1):",
        "   mã danh mục + mục của danh mục phần thô (39 mục) chưa có mã (PT-xx). Ghi chú vật liệu đọc bằng data/rules/material_notes.csv",
        "   (so nguyên từ); vật liệu tường đọc bằng material_rules.csv. Sửa mẫu ở file CSV rồi sinh lại; ý kiến ghi ở cột vàng \"Duyệt\".",
        "   \"Chữ khớp trên bản vẽ build\": số chữ trên các bản vẽ build chứa từ khóa (so nguyên từ). \"Mức phủ\": có quy tắc tự động /",
        "   có từ khóa nhưng chưa nối vào quy tắc / chưa có định nghĩa / không đọc từ bản vẽ (vật tư luân chuyển).",
        "4. Sheet \"Tổng hợp\": số tín hiệu, đã kiểm, đúng, sai, thiếu quy tắc và tỷ lệ đúng của từng bản vẽ (công thức).",
        "",
        "Mã vật liệu (cột \"Vật liệu đúng\"): họ vật liệu tường (material_families), mã vật liệu phần thô (sheet Vật liệu, cột Mã), cộng thêm:",
        "   CONCRETE: bê tông (cột, vách), không tính vào khối xây · WALL_MASONRY: khối xây nhưng không rõ loại gạch",
        f"   {NOT_MATERIAL}: tín hiệu không phải vật liệu · DOOR / WINDOW: cửa đi / cửa sổ (tín hiệu block)",
        "Dòng thiếu quy tắc: thêm quy tắc vào data/rules/material_rules.csv rồi chạy lại scripts/build_material_check_xlsx.py.",
        "Lưu ý: chỉ chỉnh quy tắc theo bản vẽ nhóm build; bản vẽ nhóm test chỉ dùng để báo cáo (Quy ước B7).",
        "Dòng ví dụ: \"gạch đặc\" → hệ thống gán CLAY_SOLID|CLAY_HOLLOW → người kiểm tra chọn CLAY_SOLID → Kết quả: Đúng.",
    ]:
        g.append([line])
    g.column_dimensions["A"].width = 130
    for row in g.iter_rows():
        for c in row:
            c.font = FONT
    g["A1"].font = Font(name="Arial", size=12, bold=True)

    # ---------------------------------------------------------------- Định nghĩa
    s = wb.create_sheet("Định nghĩa")
    header(s, ["Mã quy tắc", "Tín hiệu", "Mẫu (đã bỏ dấu)", "Kết quả (họ / mã vật liệu)", "Cấu kiện", "Ưu tiên", "Nguồn", "Ghi chú"],
           [12, 14, 26, 30, 16, 9, 22, 70])
    for r in rules:
        s.append([r.rule_id, SIGNAL_VI.get(r.signal, r.signal), r.pattern, rule_label(r), r.element, r.priority,
                  "Tên gọi khác (danh mục)" if r.rule_id.startswith("A-") else "material_rules.csv", r.note])
    s.append([])
    s.append(["Họ vật liệu", "Tên"])
    for c in s[s.max_row]:
        c.font, c.fill = BOLD, HEAD
    for f in families.itertuples():
        s.append([f.family_id, f.name])
    for row in s.iter_rows(min_row=2):
        for c in row:
            if not c.font.b:
                c.font = FONT

    # ---------------------------------------------------------------- Đối chiếu
    o = wb.create_sheet("Đối chiếu")
    cols = ["Bản vẽ", "Mặt bằng", "Tín hiệu", "Nội dung trên bản vẽ", "Nội dung đã chuẩn hóa", "Số lần", "Quy tắc khớp",
            "Hệ thống gán", "Ghi chú quy tắc", "Vật liệu đúng", "Ghi chú người kiểm tra", "Kết quả"]
    header(o, cols, [16, 26, 13, 40, 34, 8, 12, 26, 40, 22, 30, 14])
    texts: list[str] = []
    data = [row for f in files for row in signals(f, rules, texts)]
    for i, r in enumerate(data, start=2):
        o.append([r["file"], r["plan"], r["kind"], r["value"], r["norm"], r["n"], r["rule"], r["result"], r["note"], None, None,
                  f'=IF(J{i}="","Chưa kiểm",IF(J{i}="{NOT_MATERIAL}",IF(H{i}="","Đúng","Sai"),'
                  f'IF(H{i}="","Thiếu quy tắc",IF(ISNUMBER(SEARCH("|"&J{i}&"|","|"&H{i}&"|")),"Đúng","Sai"))))'])
    last = max(len(data) + 1, 2) + 200          # chừa 200 dòng để người kiểm tra thêm tín hiệu tự tìm
    for i in range(len(data) + 2, last + 1):
        o.cell(row=i, column=12, value=f'=IF(AND(D{i}="",J{i}=""),"",IF(J{i}="","Chưa kiểm",IF(J{i}="{NOT_MATERIAL}",'
                                         f'IF(H{i}="","Đúng","Sai"),IF(H{i}="","Thiếu quy tắc",'
                                         f'IF(ISNUMBER(SEARCH("|"&J{i}&"|","|"&H{i}&"|")),"Đúng","Sai")))))')
    for row in o.iter_rows(min_row=2, max_row=last):
        for c in row:
            c.font = FONT
        row[9].fill = row[10].fill = INPUT
    rough_ids = [x for x in catalog.materials.material_id if x not in OUT_OF_SCOPE]
    rough_ids += list(dict.fromkeys(x.material_id for x in load_note_rules() if x.material_id not in rough_ids))
    codes = list(families.family_id) + ["CONCRETE", "WALL_MASONRY", "DOOR", "WINDOW", NOT_MATERIAL] + rough_ids
    lst = wb.create_sheet("Danh sách")
    for c in codes:
        lst.append([c])
    lst.sheet_state = "hidden"
    dv = DataValidation(type="list", formula1=f"='Danh sách'!$A$1:$A${len(codes)}", allow_blank=True,
                        errorTitle="Mã không hợp lệ", error="Chọn mã trong danh sách (xem sheet Hướng dẫn).")
    o.add_data_validation(dv)
    dv.add(f"J2:J{last}")
    o.auto_filter.ref = f"A1:L{last}"

    mat_last = material_sheet(wb, catalog, rules, texts)

    # ---------------------------------------------------------------- Tổng hợp
    t = wb.create_sheet("Tổng hợp")
    header(t, ["Bản vẽ", "Tín hiệu", "Hệ thống có quy tắc", "Đã kiểm", "Đúng", "Sai", "Thiếu quy tắc", "Tỷ lệ đúng (đúng / đã kiểm)"],
           [18, 10, 18, 10, 9, 9, 14, 26])
    rng = lambda col: f"'Đối chiếu'!${col}$2:${col}${last}"
    for f in [p.name for p in files] + ["Tất cả"]:
        i = t.max_row + 1
        crit = f'{rng("A")},A{i}' if f != "Tất cả" else f'{rng("A")},"<>"'
        t.append([f, f"=COUNTIFS({crit})", f'=COUNTIFS({crit},{rng("H")},"<>")',
                  f'=COUNTIFS({crit},{rng("J")},"<>")', f'=COUNTIFS({crit},{rng("L")},"Đúng")',
                  f'=COUNTIFS({crit},{rng("L")},"Sai")', f'=COUNTIFS({crit},{rng("L")},"Thiếu quy tắc")',
                  f'=IF(D{i}=0,"",E{i}/D{i})'])
        t.cell(row=i, column=8).number_format = "0.0%"
    for row in t.iter_rows(min_row=2):
        for c in row:
            c.font = BOLD if row[0].value == "Tất cả" else FONT
    i, total = t.max_row + 1, t.max_row          # dòng "Tất cả" là dòng cuối của bảng trên
    t.append(["Chỉ tiêu S10: tỷ lệ đúng ≥ 90% và không có dòng Sai", None, None, None, None, None, None,
              f'=IF(D{total}=0,"Chưa kiểm dòng nào",IF(AND(H{total}>=0.9,F{total}=0),"Đạt","Chưa đạt"))'])
    for c in t[i]:
        c.font = BOLD
    t.append([])
    t.append(["Mức phủ định nghĩa vật liệu (sheet Vật liệu)", "Số vật liệu", "Tỷ lệ"])
    for c in t[t.max_row]:
        c.font, c.fill = BOLD, HEAD
    first = t.max_row + 1
    for k in (COVER_RULE, COVER_KEY, COVER_NONE, COVER_OUT):
        i = t.max_row + 1
        t.append([k, f"=COUNTIF('Vật liệu'!$O$2:$O${mat_last},A{i})",
                  f'=IF(SUM($B${first}:$B${first + 3})=0,"",B{i}/SUM($B${first}:$B${first + 3}))'])
        t.cell(row=i, column=3).number_format = "0.0%"
        for c in t[i]:
            c.font = FONT
    i = t.max_row + 1
    t.append([f"Đã chốt (có quy tắc + không đọc từ bản vẽ), mục tiêu ≥ {TARGET:.0%}", f"=B{first}+B{first + 3}",
              f'=IF(SUM($B${first}:$B${first + 3})=0,"",B{i}/SUM($B${first}:$B${first + 3}))',
              f'=IF(C{i}="","",IF(C{i}>={TARGET},"Đạt mục tiêu","Chưa đạt"))'])
    t.cell(row=i, column=3).number_format = "0.0%"
    for c in t[i]:
        c.font = BOLD
    t.append([])
    t.append(["Tỷ lệ đúng chỉ tính trên dòng đã kiểm. Bản vẽ nhóm build dùng để chỉnh quy tắc; báo cáo độ chính xác dùng nhóm test."])
    t.cell(row=t.max_row, column=1).font = Font(name="Arial", size=9, italic=True)

    wb.calculation.fullCalcOnLoad = True     # openpyxl không lưu giá trị công thức: Excel tính khi mở file
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    by = Counter((r["file"], bool(r["rule"])) for r in data)
    print(f"{OUT.relative_to(ROOT)}: {len(rules)} quy tắc, {len(data)} tín hiệu "
          + ", ".join(f"{f.name}: {by[(f.name, True)]} có quy tắc / {by[(f.name, False)]} chưa" for f in files))


if __name__ == "__main__":
    main()
