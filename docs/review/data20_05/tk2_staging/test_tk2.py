import hashlib
import pytest
import ezdxf
from candidate import load_source, native_rows, read_region

UNITS = {"DK": "mm", "DAI": "mm", "DT": "m", "TL": "kg"}


@pytest.fixture
def source(tmp_path):
    d = ezdxf.new()
    d.units = 4
    d.blocks.new("TK_2")
    d.blocks.new("TK_14")
    frames = []
    for x, label, count in [(0, "C-1", 2), (6000, "C-2", 2), (12000, "C-1A", 4)]:
        m = d.modelspace()
        frame = m.add_lwpolyline([(x-500, -500), (x+4500, -500), (x+4500, 4000), (x-500, 4000)], close=True)
        frames.append(frame.dxf.handle)
        m.add_text(label, dxfattribs={"insert": (x, 0), "height": 100})
        m.add_text(f"(SL: {count})", dxfattribs={"insert": (x+1000, 0), "height": 100})
        for mark, y in [("3", 3000), ("4", 2000)]:
            b = m.add_blockref("TK_2", (x+1000, y))
            for i, (tag, value) in enumerate({"SH":mark,"DK":"20","DAI":"4300","SL1":"2",
                      "SLA":str(2*count),"DT":str(8.6*count),"TL":str(21.2*count)}.items()):
                b.add_attrib(tag, value, insert=(x+1000+i*100, y))
    f = tmp_path / "source.dxf"
    d.saveas(f)
    digest = hashlib.sha256(f.read_bytes()).hexdigest()
    d, ref = load_source(f, digest)
    return d, ref, frames


def parse(source, index=1):
    d, ref, frames = source
    return read_region(d, ref, frames[index], units=UNITS, units_evidence="SYNTHETIC table header")


def test_identical_numbers_stay_in_their_own_geometry_and_paths(source):
    a, _ = parse(source, 0)
    b, _ = parse(source, 1)
    assert len(a) == len(b) == 2
    assert {r["group"] for r in a} == {"C-1"}
    assert {r["group"] for r in b} == {"C-2"}
    assert a[0]["raw"] == b[0]["raw"]
    assert a[0]["handlepath"] != b[0]["handlepath"]
    assert all(r["attrib_sources"]["SH"]["type"] == "ATTRIB" for r in b)


def test_total_bars_are_not_multiplied_by_members_again(source):
    rows, warn = parse(source)
    assert not warn
    assert [r["total_bars"] for r in rows] == [4, 4]
    assert [r["length_total_m"] for r in rows] == [17.2, 17.2]
    assert sum(r["length_total_m"] for r in rows)*2.470 == pytest.approx(84.968)
    assert all(r["segment"] is None and r["axis"] is None and not r["checked"] for r in rows)


def test_four_members_remain_separate_from_two_member_table(source):
    rows, _ = parse(source, 2)
    assert [r["total_bars"] for r in rows] == [8, 8]


def test_unknown_units_never_use_drawing_units_as_cut_length_proof(source):
    d, ref, frames = source
    rows, warnings = read_region(d, ref, frames[1], units={}, units_evidence="")
    assert rows == [] and warnings


def test_combined_frame_with_multiple_labels_is_pending(source):
    d, ref, _ = source
    f = d.modelspace().add_lwpolyline([(-1000,-1000),(17000,-1000),(17000,5000),(-1000,5000)],close=True)
    rows, warnings = read_region(d, ref, f.dxf.handle, units=UNITS, units_evidence="SYN")
    assert rows == [] and any("duy nhất" in w for w in warnings)


@pytest.mark.parametrize("tag,value", [("SLA","8"),("DT","34.4"),("DK","nan"),("SL1","2.5")])
def test_conflicting_or_invalid_attributes_are_not_repaired(source, tag, value):
    d, ref, frames = source
    for e in d.modelspace().query("INSERT"):
        if 6000 < e.dxf.insert.x < 10500:
            e.get_attrib(tag).dxf.text = value
    rows, warnings = read_region(d, ref, frames[1], units=UNITS, units_evidence="SYN")
    assert rows == [] and warnings


def test_unresolved_stirrup_block_keeps_raw_source_without_assigning_segment(source):
    d, ref, frames = source
    b = d.modelspace().add_blockref("TK_14", (8000, 1000))
    for tag, value in {"SH":"7","DK":"6","DAI":"800","SL1":"77","SLA":"154","DT":"123.2","TL":"27.3"}.items():
        b.add_attrib(tag, value)
    rows, warnings = read_region(d, ref, frames[1], units=UNITS, units_evidence="SYN")
    assert len(rows) == 2 and any("TK_14" in w for w in warnings)
    assert any(r["raw"]["SH"] == "7" and r["segment"] is None for r in native_rows(d, ref))


def test_changed_source_hash_is_rejected(source):
    with pytest.raises(ValueError, match="Hash"):
        load_source(source[1]["file"], "0"*64)


@pytest.mark.parametrize("duplicate", [False, True])
def test_missing_or_duplicate_tags_keep_source_but_do_not_create_quantities(source, duplicate):
    d, _, _ = source
    for e in d.modelspace().query("INSERT"):
        if 6000 < e.dxf.insert.x < 10500:
            if duplicate:
                e.add_attrib("SLA", "999")
            else:
                e.delete_attrib("SLA")
    rows, warnings = parse(source)
    assert not rows and warnings
