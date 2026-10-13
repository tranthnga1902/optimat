"""Sinh một mặt bằng DXF mẫu để thử module nhận diện và đo bóc.

    python scripts/make_sample_dxf.py

Nhà 5 m x 12 m (kích thước phủ bì): tường bao 220, một tường ngăn 110 dài 4,56 m,
một cửa đi D1 trên tường bao và một cửa sổ S1, hai ghi chú vật liệu và một hatch ANSI31.
Đáp án đo tay nằm trong data/ground_truth/ và tests/test_takeoff.py.
"""
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
doc = ezdxf.new("R2010")
doc.header["$INSUNITS"] = 4  # mm
msp = doc.modelspace()
doc.layers.add("TUONG")
doc.layers.add("CUA")
doc.layers.add("KICHTHUOC")

W, L, T = 5000, 12000, 220
# tường bao: hai hình chữ nhật lệch nhau đúng một chiều dày
msp.add_lwpolyline([(0, 0), (W, 0), (W, L), (0, L)], close=True, dxfattribs={"layer": "TUONG"})
msp.add_lwpolyline([(T, T), (W - T, T), (W - T, L - T), (T, L - T)], close=True, dxfattribs={"layer": "TUONG"})
# tường ngăn 110 nằm ngang ở y = 6000
msp.add_line((T, 6000), (W - T, 6000), dxfattribs={"layer": "TUONG"})
msp.add_line((T, 6110), (W - T, 6110), dxfattribs={"layer": "TUONG"})
# nét không phải tường, để kiểm tra việc lọc layer
msp.add_line((0, -800), (W, -800), dxfattribs={"layer": "KICHTHUOC"})

for name in ("D1", "S1"):
    block = doc.blocks.new(name)
    block.add_line((0, 0), (900, 0))
msp.add_blockref("D1", (2500, 110), dxfattribs={"layer": "CUA"})      # cửa đi trên tường bao phía dưới
msp.add_blockref("S1", (110, 3000), dxfattribs={"layer": "CUA"})      # cửa sổ trên tường bao bên trái
# ghi chú vật liệu: ghi chú có số chiều dày áp dụng cho mọi tường cùng chiều dày
msp.add_text("Tường gạch đặc 220, VXM M75", dxfattribs={"layer": "KICHTHUOC", "height": 150}).set_placement((600, 600))
msp.add_text("Tường ngăn 110 xây gạch AAC", dxfattribs={"layer": "KICHTHUOC", "height": 150}).set_placement((600, 6400))
# hatch mặt cắt gạch trên đoạn tường bao phía dưới
doc.layers.add("HATCH")
hatch = msp.add_hatch(dxfattribs={"layer": "HATCH"})
hatch.set_pattern_fill("ANSI31", scale=20)
hatch.paths.add_polyline_path([(T, 0), (W - T, 0), (W - T, T), (T, T)], is_closed=True)

out = ROOT / "data/sample/sample_floor.dxf"
doc.saveas(out)
print(f"Đã ghi {out}")
