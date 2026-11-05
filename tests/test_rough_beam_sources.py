"""O01: chọn nguồn theo tầng, fixture SYNTHETIC không đọc CAD/DB."""
import pytest
from pydantic import ValidationError

from optimat.catalog.repository import Catalog
from optimat.drawing.review import ReviewWall
from optimat.rough.beams import Beam
from optimat.rough.models import ProjectParams
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough


@pytest.fixture(scope="module")
def cat():
    return Catalog.from_csv(None)


def beam(source="structural", **kw):
    return Beam(**(dict(id="D1", x1=0, y1=0, x2=4000, y2=0, b_mm=200, d_mm=400, source=source) | kw))


def plan(floor=2, **kw):
    return PlanInput(**(dict(name=f"TẦNG {floor}", height_mm=3000, walls=[]) | kw))


def request(**kw):
    return RoughRequest(**(dict(plans=[], params=ProjectParams(slab_thickness_mm=100,
        formwork_type="go", steel_kg_per_m3={"DAM": 100})) | kw))


def total(res, code="DAM", formwork=False):
    return next(t for t in (res.formwork if formwork else res.totals) if t.code == code)


def test_kc_only_its_floor_and_no_manual_double_count(cat, monkeypatch):
    calls = []
    def infer(cols, walls):
        calls.append(True)
        return [beam("inferred", id="SUY")]
    monkeypatch.setattr("optimat.rough.takeoff.infer_beams", infer)
    req = request(plans=[plan(beams=[beam("manual")]), plan(3)],
                  structural_beams={"KC TẦNG 2": [beam()]})
    res = compute_rough(req, cat)
    assert len(calls) == 1
    assert total(res).quantity == pytest.approx(.48)
    assert total(res, "DAM", True).quantity == pytest.approx(6.4)
    assert res.beams["TẦNG 2"] == []
    assert any("chưa được chọn" in w for w in res.warnings)
    assert {w.plan for w in res.works if w.code == "DAM"} == {"KC TẦNG 2 → T2", "TẦNG 3"}


def test_explicit_manual_replaces_kc(cat):
    req = request(plans=[plan(beams=[beam("manual")])], structural_beams={"KC TẦNG 2": [beam(x2=8000)]},
        beam_floor_sources={"T2": dict(source="manual", ref="TẦNG 2", evidence="Chọn thay thế")})
    res = compute_rough(req, cat)
    assert total(res).quantity == pytest.approx(.24)
    assert total(res, "DAM", True).quantity == pytest.approx(3.2)
    assert res.beams["KC TẦNG 2"][0].x2 == 8000
    assert next(w for w in res.works if w.code == "DAM").status == "C"


@pytest.mark.parametrize("empty", [[], [beam(keep=False)]])
def test_empty_kc_no_inference_or_manual_fallback(cat, monkeypatch, empty):
    monkeypatch.setattr("optimat.rough.takeoff.infer_beams", lambda *a: pytest.fail("Không được suy bù KC"))
    res = compute_rough(request(plans=[plan(beams=[beam("manual")])],
                                structural_beams={"KC TẦNG 2": empty}), cat)
    assert total(res).quantity is None and not total(res).complete
    assert total(res, "DAM", True).status == "D"


def test_missing_kc_section_not_filled_by_manual(cat):
    res = compute_rough(request(plans=[plan(beams=[beam("manual")])],
                     structural_beams={"KC TẦNG 2": [beam(d_mm=None)]}), cat)
    assert total(res).quantity is None and total(res).status == "D"
    assert any("cao dầm" in m for w in res.works if w.code == "DAM" for m in w.missing)


def overlapping(choice=False, reverse=False):
    views = {"A": [beam()], "B": [beam()]}
    scopes = {"A": dict(floors=["T2", "T3", "T4"], evidence="Phạm vi A"),
              "B": dict(floors=["T4", "T5"], evidence="Phạm vi B")}
    if reverse:
        views = dict(reversed(list(views.items())))
    return request(structural_beams=views, beam_view_scopes=scopes, structural_floors={"A": 3, "B": 2},
        beam_floor_sources={"T4": dict(source="structural", ref="B", evidence="Chọn B cho T4")} if choice else {})


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("choice,expected,complete", [(True, .96, True), (False, .72, False)])
def test_overlapping_views_keep_each_floor_once(cat, choice, expected, complete, reverse):
    res = compute_rough(overlapping(choice, reverse), cat)
    assert total(res).quantity == pytest.approx(expected)
    assert total(res).complete is complete
    assert total(res, "DAM", True).quantity == pytest.approx(expected / .24 * 3.2)
    known = [w for w in res.works if w.code == "DAM" and w.quantity is not None]
    assert len(known) == (4 if choice else 3)
    assert all(w.quantity == pytest.approx(.24) for w in known)
    assert set(res.beams) == {"A", "B"}
    if not choice:
        assert total(res).status == "D"
        assert any(w.plan == "T4" and w.quantity is None for w in res.works if w.code == "DAM")
        mats = [m for m in res.materials if any(u.work == "DAM" for u in m.uses)]
        assert mats and all(not m.complete and m.status == "D" for m in mats)
        from optimat.rough.boq import export_for_optimizer, boq_workbook
        assert export_for_optimizer(res)["missing"]
        assert any("nhiều view" in str(row) for row in boq_workbook(res)["Theo tầng"].values)


