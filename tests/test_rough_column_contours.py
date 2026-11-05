"""Cột ký hiệu SYNTHETIC: khung bao không thay thế đường bao chữ nhật."""
import pytest
from types import SimpleNamespace

from optimat.catalog.repository import Catalog
from optimat.drawing.dxf_reader import Drawing, Segment
from optimat.rough.columns import detect_columns
from optimat.rough.models import ProjectParams
from optimat.rough.takeoff import compute_rough, rough_from_drawing


def drawing(edges, offset=(0, 0), block=False):
    x, y = offset
    return Drawing(
        segments=[Segment(a+x, b+y, c+x, d+y, "0" if block else "COT", source="COT" if block else "")
                  for a, b, c, d in edges],
        texts=[], blocks=[], hatches=[], layers=["0" if block else "COT"],
        layer_classes={}, unit_scale=1.0, warnings=[])


RECT = [(0, 0, 225, 0), (225, 0, 225, 335), (225, 335, 0, 335), (0, 335, 0, 0)]


@pytest.mark.parametrize("edges", [
    RECT[:2],                         # L
    RECT[:3],                         # U
    [(0, 0, 225, 335)],               # đường chéo
    [(0, 0, 225, 335), (225, 335, 0, 335), (0, 335, 225, 0), (225, 0, 0, 0)],  # nơ kín
    [(0, 0, 225, 0), (225, 0, 200, 335), (200, 335, 0, 335), (0, 335, 0, 0)],  # hình thang
    RECT[:2] + [(225, 335, 113, 335), (112.5, 335, 0, 335), RECT[3]],  # khe 0,5 mm
])
def test_bbox_without_rectangle_is_not_a_column(edges):
    assert detect_columns(drawing(edges)) == []


@pytest.mark.parametrize("offset,block", [((0, 0), False), ((1234.25, -876.75), False),
                                          ((50_000_000.25, 40_000_000.75), True)])
@pytest.mark.parametrize("split", [False, True])
def test_rectangle_keeps_measured_dimensions_with_split_edges_and_extra_lines(offset, block, split, monkeypatch):
    if block:
        monkeypatch.setattr("optimat.rough.columns.match_block_signal",
                            lambda name: SimpleNamespace(vai_tro="COLUMN") if name == "COT" else None)
    edges = RECT if not split else [
        (0, 0, 100, 0), (100, 0, 225, 0), *RECT[1:],
        (0, 0, 225, 335), (0, 0, 50, 100),  # nét phụ không phá đường bao
    ]
    cols = detect_columns(drawing(edges, offset, block))
    assert len(cols) == 1
    c = cols[0]
    assert (c.b_mm, c.h_mm) == (225, 335)
    assert c.x == pytest.approx(offset[0] + 112.5, abs=0.051)
    assert c.y == pytest.approx(offset[1] + 167.5, abs=0.051)


@pytest.mark.parametrize("closed", [False, True])
def test_normal_rough_entrypoint_does_not_invent_or_round_column_volume(closed):
    cat = Catalog.from_csv(None)
    req = rough_from_drawing(drawing(RECT if closed else RECT[:3]),
                             params=ProjectParams(slab_thickness_mm=100),
                             floor_height_mm=3300, catalog=cat)
    columns = [c for p in req.plans for c in p.columns]
    assert len(columns) == int(closed)
    result = compute_rough(req, cat)
    works = [w for w in result.works if w.code == "COT"]
    if closed:
        assert (columns[0].b_mm, columns[0].h_mm) == (225, 335)
        assert sum(w.quantity for w in works) == pytest.approx(0.225 * 0.335 * 3.2, abs=0.0005)
    else:
        assert not works


