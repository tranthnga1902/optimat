"""Phần thô S4b: suy dầm từ cột và tường, khối lượng và cốp pha dầm."""
import pytest

from optimat.drawing.review import ReviewWall
from optimat.rough.beams import Beam, beam_works, infer_beams
from optimat.rough.columns import Column
from optimat.rough.models import ProjectParams

COLS = [Column(id="C1", x=0, y=0, b_mm=200, h_mm=200), Column(id="C2", x=5000, y=0, b_mm=200, h_mm=200),
        Column(id="C3", x=5000, y=4000, b_mm=200, h_mm=200), Column(id="C4", x=0, y=4000, b_mm=200, h_mm=200),
        Column(id="C5", x=12000, y=4000, b_mm=200, h_mm=200)]       # nhịp C3-C5 không có tường: không suy dầm
WALLS = [ReviewWall(id="A", cls="220", x1=0, y1=0, x2=5000, y2=0), ReviewWall(id="B", cls="220", x1=5000, y1=0, x2=5000, y2=4000),
         ReviewWall(id="C", cls="220", x1=5000, y1=4000, x2=0, y2=4000), ReviewWall(id="D", cls="110", x1=0, y1=4000, x2=0, y2=0)]


def test_infer_beams_along_walls():
    beams = infer_beams(COLS, WALLS)
    spans = sorted(round(b.length_mm) for b in beams)
    assert spans == [3800, 3800, 4800, 4800]


def test_beam_works():
    beams = infer_beams(COLS, WALLS)
    works, warnings = beam_works("T1", beams, ProjectParams(beam_width_mm=200, beam_depth_mm=400, slab_thickness_mm=100))
    dam = next(w for w in works if w.code == "DAM")
    assert dam.quantity == pytest.approx(17.2 * 0.2 * 0.3, abs=1e-3)
    assert next(w for w in works if w.code == "COP_PHA").quantity == pytest.approx(0.8 * 17.2, abs=1e-3)
    assert "suy từ tường và cột" in warnings[0]


def test_beam_missing_section_and_manual_override():
    beams = [Beam(id="D1", x1=0, y1=0, x2=4000, y2=0, source="manual"),
             Beam(id="D2", x1=0, y1=0, x2=3000, y2=0, b_mm=220, d_mm=500, source="manual")]
    works, warnings = beam_works("T1", beams, ProjectParams(slab_thickness_mm=100))
    missing = next(w for w in works if w.code == "DAM" and w.quantity is None)
    assert set(missing.missing) == {"rộng dầm", "cao dầm"}
    d2 = next(w for w in works if w.code == "DAM" and w.quantity is not None)
    assert d2.quantity == pytest.approx(3 * 0.22 * 0.4) and not warnings