@pytest.mark.parametrize("count", [0, 2, 4])
def test_count_mismatch_is_pending_not_multiplied(cat, count):
    req = overlapping(True)
    req.structural_floors["A"] = count
    res = compute_rough(req, cat)
    assert total(res).quantity == pytest.approx(.48)  # chỉ B:T4/T5
    assert not total(res).complete


def test_unknown_scope_does_not_disable_other_floor_inference(cat, monkeypatch):
    monkeypatch.setattr("optimat.rough.takeoff.infer_beams", lambda *a: [beam("inferred")])
    res = compute_rough(request(plans=[plan(3)], structural_beams={"KHÔNG RÕ": [beam()]}), cat)
    assert total(res).quantity == pytest.approx(.24)
    assert total(res).status == "D" and not total(res).complete


def test_none_and_empty_plan_beams_are_different(cat, monkeypatch):
    calls = []
    monkeypatch.setattr("optimat.rough.takeoff.infer_beams", lambda *a: calls.append(1) or [beam("inferred")])
    res = compute_rough(request(plans=[plan(2), plan(3, beams=[])]), cat)
    assert calls == [1] and total(res).quantity == pytest.approx(.24)
    assert not total(res).complete and total(res).status == "D"
    assert any("beams=[]" in w for w in res.warnings)


def test_all_local_beams_removed_keeps_pending_and_other_floor_known(cat, monkeypatch):
    monkeypatch.setattr("optimat.rough.takeoff.infer_beams", lambda *a: pytest.fail("Không suy bù dầm đã loại"))
    res = compute_rough(request(plans=[plan(2, beams=[beam("manual", keep=False)]),
                                       plan(3, beams=[beam("manual")])]), cat)
    assert total(res).quantity == pytest.approx(.24) and not total(res).complete and total(res).status == "D"
    assert total(res, "DAM", True).quantity == pytest.approx(3.2) and not total(res, "DAM", True).complete
    assert res.beams["TẦNG 2"][0].keep is False
    assert any(w.plan == "TẦNG 2" and w.quantity is None and w.missing for w in res.works if w.code == "DAM")


def test_no_kc_depth_transfer_or_false_alignment(cat):
    wall = ReviewWall(id="W1", cls="220", role="envelope", x1=0, y1=0, x2=10000, y2=0, mat="GN01")
    res = compute_rough(request(plans=[plan(2, walls=[wall]), plan(3, walls=[wall], beams=[])],
                         structural_beams={"KC TẦNG 2": [beam()]}), cat)
    masonry = [w for w in res.works if w.code == "XAY"]
    assert len(masonry) == 2 and all(w.status == "D" for w in masonry)
    assert all(any("cao dầm" in m or "chiều cao dầm" in m for m in w.missing) for w in masonry)
    assert all("KC TẦNG 2" not in d.source for w in masonry for d in w.dimensions)


def test_beams_not_lost_when_plan_height_missing(cat):
    res = compute_rough(request(plans=[plan(height_mm=None, beams=[beam("manual")])]), cat)
    assert total(res).quantity == pytest.approx(.24)


@pytest.mark.parametrize("patch", [
    {"beam_view_scopes": {"missing": dict(floors=["T2"], evidence="x")}},
    {"beam_view_scopes": {"KC TẦNG 2": dict(floors=["T2", "T2"], evidence="x")}},
    {"beam_view_scopes": {"KC TẦNG 2": dict(floors=["L1"], evidence="x")}},
    {"beam_view_scopes": {"KC TẦNG 2": dict(floors=["T2"], evidence=" ")}},
    {"beam_floor_sources": {"T3": dict(source="structural", ref="KC TẦNG 2", evidence="x")}},
    {"beam_floor_sources": {"T2": dict(source="manual", ref="missing", evidence="x")}},
    {"plans": [dict(name="x", walls=[], beam_floor_key="T2")]},
])
def test_bad_scope_or_choice_validation(patch):
    with pytest.raises(ValidationError):
        request(**(dict(structural_beams={"KC TẦNG 2": [beam()]}) | patch))


def test_explicit_plan_mapping_and_lau_equivalent(cat):
    p = plan(name="Mặt bằng tùy đặt", beam_floor_key="T2", beam_floor_evidence="Theo hồ sơ", beams=[beam("manual")])
    res = compute_rough(request(plans=[p], structural_beams={"KC LẦU 1": [beam()]}), cat)
    assert total(res).quantity == pytest.approx(.24)
    assert res.beams[p.name] == []


@pytest.mark.parametrize("kc_floor,expected", [("T3", .48), ("T2", .24)])
def test_plan_and_kc_same_name_keep_source_maps_without_legacy_overwrite(cat, kc_floor, expected):
    p = plan(beams=[beam("manual", id="LOCAL")])
    req = request(plans=[p], structural_beams={p.name: [beam(id="KC")]},
        beam_view_scopes={p.name: dict(floors=[kc_floor], evidence="Xác nhận tầng KC")})
    res = compute_rough(req, cat)
    assert total(res).quantity == pytest.approx(expected) and total(res).complete
    assert total(res, "DAM", True).quantity == pytest.approx(expected / .24 * 3.2)
    assert p.name not in res.beams
    assert res.plan_beams[p.name][0].id == "LOCAL" and res.plan_beams[p.name][0].source == "manual"
    assert res.structural_beams[p.name][0].id == "KC" and res.structural_beams[p.name][0].source == "structural"
    assert any("trùng" in w and "plan_beams" in w for w in res.warnings)
