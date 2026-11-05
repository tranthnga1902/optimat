"""Instance cột: vị trí, nguồn, đoạn cao độ và ưu tiên KT/KC."""
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from optimat.catalog.repository import Catalog
from optimat.drawing.dxf_reader import Drawing, BlockRef, TextItem
from optimat.rough.columns import Column
from optimat.rough.models import ProjectParams
from optimat.rough.structural import ColumnSpan, element_of
from optimat.rough.structural_column_instances import (StructuralColumnInstance, instance_column_works,
                                                     read_column_instances)
from optimat.rough.takeoff import PlanInput, RoughRequest, compute_rough


def instance(**kw):
    values = dict(instance_id="col-4-A-level-2", code="C-2", grid_x="4", grid_y="A", floor_key="T2",
                  z_from_mm=3150, z_to_mm=6750, b_mm=220, h_mm=220, top_slab_thickness_mm=120,
                  top_slab_source="Sàn đỉnh đoạn: DIM h=120; handle SL1", file="structure.dxf", sheet="KC-02",
                  layers=["COLUMN"], handles=["AB1"], evidence=["Mặt cắt 2-2, DIM b/h; cao độ hai đầu"])
    return StructuralColumnInstance(**(values | kw))


def test_instance_gross_and_conditional_net_preserve_raw_precision():
    c = instance()
    work = instance_column_works([c])[0]
    assert work.quantity == pytest.approx(.168)
    detail = work.quantity_detail
    assert detail.rows[0].raw_quantity == "0.17424"
    assert detail.rows[1].raw_quantity == "0.005808"
    assert detail.total_raw == "0.168432"
    assert detail.legacy_delta == "0.000432"
    assert "handle AB1" in work.evidence
    assert "layer COLUMN" in work.evidence
    assert instance_column_works([instance(deduct_top_slab=False)])[0].quantity_detail.total_raw == "0.17424"


def test_missing_top_slab_does_not_use_global_slab_or_claim_net():
    work = instance_column_works([instance(top_slab_thickness_mm=None, top_slab_source=None)])[0]
    assert work.quantity is None
    assert work.quantity_detail.rows[0].raw_quantity == "0.17424"
    assert work.quantity_detail.rows[1].raw_quantity is None
    assert work.quantity_detail.total_raw is None
    assert not work.quantity_detail.complete


@pytest.mark.parametrize("field", ["b_mm", "h_mm", "z_from_mm", "z_to_mm", "grid_x"])
def test_missing_measurement_or_identity_stays_null(field):
    work = instance_column_works([instance(**{field: None})])[0]
    assert work.quantity is None and work.missing


@pytest.mark.parametrize("kw", [dict(b_mm=float("nan")), dict(h_mm=-1), dict(z_to_mm=float("inf")),
    dict(z_to_mm=3000), dict(top_slab_thickness_mm=4000), dict(top_slab_source=None),
    dict(matched_plan="Tầng 2")])
def test_invalid_instances_are_rejected(kw):
    with pytest.raises(ValidationError):
        instance(**kw)


def test_hyphenated_column_code_uses_existing_rule_without_changing_section_code():
    assert element_of("C-12")[0] == "COLUMN"
    assert element_of("C–12")[2] == "c12"
    assert element_of("MC1-1")[0] == "SECTION"
    assert element_of("X-12") is None


def test_same_type_at_different_grid_is_two_physical_segments():
    work = instance_column_works([instance(), instance(instance_id="col-4-B", grid_y="B")])
    cot = [w for w in work if w.code == "COT"]
    assert len(cot) == 2
    assert sum(float(w.quantity_detail.total_raw) for w in cot) == pytest.approx(.336864)


