import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from optimat.drawing import dwg_convert
from optimat.drawing.dwg_convert import DwgConversionError
from optimat.drawing.dxf_reader import read_drawing


@pytest.fixture
def libre(tmp_path, monkeypatch):
    executable = tmp_path / "dwg2dxf"
    executable.touch()
    monkeypatch.setenv("LIBREDWG_CONVERTER_PATH", str(executable))
    return executable


def test_libre_preferred_over_oda(libre, monkeypatch):
    monkeypatch.setenv("ODA_CONVERTER_PATH", str(libre))
    assert dwg_convert.find_converter() == str(libre)


def test_libre_found_on_path(monkeypatch):
    monkeypatch.delenv("LIBREDWG_CONVERTER_PATH", raising=False)
    monkeypatch.setattr(dwg_convert.shutil, "which", lambda name: "/usr/local/bin/dwg2dxf" if name == "dwg2dxf" else None)
    assert dwg_convert.find_converter() == "/usr/local/bin/dwg2dxf"


@pytest.mark.parametrize("extension", ["dwf", "dwfx"])
def test_dwf_requires_conversion(tmp_path, extension):
    from optimat.drawing.ingest import check_upload
    from optimat.drawing.dwg_convert import DrawingError
    with pytest.raises(DrawingError, match="DXF"):
        read_drawing(str(tmp_path / f"drawing.{extension}"))
    with pytest.raises(DrawingError, match="DXF"):
        check_upload(f"drawing.{extension}", b"DWF")


def test_libre_dwg_read(tmp_path, monkeypatch, libre, sample_dxf):
    def run(args, **kwargs):
        assert args[:4] == [str(libre), "-a", "r2018", "-o"]
        assert Path(args[5]).read_bytes() == b"DWG"
        shutil.copyfile(sample_dxf, args[4])
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(dwg_convert.subprocess, "run", run)
    source = tmp_path / "kiến trúc.dwg"
    source.write_bytes(b"DWG")
    assert read_drawing(str(source)).segments


@pytest.mark.parametrize("failure", ["exit", "missing", "empty", "timeout", "oserror"])
def test_libre_failures(tmp_path, monkeypatch, libre, failure):
    def run(args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args, 120)
        if failure == "oserror":
            raise OSError("missing library")
        if failure == "empty":
            Path(args[4]).touch()
        return SimpleNamespace(returncode=1 if failure == "exit" else 0, stdout="", stderr="bad DWG")

    monkeypatch.setattr(dwg_convert.subprocess, "run", run)
    source = tmp_path / "drawing.dwg"
    source.write_bytes(b"bad")
    output = tmp_path / "out"
    output.mkdir()
    stale = output / "drawing.dxf"
    stale.write_bytes(b"old DXF")
    with pytest.raises(DwgConversionError):
        dwg_convert.convert_dwg_to_dxf(str(source), str(output))
    assert stale.read_bytes() == b"old DXF"
