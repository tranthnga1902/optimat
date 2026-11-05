"""Dữ liệu dựng trong bộ nhớ để kiểm cổng ACTUAL, không phải báo giá thực tế."""
from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from optimat.catalog.repository import Catalog
from optimat.optimize.problem import build_space, optimize
from optimat.schemas import Constraints, WallGroup


@pytest.fixture
def procurement_catalog():
    return Catalog(
        materials=pd.DataFrame([
            dict(material_id="B1", name="Gạch thử", family="CLAY_SOLID", unit="viên", lambda_w_mk=0.8,
                 unit_weight_kg=2, waste_pct=None, data_kind="ACTUAL"),
            dict(material_id="M1", name="Vữa thử", family="MORTAR", unit="m³", lambda_w_mk=None,
                 unit_weight_kg=1800, waste_pct=None, data_kind="ACTUAL")]),
        suppliers=pd.DataFrame([dict(supplier_id="S1", name="Đại lý thử", province="X", lat=21.0, lon=105.0,
                                    lead_time_days=2, data_kind="ACTUAL")]),
        supplier_materials=pd.DataFrame([
            dict(supplier_id="S1", material_id=mid, base_price=price, sale_unit=unit, data_kind="ACTUAL",
                 price_level="QUOTE", price_date="2026-11-01", vat_included="YES", transport_included="YES",
                 quote_reference=f"Báo giá giả lập TEST-20261101, dòng {mid}")
            for mid, price, unit in [("B1", 5, "viên"), ("M1", 100, "m3")]]),
        vehicles=pd.DataFrame([dict(vehicle_id="V1", name="Xe thử", payload_ton=1, base_fee=50,
                                    fee_per_km=2, data_kind="ACTUAL")]),
        labor_rates=pd.DataFrame([dict(province="X", grade="3/7", rate_per_day=100, valid_from="2026-01-01",
                                      source="Nguồn giả lập cho kiểm thử", data_kind="ACTUAL")]),
        wall_systems=pd.DataFrame([dict(wall_system_id="W1", material_id="B1", detect_class=110,
                                       role="partition", masonry_thickness_mm=100, units_per_m3=100, unit_factor=1,
                                       mortar_m3_per_m3=0.2, labor_day_per_m3=2, mortar_material_id="M1",
                                       mortar_density=1800, norm_code="AE.TEST", data_kind="ACTUAL")]))


@pytest.fixture
def procurement_group():
    return WallGroup(wall_type="110", role="partition", length_m=3, gross_area_m2=10, opening_area_m2=0,
                     net_area_m2=10, min_confidence=1, design_material_id="B1", design_wall_system_id="W1",
                     design_material_share=1)


def purchase_constraints(**kw):
    return Constraints(procurement_mode=True, site_lat=21.01, site_lon=105.01, province="X", order_date="2026-11-03", **kw)


def test_procurement_prices_main_and_mortar_and_preserves_quote(procurement_catalog, procurement_group):
    class WrongModel:
        def knows(self, *_):
            raise AssertionError("Chế độ ACTUAL không được lấy giá mô hình")

    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, WrongModel(), method="brute")
    assert len(result.solutions) == 1
    solution = result.solutions[0]
    choice = solution.choices[0]
    assert choice.quantity == 100 and choice.unit_price == 5
    assert choice.main_material_cost == 500 and choice.mortar_cost == 20 and choice.material_cost == 520
    assert choice.mortar_material_id == "M1" and choice.mortar_unit == "m³"
    assert choice.mortar_quantity == pytest.approx(0.2) and choice.mortar_unit_price == 100
    assert choice.transport_cost == 0 and not choice.transport_estimated
    assert choice.supply_estimated and choice.cost_complete and "ACTUAL/QUOTE" == choice.price_source
    assert "TEST-20261101, dòng B1" in choice.cost_basis and "TEST-20261101, dòng M1" in choice.cost_basis
    assert solution.total_cost == 720
    assert any("ƯỚC TÍNH" in n for n in result.notes)


