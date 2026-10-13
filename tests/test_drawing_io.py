"""Chuyển DWG và phân loại layer. Các bài về tìm ODA File Converter được chuyển thể từ
tests/test_dwg_parser.py của dự án floor-plan-exit-router (giấy phép MIT)."""
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