def test_matched_instance_replaces_only_one_local_column_and_keeps_other_floor():
    cat = Catalog.from_csv()
    c = Column(id="local1", x=0, y=0, b_mm=220, h_mm=220)
    plans = [PlanInput(name=f"Tầng {i}", height_mm=3600, height_source="nhập tay", walls=[], columns=[c]) for i in [1, 2]]
    req = RoughRequest(params=ProjectParams(slab_thickness_mm=100), plans=plans, structural_columns=[instance(
        matched_plan="Tầng 2", matched_column_id="local1", mapping_evidence="căn chỉnh trục hai bản vẽ")])
    result = compute_rough(req, cat)
    cot = [w for w in result.works if w.code == "COT"]
    assert len(cot) == 2
    assert next(w for w in cot if w.plan == "Tầng 1").quantity == pytest.approx(.169)
    kc = next(w for w in cot if w.basis == "structural_instance")
    assert kc.quantity_detail.total_raw == "0.168432"
    assert kc.quantity == pytest.approx(.168)


def test_unmapped_local_and_schedule_are_pending_not_double_counted():
    plan = PlanInput(name="Tầng 2", height_mm=3600, walls=[], columns=[Column(id="local", x=0, y=0, b_mm=220, h_mm=220)])
    req = RoughRequest(plans=[plan], structural_columns=[instance()], column_schedule=[ColumnSpan(
        code="C-2", count=2, z_from_mm=3150, z_to_mm=6750, b_mm=220, h_mm=220)])
    result = compute_rough(req, Catalog.from_csv())
    cot = [w for w in result.works if w.code == "COT"]
    assert len(cot) == 3
    assert len([w for w in cot if w.quantity is not None]) == 1
    assert all(w.missing for w in cot if w.quantity is None)
    assert not next(t for t in result.totals if t.code == "COT").complete


def test_schedule_only_keeps_legacy_measurements_without_making_instances():
    req = RoughRequest(plans=[], column_schedule=[ColumnSpan(code="C1", count=2,
        z_from_mm=-500, z_to_mm=2500, b_mm=200, h_mm=300)])
    cot = [w for w in compute_rough(req, Catalog.from_csv()).works if w.code == "COT"]
    assert len(cot) == 1 and cot[0].quantity == pytest.approx(.36)


def test_partial_schedule_does_not_hide_columns_on_proven_other_floor():
    col = Column(id="local", x=0, y=0, b_mm=220, h_mm=220)
    req = RoughRequest(plans=[PlanInput(name=f"Tầng {n}", height_mm=3600, walls=[], columns=[col]) for n in [1, 2]],
        column_schedule=[ColumnSpan(code="C1", count=2, z_from_mm=3150, z_to_mm=6750,
                                   b_mm=220, h_mm=220, floor_key="T2")])
    cot = [w for w in compute_rough(req, Catalog.from_csv()).works if w.code == "COT"]
    assert next(w for w in cot if w.plan == "Tầng 1").quantity is not None
    assert next(w for w in cot if w.plan == "Tầng 2").quantity is None


def test_reader_uses_explicit_attributes_keeps_layer_and_missing_labels():
    attrs = dict(COLUMN_CODE="C-7", GRID_X="8", GRID_Y="B", Z_FROM_MM="-400", Z_TO_MM="3200",
                 WIDTH_MM="250", DEPTH_MM="300", TOP_SLAB_THICKNESS_MM="150")
    drawing = Drawing(segments=[], hatches=[], blocks=[BlockRef("col", 100, 100, "KC-COT", attrs)],
        texts=[TextItem("C-8", 700, 100, "KC-TEXT", "unicode")], layers=[], layer_classes={}, unit_scale=1, warnings=[])
    view = SimpleNamespace(ma="BV06", title="Mặt bằng cột tầng 2", bbox=(0, 0, 1000, 1000))
    found = read_column_instances(drawing, [view])
    assert len(found) == 2 and found[0].grid_y == "B"
    assert found[0].layers == ["KC-COT"] and found[0].floor_key == "T2"
    assert found[0].z_from_mm == -400
    assert instance_column_works([found[1]])[0].quantity is None