def test_non_wall_materials_pick_supplier_and_keep_design_code(procurement_catalog, procurement_group):
    from optimat.schemas import MaterialDemand
    cat = procurement_catalog
    cat.materials = pd.concat([cat.materials, pd.DataFrame([dict(material_id="T1", name="Thép thử", family="STEEL",
                                                                 unit="kg", unit_weight_kg=1, data_kind="ACTUAL")])])
    cat.suppliers = pd.concat([cat.suppliers, pd.DataFrame([dict(supplier_id="S2", name="Đại lý xa", province="X", lat=21.5,
                                                                 lon=105.5, lead_time_days=1, data_kind="ACTUAL")])])
    quote = dict(material_id="T1", sale_unit="kg", data_kind="ACTUAL", price_level="QUOTE", price_date="2026-11-01",
                 vat_included="YES", quote_reference="Báo giá giả lập TEST-T1")
    cat.supplier_materials = pd.concat([cat.supplier_materials, pd.DataFrame([
        dict(supplier_id="S1", base_price=20, transport_included="YES", **quote),
        dict(supplier_id="S2", base_price=15, transport_included="NO", **quote)])])
    demand = MaterialDemand(material_id="T1", quantity=100, unit="kg", raw_class="thep")
    missing = MaterialDemand(material_id="X9", quantity=1, unit="kg")
    result = optimize([procurement_group], purchase_constraints(), cat, method="brute", materials=[demand, missing])
    steel = [[c for c in s.choices if c.raw_class == "thep"] for s in result.solutions]
    assert steel and all(len(c) == 1 and c[0].material_id == "T1" for c in steel)
    assert {c[0].supplier_id for c in steel} <= {"S1", "S2"}
    t = steel[0][0]  # phương án rẻ nhất: S2 giá thấp hơn dù phải tự chở (1 chuyến)
    assert t.supplier_id == "S2" and t.trips == 1 and t.transport_cost > 0
    assert result.solutions[0].total_cost == 720 + 1500 + t.transport_cost
    assert any("CHƯA gồm" in n and "X9" in n for n in result.notes)
    # chỉ có vật tư ngoài tường vẫn tối ưu được
    alone = optimize([], purchase_constraints(), cat, method="brute", materials=[demand])
    assert alone.solutions and all(c.material_id == "T1" for s in alone.solutions for c in s.choices)


def test_non_wall_material_falls_back_to_bulletin_price(procurement_catalog, monkeypatch):
    from optimat.catalog.pricing import PriceOffer
    from optimat.optimize import problem
    from optimat.schemas import MaterialDemand
    cat = procurement_catalog
    cat.materials = pd.concat([cat.materials, pd.DataFrame([dict(material_id="XM", name="Xi măng thử", family="CEMENT",
                                                                 unit="tấn", data_kind="ACTUAL")])])
    rows = [PriceOffer(supplier_id="CBG-1", supplier_name="Công ty A", price=p, unit="tấn", price_level="BULLETIN",
                       price_date=d, data_kind="ACTUAL", source_detail="Công bố giá 02.01/2026", source="price_records")
            for p, d in [(1_500_000, "2026-10-01"), (1_000_000, "2026-12-01")]]  # dòng thứ hai sau ngày đặt: bỏ
    monkeypatch.setattr(problem, "_latest_price_records", lambda ids: {"XM": rows})
    result = optimize([], purchase_constraints(), cat, method="brute",
                      materials=[MaterialDemand(material_id="XM", quantity=2, unit="tấn", raw_class="xi_mang")])
    assert len(result.solutions) == 1
    c = result.solutions[0].choices[0]
    assert c.unit_price == 1_500_000 and c.price_source == "ACTUAL/BULLETIN" and c.vehicle_id == "CHUA_TINH"
    assert c.transport_cost == 0 and result.solutions[0].total_cost == 3_000_000 and result.solutions[0].supply_days == 0
    assert "chưa VAT" in c.cost_basis and any("GIÁ CÔNG BỐ" in n for n in result.notes)


@pytest.mark.parametrize("table", ["labor_rates", "suppliers", "supplier_materials", "materials", "wall_systems"])
def test_procurement_rejects_sample_inputs(procurement_catalog, procurement_group, table):
    getattr(procurement_catalog, table).loc[:, "data_kind"] = "SAMPLE"
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    assert result.solutions == []


@pytest.mark.parametrize("change", ["no_mortar", "other_seller", "wrong_unit", "missing_unit", "unknown_vat",
                                    "unknown_delivery", "future_quote", "expired_quote"])
