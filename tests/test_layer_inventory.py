from types import SimpleNamespace

import ezdxf

from optimat.drawing.layer_inventory import layer_inventory


def test_inventory_keeps_empty_layers_and_counts_raw_entities(monkeypatch):
    doc = ezdxf.new()
    doc.layers.new("EMPTY")
    doc.layers.new("WALL")
    model = doc.modelspace()
    model.add_line((0, 0), (1, 0), dxfattribs={"layer": "wall"})
    model.add_circle((0, 0), 1, dxfattribs={"layer": "WALL"})
    rule = SimpleNamespace(ma="L01", mau="wall", vai_tro="WALL")
    monkeypatch.setattr("optimat.drawing.layer_inventory.match_layer", lambda name: rule if name == "wall" else None)
    drawing = SimpleNamespace(doc=doc, layers=[layer.dxf.name for layer in doc.layers])
    result = {row["name"]: row for row in layer_inventory(drawing)}
    assert result["WALL"]["types"] == {"LINE": 1, "CIRCLE": 1}
    assert result["WALL"]["rule"] == "L01"
    assert result["WALL"]["count"] == 2
    assert result["EMPTY"]["count"] == 0
    assert result["EMPTY"]["rule"] is None
