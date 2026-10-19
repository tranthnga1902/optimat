"""Danh sách từng đối tượng nhận diện được trên bản vẽ: tường, cửa, cặp nét bị loại (kèm lý do) và block khớp
ký hiệu không phải cửa trong bảng drawing_concepts (cột, cao độ, trục, nội thất...).
Dùng cho scripts/list_objects.py và trang quản trị "Ký hiệu nhận diện" (/api/concepts/try)."""
from __future__ import annotations

from .concepts import OPENING_KINDS, match_block_signal
from .dxf_reader import Drawing
from .takeoff import takeoff_plans

COLS = ["ban_ve", "mat_bang", "loai", "ma", "layer", "lop_day", "day_mm", "dai_m", "rong_mm", "cao_mm",
        "x1", "y1", "x2", "y2", "vai_tro", "vat_lieu", "phuong_an_tuong", "do_tin_cay", "ghi_chu"]


def list_objects(d: Drawing, file_label: str):
    for p in takeoff_plans(d):
        r = p.result
        base = {"ban_ve": file_label, "mat_bang": p.name}
        for w in r.walls:
            yield {**base, "loai": "tuong", "ma": w.wall_id, "layer": w.layer, "lop_day": w.thickness_class,
                   "day_mm": w.thickness_mm and round(w.thickness_mm), "dai_m": round(w.length_mm / 1000, 2),
                   "x1": round(w.x1), "y1": round(w.y1), "x2": round(w.x2), "y2": round(w.y2), "vai_tro": w.role,
                   "vat_lieu": w.material_id, "phuong_an_tuong": w.wall_system_id,
                   "do_tin_cay": round(w.confidence, 2), "ghi_chu": w.material_rule}
        for o in r.openings:
            yield {**base, "loai": o.kind if o.kind != "block" else "cua", "ma": o.name, "rong_mm": o.width_mm,
                   "cao_mm": o.height_mm, "x1": round(o.x), "y1": round(o.y), "ghi_chu": o.evidence or None,
                   "vai_tro": f"trừ vào {o.wall_id}" if o.wall_id else "chưa trừ"}
        for j in r.rejected:
            yield {**base, "loai": "loai_bo", "lop_day": j["cls"], "x1": round(j["x1"]), "y1": round(j["y1"]),
                   "x2": round(j["x2"]), "y2": round(j["y2"]), "ghi_chu": j["reason"]}
        x0, y0, x1, y1 = p.bbox
        for b in d.blocks:
            s = match_block_signal(b.name)
            if s and s.vai_tro not in OPENING_KINDS and x0 <= b.x <= x1 and y0 <= b.y <= y1:
                yield {**base, "loai": s.khai_niem, "ma": b.name, "layer": b.layer, "x1": round(b.x), "y1": round(b.y),
                       "vai_tro": s.vai_tro, "ghi_chu": f"ký hiệu {s.ma}"}
