"""Đối chiếu một bản vẽ với Quy ước bản vẽ v1.0 (mục A4) và gắn nguồn cho từng bộ phận nhận được.

    analyze(path) -> ConventionReport
        checks : mỗi điều khoản QU-01…QU-23 một kết quả: dat | vi_pham | chua_kiem | khong_ap_dung, kèm bằng chứng
        plans  : từng mặt bằng: tường, cửa, cột kèm nguồn
                     quy_uoc    khớp ký hiệu của quy ước (ghi mã QU, mã ký hiệu trong concepts.csv)
                     hinh_hoc   không theo quy ước, hệ thống đoán bằng hình học: người dùng phải duyệt
                     nguoi_dung người dùng chỉ định layer tường
                 và mức tin cậy theo mục B4 (cao ≥ 0,8; trung bình 0,6–0,8; thấp < 0,6)
Có vi phạm mức B: bản vẽ "ngoài quy ước", vẫn bóc nhưng không tính vào số liệu cam kết tầng 1.
Hàm này chỉ đọc và báo, không đổi kết quả nhận dạng.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Literal, Optional

import numpy as np
from pydantic import BaseModel, Field

from .. import config
from ..catalog.repository import Catalog
from ..rough.areas import plan_geometry, room_labels
from ..rough.columns import detect_columns
from ..rough.walls import review_input_from_takeoff
from .concepts import load_clauses, match_block, match_layer
from .dxf_reader import Drawing, crop, read_drawing
from .encoding import normalize
from .layer_classifier import LayerClass
from .material_notes import find_material_notes
from .plans import find_plans, has_only_other_plans
from .takeoff import takeoff_plans
from .walls import STRIP_CONFIDENCE, _pairs

Status = Literal["dat", "vi_pham", "chua_kiem", "khong_ap_dung"]
HATCH_WALL_SHARE = 0.8        # QU-10 đạt khi ít nhất phần này chiều dài tường có hatch trong bề dày
COLUMN_SIDE_QU16 = (200.0, 600.0)


class Check(BaseModel):
    ma: str
    nhom: str
    dieu_khoan: str
    muc: str
    cach_kiem: str
    trang_thai: Status
    ket_qua: str                                         # một câu cho người đọc
    bang_chung: list[str] = Field(default_factory=list)


class Element(BaseModel):
    id: str
    khai_niem: str                                       # Tường 220, Cửa đi, Cột...
    nguon: Literal["quy_uoc", "hinh_hoc", "nguoi_dung"]
    qu: str                                              # điều khoản làm căn cứ
    ly_do: str
    do_tin_cay: Optional[float] = None
    muc_tin_cay: str = ""                                # cao | trung_binh | thap (B4)
    hinh: list[float] = Field(default_factory=list)      # tường: x1, y1, x2, y2; cửa: x, y; cột: x, y, b, h (mm)
    dai_m: Optional[float] = None


class PlanConcepts(BaseModel):
    name: str
    title: str = ""                                      # tiêu đề gốc khi tên đã đánh số thêm (QU-05)
    level_m: Optional[float] = None
    height_mm: Optional[float] = None
    bbox: list[float]
    walls: list[Element] = Field(default_factory=list)
    openings: list[Element] = Field(default_factory=list)
    columns: list[Element] = Field(default_factory=list)
    rooms: list[str] = Field(default_factory=list)
    closed: bool = False
    gt: Optional[dict] = None                            # chấm với đáp án đo tay (recognition_eval) khi có


class ConventionReport(BaseModel):
    file: str
    trong_quy_uoc: Optional[bool]                        # None: file không có mặt bằng kiến trúc (không áp dụng)
    checks: list[Check]
    plans: list[PlanConcepts]
    layers: dict[str, str] = Field(default_factory=dict)          # layer -> vai trò
    layer_signal: dict[str, str] = Field(default_factory=dict)    # layer -> mã ký hiệu đã khớp (L05...)
    warnings: list[str] = Field(default_factory=list)


def band(conf: Optional[float]) -> str:
    if conf is None:
        return ""
    return "cao" if conf >= 0.8 else "trung_binh" if conf >= 0.6 else "thap"


def _layer_norm(name: str) -> str:
    return normalize(name).replace("_", " ").replace("-", " ")


# ------------------------------------------------------------------ nguồn của từng bộ phận (S9.5)
def wall_elements(result, drawing: Drawing, user_layers: bool) -> list[Element]:
    auto = set(result.auto_wall_layers)
    out = []
    for w in result.walls:
        cls = f"lớp {w.thickness_class}" + (f" (đo {w.thickness_mm:.0f} mm)" if w.thickness_mm else "")
        if abs(w.confidence - STRIP_CONFIDENCE) < 1e-9:
            src, qu, why = "hinh_hoc", "QU-09", f"tường một nét + hatch trên layer {w.layer}: không phải hai nét song song"
        elif w.confidence <= 0.5:
            src, qu, why = "hinh_hoc", "QU-10", (f"cặp nét {cls} có hatch nhưng nằm trên layer {w.layer} (không phải layer tường): "
                                               "có thể là bồn hoa, quầy xây")
        elif user_layers:
            src, qu, why = "nguoi_dung", "QU-08", f"layer {w.layer} do người dùng chỉ định là layer tường; cặp nét {cls}"
        elif w.layer in auto:
            src, qu, why = "hinh_hoc", "QU-08", (f"layer {w.layer} không theo tên quy ước, tự nhận là layer tường vì có nhiều "
                                               f"cặp nét song song; cặp nét {cls}")
        else:
            s = match_layer(_layer_norm(w.layer))
            sig = f"ký hiệu {s.ma} \"{s.mau}\"" if s else "vai trò layer tường"
            src, qu, why = "quy_uoc", "QU-08, QU-09", f"layer {w.layer} khớp {sig}; hai nét song song {cls}"
        out.append(Element(id=w.wall_id, khai_niem=f"Tường {w.thickness_class}", nguon=src, qu=qu, ly_do=why,
                           do_tin_cay=w.confidence, muc_tin_cay=band(w.confidence),
                           hinh=[round(v, 1) for v in (w.x1, w.y1, w.x2, w.y2)], dai_m=round(w.length_mm / 1000, 2)))
    return out


def opening_elements(result, drawing: Drawing) -> list[Element]:
    out = []
    for i, o in enumerate(result.openings, start=1):
        name = "Cửa sổ" if o.kind == "window" else "Cửa đi" if o.kind == "door" else "Lỗ mở (block)"
        ev = o.evidence or ""
        if ev.startswith("block"):
            blk = ev.split(" ", 1)[1] if " " in ev else o.name
            s = match_block(blk)
            why = f"block {blk} khớp ký hiệu {s.ma} (tiền tố {s.mau})" if s else f"block {blk} trên layer cửa hoặc theo quy tắc block"
            src = "quy_uoc"
        elif ev in ("cung cánh cửa", "nét kính"):
            src, why = "quy_uoc", f"khe tường có {ev}"
        else:
            src, why = "hinh_hoc", ev or "không rõ dấu hiệu"
        extra = [] if o.wall_id else ["chưa gắn vào tường nào, không trừ"]
        if o.kind in ("door", "window") and not ev.startswith("block"):
            extra.append("chưa có chiều cao, không trừ" if o.height_mm is None
                         else f"cao {o.height_mm:.0f} mm theo thông số cửa của dự án (chưa đọc bảng thống kê cửa, QU-15)")
        out.append(Element(id=f"O{i}", khai_niem=name, nguon=src, qu="QU-14",
                           ly_do="; ".join([why] + extra) + ("; chưa có rộng, không trừ" if o.width_mm is None
                                                              else f"; rộng {o.width_mm:.0f} mm"), hinh=[round(o.x, 1), round(o.y, 1)]))
    return out


def column_elements(columns) -> list[Element]:
    lo, hi = COLUMN_SIDE_QU16
    out = []
    for c in columns:
        inside = lo <= min(c.b_mm, c.h_mm) and max(c.b_mm, c.h_mm) <= hi
        out.append(Element(
            id=c.id, khai_niem="Cột", nguon="quy_uoc" if inside else "hinh_hoc", qu="QU-16",
            ly_do=f"hình chữ nhật kín tô đặc {c.b_mm:.0f}×{c.h_mm:.0f} mm"
                  + ("" if inside else f", ngoài dải cạnh {lo:.0f}–{hi:.0f} mm của QU-16"),
            hinh=[c.x, c.y, c.b_mm, c.h_mm]))
    return out


def _hatched_share(walls, drawing: Drawing) -> tuple[float, list[str]]:
    """QU-10, ước lượng: phần chiều dài tường có nét hatch (hatch bị phá) hoặc tâm vùng tô nằm trong bề dày tường."""
    pts = [((s.x1 + s.x2) / 2, (s.y1 + s.y2) / 2) for s in drawing.segments if s.kind == "hatch"]
    pts += [(sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
            for h in drawing.hatches for poly in h.polygons if poly]
    if not walls:
        return 1.0, []
    P = np.array(pts) if pts else np.zeros((0, 2))
    total = hit = 0.0
    bare = []
    for w in walls:
        L = math.hypot(w.x2 - w.x1, w.y2 - w.y1)
        if L == 0:
            continue
        total += L
        ux, uy = (w.x2 - w.x1) / L, (w.y2 - w.y1) / L
        half = (w.thickness_mm or float(w.thickness_class)) / 2
        if len(P):
            dx, dy = P[:, 0] - w.x1, P[:, 1] - w.y1
            along, across = dx * ux + dy * uy, np.abs(dx * -uy + dy * ux)
            if np.any((along >= 0) & (along <= L) & (across <= half)):
                hit += L
                continue
        bare.append(w.wall_id)
    return (hit / total if total else 1.0), bare


# ------------------------------------------------------------------ đối chiếu từng điều khoản (S9.4)
def analyze(path: str, floor_height_mm: float | None = None, layer_overrides: dict | None = None,
            catalog: Catalog | None = None, gt_folder: str | None = None) -> ConventionReport:
    """Đọc file, bóc tách từng mặt bằng rồi đối chiếu (dùng cho scripts/concept_report.py)."""
    drawing = read_drawing(path, layer_overrides)
    takeoffs = takeoff_plans(drawing, floor_height_mm, catalog or Catalog.load())
    return analyze_drawing(drawing, takeoffs, Path(path).name, layer_overrides, gt_folder)


def analyze_drawing(drawing: Drawing, takeoffs: list, file_name: str, layer_overrides: dict | None = None,
                    gt_folder: str | None = None) -> ConventionReport:
    """Đối chiếu bản vẽ đã đọc và kết quả takeoff_plans có sẵn (trang kiểm tra dùng lại, không đọc file lần nữa)."""
    path = file_name
    regions = {p.name: p for p in find_plans(drawing)}
    structural_only = not regions and has_only_other_plans(drawing)
    user_layers = drawing.user_wall_layers or bool(layer_overrides and any(v == "WALL" for v in layer_overrides.values()))
    from .recognition_eval import evaluate_plan, load_ground_truth
    gts = [g for g in load_ground_truth(gt_folder) if g.get("file") == Path(file_name).name]

    plans: list[PlanConcepts] = []
    per_plan: dict[str, dict] = {}
    for p in takeoffs:
        sub = crop(drawing, p.bbox) if p.name in regions else drawing
        res = p.result
        cols = detect_columns(sub)
        walls_in, _, _ = review_input_from_takeoff(res)
        labels = room_labels(sub)
        geom = plan_geometry([w for w in walls_in if w.masonry], labels)
        gt = next((g for g in gts if g.get("plan") == p.name), None)
        plans.append(PlanConcepts(
            name=p.name, title=regions[p.name].title if p.name in regions else "", level_m=p.level_m,
            height_mm=p.height_mm, bbox=p.bbox, walls=wall_elements(res, sub, user_layers),
            openings=opening_elements(res, sub), columns=column_elements(cols),
            rooms=[f"{t} ({k})" for k, t, _, _ in labels], closed=geom.closed,
            gt=evaluate_plan(gt, [w for w in res.walls if w.is_masonry]) if gt else None))
        per_plan[p.name] = {"res": res, "sub": sub, "cols": cols, "labels": labels}

    checks = _checks(path, drawing, regions, plans, per_plan, structural_only)
    b_fail = [c.ma for c in checks if c.trang_thai == "vi_pham" and c.muc == "B"]
    layer_signal = {}
    for name in drawing.layers:
        s = match_layer(_layer_norm(name))
        if s:
            layer_signal[name] = s.ma
    warnings = []
    if not gts:
        warnings.append("Chưa có đáp án đo tay cho bản vẽ này (data/ground_truth/plans): chưa chấm được độ chính xác.")
    return ConventionReport(file=Path(file_name).name, trong_quy_uoc=(not b_fail) if regions or plans else None, checks=checks, plans=plans,
                            layers={k: v.value for k, v in drawing.layer_classes.items()}, layer_signal=layer_signal,
                            warnings=warnings)


def _checks(path, drawing: Drawing, regions, plans: list[PlanConcepts], per_plan, structural_only) -> list[Check]:
    out: dict[str, tuple[Status, str, list[str]]] = {}
    texts_norm = [normalize(t.text) for t in drawing.texts]
    has_plans = bool(regions)
    arch_na = ("khong_ap_dung", "File không có mặt bằng kiến trúc.", [])

    # Định dạng và đơn vị
    suffix = Path(path).suffix.lower()
    out["QU-01"] = ("dat", f"File {suffix}.", []) if suffix in (".dxf", ".dwg") else ("vi_pham", f"File {suffix}.", [])
    ins = int(drawing.doc.header.get("$INSUNITS", 0) or 0) if drawing.doc is not None else None
    walls_all = [w for p in plans for w in p.walls]
    thick = [float(w.ly_do.split("đo ")[1].split(" mm")[0]) for w in walls_all if "đo " in w.ly_do]
    ev = [f"$INSUNITS = {ins}" + (" (không khai báo, coi là mm)" if ins == 0 else ""), f"hệ số đổi sang mm: {drawing.unit_scale:g}"]
    if thick:
        ev.append(f"chiều dày tường đo được {min(thick):.0f}–{max(thick):.0f} mm trên {len(thick)} tường")
    if has_plans and not walls_all:
        out["QU-02"] = ("vi_pham", "Không nhận được tường nào trong dải 85–370 mm: có thể sai đơn vị hoặc tỷ lệ.", ev)
    elif not has_plans:
        out["QU-02"] = ("chua_kiem", "Không có mặt bằng kiến trúc để kiểm chiều dày tường.", ev)
    else:
        out["QU-02"] = ("dat", "Chiều dày tường đo được nằm trong dải 85–370 mm" + (", đơn vị không khai báo nên coi là mm." if ins == 0 else "."), ev)
    enc = Counter(t.encoding for t in drawing.texts)
    vni = [t.text[:30] for t in drawing.texts if t.encoding in ("vni", "ma_cu_2")][:5]
    out["QU-03"] = (("vi_pham", f"{enc['vni'] + enc['ma_cu_2']} chữ dùng bảng mã VNI hoặc mã cũ khác "
                     "(đã tự chuyển sang Unicode, kiểm tra lại chữ).", vni) if vni else
                    ("dat", "Chữ dùng Unicode hoặc TCVN3.", [f"{k}: {v} chữ" for k, v in enc.most_common()]))

    # Tổ chức mặt bằng
    if has_plans:
        out["QU-04"] = ("dat", f"Tìm được {len(regions)} tiêu đề mặt bằng tầng.", list(regions))
    elif structural_only:
        out["QU-04"] = ("khong_ap_dung", "File chỉ có mặt bằng kết cấu, móng, điện nước…: không có mặt bằng kiến trúc.", [])
    else:
        out["QU-04"] = ("vi_pham", "Không có tiêu đề \"MẶT BẰNG …\": cả file được đo như một mặt bằng.", [])
    renamed = [p for p in plans if p.title]
    out["QU-05"] = (("vi_pham", f"{len(renamed)} tiêu đề trùng tên; hệ thống đã đánh số thêm để không ghi đè.",
                     [f"\"{p.title}\" → \"{p.name}\"" for p in renamed]) if renamed else
                    ("dat", "Tên các mặt bằng không trùng nhau.", []) if has_plans else arch_na)
    no_level = [p.name for p in plans if p.level_m is None]
    out["QU-06"] = (arch_na if not has_plans else
                    ("vi_pham", "Mặt bằng chưa có cao độ sàn: chiều cao tầng lấy mặc định.", no_level) if no_level else
                    ("dat", "Mọi mặt bằng có cao độ sàn.", [f"{p.name}: {p.level_m:+.2f} m ({regions[p.name].level_source})" for p in plans
                                                          if p.name in regions]))
    out["QU-07"] = ("chua_kiem", "Chưa so hệ trục giữa các tầng (giai đoạn 3).", []) if has_plans else arch_na

    # Layer
    wall_layers = sorted({l for v in per_plan.values() for l in v["res"].wall_layers})
    auto = sorted({l for v in per_plan.values() for l in v["res"].auto_wall_layers})
    roles = Counter(drawing.layer_classes.values())
    ev = [f"{r.value}: {n} layer" for r, n in roles.most_common()] + [f"layer làm tường: {', '.join(wall_layers) or '—'}"]
    if not has_plans:
        out["QU-08"] = arch_na
    elif auto:
        out["QU-08"] = ("vi_pham", f"Tường nằm trên layer không theo tên quy ước, hệ thống tự nhận bằng hình học: {', '.join(auto)}.", ev)
    else:
        out["QU-08"] = ("dat", "Tường nằm trên layer đặt tên theo quy ước.", ev)

    # Tường
    strips = [(p.name, w) for p in plans for w in p.walls if w.qu == "QU-09" and w.nguon == "hinh_hoc"]
    empty = [p.name for p in plans if not p.walls]
    if not has_plans:
        out["QU-09"] = arch_na
    elif empty or strips:
        ev = [f"{n}: không nhận được tường nào" for n in empty]
        if strips:
            ev.append(f"{len(strips)} tường một nét + hatch, dài {sum(w.dai_m or 0 for _, w in strips):.1f} m: "
                      + ", ".join(f"{n} {w.id}" for n, w in strips[:12]))
        out["QU-09"] = ("vi_pham", "Có tường không vẽ bằng hai nét song song." if strips else "Có mặt bằng không có tường hai nét.", ev)
    else:
        by = Counter()
        for w in walls_all:
            by[w.khai_niem] += w.dai_m or 0
        out["QU-09"] = ("dat", "Tường vẽ bằng hai nét song song đúng dải chiều dày.", [f"{k}: {v:.1f} m" for k, v in sorted(by.items())])
    if has_plans:
        shares, bare_all = [], []
        for name, v in per_plan.items():
            share, bare = _hatched_share(v["res"].walls, v["sub"])
            shares.append(f"{name}: {share:.0%} chiều dài tường có hatch")
            bare_all += [f"{name}: {b}" for b in bare]
        total = [float(s.split(": ")[1].split("%")[0]) / 100 for s in shares]
        ok = all(t >= HATCH_WALL_SHARE for t in total)
        out["QU-10"] = (("dat" if ok else "vi_pham"),
                        ("Tường có hatch trong bề dày" if ok else f"Dưới {HATCH_WALL_SHARE:.0%} chiều dài tường có hatch") +
                        " (ước lượng: có nét hatch hoặc tâm vùng tô nằm trong bề dày tường).",
                        shares + (["tường không thấy hatch: " + ", ".join(bare_all[:15])] if bare_all else []))
    else:
        out["QU-10"] = arch_na
    # chỉ tính cặp nét giống tường (đúng dải chiều dày, chồng nhau ≥ MIN_WALL_OVERLAP_MM) trong block có tên, không phải block cửa
    # nét layer "0" trong block nhận layer của block khi chèn (cách vẽ nội thất, ký hiệu): không coi là nét tường
    layers_w = (set(wall_layers) | {l for l, c in drawing.layer_classes.items() if c == LayerClass.WALL}) - {"0"}
    by_block: dict[str, list] = {}
    for s in drawing.segments:
        if s.kind != "line" or not s.source or s.layer not in layers_w:
            continue
        parts = [x for x in s.source.split("/") if not x.startswith("*")]
        if parts and not any(match_block(x) for x in parts):
            by_block.setdefault(parts[-1], []).append(s)
    named = Counter({b: sum(o for o, *_ in _pairs(segs)) / 1000 for b, segs in by_block.items()})
    named = +named   # bỏ block không có cặp nét nào
    out["QU-11"] = (("vi_pham", "Có cặp nét giống tường nằm trong block có tên: hệ thống bỏ qua, không thành tường.",
                     [f"block {k}: {v:.1f} m cặp nét" for k, v in named.most_common(10)]) if named else
                    ("dat", "Không có cặp nét giống tường nằm trong block có tên.",
                     [f"{len(by_block)} block có tên có nét lẻ trên layer tường, không thành cặp tường"] if by_block else []))
    big = [a for a in drawing.arcs if drawing.layer_classes.get(a.layer) == LayerClass.WALL and a.r > config.DOOR_ARC_RADIUS_MM[1]]
    out["QU-12"] = (("vi_pham", f"{len(big)} cung tròn lớn trên layer tường: tường cong không được bóc.",
                     [f"layer {a.layer}, bán kính {a.r:.0f} mm" for a in big[:10]]) if big else
                    ("dat", "Không có cung tròn lớn trên layer tường.", []))
    open_ = [p.name for p in plans if not p.closed]
    out["QU-13"] = (arch_na if not has_plans else
                    ("vi_pham", "Tường bao chưa khép kín: chưa tính được diện tích sàn, nền, chống thấm.", open_) if open_ else
                    ("dat", "Tường bao khép kín ở mọi mặt bằng.", []))

    # Cửa
    if has_plans:
        ev = []
        for p in plans:
            c = Counter(o.ly_do.split(";")[0].split(" khớp")[0].split(" trên")[0] if o.ly_do.startswith("block")
                        else o.ly_do.split(";")[0] for o in p.openings)
            ev.append(f"{p.name}: {len(p.openings)} lỗ mở" + (" (" + ", ".join(f"{k} ×{v}" for k, v in c.most_common(4)) + ")" if c else ""))
        none = [p.name for p in plans if p.walls and not p.openings]
        out["QU-14"] = (("vi_pham", "Mặt bằng có tường nhưng không thấy dấu hiệu cửa nào.", ev) if none else
                        ("dat", "Cửa nhận được theo cung cánh cửa, nét kính hoặc block cửa.", ev))
    else:
        out["QU-14"] = arch_na
    sched = any("thong ke cua" in t for t in texts_norm)
    out["QU-15"] = (arch_na if not has_plans else
                    ("dat", "Có chữ \"thống kê cửa\" trên bản vẽ (hệ thống chưa đọc bảng, giai đoạn 3).", []) if sched else
                    ("vi_pham", "Không có bảng thống kê cửa: cửa không có kích thước trong block hay quy tắc block thì lấy theo "
                                "thông số cửa của dự án; dự án chưa nhập thì để trống, chưa trừ vào tường.", []))

    # Bộ phận khác
    if has_plans:
        cols = [c for p in plans for c in p.columns]
        out["QU-16"] = (("vi_pham", "Không nhận được cột nào (hình chữ nhật kín tô đặc).", []) if not cols else
                        ("dat", f"Nhận {len(cols)} cột từ hình chữ nhật kín tô đặc.",
                         [f"{p.name}: {len(p.columns)} cột" for p in plans]
                         + [f"dải cạnh hệ thống đang dùng {config.COLUMN_SIDE_MM[0]:.0f}–{config.COLUMN_SIDE_MM[1]:.0f} mm "
                            f"(QU-16 ghi {COLUMN_SIDE_QU16[0]:.0f}–{COLUMN_SIDE_QU16[1]:.0f} mm)"]))
        stair_rej = Counter(r["reason"] for v in per_plan.values() for r in v["res"].rejected if "thang" in r.get("reason", ""))
        updown = sum(1 for t in texts_norm if re.search(r"\b(len|xuong)\b", t))
        ev = [f"{k}: {n} cặp nét bị loại khỏi tường" for k, n in stair_rej.items()] + [f"chữ LÊN/XUỐNG: {updown}"]
        out["QU-17"] = (("dat", "Có dấu hiệu cầu thang (chưa đếm bậc tự động).", ev) if stair_rej or updown else
                        ("vi_pham", "Không thấy nét bậc hay chữ LÊN/XUỐNG.", ev))
        voids = [t for t in drawing.texts if re.search(r"thong tang|gieng troi", normalize(t.text))]
        out["QU-18"] = ("chua_kiem", "Chưa nhận dấu chéo ô trống (giai đoạn 3); diện tích ô trống người dùng nhập tay.",
                        [f"chữ \"{t.text.strip()[:30]}\"" for t in voids[:6]])
        no_room = [p.name for p in plans if not p.rooms]
        out["QU-19"] = (("vi_pham", "Mặt bằng không có tên phòng cần cho phần thô (WC, vệ sinh, ban công…).", no_room) if no_room else
                        ("dat", "Có tên phòng trong các mặt bằng.", [f"{p.name}: {', '.join(p.rooms[:6])}" for p in plans]))
        text_mat = sum(1 for v in per_plan.values() for w in v["res"].walls if w.material_source == "text")
        hits = Counter((h.material_id, h.ten) for h in find_material_notes(drawing))
        ev = [f"{text_mat} tường có vật liệu lấy từ ghi chú chữ (material_rules.csv)"] + [
            f"{mid} {ten}: {n} ghi chú" for (mid, ten), n in hits.most_common(12)]
        out["QU-20"] = (("dat", f"Đọc được ghi chú của {len(hits)} vật liệu phần thô (data/rules/material_notes.csv).", ev) if hits else
                        ("vi_pham", "Không có ghi chú vật liệu phần thô nào (mác bê tông, mác vữa, loại gạch…).", ev))
    else:
        for ma in ("QU-16", "QU-17", "QU-18", "QU-19", "QU-20"):
            out[ma] = arch_na
    for ma in ("QU-21", "QU-22", "QU-23"):
        out[ma] = (("chua_kiem", "Chưa đọc bản vẽ kết cấu (giai đoạn 3).", []) if structural_only else
                   ("khong_ap_dung", "File kiến trúc: điều khoản dành cho bản vẽ kết cấu.", []))

    return [Check(ma=c.ma, nhom=c.nhom, dieu_khoan=c.dieu_khoan, muc=c.muc, cach_kiem=c.cach_kiem,
                  trang_thai=out[c.ma][0], ket_qua=out[c.ma][1], bang_chung=out[c.ma][2]) for c in load_clauses()]