def test_procurement_blocks_incomplete_quotes(procurement_catalog, procurement_group, change):
    sm = procurement_catalog.supplier_materials
    if change == "no_mortar":
        procurement_catalog.supplier_materials = sm[sm.material_id != "M1"]
    elif change == "other_seller":
        procurement_catalog.supplier_materials.loc[sm.material_id == "M1", "supplier_id"] = "S2"
    elif change in ("wrong_unit", "missing_unit"):
        sm.loc[sm.material_id == "M1", "sale_unit"] = "bao" if change == "wrong_unit" else None
    elif change == "unknown_vat":
        sm.loc[:, "vat_included"] = "UNKNOWN"
    elif change == "unknown_delivery":
        sm.loc[:, "transport_included"] = "UNKNOWN"
    elif change == "future_quote":
        sm.loc[:, "price_date"] = "2026-12-01"
    else:
        sm.loc[:, "valid_until"] = "2026-11-02"
    result = optimize([procurement_group], purchase_constraints(budget=1e9), procurement_catalog, method="brute")
    assert not result.solutions and result.n_evaluated == 0


def test_procurement_does_not_hide_unquoted_group_under_budget(procurement_catalog, procurement_group):
    missing = procurement_group.model_copy(update={"wall_type": "330", "design_wall_system_id": "W330"})
    result = optimize([procurement_group, missing], purchase_constraints(budget=1e9), procurement_catalog, method="brute")
    assert not result.solutions and any("tổng thiếu nhóm" in n for n in result.notes)
    assert not optimize([procurement_group], purchase_constraints(budget=710), procurement_catalog, method="brute").solutions


def test_procurement_freight_and_time_are_explicit_estimates(procurement_catalog, procurement_group):
    procurement_catalog.supplier_materials.loc[:, "transport_included"] = "NO"
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    choice = result.solutions[0].choices[0]
    assert choice.transport_cost > 0 and choice.transport_estimated and choice.supply_estimated
    assert "ước tính" in choice.cost_basis


def test_delivered_quote_needs_neither_vehicle_record_nor_supplier_coordinates(procurement_catalog, procurement_group):
    procurement_catalog.vehicles = procurement_catalog.vehicles.iloc[0:0]
    procurement_catalog.suppliers.loc[:, ["lat", "lon"]] = float("nan")
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    choice = result.solutions[0].choices[0]
    assert choice.vehicle_id == "DELIVERY_INCLUDED" and choice.transport_cost == 0 and choice.trips == 0
    assert choice.distance_km is None and not choice.transport_estimated
    assert result.solutions[0].total_cost == 720
    assert not optimize([procurement_group], purchase_constraints(max_vehicle_ton=1), procurement_catalog, method="brute").solutions


def test_delivered_quote_under_access_limit_needs_vehicle_evidence(procurement_catalog, procurement_group):
    assert not optimize([procurement_group], purchase_constraints(max_vehicle_ton=1), procurement_catalog, method="brute").solutions
    procurement_catalog.suppliers["max_truck_ton"] = 1.0
    assert optimize([procurement_group], purchase_constraints(max_vehicle_ton=1), procurement_catalog, method="brute").solutions


def test_non_delivered_quote_rejects_sample_vehicle(procurement_catalog, procurement_group):
    procurement_catalog.supplier_materials.loc[:, "transport_included"] = "NO"
    procurement_catalog.vehicles.loc[:, "data_kind"] = "SAMPLE"
    assert not optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute").solutions


def test_procurement_requires_province_even_when_only_one_labor_province_exists(procurement_catalog, procurement_group):
    cons = purchase_constraints().model_copy(update={"province": None})
    result = optimize([procurement_group], cons, procurement_catalog, method="brute")
    assert not result.solutions and any("Cần chọn địa bàn" in n for n in result.notes)


def test_design_mortar_override_does_not_leak_to_approved_alternative(procurement_catalog, procurement_group):
    mortar = procurement_catalog.materials.iloc[1].copy()
    mortar["material_id"], mortar["name"] = "M2", "Vữa mác khác"
    procurement_catalog.materials = pd.concat([procurement_catalog.materials, pd.DataFrame([mortar])], ignore_index=True)
    offer = procurement_catalog.supplier_materials.iloc[1].copy()
    offer["material_id"], offer["base_price"] = "M2", 200
    offer["quote_reference"] = "Báo giá giả lập TEST-20261101, dòng M2"
    procurement_catalog.supplier_materials = pd.concat([procurement_catalog.supplier_materials, pd.DataFrame([offer])], ignore_index=True)
    alt = procurement_catalog.wall_systems.iloc[0].copy()
    alt["wall_system_id"] = "W2"
    procurement_catalog.wall_systems = pd.concat([procurement_catalog.wall_systems, pd.DataFrame([alt])], ignore_index=True)
    group = procurement_group.model_copy(update={"design_mortar_material_id": "M2"})
    spaces, _, _ = build_space([group], purchase_constraints(approved_wall_system_ids=["W2"]), procurement_catalog, None)
    options = {o["wall_system_id"]: o for o in spaces[0].options}
    assert options["W1"]["mortar_material_id"] == "M2" and options["W1"]["mortar_cost"] == pytest.approx(40)
    assert options["W2"]["mortar_material_id"] == "M1" and options["W2"]["mortar_cost"] == pytest.approx(20)


