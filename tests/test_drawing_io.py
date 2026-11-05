"""Chuyển DWG và phân loại layer. Các bài về tìm ODA File Converter được chuyển thể từ
tests/test_dwg_parser.py của dự án floor-plan-exit-router (giấy phép MIT)."""
from pathlib import Path

import pytest

from optimat.drawing import dwg_convert
from optimat.drawing.dwg_convert import DrawingError, DwgConversionUnavailable
from optimat.drawing.dxf_reader import read_drawing
from optimat.drawing.layer_classifier import LayerClass, apply_overrides, default_classification


def _no_converter(monkeypatch):
    monkeypatch.delenv("ODA_CONVERTER_PATH", raising=False)
    monkeypatch.setattr(dwg_convert.shutil, "which", lambda name: None)
    monkeypatch.setattr(dwg_convert.glob, "glob", lambda pattern: [])


def test_find_converter_respects_env_var(tmp_path, monkeypatch):
    fake = tmp_path / "ODAFileConverter.exe"
    fake.write_bytes(b"")
    monkeypatch.setenv("ODA_CONVERTER_PATH", str(fake))
    assert dwg_convert.find_converter() == str(fake)


def test_dwg_without_converter_gives_clear_error(tmp_path, monkeypatch):
    _no_converter(monkeypatch)
    assert dwg_convert.is_available() is False
    dwg = tmp_path / "nha.dwg"
    dwg.write_bytes(b"fake")
    with pytest.raises(DwgConversionUnavailable) as exc:
        read_drawing(str(dwg))
    assert "ODA_CONVERTER_PATH" in str(exc.value) and "opendesign.com" in str(exc.value)


def test_dwg_goes_through_converter(tmp_path, monkeypatch, sample_dxf):
    """Giả lập ODA File Converter bằng một hàm chép file DXF mẫu ra thư mục đích."""
    import shutil
    from pathlib import Path

    fake = tmp_path / "ODAFileConverter"
    fake.write_bytes(b"")
    monkeypatch.setenv("ODA_CONVERTER_PATH", str(fake))

    def fake_run(args, **kwargs):
        in_dir, out_dir = Path(args[1]), Path(args[2])
        for f in in_dir.glob("*.dwg"):
            shutil.copy(sample_dxf, out_dir / (f.stem + ".dxf"))
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(dwg_convert.subprocess, "run", fake_run)
    dwg = tmp_path / "nha.dwg"
    dwg.write_bytes(b"fake")
    drawing = read_drawing(str(dwg))
    assert len(drawing.segments) > 0 and "TUONG" in drawing.layers


def test_unsupported_and_broken_files(tmp_path):
    pdf = tmp_path / "nha.pdf"
    pdf.write_bytes(b"x")
    with pytest.raises(DrawingError):
        read_drawing(str(pdf))
    bad = tmp_path / "hong.dxf"
    bad.write_text("day khong phai dxf")
    with pytest.raises(DrawingError):
        read_drawing(str(bad))


def test_layer_classifier_vietnamese():
    c = default_classification(["TƯỜNG XÂY", "A-WALL", "Cua_di", "KÍCH THƯỚC", "TRUC", "NOI THAT", "0", "Layer1"])
    assert c["TƯỜNG XÂY"] == c["A-WALL"] == LayerClass.WALL
    assert c["Cua_di"] == LayerClass.OPENING
    assert c["KÍCH THƯỚC"] == c["TRUC"] == LayerClass.ANNOTATION
    assert c["NOI THAT"] == LayerClass.IGNORE
    assert c["0"] == c["Layer1"] == LayerClass.UNKNOWN
    merged = apply_overrides(c, {"Layer1": "WALL", "0": "khong-hop-le"})
    assert merged["Layer1"] == LayerClass.WALL and merged["0"] == LayerClass.UNKNOWN