def test_duplicate_ids_and_invalid_mapping_cannot_silently_replace_columns():
    with pytest.raises(ValidationError):
        RoughRequest(plans=[], structural_columns=[instance(), instance()])
    with pytest.raises(ValidationError):
        RoughRequest(plans=[], structural_columns=[instance(matched_plan="missing", matched_column_id="1", mapping_evidence="x")])
    with pytest.raises(ValidationError):
        RoughRequest(plans=[], structural_columns=[instance(), instance(instance_id="another-source-same-segment")])
    with pytest.raises(ValidationError):
        RoughRequest(plans=[], structural_columns=[instance(), instance(instance_id="overlap", z_from_mm=6000, z_to_mm=9000)])


def test_distinct_vertical_segments_at_same_grid_are_not_collapsed():
    req = RoughRequest(plans=[], structural_columns=[instance(), instance(instance_id="upper", floor_key="T3",
        z_from_mm=6750, z_to_mm=10300)])
    cot = [w for w in compute_rough(req, Catalog.from_csv()).works if w.code == "COT"]
    assert len(cot) == 2 and all(w.quantity is not None for w in cot)
    assert {w.quantity_detail.rows[0].raw_quantity for w in cot} == {"0.17424", "0.17182"}


def test_complete_instance_does_not_create_unrequested_steel_ratio_or_concrete_grade():
    req = RoughRequest(plans=[], structural_columns=[instance()])
    result = compute_rough(req, Catalog.from_csv())
    steel = [w for w in result.works if w.code == "COT_THEP"]
    assert steel and all(w.quantity is None for w in steel)
    assert req.params.steel_kg_per_m3 == {} and req.params.concrete_grade is None


@pytest.mark.parametrize("field,value", [("Z_TO_MM", "nan"), ("WIDTH_MM", "bad"), ("Z_TO_MM", "-900")])
def test_reader_invalid_attribute_keeps_pending_not_exception_or_zero(field, value):
    attrs = dict(COLUMN_CODE="C-9", GRID_X="3", GRID_Y="D", Z_FROM_MM="-400", Z_TO_MM="3200",
                 WIDTH_MM="250", DEPTH_MM="300", TOP_SLAB_THICKNESS_MM="150")
    attrs[field] = value
    drawing = Drawing(segments=[], hatches=[], blocks=[BlockRef("col", 100, 100, "KC-COT", attrs)],
        texts=[], layers=[], layer_classes={}, unit_scale=1, warnings=[])
    view = SimpleNamespace(ma="BV06", title="Mặt bằng cột tầng 2", bbox=(0, 0, 1000, 1000))
    found = read_column_instances(drawing, [view])
    assert len(found) == 1
    assert instance_column_works(found)[0].quantity is None


def geometric_records():
    def row(kind, handle, **values):
        return dict(kind=kind, handle=handle, layer="source", **values)
    return [
        row("CIRCLE", "v-bubble", p=(1000, 5000), radius=100),
        row("TEXT", "v-label", text="7", p=(970, 4960), height=100),
        row("LINE", "v-axis", a=(1000, 4800), b=(1000, 0)),
        row("CIRCLE", "h-bubble", p=(-200, 1000), radius=100),
        row("TEXT", "h-label", text="A", p=(-230, 960), height=100),
        row("LINE", "h-axis", a=(0, 1000), b=(5000, 1000)),
        row("LWPOLYLINE", "column-shape", vertices=[(900,900),(1100,900),(1100,1100),(900,1100)], closed=True),
        row("LEADER", "label-leader", vertices=[(1000,900),(1500,500)]),
        row("TEXT", "column-label", text="C-9", p=(1500,500), height=100),
        row("TEXT", "plan-title", text="Mặt bằng cột tầng 2", p=(2000,5500), height=200),
        row("TEXT", "detail-title", text="Cột C-9 (SL=01)", p=(10000,0), height=200),
        row("TEXT", "low", text="+3.300", p=(9000,1500), height=100),
        row("TEXT", "high", text="+6.900", p=(9000,4500), height=100),
        row("TEXT", "cut-left", text="1", p=(8000,3000), height=100),
        row("TEXT", "cut-right", text="1", p=(8500,3000), height=100),
        row("LINE", "cut-stroke1", a=(7800,2950), b=(8200,2950)),
        row("LINE", "cut-stroke2", a=(8300,2950), b=(8700,2950)),
        row("TEXT", "section-title", text="1-1", p=(13000,1000), height=200),
        row("DIMENSION", "width", p=(13100,2000), a=(12800,1700), b=(13400,1700), value=300, measured=600, vertical=False),
        row("DIMENSION", "depth", p=(13500,2300), a=(13600,1800), b=(13600,2600), value=400, measured=800, vertical=True),
        row("LWPOLYLINE", "concrete-section", vertices=[(12800,1800),(13400,1800),(13400,2600),(12800,2600)], closed=True),
    ]


