"""Sinh bộ file CAD mẫu cho bước tiếp nhận hồ sơ (S02), mỗi file một lỗi điển hình.

    python scripts/make_ingest_samples.py

Ghi vào data/sample/ingest/ kèm expected.json: trạng thái và mã cảnh báo mong đợi của từng file
(tests/test_ingest.py đối chiếu với drawing/ingest.py).
"""
import json
from pathlib import Path

import ezdxf

OUT = Path(__file__).resolve().parents[1] / "data/sample/ingest"


def house(insunits: int = 4, k: float = 1.0):
    """Nhà 6 m x 10 m vẽ đủ các loại đối tượng S02 đọc; k đổi kích thước theo đơn vị bản vẽ."""
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = insunits
    msp = doc.modelspace()
    for name in ("TUONG", "CUA", "KICHTHUOC", "GHICHU", "HATCH"):
        doc.layers.add(name)
    w, h = 6000 * k, 10000 * k
    msp.add_lwpolyline([(0, 0), (w, 0), (w, h), (0, h)], close=True, dxfattribs={"layer": "TUONG"})
    msp.add_polyline2d([(220 * k, 220 * k), (w - 220 * k, 220 * k), (w - 220 * k, h - 220 * k)],
                       dxfattribs={"layer": "TUONG"})
    msp.add_line((0, 5000 * k), (w, 5000 * k), dxfattribs={"layer": "TUONG"})
    msp.add_line((0, 5110 * k), (w, 5110 * k), dxfattribs={"layer": "TUONG"})
    msp.add_arc((1000 * k, 0), 900 * k, 0, 90, dxfattribs={"layer": "CUA"})
    door = doc.blocks.new("D1")
    door.add_line((0, 0), (900, 0))
    door.add_arc((0, 0), 900, 0, 90)
    msp.add_blockref("D1", (1000 * k, 0), dxfattribs={"layer": "CUA", "xscale": k, "yscale": k})
    hatch = msp.add_hatch(color=1, dxfattribs={"layer": "HATCH"})
    hatch.set_pattern_fill("ANSI31", scale=10 * k)
    hatch.paths.add_polyline_path([(0, 0), (w, 0), (w, 220 * k), (0, 220 * k)], is_closed=True)
    msp.add_text("Tường gạch đặc 220", dxfattribs={"layer": "GHICHU", "height": 150 * k}).set_placement((500 * k, 600 * k))
    msp.add_mtext("Ghi chú:\\PVữa M75", dxfattribs={"layer": "GHICHU", "char_height": 150 * k}).set_location((500 * k, 900 * k))
    msp.add_linear_dim(base=(0, -800 * k), p1=(0, 0), p2=(w, 0), dimstyle="Standard",
                       dxfattribs={"layer": "KICHTHUOC"}).render()
    return doc


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    expected = {}

    def save(name, doc, status="ok", codes=(), fmt="asc"):
        doc.saveas(OUT / name, fmt=fmt)
        expected[name] = {"status": status, "codes": sorted(codes)}

    save("01_hop_le_mm.dxf", house())
    save("02_thieu_don_vi.dxf", house(insunits=0), codes=["NO_UNITS"])
    save("03_don_vi_met.dxf", house(insunits=6, k=0.001))                    # mét: đổi về mm, không cảnh báo

    doc = house(insunits=4, k=0.01)                                          # khai báo mm nhưng vẽ theo tỷ lệ 1:100
    save("04_sai_ty_le.dxf", doc, codes=["SCALE_SUSPECT"])

    doc = house()
    doc.dimstyles.get("Standard").dxf.dimlfac = 100.0
    dim = doc.modelspace().add_linear_dim(base=(0, -1500), p1=(0, 0), p2=(6000, 0), text="60",
                                          dimstyle="Standard", dxfattribs={"layer": "KICHTHUOC"})
    dim.render()
    save("05_dimlfac_ghi_de.dxf", doc, codes=["DIMLFAC", "DIM_TEXT_MISMATCH"])

    doc = house()
    doc.add_xref_def("..\\kien_truc\\nen.dwg", "NEN_XREF")
    doc.modelspace().add_blockref("NEN_XREF", (0, 0))
    doc.add_xref_def("..\\ket_cau\\truc.dwg", "TRUC_OVERLAY", flags=28)       # 4 xref + 8 overlay + 16 phụ thuộc ngoài
    doc.modelspace().add_blockref("TRUC_OVERLAY", (0, 0))
    save("06_xref.dxf", doc, codes=["XREF"])

    doc = house()
    for name in ("A1-MAT BANG", "A1-MAT DUNG"):
        lay = doc.layouts.new(name)
        lay.add_line((0, 0), (420, 297))
        lay.add_text(name).set_placement((10, 10))
    save("07_nhieu_layout.dxf", doc, codes=["MULTI_LAYOUT"])

    doc = house()
    doc.styles.add("VNI_TIMES", font="VNI-Times.ttf")
    doc.modelspace().add_text("Töôøng gaïch", dxfattribs={"layer": "GHICHU", "style": "VNI_TIMES"})
    doc.modelspace().add_spline([(0, 0), (1000, 500), (2000, 0)], dxfattribs={"layer": "GHICHU"})
    save("08_font_vni_spline.dxf", doc, codes=["FONT_UNSUPPORTED", "UNSUPPORTED_ENTITY"])

    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    doc.layouts.new("CHI_LAYOUT").add_line((0, 0), (420, 297))
    save("09_modelspace_rong.dxf", doc, status="failed", codes=["EMPTY_MODEL", "MULTI_LAYOUT"])

    (OUT / "10_dxf_hong.dxf").write_text("0\nSECTION\n2\nENTITIES\n0\nLINE\n8\n0\n10\nkhong_phai_so\n", encoding="ascii")
    # chế độ phục hồi đọc được khung file nhưng không còn đối tượng nào: thất bại, không bóc tách
    expected["10_dxf_hong.dxf"] = {"status": "failed", "codes": ["EMPTY_MODEL", "FONT_MISSING", "NO_UNITS", "RECOVERED"]}
    (OUT / "11_dwg_hong.dwg").write_bytes(b"AC1032" + b"\x00" * 64)          # đúng chữ ký DWG, nội dung hỏng
    expected["11_dwg_hong.dwg"] = {"status": "failed", "codes": ["CONVERSION_FAILED"]}
    (OUT / "12_pdf_doi_ten.dxf").write_bytes(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    expected["12_pdf_doi_ten.dxf"] = {"status": "rejected", "codes": ["UPLOAD_REJECTED"]}

    save("13_nhi_phan.dxf", house(), fmt="bin")                               # DXF nhị phân: kết quả như 01

    doc = house()
    prev = "D1"
    for i in range(1, 6):                                                    # block lồng 5 cấp, cấp trong cùng là D1
        blk = doc.blocks.new(f"LONG_{i}")
        blk.add_blockref(prev, (100, 0))
        blk.add_line((0, 0), (0, 100))
        prev = blk.name
    doc.modelspace().add_blockref(prev, (3000, 3000), dxfattribs={"layer": "CUA"})
    save("14_block_long_sau.dxf", doc)

    # không có HEADER nhưng có chữ "$INSUNITS" trong TEXT: vẫn là chưa khai báo đơn vị, không được coi là mét
    tags = ["0", "SECTION", "2", "ENTITIES", "0", "TEXT", "8", "GHICHU", "10", "0", "20", "0", "30", "0", "40", "250",
            "1", "$INSUNITS", "0", "LINE", "8", "TUONG", "10", "0", "20", "0", "30", "0", "11", "6000", "21", "0",
            "31", "0", "0", "ENDSEC", "0", "EOF", ""]
    (OUT / "15_khong_header_chu_insunits.dxf").write_text("\n".join(tags), encoding="ascii")
    expected["15_khong_header_chu_insunits.dxf"] = {"status": "ok", "codes": ["FONT_MISSING", "NO_UNITS"]}

    (OUT / "expected.json").write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {len(expected)} file vào {OUT}")


if __name__ == "__main__":
    main()
