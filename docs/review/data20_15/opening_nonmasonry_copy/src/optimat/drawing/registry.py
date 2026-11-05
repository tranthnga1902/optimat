"""Hồ sơ chuẩn hóa kiến trúc–kết cấu (S03): mỗi cấu kiện một mục, mọi số liệu kèm bằng chứng dẫn ngược về bản vẽ.

Nhận theo quy ước, không đoán:
- loại hình vẽ theo tiêu đề (sheets.py, data/rules/loai_ban_ve.csv); ký hiệu cấu kiện theo data/rules/ky_hieu_cau_kien.csv,
  người dùng gán thêm ký hiệu lạ qua symbol_overrides; vai trò layer theo concepts.csv, ghi đè qua layer_overrides;
- tên cấu kiện chuẩn hóa thành khóa bỏ dấu, chữ thường ("ĐK2" -> "dk2"); tầng chuẩn hóa thành T1, T2…, ST (sân thượng), MAI, MONG
  (miền Nam: TRỆT = T1, LẦU n = T(n+1)); tọa độ đổi về gốc góc dưới trái của hình vẽ × tỷ lệ hình vẽ (mm thật);
- tiết diện: chữ ghi ("D1 220X400"), mặt cắt chi tiết (structural.detail_sections); hai nguồn khác nhau thì để trống
  và báo xung đột; không có nguồn nào thì để trống (Quy ước B7), không lấy số mặc định;
- mức tin cậy theo data/rules/do_tin_cay.csv: mỗi quy tắc bị chạm hạ mức về mức của quy tắc đó, quy tắc có
  can_xac_nhan = 1 đưa cấu kiện vào danh sách chờ người dùng xác nhận.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field

from .. import config
from ..rough import structural as st
from .concepts import match_block_signal, match_layer
from .dimensions import inside, read_dimensions, view_scale
from .dxf_reader import Drawing
from .encoding import normalize
from .plans import find_plans
from .sheets import TITLE_REL_HEIGHT, find_views, sheet_inventory, sheet_type_of

CONFIDENCE_FILE = config.DATA_DIR / "rules" / "do_tin_cay.csv"
LEVELS = {"thap": 0, "trung_binh": 1, "cao": 2}
DETAIL_TYPES = ("BV05", "BV07", "BV09")
TYPICAL_ROLE = {"BV05": "FOUNDATION", "BV07": "COLUMN", "BV09": "BEAM"}
REQUIRED = {"BEAM": ("b_mm", "d_mm"), "COLUMN": ("b_mm", "h_mm"), "FOUNDATION": ("length_mm", "width_mm", "height_mm")}
SIZE_TOLERANCE = 0.2            # nét trên mặt bằng lệch tiết diện ghi quá 20% thì báo
SYMBOL_LIKE = re.compile(r"(?!a\d)[a-z]{1,3}\d{1,3}[a-z]?")      # "a200" là bước thép, không phải ký hiệu
REV_RE = re.compile(r"\b(?:rev|revision|phien ban|lan sua|version|ver)\b\.?\s*[:.\-]?\s*([a-z]?\d+(?:\.\d+)?|[a-z])\b")
TITLE_WORDS = ("mat bang", "chi tiet", "mat cat", "bang thong ke", "mat dung", "thong ke")


class EvidenceRef(BaseModel):
    """Nơi lấy một thông tin: file, layout, handle đối tượng CAD, khung (mm bản vẽ, WCS) và quy tắc đã khớp."""
    file: str
    layout: str = "Model"
    handle: Optional[str] = None      # TEXT/MTEXT/INSERT; None khi bản vẽ không có tài liệu ezdxf gốc
    bbox: tuple[float, float, float, float]
    rule: str                         # K03, BV08, TC…, SIZE_TEXT, MAT_CAT, NGUOI_DUNG
    text: str = ""


class Occurrence(BaseModel):
    """Một lần ký hiệu xuất hiện trên mặt bằng."""
    view: str
    sheet_type: str
    floors: list[str]
    x_mm: float                       # tọa độ chuẩn hóa: gốc góc dưới trái hình vẽ, đã nhân tỷ lệ
    y_mm: float
    axis: Optional[str] = None        # "2/B": trục đứng gần nhất / trục ngang gần nhất
    drawn_width_mm: Optional[float] = None   # dầm: khoảng cách cặp nét (đã nhân tỷ lệ); None: không thấy nét
    evidence: EvidenceRef


class SizeValue(BaseModel):
    values: dict[str, float]
    source: Literal["chu", "mat_cat", "chi_tiet", "nguoi_dung"]
    evidence: EvidenceRef


class Component(BaseModel):
    id: str                           # "BEAM:d7a"
    role: str
    kind: str                         # dầm, cột, móng, đà kiềng
    name: str                         # ký hiệu như trên bản vẽ ("D7A", "ĐK2")
    occurrences: list[Occurrence] = Field(default_factory=list)
    details: list[EvidenceRef] = Field(default_factory=list)
    size_sources: list[SizeValue] = Field(default_factory=list)
    size: dict[str, Optional[float]] = Field(default_factory=dict)   # thông số đã chốt; None = còn thiếu
    rules: list[str] = Field(default_factory=list)
    confidence: str = "cao"
    needs_confirmation: bool = False
    status: Literal["tu_dong", "xac_nhan", "loai_bo"] = "tu_dong"


class Issue(BaseModel):
    kind: Literal["xung_dot_kich_thuoc", "thieu_chi_tiet", "chi_tiet_khong_dung", "lech_phien_ban", "da_tang",
                  "trung_tang", "tang_khong_khop", "ty_le"]
    message: str
    component: Optional[str] = None
    evidence: list[EvidenceRef] = Field(default_factory=list)


class ViewInfo(BaseModel):
    file: str
    title: str
    sheet_type: str
    sheet_name: str
    floors: list[str]
    scale: Optional[float]            # None: không có đường kích thước
    origin: Optional[tuple[float, float]]
    evidence: EvidenceRef


class Floor(BaseModel):
    key: str
    names: list[str]
    elevation_m: Optional[float] = None
    views: list[str] = Field(default_factory=list)


class Unmatched(BaseModel):
    kind: Literal["ky_hieu", "tieu_de", "layer"]
    text: str
    evidence: Optional[EvidenceRef] = None


class LayerMap(BaseModel):
    file: str
    layer: str
    role: str
    rule: Optional[str] = None        # mã ký hiệu concepts.csv (L05…); None: chưa có quy tắc


class Registry(BaseModel):
    """Hồ sơ chuẩn hóa: lược đồ JSON xuất ở docs/schema/ho_so_chuan_hoa.schema.json."""
    files: list[str]
    sheets: list[dict]
    views: list[ViewInfo]
    floors: list[Floor]
    layers: list[LayerMap]
    components: list[Component]
    issues: list[Issue]
    unmatched: list[Unmatched]
    revisions: dict[str, list[str]] = Field(default_factory=dict)    # file -> các phiên bản ghi trên bản vẽ
    confidence_rules: list[dict] = Field(default_factory=list)


@lru_cache(maxsize=2)
def load_confidence_rules(path: str | None = None) -> dict[str, dict]:
    rows = pd.read_csv(path or CONFIDENCE_FILE, dtype=str, keep_default_na=False).to_dict("records")
    out = {r["ma"]: {**r, "can_xac_nhan": r["can_xac_nhan"] == "1"} for r in rows}
    bad = [r["ma"] for r in rows if r["muc"] not in LEVELS]
    if bad:
        raise ValueError(f"do_tin_cay.csv: mức không hợp lệ ở {', '.join(bad)} (chỉ nhận {', '.join(LEVELS)}).")
    return out


@lru_cache(maxsize=2)
def _element_rules() -> tuple[tuple[str, re.Pattern, str, str], ...]:
    # cùng file, cùng thứ tự với structural.load_element_rules; cần thêm mã dòng (K03) làm bằng chứng
    rows = pd.read_csv(st.ELEMENT_FILE, dtype=str, keep_default_na=False).to_dict("records")
    return tuple((r["ma"], re.compile(r["mau"]), r["vai_tro"], r["ten"]) for r in rows)


def symbol_key(text: str) -> str:
    return re.sub(r"\s+", "", normalize(text))


def match_symbol(text: str, overrides: dict[str, str] | None = None) -> tuple[str, str, str, str] | None:
    """Ký hiệu -> (vai trò, tên loại, khóa, mã quy tắc). Gán của người dùng thắng quy tắc."""
    key = symbol_key(text)
    if overrides and key in overrides:
        return overrides[key], "người dùng gán", key, "NGUOI_DUNG"
    for ma, pat, role, name in _element_rules():
        if pat.fullmatch(key):
            return role, name, key, ma
    return None


def floors_of(title: str) -> list[str]:
    """Tầng chuẩn hóa của một tiêu đề: "MẶT BẰNG DẦM SÀN LẦU 2-3-4" -> [T3, T4, T5]; "… MÓNG" -> [MONG]; "TẦNG 1" -> [T1]."""
    t = normalize(title)
    if re.search(r"\b(mong|da kieng|giang mong)\b", t):
        return ["MONG"]
    t = re.sub(r"\(.*?\)|[±+-]?\d+[.,]\d+|\b(tl|ti le)\b.*$", " ", t)     # bỏ cao độ, tỷ lệ
    m = re.search(r"\b(tret|lau|tang|mai|san thuong)\b.*$", t)
    if not m:
        return []
    out, nums, prefix = [], [], "tang"
    for tok in re.findall(r"[a-z]+|\d+", m.group(0)):
        if tok in ("lau", "tang"):
            prefix = tok
        elif tok == "tret":
            out.append("T1")
        elif tok == "mai":
            out.append("MAI")
        elif tok == "thuong":           # sân thượng: sàn trên cùng, khác mái
            out.append("ST")
        elif tok.isdigit():
            nums.append(int(tok))
            out.append(f"T{int(tok) + (prefix == 'lau')}")
    # "LẦU 2-LẦU 5": hai đầu số tăng dần là một dải (cùng cách đếm với structural.floor_count)
    if len(m.group(0).split("-")) == 2 and len(nums) == len(out) == 2 and nums[1] > nums[0]:
        a = int(out[0][1:])
        out = [f"T{i}" for i in range(a, a + nums[1] - nums[0] + 1)]
    return list(dict.fromkeys(out))


def _handles(drawing: Drawing) -> dict[tuple[int, int], str]:
    """Handle của TEXT/MTEXT/INSERT trong model space theo điểm chèn (mm, làm tròn): chữ nằm trong block lấy handle INSERT."""
    doc, s = getattr(drawing, "doc", None), drawing.unit_scale
    if doc is None:
        return {}
    out = {}
    for e in doc.modelspace().query("TEXT MTEXT INSERT"):
        p = e.dxf.insert if e.dxftype() == "MTEXT" else e.ocs().to_wcs(e.dxf.insert)
        out[(round(p.x * s), round(p.y * s))] = e.dxf.handle
        if e.dxftype() == "INSERT":
            for a in e.attribs:
                q = a.ocs().to_wcs(a.dxf.insert)
                out[(round(q.x * s), round(q.y * s))] = e.dxf.handle
    return out


def _ev(file: str, t, rule: str, handles: dict) -> EvidenceRef:
    h = t.height or 100.0
    # shortcut: khung chữ ước theo số ký tự × 0,7 cao chữ, chưa tính góc xoay; đủ để khoanh vùng trên trang duyệt
    return EvidenceRef(file=file, handle=handles.get((round(t.x), round(t.y))),
                       bbox=(round(t.x, 1), round(t.y, 1), round(t.x + len(t.text) * 0.7 * h, 1), round(t.y + h, 1)),
                       rule=rule, text=t.text.strip())


def _axes(drawing: Drawing, bbox) -> tuple[list[tuple[float, str]], list[tuple[float, str]]]:
    """Đầu trục trong khung: block khái niệm Trục (nhãn = thuộc tính đầu) hoặc chữ ≤ 3 ký tự trên layer Trục.
    Đầu trục gần cạnh trên/dưới khung là trục đứng (lấy x), gần cạnh trái/phải là trục ngang (lấy y)."""
    x0, y0, x1, y1 = st._grown(bbox)
    marks = [(b.x, b.y, str(next(iter(b.attribs.values())))) for b in drawing.blocks
             if b.attribs and (sig := match_block_signal(b.name)) and sig.khai_niem == "Trục"]
    marks += [(t.x, t.y, t.text.strip()) for t in drawing.texts if len(t.text.strip()) <= 3
              and (sig := match_layer(normalize(t.layer))) and sig.khai_niem == "Trục"]
    vertical, horizontal = [], []
    for x, y, label in marks:
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        dy, dx = min(y - bbox[1], bbox[3] - y), min(x - bbox[0], bbox[2] - x)
        (vertical if dy < dx else horizontal).append((x if dy < dx else y, label))
    return vertical, horizontal


def _axis_name(vertical, horizontal, x: float, y: float) -> str | None:
    if not vertical and not horizontal:
        return None
    v = min(vertical, key=lambda a: abs(a[0] - x))[1] if vertical else "?"
    h = min(horizontal, key=lambda a: abs(a[0] - y))[1] if horizontal else "?"
    return f"{v}/{h}"


def _written(file: str, drawing: Drawing, overrides, handles) -> list[tuple[str, SizeValue]]:
    """Tiết diện ghi chữ cạnh ký hiệu ("ĐÀ KIỀNG ĐK2 300X500", "C1 220x220") -> [(id cấu kiện, giá trị)]."""
    out = []
    for t in drawing.texts:
        m = st.SIZE_RE.search(t.text)
        if not m:
            continue
        for word in re.split(r"[\s(),:]+", t.text[:m.start()]):
            e = match_symbol(word, overrides) if word else None
            if e and e[0] in REQUIRED and e[0] != "FOUNDATION":
                a, b = float(m.group(1)), float(m.group(2))
                keys = REQUIRED[e[0]]
                out.append((f"{e[0]}:{e[2]}", SizeValue(values={keys[0]: a, keys[1]: b}, source="chu",
                                                        evidence=_ev(file, t, "SIZE_TEXT", handles))))
    return out


def _new(cid: str, role: str, kind: str, name: str) -> Component:
    return Component(id=cid, role=role, kind=kind, name=name)


def build_registry(sources: list[tuple[str, Drawing]], symbol_overrides: dict[str, str] | None = None,
                   dims: dict[str, list] | None = None) -> Registry:
    """sources: [(tên file, bản vẽ đã đọc)], kiến trúc và kết cấu chung một hồ sơ. dims: đường kích thước theo file
    (mặc định đọc từ tài liệu ezdxf). symbol_overrides: {khóa ký hiệu: vai trò} người dùng gán cho ký hiệu chưa có quy tắc."""
    overrides = {symbol_key(k): v for k, v in (symbol_overrides or {}).items()}
    comps: dict[str, Component] = {}
    issues: list[Issue] = []
    unmatched: list[Unmatched] = []
    views_out: list[ViewInfo] = []
    layers: list[LayerMap] = []
    revisions: dict[str, list[str]] = {}
    floors: dict[str, Floor] = {}
    all_views = []
    typical: dict[str, list[EvidenceRef]] = {}
    for file, d in sources:
        handles = _handles(d)
        fdims = (dims or {}).get(file)
        fdims = read_dimensions(d) if fdims is None else fdims
        views = find_views(d, bbox_for=st.PLAN_TYPES + ("BV05",))
        all_views += views
        revs = sorted({m.group(1) for t in d.texts if (m := REV_RE.search(normalize(t.text)))})
        if revs:
            revisions[file] = revs
        for name in d.layers:
            sig = match_layer(normalize(name))
            role = d.layer_classes.get(name, "UNKNOWN")
            layers.append(LayerMap(file=file, layer=name, role=getattr(role, "value", role),
                                   rule=sig.ma if sig else None))
            if d.layer_classes.get(name) == "UNKNOWN" and name != "0":
                unmatched.append(Unmatched(kind="layer", text=name))
        for p in find_plans(d):          # mặt bằng kiến trúc: cao độ tầng
            for key in floors_of(p.title or p.name):
                f = floors.setdefault(key, Floor(key=key, names=[]))
                f.names.append(p.name)
                f.elevation_m = f.elevation_m if f.elevation_m is not None else p.level_m
        # tiêu đề nhận được loại -> ViewInfo; chữ cỡ tiêu đề không nhận được loại -> unmatched
        title_texts = {(round(v.x), round(v.y)) for v in views}
        big = max((t.height for t in d.texts if sheet_type_of(t.text)), default=0)
        for t in d.texts:
            n = normalize(t.text).strip()
            if (round(t.x), round(t.y)) not in title_texts and big and t.height >= TITLE_REL_HEIGHT * big \
                    and n.startswith(TITLE_WORDS) and not sheet_type_of(t.text):
                unmatched.append(Unmatched(kind="tieu_de", text=t.text.strip(), evidence=_ev(file, t, "-", handles)))
        by_pos = {(round(t.x), round(t.y)): t for t in d.texts}
        for v in views:
            t = by_pos.get((round(v.x), round(v.y)))
            ev = _ev(file, t, v.ma, handles) if t else EvidenceRef(file=file, bbox=(v.x, v.y, v.x, v.y), rule=v.ma,
                                                                   text=v.title)
            if v.bbox:
                ev.bbox = tuple(round(c, 1) for c in v.bbox)
            fl = floors_of(v.title)
            scale = view_scale(inside(fdims, v.bbox)) if v.bbox else None
            views_out.append(ViewInfo(file=file, title=v.title, sheet_type=v.ma, sheet_name=v.ten, floors=fl,
                                      scale=scale, origin=(v.bbox[0], v.bbox[1]) if v.bbox else None, evidence=ev))
            for key in fl:
                floors.setdefault(key, Floor(key=key, names=[])).views.append(v.title)
            if v.ma in DETAIL_TYPES:
                keyed = False
                for word in re.split(r"[\s(),:]+", v.title):
                    e = match_symbol(word, overrides) if word else None
                    if e and e[0] in REQUIRED:
                        cid, keyed = f"{e[0]}:{e[2]}", True
                        comps.setdefault(cid, _new(cid, e[0], e[1], word.upper())).details.append(ev)
                if not keyed:          # "CHI TIẾT CỘT ĐIỂN HÌNH": chi tiết chung cho mọi cấu kiện cùng loại
                    typical.setdefault(TYPICAL_ROLE[v.ma], []).append(ev)
                continue
            if v.ma not in st.PLAN_TYPES or not v.bbox:
                continue
            if len(fl) > 1:
                issues.append(Issue(kind="da_tang", message=f"{v.title}: một hình vẽ dùng cho {len(fl)} tầng "
                                    f"({', '.join(fl)}); khối lượng nhân số tầng, cần xác nhận.", evidence=[ev]))
            if scale is None:
                issues.append(Issue(kind="ty_le", message=f"{v.title}: không có đường kích thước, chưa suy được tỷ lệ "
                                    "(đang coi số đo là mm thật).", evidence=[ev]))
            s = scale or 1.0
            vert, horiz = _axes(d, v.bbox)
            axis_labels = {lbl for _, lbl in vert + horiz}
            lines = st._lines(d, st._grown(v.bbox))
            x0, y0, x1, y1 = st._grown(v.bbox)
            for t in d.texts:
                if not (x0 <= t.x <= x1 and y0 <= t.y <= y1):
                    continue
                e = match_symbol(t.text, overrides)
                if e is None:
                    key = symbol_key(t.text)
                    if SYMBOL_LIKE.fullmatch(key) and t.text.strip() not in axis_labels and not floors_of(t.text):
                        unmatched.append(Unmatched(kind="ky_hieu", text=t.text.strip(),
                                                   evidence=_ev(file, t, "-", handles)))
                    continue
                if e[0] not in REQUIRED:
                    continue
                width = None
                if e[0] == "BEAM":
                    p = st._nearest_pair(lines, t.x, t.y)
                    width = round(p[5] * s, 1) if p else None
                cid = f"{e[0]}:{e[2]}"
                comps.setdefault(cid, _new(cid, e[0], e[1], t.text.strip().upper())).occurrences.append(Occurrence(
                    view=v.title, sheet_type=v.ma, floors=fl, x_mm=round((t.x - v.bbox[0]) * s, 1),
                    y_mm=round((t.y - v.bbox[1]) * s, 1), axis=_axis_name(vert, horiz, t.x, t.y),
                    drawn_width_mm=width, evidence=_ev(file, t, e[3], handles)))
        for cid, sv in _written(file, d, overrides, handles):
            role, key = cid.split(":", 1)
            comps.setdefault(cid, _new(cid, role, role.lower(), key.upper())).size_sources.append(sv)
        # mặt cắt, chi tiết móng: dùng lại cách đọc của rough/structural.py
        details = st.detail_sections(d, views, fdims)
        for key, (b, h) in st.beam_detail_sizes(details).items():
            cid = f"BEAM:{key}"
            c = comps.setdefault(cid, _new(cid, "BEAM", "dầm", key.upper()))
            ev = c.details[0] if c.details else EvidenceRef(file=file, bbox=(0, 0, 0, 0), rule="MAT_CAT")
            c.size_sources.append(SizeValue(values={"b_mm": b, "d_mm": h}, source="mat_cat", evidence=ev))
        for key, size in st.footing_detail_sizes(views, details, fdims).items():
            cid = f"FOUNDATION:{key}"
            c = comps.setdefault(cid, _new(cid, "FOUNDATION", "móng", key.upper()))
            vals = {k: v for k, v in size.items() if k in REQUIRED["FOUNDATION"] + ("lean_thickness_mm",) and v is not None}
            if vals:
                ev = c.details[0] if c.details else EvidenceRef(file=file, bbox=(0, 0, 0, 0), rule="CHI_TIET")
                c.size_sources.append(SizeValue(values=vals, source="chi_tiet", evidence=ev))
    for c in comps.values():
        if not c.details:
            c.details = list(typical.get(c.role, []))
    _floor_issues(floors, views_out, issues)
    if len({r for rs in revisions.values() for r in rs}) > 1:
        issues.append(Issue(kind="lech_phien_ban", message="Phiên bản ghi trên bản vẽ không thống nhất: "
                            + "; ".join(f"{f}: {', '.join(r)}" for f, r in revisions.items())))
    reg = Registry(files=[f for f, _ in sources], sheets=sheet_inventory(all_views), views=views_out,
                   floors=sorted(floors.values(), key=lambda f: f.key), layers=layers,
                   components=sorted(comps.values(), key=lambda c: c.id), issues=issues, unmatched=unmatched,
                   revisions=revisions)
    for c in reg.components:
        _resolve(c, reg)
    return score(reg)


def _floor_issues(floors: dict[str, Floor], views: list[ViewInfo], issues: list[Issue]) -> None:
    arch = {k for k, f in floors.items() if f.names}
    for key, f in floors.items():
        for typ in st.PLAN_TYPES:
            same = [v for v in views if v.sheet_type == typ and key in v.floors]
            if len(same) > 1:
                issues.append(Issue(kind="trung_tang", message=f"Tầng {key} có {len(same)} hình vẽ {same[0].sheet_name}: "
                                    + ", ".join(v.title for v in same), evidence=[v.evidence for v in same]))
        if arch and key not in arch and key != "MONG" and f.views:
            issues.append(Issue(kind="tang_khong_khop", message=f"Tầng {key} có trên bản vẽ kết cấu ({', '.join(f.views)}) "
                                "nhưng không có mặt bằng kiến trúc tương ứng."))


def _resolve(c: Component, reg: Registry) -> None:
    """Chốt thông số từ các nguồn: một bộ số thống nhất thì lấy, khác nhau thì để trống và báo, không có thì để trống."""
    if c.status == "loai_bo":
        return
    keys = REQUIRED.get(c.role, ())
    user = [s for s in c.size_sources if s.source == "nguoi_dung"]
    c.size = {k: None for k in keys}
    c.rules = []
    for k in keys + (("lean_thickness_mm",) if c.role == "FOUNDATION" else ()):
        # số người dùng nhập thắng theo từng thông số; thông số họ không nhập vẫn lấy từ bản vẽ
        vals = {s.values[k] for s in user if k in s.values} or {s.values[k] for s in c.size_sources if k in s.values}
        if len(vals) == 1:
            c.size[k] = vals.pop()
        elif len(vals) > 1:
            c.rules.append("TC03")
            reg.issues.append(Issue(kind="xung_dot_kich_thuoc", component=c.id,
                                    message=f"{c.name}: {k} mâu thuẫn giữa các nguồn ({', '.join(f'{v:g}' for v in sorted(vals))}); "
                                    "để trống, cần người dùng chọn.", evidence=[s.evidence for s in c.size_sources]))
    if c.role == "BEAM" and c.size.get("b_mm") and not user:
        for o in c.occurrences:
            if o.drawn_width_mm and abs(o.drawn_width_mm - c.size["b_mm"]) > SIZE_TOLERANCE * c.size["b_mm"]:
                c.rules.append("TC03")
                reg.issues.append(Issue(kind="xung_dot_kich_thuoc", component=c.id, evidence=[o.evidence],
                                        message=f"{c.name} ({o.view}): rộng ghi {c.size['b_mm']:g} mm, nét trên mặt bằng "
                                        f"{o.drawn_width_mm:g} mm: kiểm tra tỷ lệ hoặc ký hiệu."))
    if not c.details and not c.size_sources and c.occurrences:
        reg.issues.append(Issue(kind="thieu_chi_tiet", component=c.id, evidence=[c.occurrences[0].evidence],
                                message=f"{c.name}: có trên mặt bằng nhưng không có chi tiết, mặt cắt hay tiết diện ghi chữ."))
    if any(v is None for v in c.size.values()):
        c.rules.append("TC02")
    if not c.occurrences:
        c.rules.append("TC08")
        reg.issues.append(Issue(kind="chi_tiet_khong_dung", component=c.id, evidence=c.details[:1],
                                message=f"{c.name}: có chi tiết hoặc tiết diện nhưng không có ký hiệu trên mặt bằng nào."))
    if c.role == "BEAM" and any(o.drawn_width_mm is None for o in c.occurrences):
        c.rules.append("TC04")
    if any(len(o.floors) > 1 for o in c.occurrences):
        c.rules.append("TC05")
    if any(v.scale is None for v in reg.views if v.title in {o.view for o in c.occurrences}):
        c.rules.append("TC06")
    if any(i.kind == "lech_phien_ban" for i in reg.issues):
        c.rules.append("TC07")
    c.rules = sorted(set(c.rules)) or ["TC01"]


def score(reg: Registry) -> Registry:
    """Mức tin cậy = mức thấp nhất của các quy tắc bị chạm; xác nhận của người dùng (TC09) thắng."""
    rules = load_confidence_rules()
    reg.confidence_rules = list(rules.values())
    for c in reg.components:
        if c.status == "loai_bo":
            c.confidence, c.needs_confirmation = "cao", False
            continue
        # xác nhận ký hiệu không điền thông số còn thiếu: TC02 vẫn hạ mức
        hit = (["TC09"] + ["TC02"] * any(v is None for v in c.size.values())) if c.status == "xac_nhan" else c.rules
        c.confidence = min((rules[r]["muc"] for r in hit), key=LEVELS.get)
        c.needs_confirmation = c.status == "tu_dong" and any(rules[r]["can_xac_nhan"] for r in hit)
    return reg


class Decision(BaseModel):
    status: Literal["xac_nhan", "loai_bo", "tu_dong"] = "xac_nhan"
    size: dict[str, float] = Field(default_factory=dict)    # thông số người dùng nhập (mm)


def apply_decisions(reg: Registry, decisions: dict[str, Decision], user: str = "nguoi_dung") -> Registry:
    """Xác nhận / loại bỏ / nhập thông số cho từng cấu kiện; không đọc lại bản vẽ."""
    reg = reg.model_copy(deep=True)
    unknown = set(decisions) - {c.id for c in reg.components}
    if unknown:
        raise ValueError(f"Không có cấu kiện: {', '.join(sorted(unknown))}")
    reg.issues = [i for i in reg.issues if i.kind not in ("xung_dot_kich_thuoc", "thieu_chi_tiet", "chi_tiet_khong_dung")]
    for c in reg.components:
        dec = decisions.get(c.id)
        if dec:
            c.status = dec.status
            if dec.size:
                bad = [k for k, v in dec.size.items() if not v > 0]
                if bad:
                    raise ValueError(f"{c.name}: thông số phải lớn hơn 0 ({', '.join(bad)}).")
                src = [o.evidence for o in c.occurrences] + c.details + [s.evidence for s in c.size_sources]
                ev = src[0].model_copy(update={"rule": "NGUOI_DUNG"})
                c.size_sources = [s for s in c.size_sources if s.source != "nguoi_dung"]
                c.size_sources.append(SizeValue(values=dec.size, source="nguoi_dung", evidence=ev))
        _resolve(c, reg)
    return score(reg)
