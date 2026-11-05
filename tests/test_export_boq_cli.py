"""The BOQ CLI must retain project opening defaults, like compare_estimate."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

SPEC = importlib.util.spec_from_file_location("export_boq_cli", Path(__file__).resolve().parents[1] / "scripts/export_boq.py")
cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)


@pytest.mark.parametrize("defaults", [{"door_height_mm": 2000}, None])
def test_cli_passes_opening_defaults_without_losing_project_params(tmp_path, monkeypatch, defaults):
    raw = {"slab_thickness_mm": 100}
    if defaults is not None:
        raw["openings"] = defaults
    params = tmp_path / "params.json"
    params.write_text(json.dumps(raw), encoding="utf-8")
    seen = {}

    def build_request(drawing, project_params, height, catalog, filename, **kwargs):
        seen.update(params=project_params, height=height, **kwargs)
        return SimpleNamespace(rebar=[])

    monkeypatch.setattr(sys, "argv", ["export_boq.py", "architecture.dxf", "--structural", "structure.dxf",
                                     "--height", "3300", "--params", str(params), "--out", str(tmp_path / "boq.xlsx")])
    monkeypatch.setattr(cli.Catalog, "load", lambda: object())
    monkeypatch.setattr(cli, "read_drawing", lambda path: path)
    monkeypatch.setattr(cli, "rough_from_drawing", build_request)
    monkeypatch.setattr(cli, "compute_rough", lambda *args: SimpleNamespace(works=[], warnings=[]))
    monkeypatch.setattr(cli, "boq_workbook", lambda *args: SimpleNamespace(save=lambda path: None))
    cli.main()
    assert seen["params"].slab_thickness_mm == 100
    assert seen["height"] == 3300
    assert seen["structural"] == ["structure.dxf"]
    assert (seen["openings"].door_height_mm if seen["openings"] else None) == (2000 if defaults else None)


def test_invalid_opening_default_is_not_silently_ignored(tmp_path, monkeypatch):
    params = tmp_path / "params.json"
    params.write_text(json.dumps({"openings": {"door_height_mm": "not-a-number"}}), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["export_boq.py", "architecture.dxf", "--params", str(params)])
    with pytest.raises(ValidationError):
        cli.main()
