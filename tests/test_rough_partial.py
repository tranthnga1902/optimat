"""Q02/N02-b3: số SYNTHETIC biết một phần không được trình bày như lượng hoàn chỉnh."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from optimat.catalog.repository import Catalog
from optimat.rough import takeoff
from optimat.rough.boq import boq_workbook, export_for_optimizer
from optimat.rough.materials import STEEL_NAME, _Bill, materials_for_works
from optimat.rough.models import MaterialLine, ProjectParams, WORKS, WorkItem
from optimat.rough.rebar import RebarRow, RebarScope, RebarSourceRef, RebarTable, resolve_rebar_tables
from optimat.rough.status import assign_status
from optimat.rough.steel import steel_works
from optimat.rough.takeoff import RoughRequest, RoughResult, compute_rough

REASON = "SYNTHETIC: chưa xác nhận phạm vi nguồn"


@pytest.fixture
def catalog():
    original = Catalog.from_csv(None)
    materials = original.materials.copy(deep=True)
    # Chỉ bản sao trong RAM: không để thiếu % che lỗi scope ở dây buộc/bê tông/xi măng.
    materials.loc[materials.material_id.isin(["TH10", "BT03", "XM02"]), "waste_pct"] = 0
    return replace(original, materials=materials)


def work(code, quantity, **fields):
    name, unit = WORKS[code]
    return WorkItem(code=code, name=name, unit=unit, quantity=quantity, **fields)


def rows_for(levels=(None, None)):
    tables = []
    for index, level in enumerate(levels):
        row = RebarRow(table="SYNTHETIC", row=1, element="D1", element_code="DAM", mark="1", dia_mm=16,
                       cut_length_mm=2000, total_bars=10, kg_per_m=1.58, kg=31.6,
                       evidence=f"SYNTHETIC source table {index}", raw_cells={"chieu_dai": "2000", "_length_unit": "mm"})
        tables.append(RebarTable(table_id=str(index), title="SYNTHETIC", rows=[row],
                      scope_from_title=RebarScope(levels=(level,), element_code="DAM", quantity_basis="total")
                      if level is not None else None))
    return resolve_rebar_tables(tables, source=RebarSourceRef.from_bytes(b"SYNTHETIC partial probe"))[0]


@pytest.mark.parametrize("code", ["COT_THEP", "COP_PHA", "DAM", "XAY"])
@pytest.mark.parametrize("quantity", [None, 0, -1.25, 2.5])
def test_numeric_or_empty_work_with_missing_is_d_and_keeps_value(code, quantity):
    w = work(code, quantity, missing=[REASON])
    assign_status([w], ProjectParams(), {})
    assert w.quantity == quantity and w.status == "D"
    assert w.inputs == [f"thiếu: {REASON}"]


@pytest.mark.parametrize("code", ["COT_THEP", "GIANG_TUONG"])
@pytest.mark.parametrize("prior", ["C", "D"])
@pytest.mark.parametrize("has_inputs", [True, False])
def test_structured_dependency_status_and_inputs_are_not_upgraded(code, prior, has_inputs):
    proof = f"SYNTHETIC dependency: {prior}" if has_inputs else f"phụ thuộc đã có: {prior}"
    w = work(code, 1, status=prior, inputs=[proof] if has_inputs else [], source="structural", basis="bang_thong_ke")
    assign_status([w], ProjectParams(), {})
    assert w.status == prior and w.quantity == 1 and proof in w.inputs
    inputs = list(w.inputs)
    assign_status([w], ProjectParams(), {})
    assert w.status == prior and w.inputs == inputs


@pytest.mark.parametrize("manual", [None, 0.0632, 0.2])
def test_pending_scope_survives_compute_and_manual_total(catalog, manual):
    rows = rows_for()
    params = ProjectParams(steel_schedule_t={} if manual is None else {"DAM": manual})
    result = compute_rough(RoughRequest(plans=[], rebar=rows, params=params), catalog)
    steel = next(w for w in result.works if w.code == "COT_THEP")
    expected = round(0.0632 if manual is None else manual, 3)
    assert steel.quantity == expected and steel.status == "D" and steel.missing
    assert all("chờ xác nhận" in m for m in steel.missing) and len(steel.evidence) == 2
    assert any("chờ xác nhận" in i for i in steel.inputs)
    total = next(t for t in result.totals if t.code == "COT_THEP")
    assert total.quantity == expected and not total.complete and total.status == "D"
    wire = next(m for m in result.materials if m.material_id == "TH10")
    assert wire.quantity == pytest.approx(round(expected * ((7.85 + 16.07) / 2), 3)) and wire.waste_pct == 0
    assert not wire.complete and wire.status == "D" and all(u.status == "D" for u in wire.uses)
    assert any("chờ xác nhận" in m for m in wire.missing)
    assert "hao hụt thi công (%)" not in wire.missing
    assert next(m for m in result.materials if m.name == STEEL_NAME).status == "D"


@pytest.mark.parametrize("unknown_missing", [[], [REASON]])
def test_known_plus_unknown_kg_retains_subtotal_and_reason(catalog, unknown_missing):
    rows = rows_for((1, 2))
    rows[1].kg = None
    rows[1].missing = unknown_missing
    result = compute_rough(RoughRequest(plans=[], rebar=rows), catalog)
    w = next(w for w in result.works if w.code == "COT_THEP")
    assert w.quantity == 0.032 and w.status == "D" and w.missing
    assert not next(t for t in result.totals if t.code == "COT_THEP").complete


@pytest.mark.parametrize("levels,count,expected_t", [((1, 1), 1, 0.032), ((1, 2), 2, 0.063)])
def test_resolved_same_or_independent_scope_is_not_marked_pending(catalog, levels, count, expected_t):
    rows = rows_for(levels)
    assert len(rows) == count and sum(r.kg for r in rows) == pytest.approx(31.6 * count)
    result = compute_rough(RoughRequest(plans=[], rebar=rows), catalog)
    w = next(w for w in result.works if w.code == "COT_THEP")
    assert w.quantity == expected_t and w.status == "A" and not w.missing
    assert next(t for t in result.totals if t.code == "COT_THEP").complete
    wire = next(m for m in result.materials if m.material_id == "TH10")
    assert wire.complete and wire.status != "D" and not any("chờ xác nhận" in m for m in wire.missing)


def test_steel_ratio_keeps_missing_from_known_concrete_volume():
    concrete = work("DAM", 2, missing=[REASON])
    steel, _ = steel_works([concrete], ProjectParams(steel_kg_per_m3={"DAM": 100}))
    assign_status([concrete, *steel], ProjectParams(steel_kg_per_m3={"DAM": 100}), {})
    assert steel[0].quantity == 0.2 and steel[0].status == "D" and REASON in steel[0].missing


def test_work_and_formwork_totals_keep_partial_numeric_subtotal(catalog, monkeypatch):
    works = [work("COP_PHA", 100, formwork_of="MONG", missing=[REASON]),
             work("COP_PHA", 50, formwork_of="MONG"),
             work("COP_PHA", None, formwork_of="MONG", missing=["SYNTHETIC unknown face"])]
    monkeypatch.setattr(takeoff, "foundation_works", lambda params: (works, []))
    result = compute_rough(RoughRequest(plans=[], params=ProjectParams(formwork_type="go")), catalog)
    total = next(t for t in result.totals if t.code == "COP_PHA")
    assert total.quantity == 150 and not total.complete and total.status == "D"
    assert result.formwork[0].quantity == 150 and not result.formwork[0].complete
    assert result.formwork[0].status == "D"


def test_unrelated_formwork_material_is_not_downgraded_by_pending_steel(catalog, monkeypatch):
    monkeypatch.setattr(takeoff, "foundation_works", lambda params: ([work("COP_PHA", 100, formwork_of="MONG")], []))
    result = compute_rough(RoughRequest(plans=[], rebar=rows_for(), params=ProjectParams(formwork_type="go")), catalog)
    wood = next(m for m in result.materials if m.material_id == "CP03")
    assert wood.complete and wood.status != "D" and not any("chờ xác nhận" in m for m in wood.missing)
    assert next(m for m in result.materials if m.material_id == "TH10").status == "D"


@pytest.mark.parametrize("kind", ["concrete", "mortar"])
def test_intermediate_and_all_dependent_materials_keep_partial_quantity(catalog, kind):
    bill = _Bill(catalog)
    w = work("DAM" if kind == "concrete" else "CAN_NEN", 2, missing=[REASON], status="D")
    if kind == "concrete":
        bill.concrete("M250", "ready_mix", 2, w, ())
    else:
        bill.mortar("VU02", "M75", 2, w, "SYNTHETIC mortar source")
    result = bill.result([w])
    assert len(result.intermediates) == 1
    assert result.intermediates[0].quantity == 2 and not result.intermediates[0].complete
    assert all(not m.complete and m.status == "D" and REASON in m.missing for m in result.materials)
    assert any(m.quantity is not None and m.quantity > 0 for m in result.materials)


def test_d_status_without_missing_is_propagated_to_material_uses(catalog):
    bill = _Bill(catalog)
    bill.add("XM02", "SYNTHETIC", "tấn", 2, work("COT", 2, status="D"), "SYNTHETIC", waste_included=True)
    m = bill.result([]).materials[0]
    assert m.quantity == 2 and not m.complete and m.status == "D" and m.uses[0].status == "D"
    assert any("nguồn công tác chưa đầy đủ" in reason for reason in m.missing)


def test_group_and_class_weight_cannot_be_complete_for_partial_quantities(catalog):
    lines = [MaterialLine(material_id="TH10", name="SYNTHETIC wire", unit="kg", quantity=1, weight_kg=1,
                          group_id="phan_tho", raw_class="thep", complete=False, status="D", missing=[REASON]),
             MaterialLine(material_id="XM02", name="SYNTHETIC cement", unit="tấn", quantity=2, weight_kg=2000,
                          group_id="phan_tho", raw_class="xi_mang", complete=True, status="A")]
    group = next(g for g in takeoff.group_totals(lines, catalog) if g.group_id == "phan_tho")
    assert group.weight_kg == 2001 and not group.weight_complete and group.status == "D"
    classes = {g.group_id: g for g in takeoff.class_totals(lines)}
    assert not classes["thep"].weight_complete and classes["xi_mang"].weight_complete
    result = RoughResult(works=[], materials=lines, by_group=takeoff.group_totals(lines, catalog),
                         by_class=takeoff.class_totals(lines))
    workbook = boq_workbook(result)
    for sheet, key in (("Theo nhóm", "phan_tho"), ("Theo loại", "thep")):
        row = next(r for r in workbook[sheet].values if r[0] == key)
        assert "chưa đủ dữ liệu khối lượng" in row and "thiếu khối lượng riêng" not in row
    material = next(r for r in workbook["Vật liệu"].values if r[0] == "TH10")
    assert REASON in material


def test_reference_price_remains_but_incomplete_wire_has_no_cost_or_optimizer_quantity(catalog, monkeypatch):
    from optimat.catalog import pricing
    monkeypatch.setattr(pricing, "price_offers", lambda *args: {"TH10": [SimpleNamespace(
        price=100, unit="kg", price_level="QUOTE", supplier_name="SYNTHETIC", price_date="", data_kind="SYNTHETIC")]})
    request = RoughRequest(plans=[], rebar=rows_for())
    result = compute_rough(request, catalog)
    wire = next(m for m in result.materials if m.material_id == "TH10")
    assert wire.best_price == 100 and wire.price_source and wire.est_cost is None
    out = export_for_optimizer(result)
    assert not any(m["material_id"] == "TH10" for m in out["materials"])
    assert any(m["material_id"] == "TH10" and m["known_part"] == wire.quantity
               and "chờ xác nhận" in m["reason"] for m in out["missing"])
    copied = RoughResult.model_validate_json(result.model_dump_json())
    assert copied.totals[0].quantity == result.totals[0].quantity and not copied.totals[0].complete
    wb = boq_workbook(result, request)
    material_rows = list(wb["Vật liệu"].values)
    header = material_rows[0]
    exported_wire = next(r for r in material_rows[1:] if r[0] == "TH10")
    assert exported_wire[header.index("Đủ số")] == "thiếu"
    assert "chờ xác nhận" in exported_wire[header.index("missing_reason")]


def test_legacy_json_confirmed_label_does_not_clear_existing_partial(catalog):
    row = rows_for()[0].model_dump(mode="json")
    row["scope_source"] = "confirmed"
    request = RoughRequest.model_validate({"plans": [], "rebar": [row]})
    result = compute_rough(request, catalog)
    assert result.works[0].quantity == 0.032 and result.works[0].status == "D"
    assert result.works[0].missing and request.rebar[0].missing == row["missing"]


def test_raw_waste_parts_keep_precision_sign_cancellation_and_unknown(catalog):
    bill = _Bill(catalog)
    clean = work("COT", 1, status="A")
    pending = work("COT", 1, status="D", missing=[REASON])
    for _ in range(100):
        bill.add("XM02", "SYNTHETIC", "tấn", 0.000049, clean, "SYNTHETIC", waste_included=False)
    bill.add("XM02", "SYNTHETIC", "tấn", -0.002, pending, "SYNTHETIC", waste_included=True)
    bill.add("XM02", "SYNTHETIC", "tấn", None, clean, "SYNTHETIC unknown", waste_included=False)
    m = bill.result([]).materials[0]
    assert m.quantity == 0.003 and m.quantity_with_waste == 0.003
    assert sum(u.quantity or 0 for u in m.uses) == -0.002
    assert not m.complete and m.status == "D" and REASON in m.missing
