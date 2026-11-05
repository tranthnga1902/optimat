"""Bảng thống kê cốt thép trên bản vẽ (S07-01…04): đọc dòng, tính kg, kiểm sai đơn vị và dòng trùng.

Quy ước bảng đã chuẩn hóa (data/rules/bang_thep.csv):
    tiêu đề    = chữ có "THỐNG KÊ THÉP" / "THỐNG KÊ CỐT THÉP"
    dòng tiêu đề cột = một hàng chữ phía dưới tiêu đề, khớp ít nhất cột đường kính và chiều dài cắt
    dòng dữ liệu     = các hàng chữ bên dưới, mỗi chữ thuộc cột có tọa độ x gần nhất; dừng ở dòng "TỔNG", tiêu đề
                       khác hoặc khoảng trống lớn hơn ROW_GAP_STOP lần khoảng cách dòng đầu
    kg dòng    = tổng số thanh × chiều dài cắt (m) × khối lượng 1 m (data/rules/thep_kg_m.csv, có nguồn)
    tổng thanh = cột tổng số thanh; không có thì số thanh 1 cấu kiện × số cấu kiện
Chiều dài cắt lấy nguyên từ bảng (đã gồm neo, nối, uốn, móc theo chi tiết thiết kế); hệ thống không tự cộng neo, nối.
Thiếu số nào thì dòng đó để trống kèm lý do (Quy ước B7). Thép tính ở đây luôn có basis = "bang_thong_ke",
tách khỏi thép ước theo hàm lượng (steel.py).
Bảng ACAD_TABLE chưa đọc được (dxf_reader bỏ qua): phải phá bảng (EXPLODE) thành TEXT/MTEXT.
"""
from __future__ import annotations

import re
import hashlib
import json
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from statistics import median
from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator

from .. import config
from ..drawing.encoding import normalize
from .models import ROLE_WORK

RULE_FILE = config.DATA_DIR / "rules" / "bang_thep.csv"
UNIT_MASS_FILE = config.DATA_DIR / "rules" / "thep_kg_m.csv"
TITLE_RE = re.compile(r"\bthong ke (cot )?thep\b")
HEADER_ROWS_MAX = 4          # dòng tiêu đề cột nằm trong chừng này hàng chữ dưới tiêu đề bảng
ROW_GAP_STOP = 3.0
KG_TOL = 0.03                # lệch so với cột khối lượng của bảng quá 3% thì cảnh báo
LENGTH_MM = (100.0, 30000.0)  # chiều dài cắt hợp lý (mm); ngoài khoảng: nghi sai đơn vị


class RebarScope(BaseModel):
    """Phạm vi áp dụng bảng; tách khỏi vị trí hình vẽ và tên/số hiệu thanh."""
    levels: tuple[int, ...]
    element_code: str
    quantity_basis: Literal["total", "per_member"]

    @model_validator(mode="after")
    def _known_scope(self):
        if not self.levels or self.element_code not in {*ROLE_WORK.values(), "ALL"}:
            raise ValueError("Phạm vi cần tập tầng và nhóm cấu kiện đã có quy ước.")
        self.levels = tuple(sorted(set(self.levels)))
        return self


class RebarSourceRef(BaseModel):
    """Context do caller tạo từ byte upload gốc; không phải chứng thực do client tự khai."""
    source_id: str
    revision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def from_bytes(cls, data: bytes) -> RebarSourceRef:
        digest = hashlib.sha256(data).hexdigest()
        return cls(source_id=f"structural:{digest}", revision_sha256=digest)

    @model_validator(mode="after")
    def _source_namespace(self):
        if self.source_id != f"structural:{self.revision_sha256}":
            raise ValueError("source_id phải thuộc namespace structural của hash nguồn gốc.")
        return self


class RebarTableRef(RebarSourceRef):
    table_id: str = Field(min_length=1)