def test_geometry_links_axis_leader_cut_and_signed_span_without_oracle(monkeypatch):
    from optimat.rough import structural_column_instances as module
    monkeypatch.setattr(module, "_cad_records", lambda _: geometric_records())
    drawing = SimpleNamespace(doc=SimpleNamespace(filename="synthetic.dxf"))
    result = module.read_column_instances(drawing, [])
    assert len(result) == 1
    col = result[0]
    assert (col.code, col.grid_x, col.grid_y, col.floor_key) == ("C-9", "7", "A", "T2")
    assert (col.z_from_mm, col.z_to_mm, col.b_mm, col.h_mm) == (3300,6900,300,400)
    assert "column-shape" in col.handles and "width" in col.handles
    work = instance_column_works(result)[0]
    assert work.quantity is None  # Không lấy slab chung/ghi chú gần nhất để ép net.
    assert float(work.quantity_detail.rows[0].raw_quantity) == pytest.approx(.432)


@pytest.mark.parametrize("removed", ["v-label", "v-axis", "column-shape", "label-leader"])
def test_geometry_missing_identity_evidence_never_assigns_grid(monkeypatch, removed):
    from optimat.rough import structural_column_instances as module
    monkeypatch.setattr(module, "_cad_records", lambda _: [r for r in geometric_records() if r["handle"] != removed])
    found = module.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")), [])
    if removed in ("v-label", "v-axis"):
        assert len(found) == 1 and found[0].grid_x is None and found[0].missing
        assert instance_column_works(found)[0].quantity is None
    else:
        assert found == []


def test_section_dimension_endpoints_must_match_one_closed_boundary(monkeypatch):
    from optimat.rough import structural_column_instances as module
    records = [r for r in geometric_records() if r["handle"] != "concrete-section"]
    monkeypatch.setattr(module, "_cad_records", lambda _: records)
    found = module.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")), [])
    assert len(found) == 1 and found[0].b_mm is None and found[0].missing


def test_staggered_neighbor_detail_does_not_supply_column_levels(monkeypatch):
    from optimat.rough import structural_column_instances as module
    records = geometric_records() + [
        dict(kind="TEXT", handle="neighbor", layer="text", text="Cột C-8", p=(-15000,-6000), height=200),
        dict(kind="TEXT", handle="neighbor-low", layer="text", text="+1.100", p=(-16000,1500), height=100),
        dict(kind="TEXT", handle="neighbor-high", layer="text", text="+8.800", p=(-16000,4500), height=100)]
    monkeypatch.setattr(module, "_cad_records", lambda _: records)
    found = module.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")), [])
    assert len(found) == 1 and (found[0].z_from_mm,found[0].z_to_mm) == (3300,6900)


def test_partially_read_profile_does_not_promote_ordinal_to_confirmed_floor(monkeypatch):
    from optimat.rough import structural_column_instances as module
    records = geometric_records() + [dict(kind="TEXT",handle="unresolved-next-level",layer="text",
        text="+10.500",p=(9000,8000),height=100)]
    monkeypatch.setattr(module,"_cad_records",lambda _: records)
    found = module.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert len(found) == 1 and found[0].z_from_mm == 3300
    assert found[0].floor_key is None and found[0].missing


