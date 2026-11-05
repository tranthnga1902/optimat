"""Inventory of declared layers and direct modelspace entities."""
from collections import Counter

from .concepts import match_layer, normalize


def layer_inventory(drawing):
    names = {name.casefold(): name for name in drawing.layers}
    counts = {}
    for entity in drawing.doc.modelspace():
        name = entity.dxf.get("layer", "0")
        key = name.casefold()
        names.setdefault(key, name)
        counts.setdefault(key, Counter())[entity.dxftype()] += 1

    result = []
    for key, name in sorted(names.items()):
        types = counts.get(key, {})
        rule = match_layer(normalize(name).replace("_", " ").replace("-", " "))
        result.append({"name": name, "types": dict(types), "count": sum(types.values()),
                       "rule": rule.ma if rule else None, "pattern": rule.mau if rule else None,
                       "role": rule.vai_tro if rule else None})
    return result