def test_procurement_mortar_tonnes_use_system_density(procurement_catalog, procurement_group):
    procurement_catalog.materials.loc[procurement_catalog.materials.material_id == "M1", "unit"] = "tấn"
    procurement_catalog.supplier_materials.loc[procurement_catalog.supplier_materials.material_id == "M1", "sale_unit"] = "tấn"
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    choice = result.solutions[0].choices[0]
    assert choice.mortar_quantity == pytest.approx(0.36) and choice.mortar_unit == "tấn"
    assert choice.mortar_cost == 36


def test_site_mix_mortar_is_not_replaced_by_finished_mortar_quote(procurement_catalog, procurement_group):
    procurement_catalog.relations = pd.DataFrame([dict(material_id="M1", relation_type="COMPOSED_OF",
                                                       related_material_id="CEMENT", quantity=300, quantity_unit="kg/m³")])
    result = optimize([procurement_group], purchase_constraints(budget=1e9), procurement_catalog, method="brute")
    assert not result.solutions and any("giá từng thành phần" in n for n in result.notes)


def test_confirmed_quantity_can_have_no_ai_confidence_score(procurement_catalog, procurement_group):
    group = WallGroup.model_validate({**procurement_group.model_dump(), "min_confidence": None})
    assert group.min_confidence is None
    assert optimize([group], purchase_constraints(), procurement_catalog, method="brute").solutions


def test_procurement_non_norm_waste_is_required_and_not_doubled(procurement_catalog, procurement_group):
    procurement_catalog.wall_systems.loc[:, "norm_code"] = "HÃNG"
    assert not optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute").solutions
    procurement_catalog.materials.loc[procurement_catalog.materials.material_id == "B1", "waste_pct"] = 10
    procurement_catalog.materials.loc[procurement_catalog.materials.material_id == "M1", "waste_pct"] = 5
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    choice = result.solutions[0].choices[0]
    assert choice.quantity == pytest.approx(110) and choice.mortar_quantity == pytest.approx(0.21)


@pytest.mark.parametrize("field,value", [("units_per_m3", float("inf")), ("mortar_density", -1), ("labor_day_per_m3", 0)])
def test_procurement_rejects_invalid_system_values(procurement_catalog, procurement_group, field, value):
    procurement_catalog.wall_systems[field] = value
    assert not optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute").solutions


def test_procurement_requires_explicit_site_and_confirmed_group(procurement_catalog, procurement_group):
    with pytest.raises(ValueError, match="nhập rõ"):
        build_space([procurement_group], Constraints(procurement_mode=True), procurement_catalog, None)
    for update in ({"design_wall_system_id": None}, {"design_material_share": 0.8}):
        assert not optimize([procurement_group.model_copy(update=update)], purchase_constraints(),
                            procurement_catalog, method="brute").solutions


def test_procurement_alternatives_need_approval_and_same_role(procurement_catalog, procurement_group):
    alt = procurement_catalog.wall_systems.iloc[0].copy()
    alt["wall_system_id"] = "W2"
    procurement_catalog.wall_systems = pd.concat([procurement_catalog.wall_systems, pd.DataFrame([alt])], ignore_index=True)
    spaces, _, _ = build_space([procurement_group], purchase_constraints(), procurement_catalog, None)
    assert {o["wall_system_id"] for o in spaces[0].options} == {"W1"}
    spaces, _, _ = build_space([procurement_group], purchase_constraints(approved_wall_system_ids=["W2"]), procurement_catalog, None)
    assert {o["wall_system_id"] for o in spaces[0].options} == {"W1", "W2"}
    procurement_catalog.wall_systems.loc[procurement_catalog.wall_systems.wall_system_id == "W2", "role"] = "envelope"
    spaces, _, _ = build_space([procurement_group], purchase_constraints(approved_wall_system_ids=["W2"]), procurement_catalog, None)
    assert {o["wall_system_id"] for o in spaces[0].options} == {"W1"}