def test_staggered_title_outside_horizontal_scope_does_not_clip_profile_top(monkeypatch):
    from optimat.rough import structural_column_instances as module
    records = [dict(r,p=(9000,9500)) if r["handle"]=="high" else r for r in geometric_records()]
    records.append(dict(kind="TEXT",handle="neighbor-above",layer="text",text="Cột C-8",p=(-15000,6000),height=200))
    monkeypatch.setattr(module,"_cad_records",lambda _:records)
    found = module.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert len(found) == 1 and (found[0].z_from_mm,found[0].z_to_mm) == (3300,6900)


def test_slab_note_is_only_a_candidate_until_its_region_at_column_is_proved(monkeypatch):
    from optimat.rough import structural_column_instances as module
    records = geometric_records() + [
        dict(kind="TEXT", handle="slab-title", layer="text", text="Mặt bằng kết cấu sàn tầng 3", p=(24000,-10000), height=200),
        dict(kind="TEXT", handle="slab-thickness", layer="text", text="h=15cm", p=(22000,-11000), height=100),
        dict(kind="TEXT", handle="slab-level", layer="text", text="+6.900", p=(22050,-10800), height=100)]
    monkeypatch.setattr(module, "_cad_records", lambda _: records)
    found = module.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")), [])
    assert len(found) == 1 and found[0].top_slab_thickness_mm is None
    candidate = found[0].top_slab_candidates[0]
    assert candidate.thickness_mm == 150 and candidate.floor_key == "T3" and not candidate.region_confirmed
    assert "slab-thickness" in candidate.handles
    assert instance_column_works(found)[0].quantity is None


def test_geometry_missing_paired_cut_keeps_measurement_pending(monkeypatch):
    from optimat.rough import structural_column_instances as module
    monkeypatch.setattr(module, "_cad_records", lambda _: [r for r in geometric_records() if r["handle"] != "cut-right"])
    found = module.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")), [])
    assert len(found) == 1 and found[0].z_to_mm is None
    assert instance_column_works(found)[0].quantity is None


def test_nested_insert_with_remote_origin_preserves_world_position_and_handle_path():
    import ezdxf
    from optimat.rough.structural_column_instances import _cad_records
    doc = ezdxf.new()
    inner = doc.blocks.new("inner", base_point=(10000, 20000))
    text = inner.add_text("4", dxfattribs={"insert": (10000,20000), "height": 100})
    outer = doc.blocks.new("outer", base_point=(50000,60000))
    outer.add_blockref("inner", (50000,60000))
    root = doc.modelspace().add_blockref("outer", (1000,2000))
    records = _cad_records(SimpleNamespace(doc=doc, unit_scale=1))
    assert len(records) == 1 and records[0]["p"] == pytest.approx((1000,2000))
    assert records[0]["handle"].startswith(root.dxf.handle + "/")
    assert records[0]["handle"].endswith("/" + text.dxf.handle)


@pytest.mark.parametrize("text,pos",[("Mặt bằng cột tầng 2",(2100,5500)),
    ("Mặt bằng cột tầng 3",(2000,5500)),("Mặt bằng cột tầng 3",(1500,5100))])
def test_two_eligible_plan_heads_stay_pending_even_if_one_is_closer(monkeypatch,text,pos):
    from optimat.rough import structural_column_instances as m
    records=geometric_records()+[dict(kind="TEXT",handle="competing-plan",layer="text",text=text,p=pos,height=200)]
    monkeypatch.setattr(m,"_cad_records",lambda _:records)
    found=m.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert len(found)==1 and found[0].floor_key is None and found[0].missing
    assert found[0].z_to_mm is None and instance_column_works(found)[0].quantity is None
    assert "competing-plan" in found[0].handles and "plan-title" in found[0].handles


