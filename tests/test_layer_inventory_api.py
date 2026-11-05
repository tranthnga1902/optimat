import pytest
from hashlib import sha256
from tempfile import SpooledTemporaryFile
from pathlib import Path
from types import SimpleNamespace

from fastapi import UploadFile

from optimat.api import main


def test_try_inventory_binds_result_to_uploaded_content(monkeypatch):
    data = b"test drawing payload"
    drawing = SimpleNamespace(layer_classes={}, layers=["EMPTY"],
                              doc=SimpleNamespace(modelspace=lambda: []))

    def read_uploaded(path):
        assert Path(path).read_bytes() == data
        return drawing

    monkeypatch.setattr(main, "read_drawing", read_uploaded)
    monkeypatch.setattr(main, "list_objects", lambda *_: [])
    monkeypatch.setattr("optimat.drawing.layer_inventory.match_layer", lambda _: None)
    with SpooledTemporaryFile() as stream:
        stream.write(data)
        stream.seek(0)
        file = UploadFile(stream, filename="scope.dxf")
        with pytest.raises(StopIteration) as done:
            main.concepts_try(file).send(None)
    result = done.value.value
    assert result["source"] == {"filename": "scope.dxf", "sha256": sha256(data).hexdigest()}
    assert result["layers"][0]["name"] == "EMPTY"
    assert result["layers"][0]["count"] == 0
    assert result["rows"] == []