def test_approved_alternative_with_changed_thickness_still_needs_retakeoff(procurement_catalog, procurement_group):
    alt = procurement_catalog.wall_systems.iloc[0].copy()
    alt["wall_system_id"], alt["masonry_thickness_mm"] = "W2", 105
    procurement_catalog.wall_systems = pd.concat([procurement_catalog.wall_systems, pd.DataFrame([alt])], ignore_index=True)
    spaces, _, notes = build_space([procurement_group], purchase_constraints(approved_wall_system_ids=["W2"]), procurement_catalog, None)
    assert {o["wall_system_id"] for o in spaces[0].options} == {"W1"}
    assert any("W2" in n and "phải tính lại khối xây" in n for n in notes)


@pytest.mark.parametrize("source", [None, "ACTUAL", "https://maps.google.com/?q=21,105", "https://example.org/dealer-profile"])
def test_supplier_profile_source_does_not_prove_quote(procurement_catalog, procurement_group, source):
    sm = procurement_catalog.supplier_materials
    sm.loc[:, "quote_reference"] = None
    procurement_catalog.suppliers["source"] = source
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    assert not result.solutions


@pytest.mark.parametrize("reference", ["ACTUAL", "N/A", "https://maps.app.goo.gl/abc"])
def test_placeholder_or_maps_document_reference_does_not_prove_price(procurement_catalog, procurement_group, reference):
    procurement_catalog.supplier_materials.loc[:, "quote_reference"] = reference
    assert not optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute").solutions


@pytest.mark.parametrize("field", ["quote_reference", "price_source_detail", "source_detail", "certificate_reference"])
def test_explicit_quote_document_fields_are_traceable(procurement_catalog, procurement_group, field):
    procurement_catalog.supplier_materials.loc[:, "quote_reference"] = None
    procurement_catalog.supplier_materials[field] = "Chứng từ giả lập BG-TEST-20261101, trang 1"
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    assert result.solutions and "BG-TEST-20261101" in result.solutions[0].choices[0].cost_basis


@pytest.mark.parametrize("product_url", ["https://maps.app.goo.gl/abc", "https://www.google.com/maps?q=21,105", "not-a-url"])
def test_maps_or_malformed_product_link_is_not_quote_source(procurement_catalog, procurement_group, product_url):
    procurement_catalog.supplier_materials.loc[:, "quote_reference"] = None
    procurement_catalog.supplier_materials["product_url"] = product_url
    assert not optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute").solutions


@pytest.mark.parametrize("field", ["product_url", "price_page_url"])
def test_quote_product_or_price_page_is_traceable_source(procurement_catalog, procurement_group, field):
    procurement_catalog.supplier_materials.loc[:, "quote_reference"] = None
    procurement_catalog.supplier_materials[field] = "https://example.org/quotes/TEST-20261101"
    assert optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute").solutions


def test_quote_document_reference_is_distinct_from_maps_contact_link(procurement_catalog, procurement_group):
    procurement_catalog.supplier_materials["product_url"] = "https://www.google.com/maps?q=21,105"
    result = optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute")
    assert result.solutions
    assert "TEST-20261101, dòng B1" in result.solutions[0].choices[0].cost_basis
    assert "maps?q=" not in result.solutions[0].choices[0].cost_basis


@pytest.mark.parametrize("expiry", ["not-a-date", "2026-13-01", " "])
def test_procurement_rejects_malformed_expiry(procurement_catalog, procurement_group, expiry):
    procurement_catalog.supplier_materials["valid_until"] = expiry
    assert not optimize([procurement_group], purchase_constraints(), procurement_catalog, method="brute").solutions


def test_scenario_quote_precedes_model_and_incompatible_unit_is_blocked(procurement_catalog, procurement_group):
    class WrongModel:
        def knows(self, *_):
            return True

        def predict(self, rows):
            return np.full(len(rows), 999999)

    cons = Constraints(site_lat=21.01, site_lon=105.01, province="X", order_date="2026-11-03")
    spaces, _, notes = build_space([procurement_group], cons, deepcopy(procurement_catalog), WrongModel())
    assert spaces[0].options[0]["unit_price"] == 5 and spaces[0].options[0]["price_source"] == "catalog"
    assert any("KỊCH BẢN" in n for n in notes)
    procurement_catalog.supplier_materials.loc[:, "sale_unit"] = "bao"
    assert not optimize([procurement_group], cons, procurement_catalog, WrongModel(), method="brute").solutions