def test_mirrored_block_arc_and_solid_in_world_coords(tmp_path):
    """Block lật gương (xscale = -1): cung cửa và vùng tô ghi theo hệ OCS phải đọc ra đúng vị trí thật."""
    import ezdxf
    from optimat.drawing.dxf_reader import read_dxf
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    blk = doc.blocks.new("CUA")
    blk.add_arc((1000, 0), 900, 0, 90)
    blk.add_solid([(0, 0), (200, 0), (0, 200), (200, 200)])
    doc.modelspace().add_blockref("CUA", (10000, 0), dxfattribs={"xscale": -1})
    path = tmp_path / "lat.dxf"
    doc.saveas(path)
    d = read_dxf(str(path))
    (a,) = d.arcs
    assert (round(a.cx), round(a.cy), round(a.start), round(a.end)) == (9000, 0, 90, 180)
    xs = sorted(round(x) for x, _ in d.hatches[0].polygons[0])
    assert xs[0] == 9800 and xs[-1] == 10000


def _every_transform_dxf(path):
    """Bản vẽ gom mọi kiểu đặt đối tượng: đơn vị mét, block lật gương, xoay, lồng 6 cấp, MINSERT, đối tượng vẽ lật (OCS)."""
    import ezdxf
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6                       # mét
    flip = {"extrusion": (0, 0, -1)}
    blk = doc.blocks.new("MOI_LOAI")
    blk.add_line((0, 0), (1, 0))
    blk.add_lwpolyline([(0, 0), (0.2, 0), (0.2, 0.2, 1), (0, 0.2)], format="xyb", close=True)
    blk.add_arc((1, 1), 0.9, 0, 90, dxfattribs=flip)
    blk.add_circle((2, 0), 0.1, dxfattribs=flip)
    blk.add_ellipse((3, 0), major_axis=(0.5, 0), ratio=0.5)
    blk.add_spline([(0, 2), (1, 3), (2, 2), (3, 3)])
    blk.add_solid([(4, 0), (4.2, 0), (4, 0.2), (4.2, 0.2)], dxfattribs=flip)
    blk.add_3dface([(5, 0), (6, 0), (6, 1), (5, 1)])
    blk.add_text("PHÒNG", dxfattribs={"height": 0.2, **flip}).set_placement((1, 2))
    h = blk.add_hatch(dxfattribs=flip)
    h.paths.add_polyline_path([(7, 0), (8, 0), (8, 1, 1), (7, 1)])
    for k in range(5):                                # lồng 6 cấp
        doc.blocks.new(f"L{k}").add_blockref("MOI_LOAI" if k == 0 else f"L{k - 1}", (0.5, 0.5))
    msp = doc.modelspace()
    msp.add_blockref("MOI_LOAI", (10, 0), dxfattribs={"xscale": -1})
    msp.add_blockref("MOI_LOAI", (20, 5), dxfattribs={"rotation": 30, "yscale": -1})
    msp.add_blockref("L4", (40, 0), dxfattribs={"rotation": 90})
    m = msp.add_blockref("MOI_LOAI", (60, 0))
    m.grid(size=(2, 2), spacing=(10, 10))
    msp.add_mline([(0, -5), (10, -5), (10, -10)])
    doc.saveas(path)
    return str(path)


def test_every_transform_read_in_world_coords(tmp_path):
    """Quy tắc chung: mọi đối tượng, đặt kiểu gì, cũng đọc ra đúng chỗ ezdxf thấy (đối chiếu khung bao từng layer)."""
    from optimat.drawing.dxf_reader import MISMATCH_WARNING, geometry_mismatch, read_dxf
    d = read_dxf(_every_transform_dxf(tmp_path / "moi_loai.dxf"))
    assert d.unit_scale == 1000
    assert geometry_mismatch(d) == {}
    assert not [w for w in d.warnings if "chưa đọc" in w or w.startswith(MISMATCH_WARNING)]
    assert sum(t.text == "PHÒNG" for t in d.texts) == 1 + 1 + 1 + 4      # lật, xoay, lồng, MINSERT 2 × 2
    t = next(t for t in d.texts if t.text == "PHÒNG")
    assert (round(t.x), round(t.y)) == (10000 - (-1000), 2000)           # chữ lật trong block lật: về lại x = +1 m