class RebarScopeAssignment(BaseModel):
    ref: RebarTableRef
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scope: RebarScope
    evidence: list[str] = Field(min_length=1)
    confirmed_by: str = Field(min_length=1)
    confirmed_at: datetime
    override_reason: Optional[str] = None

    @field_validator("confirmed_by", "override_reason")
    @classmethod
    def _nonblank_text(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Thông tin xác nhận không được chỉ có khoảng trắng.")
        return value

    @field_validator("evidence")
    @classmethod
    def _nonblank_evidence(cls, values):
        if any(not value.strip() for value in values):
            raise ValueError("Chứng cứ phạm vi không được để trống.")
        return values

    @field_validator("confirmed_at")
    @classmethod
    def _timezone_required(cls, value):
        if value.utcoffset() is None:
            raise ValueError("Thời điểm xác nhận phải có múi giờ.")
        return value


class RebarRow(BaseModel):
    table: str                                   # tiêu đề bảng
    row: int                                     # thứ tự dòng trong bảng (từ 1)
    element: str = ""                            # cấu kiện như ghi trong bảng (C1, DẦM D2, SÀN)
    element_code: Optional[str] = None           # mã công tác (COT, DAM...); trống: chưa có quy ước
    mark: str = ""
    shape: str = ""
    dia_mm: Optional[float] = None
    cut_length_mm: Optional[float] = None
    bars_per_member: Optional[float] = None
    members: Optional[float] = None
    total_bars: Optional[float] = None
    kg_per_m: Optional[float] = None
    kg_per_m_source: str = ""
    kg: Optional[float] = None                   # số hệ thống tính
    schedule_kg: Optional[float] = None          # số ghi trong bảng (chỉ đối chiếu)
    evidence: str = ""
    missing: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    table_id: str = ""                           # chỉ có nghĩa trong Drawing/phiên bản của lượt đọc
    scope: Optional[RebarScope] = None
    scope_source: Optional[Literal["title", "confirmed"]] = None
    scope_evidence: str = ""
    raw_cells: dict[str, str] = Field(default_factory=dict)   # ô gốc và đơn vị; không so trùng chỉ bằng None
    source_id: str = ""
    revision_sha256: str = ""

    @property
    def formula(self) -> str:
        n = "?" if self.total_bars is None else f"{self.total_bars:g}"
        L = "?" if self.cut_length_mm is None else f"{self.cut_length_mm / 1000:g}"
        m = "?" if self.kg_per_m is None else f"{self.kg_per_m:g}"
        return f"{n} thanh × {L} m × {m} kg/m (Ø{self.dia_mm:g})" if self.dia_mm else f"{n} thanh × {L} m × {m} kg/m"


class RebarTable(BaseModel):
    """Bảng trước dedup; resolve chỉ làm việc trên bản sao rows."""
    table_id: str
    title: str
    rows: list[RebarRow]
    scope_from_title: Optional[RebarScope] = None


class RebarTableManifest(BaseModel):
    ref: RebarTableRef
    title: str
    row_count: int
    content_sha256: str
    scope_from_title: Optional[RebarScope] = None


@lru_cache(maxsize=2)
def load_rules(path: str | None = None) -> tuple[tuple, tuple]:
    """(cột bảng: ((khóa, mẫu)...), tên cấu kiện: ((mã công tác, mẫu)...))."""
    rows = pd.read_csv(Path(path or RULE_FILE), dtype=str, keep_default_na=False).to_dict("records")
    cols = tuple((r["khoa"], re.compile(r["mau"])) for r in rows if r["nhom"] == "cot_bang")
    words = tuple((r["khoa"], re.compile(r["mau"])) for r in rows if r["nhom"] == "ten_cau_kien")
    return cols, words


@lru_cache(maxsize=2)
def unit_mass(path: str | None = None) -> dict[float, tuple[float, str]]:
    """{đường kính mm: (kg/m, nguồn)}."""
    df = pd.read_csv(Path(path or UNIT_MASS_FILE), dtype={"nguon": str})
    return {float(r.duong_kinh_mm): (float(r.kg_m), str(r.nguon)) for r in df.itertuples()}


def _num(text: str) -> Optional[float]:
    """Giữ quy ước một dấu; "1.200,5" / "1,200.5" = 1200.5 khi nhóm nghìn hợp lệ."""
    m = re.search(r"\d[\d.,]*", text or "")
    if not m:
        return None
    s = m.group(0)
    if "." in s and "," in s:
        if re.fullmatch(r"\d{1,3}(\.\d{3})+,\d+", s):
            return float(s.replace(".", "").replace(",", "."))
        if re.fullmatch(r"\d{1,3}(,\d{3})+\.\d+", s):
            return float(s.replace(",", ""))
        return None
    s = s.rstrip(".,")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def element_code(text: str) -> Optional[str]:
    """Cấu kiện ghi trong bảng -> mã công tác: ký hiệu (C1, D2, M1...) theo ky_hieu_cau_kien.csv, rồi tên (CỘT, SÀN)."""
    from .structural import element_of
    words = [w for w in re.split(r"[\s(),:;-]+", text) if w]
    for w in reversed(words):
        if (e := element_of(w)) and e[0] in ROLE_WORK:
            return ROLE_WORK[e[0]]
    plain = re.sub(r"\s+", " ", normalize(" ".join(w for w in words if not element_of(w)))).strip()
    for code, pat in load_rules()[1]:
        if pat.search(plain):
            return code
    return None


def _rows(texts, tol: float) -> list[list]:
    """Gom chữ thành hàng theo y (trên xuống)."""
    out: list[list] = []
    for t in sorted(texts, key=lambda t: -t.y):
        if out and abs(out[-1][0].y - t.y) <= tol:
            out[-1].append(t)
        else:
            out.append([t])
    return out


def _header(row) -> dict[str, tuple[float, str]]:
    cols = {}
    for t in row:
        key = normalize(t.text).strip()
        for name, pat in load_rules()[0]:
            if name not in cols and pat.search(key):
                cols[name] = (t.x, key)
                break
    return cols


def read_table(drawing, title) -> tuple[list[RebarRow], list[str]]:
    """Một bảng thống kê thép có tiêu đề title (TextItem)."""
    below = [t for t in drawing.texts if t.y < title.y and t is not title]
    h = title.height or median([t.height for t in below if t.height] or [0]) or 1.0
    tol = 0.6 * h
    rows = _rows(below, tol)
    name = title.text.strip()
    header, hy = None, None
    # Tách cụm cột theo X trước: tên cột lặp ở X khác thuộc header khác, không lấy lần khớp đầu toàn hàng.
    for index, r in enumerate(rows[:HEADER_ROWS_MAX * 3]):
        chunks, chunk, keys = [], [], set()
        ordered = sorted(r, key=lambda t: t.x)
        gaps = [b.x-a.x for a, b in zip(ordered, ordered[1:]) if b.x > a.x]
        gap = median(gaps) if gaps else 10*h
        for t in ordered:
            names = set(_header([t]))
            if chunk and (keys & names or t.x-chunk[-1].x > 2*gap):
                chunks.append(chunk)
                chunk, keys = [], set()
            chunk.append(t)
            keys.update(names)
        if chunk:
            chunks.append(chunk)
        local = []
        for chunk in chunks:
            if len(_header(chunk)) < 2:
                continue
            xs = sorted({t.x for t in chunk})
            pad = median([b-a for a, b in zip(xs, xs[1:])])/2 if len(xs) > 1 else 5*h
            if xs[0]-pad <= title.x <= xs[-1]+pad:
                local.append((chunk, xs[0]-pad, xs[-1]+pad))
        if len(local) > 1:
            return [], [f"Bảng '{name}': miền tiêu đề cột mơ hồ giữa các bảng, bỏ qua bảng."]
        if not local:
            continue
        chunk, left, right = local[0]
        cols = _header(chunk)
        hy = min(t.y for t in chunk)
        for extra in rows[index+1:index+HEADER_ROWS_MAX]:
            if "duong_kinh" in cols and "chieu_dai" in cols:
                break
            cells = [t for t in extra if left <= t.x <= right]
            if not cells:
                break
            more = _header(cells)
            if any(TITLE_RE.search(normalize(t.text)) for t in cells) or (
                not more and any(_num(t.text) is not None for t in cells)
            ):
                break
            if any(k in cols and abs(cols[k][0]-value[0]) > tol for k, value in more.items()):
                return [], [f"Bảng '{name}': miền tiêu đề cột mơ hồ, bỏ qua bảng."]
            cols.update(more)
            if more:
                hy = min(hy, min(t.y for t in cells))
        if "duong_kinh" in cols and "chieu_dai" in cols:
            header = cols
        break
    if header is None:
        return [], [f"Bảng '{name}': không thấy dòng tiêu đề cột (cần cột đường kính và chiều dài cắt), bỏ qua bảng."]
    xs = sorted(x for x, _ in header.values())
    gap = median([b - a for a, b in zip(xs, xs[1:])]) if len(xs) > 1 else 10 * h
    lo, hi = xs[0] - gap / 2, xs[-1] + gap / 2
    length_in_m = "(m)" in header["chieu_dai"][1]
    data = _rows([t for t in below if t.y < hy - tol and lo <= t.x <= hi], tol)
    masses = unit_mass()
    out, warnings, last_y, step, element = [], [], hy, None, ""
    for r in data:
        y = r[0].y
        if step is not None and last_y - y > ROW_GAP_STOP * step:
            break
        cells: dict[str, str] = {}
        for t in sorted(r, key=lambda t: t.x):
            k = min(header, key=lambda c: abs(header[c][0] - t.x))
            cells[k] = (cells.get(k, "") + " " + t.text).strip()
        joined = normalize(" ".join(cells.values()))
        if TITLE_RE.search(joined) or re.match(r"\s*tong\b", joined):
            break
        if _num(cells.get("duong_kinh", "")) is None and _num(cells.get("chieu_dai", "")) is None:
            break
        step = step or (last_y - y)
        last_y = y
        element = cells.get("cau_kien") or element
        row = RebarRow(table=name, row=len(out) + 1, element=element, element_code=element_code(element) if element else None,
                       mark=cells.get("so_hieu", ""), shape=cells.get("hinh_dang", ""),
                       dia_mm=_num(cells.get("duong_kinh", "")), schedule_kg=_num(cells.get("khoi_luong", "")),
                       bars_per_member=_num(cells.get("sl_1ck", "")), members=_num(cells.get("so_ck", "")),
                       total_bars=_num(cells.get("tong_thanh", "")),
                       raw_cells={**cells, "_length_unit": "m" if length_in_m else "mm"},
                       evidence=f"{name}, dòng {len(out) + 1} (x={r[0].x:.0f}, y={y:.0f}, layer {r[0].layer}): "
                                + " | ".join(f"{k}={v}" for k, v in cells.items()))
        L = _num(cells.get("chieu_dai", ""))
        if L is not None and length_in_m:
            L *= 1000
        if L is None:
            row.missing.append("chiều dài cắt (gồm neo, nối, uốn, móc theo chi tiết)")
        elif not LENGTH_MM[0] <= L <= LENGTH_MM[1]:
            row.missing.append(f"chiều dài cắt {L:g} mm ngoài khoảng {LENGTH_MM[0]:g}–{LENGTH_MM[1]:g} mm: nghi sai đơn vị (m/mm)")
        else:
            row.cut_length_mm = L
        product = row.bars_per_member * row.members if None not in (row.bars_per_member, row.members) else None
        if row.total_bars is None:
            row.total_bars = product
        elif product is not None and abs(product - row.total_bars) > 0.5:
            row.notes.append(f"tổng số thanh {row.total_bars:g} ≠ {row.bars_per_member:g} × {row.members:g} = {product:g}: "
                             "kiểm tra đếm trùng; đang dùng cột tổng")
        if row.total_bars is None:
            row.missing.append("số thanh")
        if row.dia_mm is None:
            row.missing.append("đường kính")
        elif row.dia_mm not in masses:
            row.missing.append(f"khối lượng 1 m của Ø{row.dia_mm:g} (chưa có trong thep_kg_m.csv)")
        else:
            row.kg_per_m, row.kg_per_m_source = masses[row.dia_mm]
        if row.element_code is None:
            row.notes.append(f"cấu kiện '{element or '(trống)'}' chưa có quy ước: Not supported, không cộng vào cốt thép")
        if not row.missing:
            row.kg = round(row.total_bars * row.cut_length_mm / 1000 * row.kg_per_m, 2)
            if row.schedule_kg:
                ratio = row.kg / row.schedule_kg
                if abs(ratio - 1) > KG_TOL:
                    unit = " (lệch khoảng 1000 lần: bảng ghi tấn hay chiều dài theo m?)" if 500 < ratio < 2000 or 5e-4 < ratio < 2e-3 else ""
                    row.notes.append(f"kg tính {row.kg:g} ≠ kg ghi trong bảng {row.schedule_kg:g}{unit}: cần review")
        for n in row.notes:
            warnings.append(f"Bảng '{name}' dòng {row.row} ({element} {row.mark}): {n}.")
        out.append(row)
    if not out:
        warnings.append(f"Bảng '{name}': có dòng tiêu đề cột nhưng không đọc được dòng thép nào.")
    return out, warnings


def _title_scope(title: str) -> RebarScope | None:
    """Chỉ nhận tiêu đề ghi tầng và nghĩa tổng; không suy từ vị trí/layer hay tên C1."""
    text = re.sub(r"\s+", " ", normalize(title)).strip()
    match = re.fullmatch(
        r"(?:bang )?thong ke (?:cot )?thep "
        r"(.+?) "
        r"(?:tang|lau) (\d+(?:\s*,\s*\d+)*) \(tong (toan tang|pham vi)\)", text)
    if not match:
        return None
    levels = tuple(sorted({int(n) for n in match[2].split(",")}))
    if len(levels) > 1 and match[3] != "pham vi":
        return None
    code = "ALL" if match[1] == "toan bo cau kien" else next(
        (code for code, pattern in load_rules()[1] if pattern.fullmatch(match[1])), None)
    return RebarScope(levels=levels, element_code=code, quantity_basis="total") if code else None


def _table_content(rows: list[RebarRow]) -> Counter:
    """So bảng có bội số, cả hình dạng/ô chưa đọc được; không so nguồn tọa độ hay tổng kg đơn thuần."""
    return Counter((normalize(r.element), normalize(r.mark), normalize(r.shape), r.element_code,
                    r.dia_mm, r.cut_length_mm, r.bars_per_member, r.members, r.total_bars,
                    r.kg_per_m, r.kg_per_m_source, r.kg, r.schedule_kg,
                    tuple(r.missing), tuple(r.notes), tuple(sorted(r.raw_cells.items()))) for r in rows)


def collect_rebar_tables(drawing) -> tuple[list[RebarTable], list[str]]:
    """Thu từng bảng đúng một lần, kể cả bảng rỗng; chưa loại bản sao hoặc áp mapping."""
    tables, warnings = [], []
    titles = sorted((t for t in drawing.texts if TITLE_RE.search(normalize(t.text))),
                    key=lambda t: (-t.y, t.x, t.text))
    for index, title in enumerate(titles):
        r, w = read_table(drawing, title)
        warnings += w
        table_id = f"table:{title.x:g}:{title.y:g}:{index}"
        scope = _title_scope(title.text)
        if scope and scope.element_code != "ALL" and any(
                row.element_code not in (None, scope.element_code) for row in r):
            warnings.append(f"Bảng {table_id}: nhóm cấu kiện trong tiêu đề khác nội dung, chưa xác định phạm vi.")
            scope = None
        tables.append(RebarTable(table_id=table_id, title=title.text, rows=r, scope_from_title=scope))
    return tables, warnings


def _content_sha256(rows: list[RebarRow]) -> str:
    # Sắp theo JSON, không so trực tiếp tuple có cả None/số; giữ số lần xuất hiện mỗi dòng.
    content = sorted((json.dumps(key, ensure_ascii=False, allow_nan=False), count)
                     for key, count in _table_content(rows).items())
    return hashlib.sha256(json.dumps(content, ensure_ascii=False).encode("utf-8")).hexdigest()


def table_manifest(tables: list[RebarTable], *, source: RebarSourceRef) -> list[RebarTableManifest]:
    """Manifest từ bảng đã thu, không đọc graph/bảng lần hai và không loại bản sao."""
    return [RebarTableManifest(ref=RebarTableRef(**source.model_dump(), table_id=t.table_id),
                               title=t.title, row_count=len(t.rows), content_sha256=_content_sha256(t.rows),
                               scope_from_title=t.scope_from_title.model_copy(deep=True) if t.scope_from_title else None)
            for t in tables]


def resolve_rebar_tables(tables: list[RebarTable], *, source: RebarSourceRef | None = None,
                         assignments: list[RebarScopeAssignment] | None = None
                         ) -> tuple[list[RebarRow], list[str]]:
    """Áp mapping trên bảng mới thu từ MỘT Drawing; caller phải tạo source từ byte upload thực.

    JSON-only rebar/nhãn confirmed không phải đầu vào cho đường này. Validate toàn bộ mapping trước khi copy/áp.
    """
    by_id = {t.table_id: t for t in tables}
    if len(by_id) != len(tables):
        raise ValueError("table_id trùng: chỉ resolve bảng từ một Drawing/phiên bản mỗi lần.")
    mapping: dict[str, RebarScopeAssignment] = {}
    for assignment in assignments or []:
        ref = assignment.ref
        if source is None or (ref.source_id, ref.revision_sha256) != (source.source_id, source.revision_sha256):
            raise ValueError(f"Bảng {ref.table_id}: nguồn/revision không khớp byte upload, cần gửi lại đúng file.")
        table = by_id.get(ref.table_id)
        if table is None:
            raise ValueError(f"Bảng {ref.table_id}: không tồn tại trong nguồn vừa đọc.")
        if ref.table_id in mapping:
            raise ValueError(f"Bảng {ref.table_id}: có nhiều assignment, cần một xác nhận duy nhất.")
        if assignment.content_sha256 != _content_sha256(table.rows):
            raise ValueError(f"Bảng {ref.table_id}: content_sha256 đã thay đổi, cần xác nhận manifest mới.")
        known_codes = {row.element_code for row in table.rows if row.element_code is not None}
        if assignment.scope.element_code != "ALL" and known_codes - {assignment.scope.element_code}:
            raise ValueError(f"Bảng {ref.table_id}: nhóm scope {assignment.scope.element_code} không khớp nhóm dòng "
                             f"{', '.join(sorted(known_codes))}; override_reason không đổi phân loại cấu kiện.")
        title_scope = _title_scope(table.title)
        if title_scope is not None and (assignment.scope != title_scope or table.scope_from_title is None) and not assignment.override_reason:
            raise ValueError(f"Bảng {ref.table_id}: scope trái tiêu đề cần override_reason.")
        mapping[ref.table_id] = assignment

    rows, warnings, seen, pending = [], [], [], set()
    for table in tables:
        assignment = mapping.get(table.table_id)
        scope = assignment.scope if assignment else table.scope_from_title
        table_id = table.table_id
        r = [row.model_copy(deep=True) for row in table.rows]
        for row in r:
            row.table_id = table_id
            row.source_id = source.source_id if source else ""
            row.revision_sha256 = source.revision_sha256 if source else ""
            row.scope = scope.model_copy(deep=True) if scope else None
            row.scope_source = "confirmed" if assignment else "title" if scope else None
            row.scope_evidence = table.title + (" | " + assignment.model_dump_json() if assignment else "")
        if not r:
            continue
        if scope is not None and scope.quantity_basis == "per_member":
            pending.add(table_id)
            warnings.append(f"Bảng {table_id}: số lượng một mẫu chưa phải tổng phạm vi; giữ nguyên, chờ xác nhận.")
        if scope is None and source is not None:
            pending.add(table_id)
            warnings.append(f"Bảng {table_id}: chưa có phạm vi được xác định; giữ nguyên, chờ xác nhận.")
        content = _table_content(r)
        duplicate = next((tid for tid, s, c in seen if scope is not None and scope.quantity_basis == "total"
                          and scope == s and content == c), None)
        if duplicate is not None:
            warnings.append(f"Bảng {table_id} '{table.title}' trùng hệt bảng {duplicate}, cùng phạm vi tổng "
                            f"{scope.element_code} tầng {scope.levels} đã đọc/xác nhận: giữ {duplicate}, không cộng lần hai.")
            continue
        for tid, previous_scope, previous_content in seen:
            overlap = (scope is not None and previous_scope is not None
                       and (scope.element_code == previous_scope.element_code
                            or "ALL" in (scope.element_code, previous_scope.element_code))
                       and bool(set(scope.levels) & set(previous_scope.levels)))
            unknown = (scope is None or previous_scope is None) and bool(content.keys() & previous_content.keys())
            if overlap or unknown:
                pending.update((tid, table_id))
                warnings.append(f"Bảng {tid} và {table_id}: nghi lặp/chồng phạm vi hoặc cùng phạm vi khác nội dung; "
                                "giữ cả hai, chờ xác nhận, chưa coi tổng là hoàn chỉnh.")
        seen.append((table_id, scope, content))
        rows += r
    for row in rows:
        if row.table_id in pending:
            row.missing.append("phạm vi/nghĩa số lượng bảng thép chưa xác nhận hoặc nghi lặp/chồng: chờ xác nhận")
    if rows:
        warnings.append("Cốt thép theo bảng thống kê: chiều dài cắt lấy nguyên từ bảng (đã gồm neo, nối, uốn, móc theo "
                        "thiết kế), hệ thống không tự cộng neo, nối.")
    return rows, warnings


def read_rebar_schedules(drawing) -> tuple[list[RebarRow], list[str]]:
    """Wrapper cũ: cùng pipeline collect/resolve, giữ tuple rows/warnings và không nhận mapping JSON-only."""
    tables, warnings = collect_rebar_tables(drawing)
    rows, resolved_warnings = resolve_rebar_tables(tables)
    return rows, warnings + resolved_warnings