def _cement(cat, monkeypatch, linked=None):
    """Xi măng có giá công bố của CBG-1; CBG-1 có thể ghép với đại lý S1 (cùng công ty)."""
    from optimat.catalog.pricing import PriceOffer
    from optimat.optimize import problem
    cat.materials = pd.concat([cat.materials, pd.DataFrame([dict(material_id="XM", name="Xi măng thử", family="CEMENT",
                                                                 unit="tấn", unit_weight_kg=1000, data_kind="ACTUAL")])])
    cat.suppliers = pd.concat([cat.suppliers, pd.DataFrame([dict(supplier_id="CBG-1", name="Công ty A (công bố)", province="X",
                                                                 data_kind="ACTUAL", linked_supplier_id=linked)])])
    rows = [PriceOffer(supplier_id="CBG-1", supplier_name="Công ty A", price=1_500_000, unit="tấn", price_level="BULLETIN",
                       price_date="2026-10-01", data_kind="ACTUAL", source_detail="Công bố giá 02.01/2026", source="price_records")]
    monkeypatch.setattr(problem, "_latest_price_records", lambda ids: {"XM": rows})
    from optimat.schemas import MaterialDemand
    return [MaterialDemand(material_id="XM", quantity=2, unit="tấn", raw_class="xi_mang")]


def test_actual_dealer_quote_replaces_bulletin_price(procurement_catalog, monkeypatch):
    cat = procurement_catalog
    demand = _cement(cat, monkeypatch)
    cat.supplier_materials = pd.concat([cat.supplier_materials, pd.DataFrame([dict(
        supplier_id="S1", material_id="XM", base_price=1_600_000, sale_unit="tấn", data_kind="ACTUAL", price_level="QUOTE",
        price_date="2026-11-01", vat_included="YES", transport_included="NO", quote_reference="Báo giá giả lập TEST-XM",
        lead_time_days=4)])])  # thời gian của báo giá đè thời gian chung của đại lý (2 ngày)
    result = optimize([], purchase_constraints(), cat, method="brute", materials=demand)
    c = result.solutions[0].choices[0]
    assert c.supplier_id == "S1" and c.supplier_name == "Đại lý thử" and c.price_source == "ACTUAL/QUOTE"
    assert c.vehicle_id == "V1" and c.trips == 2 and c.transport_cost > 0
    assert result.solutions[0].supply_days == 4 + 1
    assert "đã gồm VAT" in c.cost_basis and "chưa gồm giao hàng" in c.cost_basis
    assert not any("GIÁ CÔNG BỐ" in n for n in result.notes)


def test_quote_without_lead_time_uses_dealer_lead_time(procurement_catalog):
    sm = procurement_catalog.supplier_materials.assign(lead_time_days=[None, 7])
    offers = procurement_catalog.__class__(**{**procurement_catalog.__dict__, "supplier_materials": sm}).offers(["B1", "M1"])
    assert offers.set_index("material_id").lead_time_days.to_dict() == {"B1": 2, "M1": 7}


def test_bulletin_price_linked_to_dealer_gets_freight_and_days(procurement_catalog, monkeypatch):
    cat = procurement_catalog
    demand = _cement(cat, monkeypatch, linked="S1")
    result = optimize([], purchase_constraints(), cat, method="brute", materials=demand)
    c = result.solutions[0].choices[0]
    assert c.unit_price == 1_500_000 and c.price_source == "ACTUAL/BULLETIN"
    assert c.supplier_id == "S1" and c.supplier_name == "Đại lý thử" and c.vehicle_id == "V1"
    assert c.trips == 2 and c.transport_cost > 0 and result.solutions[0].supply_days == 2 + 1
    assert "Đại lý cùng công ty: Đại lý thử" in c.cost_basis and "chưa VAT" in c.cost_basis


def test_bulletin_company_name_matching():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("lbs", Path(__file__).parents[1] / "scripts/link_bulletin_suppliers.py")
    lbs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lbs)
    assert lbs.company_key("Công ty cổ phần xi măng sài sơn") == lbs.company_key("Sài Sơn - Công Ty Cổ Phần Xi Măng Sài Sơn")
    assert lbs.company_key("Bãi Tàm Xá - xã Vĩnh Thanh") == "bai tam xa xa vinh thanh"
    hits = lbs.match([dict(supplier_id="CBG-1", name="CÔNG TY CP XI MĂNG VICEM BÚT SƠN", tax_code=None)],
                     [dict(supplier_id="D1", name="Công ty Cổ phần Xi măng VICEM Bút Sơn"), dict(supplier_id="D2", name="Xi măng Hoàng Long")])
    assert [d["supplier_id"] for d in hits["CBG-1"]] == ["D1"]