def test_geometry_check_catches_misplaced_arc(tmp_path):
    from optimat.drawing.dxf_reader import geometry_mismatch, read_dxf
    d = read_dxf(_every_transform_dxf(tmp_path / "moi_loai.dxf"))
    d.arcs[0].cx += 50_000
    assert geometry_mismatch(d)


BUILD_TEST = [p for sub in ("build", "test") for p in sorted((Path(__file__).resolve().parents[1] / "data/drawings" / sub).glob("*.dxf"))]


@pytest.mark.parametrize("path", BUILD_TEST, ids=lambda p: p.name)
def test_real_drawing_read_in_world_coords(path):
    """Mọi bản vẽ thật đặt trong data/drawings/build, test đều phải đọc đúng vị trí như ezdxf."""
    from optimat.drawing.dxf_reader import MISMATCH_WARNING, read_dxf
    assert not [w for w in read_dxf(str(path)).warnings if w.startswith(MISMATCH_WARNING)]


def test_read_dxf_warns_on_misplaced_geometry(tmp_path, monkeypatch):
    """Bộ đọc đặt sai chỗ (giả lập lỗi cũ: cung lấy tâm theo OCS) thì read_dxf phải cảnh báo."""
    from optimat.drawing import dxf_reader
    monkeypatch.setattr(dxf_reader._Collector, "arc", lambda self, e, source="": self.arcs.append(
        dxf_reader.ArcItem(e.dxf.center.x * self.s, e.dxf.center.y * self.s, e.dxf.radius * self.s,
                           e.dxf.start_angle, e.dxf.end_angle, e.dxf.layer, source)))
    d = dxf_reader.read_dxf(_every_transform_dxf(tmp_path / "moi_loai.dxf"))
    assert [w for w in d.warnings if w.startswith(dxf_reader.MISMATCH_WARNING) and "0 ×" in w]
    assert dxf_reader.crop(d, (0, 0, 1, 1)).warnings[0].startswith(dxf_reader.MISMATCH_WARNING)   # đo từng mặt bằng


def _dims_file(tmp_path, insunits, n=12, shown_factor=1.0):
    """n đường kích thước ngang dài 1000 + 100·i đơn vị bản vẽ, chữ ghi số đo × shown_factor (mm thật)."""
    import ezdxf
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = insunits
    msp = doc.modelspace()
    for i in range(n):
        length = 1000 + 100 * i
        d = msp.add_linear_dim(base=(0, 500 * i + 300), p1=(0, 500 * i), p2=(length, 500 * i),
                               text=f"{length * shown_factor:g}")
        d.render()
    path = tmp_path / "dims.dxf"
    doc.saveas(path)
    return str(path)


def test_declared_inch_but_dimensions_in_mm(tmp_path):
    """Đổi DWG ra DXF có thể ghi $INSUNITS = inch cho bản vẽ vẽ bằng mm (bộ 46, banve1, 02/11/2026): kích thước ghi
    đúng số đo thô -> dùng mm và cảnh báo, không nhân 25,4."""
    from optimat.drawing.dxf_reader import read_dxf
    d = read_dxf(_dims_file(tmp_path, insunits=1))
    assert d.unit_scale == 1.0
    assert any("đường kích thước" in w and "mm" in w for w in d.warnings)


def test_declared_units_kept_when_dimensions_agree_or_too_few(tmp_path):
    from optimat.drawing.dxf_reader import read_dxf
    ok = read_dxf(_dims_file(tmp_path, insunits=4))                       # mm, kích thước khớp
    assert ok.unit_scale == 1.0 and not any("đường kích thước" in w for w in ok.warnings)
    few = read_dxf(_dims_file(tmp_path, insunits=1, n=3))                 # dưới NG11: tin khai báo
    assert few.unit_scale == pytest.approx(25.4)
    enlarged = read_dxf(_dims_file(tmp_path, insunits=4, shown_factor=0.5))   # toàn hình phóng to 2 lần: giữ mm
    assert enlarged.unit_scale == 1.0 and not any("đường kích thước" in w for w in enlarged.warnings)