def test_global_nearby_heading_outside_axis_footprint_cannot_supply_floor(monkeypatch):
    from optimat.rough import structural_column_instances as m
    records=[dict(r,p=(20000,5500)) if r["handle"]=="plan-title" else r for r in geometric_records()]
    monkeypatch.setattr(m,"_cad_records",lambda _:records)
    found=m.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert len(found)==1 and found[0].floor_key is None and found[0].missing


def test_duplicate_span_keeps_all_sources_and_conflicting_profile_counts_do_not_merge():
    from optimat.rough.structural_column_instances import _merge_column_spans
    a=dict(z0=0,z1=3000,b=200,h=300,expected_count=1,refs=[dict(handle="source-a")])
    b={**a,"refs":[dict(handle="source-b")]}
    spans,conflict=_merge_column_spans([a,b])
    assert not conflict and [r["handle"] for r in spans[0]["refs"]]==["source-a","source-b"]
    assert _merge_column_spans([a,{**b,"expected_count":2}])==([],True)
    assert _merge_column_spans([a,{**b,"b":250}])==([],True)


def test_larger_dimension_without_boundary_does_not_hide_valid_pair(monkeypatch):
    from optimat.rough import structural_column_instances as m
    records=geometric_records()+[dict(kind="DIMENSION",handle="oversized-unbound",layer="dim",
        p=(13100,2100),a=(12750,1700),b=(13450,1700),value=350,measured=700,vertical=False)]
    monkeypatch.setattr(m,"_cad_records",lambda _:records)
    found=m.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert (found[0].b_mm,found[0].h_mm)==(300,400)


def test_two_valid_dimension_boundaries_stay_pending(monkeypatch):
    from optimat.rough import structural_column_instances as m
    records=geometric_records()+[
        dict(kind="DIMENSION",handle="width-other",layer="dim",p=(13200,3200),a=(12800,3000),b=(13500,3000),value=350,measured=700,vertical=False),
        dict(kind="DIMENSION",handle="depth-other",layer="dim",p=(13600,3400),a=(13600,3100),b=(13600,3900),value=400,measured=800,vertical=True),
        dict(kind="LWPOLYLINE",handle="boundary-other",layer="concrete",vertices=[(12800,3100),(13500,3100),(13500,3900),(12800,3900)],closed=True)]
    monkeypatch.setattr(m,"_cad_records",lambda _:records)
    found=m.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert found[0].b_mm is None and found[0].missing
    assert {"width","width-other","depth","depth-other"} <= set(found[0].handles)
    assert any("nhiều cặp DIM" in reason for reason in found[0].missing)


def test_duplicate_dimensions_same_boundary_keep_provenance(monkeypatch):
    from optimat.rough import structural_column_instances as m
    records=geometric_records()
    records += [dict(r,handle=r["handle"]+"-copy") for r in records if r["kind"]=="DIMENSION"]
    monkeypatch.setattr(m,"_cad_records",lambda _:records)
    found=m.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert (found[0].b_mm,found[0].h_mm)==(300,400)
    assert {"width","width-copy","depth","depth-copy"}<=set(found[0].handles)


def test_conflicting_duplicate_span_preserves_both_detail_sources(monkeypatch):
    from optimat.rough import structural_column_instances as m
    records=geometric_records()+[dict(kind="TEXT",handle="other-detail-source",layer="text",text="Cột C-9",p=(-15000,-6000),height=200)]
    monkeypatch.setattr(m,"_cad_records",lambda _:records)
    def spans(_,head,heads,**kw):
        return [dict(z0=3300,z1=6900,b=300,h=400,expected_count=1 if head["handle"]=="detail-title" else 2,refs=[head])]
    monkeypatch.setattr(m,"_section_spans",spans)
    found=m.read_column_instances(SimpleNamespace(doc=SimpleNamespace(filename="x.dxf")),[])
    assert found[0].b_mm is None and found[0].missing
    assert {"detail-title","other-detail-source"} <= set(found[0].handles)
