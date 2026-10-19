"""Ghi chú vật liệu phần thô (data/rules/material_notes.csv): so nguyên từ, ghi chú thật trên bản vẽ build."""
from optimat.drawing.material_notes import load_note_rules, match_note


def ids(text):
    return {r.material_id for r in match_note(text)}


def test_real_notes_from_build_drawings():
    assert "VU02" in ids("- lót vữa XM mác 75 dày 20.")
    assert "BT02" in ids("- sàn BTCT đổ tại chỗ mác 200 dày 120.")
    assert {"DA01", "BT03"} <= ids("bê tông đá 1x2, #250.")
    assert "BT06" in ids("- bê tông gạch vỡ mác 50#, dày 100")


def test_whole_word_not_substring():
    assert "TH01" not in ids("thép trong vùng chịu nén")      # "thep tron" là chuỗi con của "thep trong"
    assert "TH01" in ids("thép tròn CB240-T")


def test_rules_valid():
    rules = load_note_rules()
    assert len(rules) > 150 and all(r.pattern == r.pattern.lower() for r in rules)