def test_dxf_block_translation_preserves_rectangle_and_rejects_open_shapes(tmp_path):
    import ezdxf
    from optimat.drawing.dxf_reader import read_drawing
    from optimat.rough.columns import column_works

    doc = ezdxf.new()
    doc.units = 4  # mm, cùng đơn vị kích thước kiểm chứng
    doc.layers.new("COT")
    block = doc.blocks.new("SECTION")
    for x1, y1, x2, y2 in RECT:
        block.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "COT"})
    model = doc.modelspace()
    model.add_blockref("SECTION", (2000, 3000))
    model.add_line((6000, 5000), (6225, 5335), dxfattribs={"layer": "COT"})
    for x1, y1, x2, y2 in RECT[:2]:
        model.add_line((x1+7000, y1+6000), (x2+7000, y2+6000), dxfattribs={"layer": "COT"})
    path = tmp_path / "columns.dxf"
    doc.saveas(path)
    cols = detect_columns(read_drawing(str(path)))
    assert [(c.x, c.y, c.b_mm, c.h_mm) for c in cols] == [(2112.5, 3167.5, 225, 335)]
    works, _ = column_works("T1", cols, 3500, ProjectParams(slab_thickness_mm=20))
    assert next(w.quantity for w in works if w.code == "COT") == pytest.approx(0.262, abs=1e-9)


@pytest.mark.parametrize("offset,bridge", [((225, 0), False), ((225, 335), False),
                                            ((400, 0), True), ((225.4, 0), False)])
def test_two_closed_polylines_keep_their_identity(tmp_path, offset, bridge):
    import ezdxf
    from optimat.drawing.dxf_reader import read_drawing

    doc = ezdxf.new()
    doc.units = 4
    doc.layers.new("COT")
    model = doc.modelspace()
    for x, y in ((0, 0), offset):
        model.add_lwpolyline([(x, y), (x+225, y), (x+225, y+335), (x, y+335)],
                             close=True, dxfattribs={"layer": "COT"})
    if bridge:
        model.add_line((225, 0), offset, dxfattribs={"layer": "COT"})
    path = tmp_path / "two_columns.dxf"
    doc.saveas(path)
    cols = detect_columns(read_drawing(str(path)))
    assert len(cols) == 2
    actual = sorted((c.x, c.y, c.b_mm, c.h_mm) for c in cols)
    expected = sorted([(112.5, 167.5, 225, 335),
                       (offset[0]+112.5, round(offset[1]+167.5, 1), 225, 335)])
    for found, target in zip(actual, expected):
        assert found == pytest.approx(target, abs=1e-7)


def test_separate_contour_ids_survive_shared_edge_without_reader_guessing():
    d = drawing(RECT + [(a+225, b, c+225, e) for a, b, c, e in RECT])
    for i, seg in enumerate(d.segments):
        seg.contour_id = i // 4
    assert [(c.b_mm, c.h_mm) for c in detect_columns(d)] == [(225, 335), (225, 335)]


def test_loose_lines_with_shared_edge_are_ambiguous_not_one_outer_column():
    d = drawing(RECT + [(a+225, b, c+225, e) for a, b, c, e in RECT])
    assert detect_columns(d) == []


def test_repeated_block_polyline_has_distinct_contours_after_crop(tmp_path):
    import ezdxf
    from optimat.drawing.dxf_reader import crop, read_drawing

    doc = ezdxf.new()
    doc.units = 4
    doc.layers.new("COT")
    block = doc.blocks.new("SECTION")
    block.add_lwpolyline([(0, 0), (225, 0), (225, 335), (0, 335)], close=True,
                         dxfattribs={"layer": "COT"})
    for x in (0, 225):
        doc.modelspace().add_blockref("SECTION", (x, 0))
    path = tmp_path / "repeated.dxf"
    doc.saveas(path)
    d = crop(read_drawing(str(path)), (-1, -1, 451, 336))
    ids = {s.contour_id for s in d.segments}
    assert None not in ids and len(ids) == 2
    assert [(c.b_mm, c.h_mm) for c in detect_columns(d)] == [(225, 335), (225, 335)]
