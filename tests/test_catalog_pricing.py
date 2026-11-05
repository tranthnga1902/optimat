"""Giá theo đúng đơn vị và nguồn; fixture tổng hợp chỉ kiểm hành vi."""
import pandas as pd
import pytest

from optimat.catalog import pricing
from optimat.catalog.repository import Catalog
from optimat.schemas import WallGroup


@pytest.fixture
def catalog(monkeypatch):
    cat = Catalog.from_csv()
    cat.supplier_materials = pd.DataFrame([
        {"supplier_id": "UNIT", "material_id": "GN01", "base_price": 50, "sale_unit": "kiện",
         "unit_conversion": 50, "price_date": "2026-11-01", "price_level": "DEALER", "data_kind": "ACTUAL"},
        {"supplier_id": "UNIT", "material_id": "GN01", "base_price": 1500, "sale_unit": "viên",
         "price_date": "2026-11-01", "price_level": "QUOTE", "data_kind": "ACTUAL"},
    ])
    cat.supplier_materials["quote_reference"] = "Phiếu giá fixture BG-01/2026; chỉ kiểm hành vi"
    cat.supplier_materials["vat_included"] = "YES"
    cat.supplier_materials["transport_included"] = "NO"
    cat.suppliers = pd.DataFrame([{"supplier_id": "UNIT", "name": "Fixture đơn vị", "data_kind": "ACTUAL"}])
    monkeypatch.setattr(pricing, "_latest_price_records", lambda ids: {})
    return cat


def brick(catalog, actual_only=False):
    group = WallGroup(wall_type="220", role="envelope", length_m=10, gross_area_m2=30, opening_area_m2=0,
                      net_area_m2=30, min_confidence=1, design_wall_system_id="W-GN01-220")
    return next(b for b in pricing.bill_of_materials([group], catalog, actual_only=actual_only) if b.kind == "main")


def test_package_price_cannot_multiply_count_and_keeps_raw_rejection(catalog):
    line = brick(catalog, actual_only=True)
    assert line.best_price == 1500 and line.best_offer.unit == "viên"
    package = next(o for o in line.offers if o.unit == "kiện")
    assert package.price == 50 and package.raw_price == "50"
    assert not package.eligible and any("Đơn vị" in r for r in package.rejection_reasons)
    assert line.est_cost == round(line.quantity * 1500)


def test_missing_sale_unit_is_not_inferred_from_material(catalog):
    catalog.supplier_materials["sale_unit"] = None
    line = brick(catalog)
    assert line.best_price is None and line.best_offer is None and line.est_cost is None
    assert len(line.offers) == 2 and all(o.unit is None for o in line.offers)
    assert all(any("Chưa rõ đơn vị" in r for r in o.rejection_reasons) for o in line.offers)


def test_real_purchase_mode_rejects_sample_offer_supplier_and_material(catalog):
    catalog.supplier_materials["data_kind"] = "SAMPLE"
    assert brick(catalog).best_price == 1500  # Chế độ kịch bản vẫn hỗ trợ fixture có đơn vị rõ.
    assert brick(catalog, True).best_price is None
    catalog.supplier_materials["data_kind"] = "ACTUAL"
    catalog.suppliers["data_kind"] = "SAMPLE"
    assert brick(catalog, True).best_price is None
    catalog.suppliers["data_kind"] = "ACTUAL"
    catalog.materials.loc[catalog.materials.material_id == "GN01", "data_kind"] = "SAMPLE"
    line = brick(catalog, True)
    assert line.est_cost is None and any("Vật liệu" in r for o in line.offers for r in o.rejection_reasons)


def test_dealer_preferred_to_cheaper_historical_reference_and_best_offer_is_exact(catalog, monkeypatch):
    bulletin = pricing.PriceOffer(supplier_id="OLD", supplier_data_kind="ACTUAL", supplier_name="Công bố cũ",
                                  price=1, unit="viên", price_level="BULLETIN", price_date="2026-03-17",
                                  data_kind="ACTUAL", source="price_records", source_detail="Nguồn lịch sử")
    monkeypatch.setattr(pricing, "_latest_price_records", lambda ids: {"GN01": [bulletin]})
    line = brick(catalog, True)
    assert line.best_price == 1500 and line.best_offer.supplier_id == "UNIT" and not line.best_offer.is_reference
    catalog.supplier_materials = catalog.supplier_materials.iloc[:0]
    reference = brick(catalog, True)
    assert reference.best_price == 1 and reference.best_offer.is_reference
    assert reference.best_offer.source_detail == "Nguồn lịch sử" and "tham khảo" in reference.price_note
    assert not bulletin.eligible  # Không sửa đối tượng nguồn dùng chung.


@pytest.mark.parametrize("price", [0, -1, float("inf"), float("nan")])
def test_invalid_prices_never_produce_cost(catalog, price):
    catalog.supplier_materials["base_price"] = price
    assert brick(catalog).est_cost is None


@pytest.mark.parametrize("value", [None, "không rõ"])
def test_actual_price_without_date_is_missing(catalog, value):
    catalog.supplier_materials["price_date"] = value
    line = brick(catalog, True)
    assert line.best_price is None and any("ngày" in r for o in line.offers for r in o.rejection_reasons)


def test_normalization_only_changes_writing_not_units():
    assert pricing.normalize_unit(" M³ ") == pricing.normalize_unit("m3")
    assert pricing.normalize_unit("m²") == pricing.normalize_unit("M2")
    assert pricing.normalize_unit(None) == ""
    assert pricing.normalize_unit("bao 50 kg") != pricing.normalize_unit("tấn")
    assert pricing.normalize_unit("50 viên") != pricing.normalize_unit("viên")


def test_ae_norm_does_not_add_waste_again_for_brick_or_mortar(catalog):
    catalog.materials.loc[catalog.materials.material_id.isin(["GN01", "VU02"]), "waste_pct"] = 50
    group = WallGroup(wall_type="220", role="envelope", length_m=10, gross_area_m2=30, opening_area_m2=0,
                      net_area_m2=30, min_confidence=1, design_wall_system_id="W-GN01-220")
    lines = pricing.bill_of_materials([group], catalog)
    assert len(lines) == 2
    for line in lines:
        assert line.waste_included
        assert line.quantity == round(group.net_area_m2 * line.qty_per_m2, 3)
    catalog.wall_systems.loc[catalog.wall_systems.wall_system_id == "W-GN01-220", "norm_code"] = ""
    lines = pricing.bill_of_materials([group], catalog)
    for line in lines:
        assert not line.waste_included
        assert line.quantity == round(group.net_area_m2 * line.qty_per_m2 * 1.5, 3)


def test_shared_selector_rejects_future_and_anonymous_actual_purchase():
    future = pricing.PriceOffer(price=1, unit="m³", price_level="BULLETIN", price_date="2026-11-04", data_kind="ACTUAL")
    anonymous = pricing.PriceOffer(price=2, unit="m3", price_level="QUOTE", price_date="2026-11-03", data_kind="ACTUAL")
    historic = pricing.PriceOffer(price=3, unit="m3", price_level="BULLETIN", price_date="2026-06-20", data_kind="ACTUAL",
                                  source_detail="Công bố fixture CB-01/2026; chỉ kiểm hành vi")
    best, checked = pricing.select_best_offer([future, anonymous, historic], "m³", "ACTUAL", True, as_of="2026-11-03")
    assert best.price == 3 and best.is_reference
    assert any("tương lai" in r for r in checked[0].rejection_reasons)
    assert any("mã nhà cung cấp" in r for r in checked[1].rejection_reasons)
    assert not future.rejection_reasons and not future.eligible
    assert pricing.select_best_offer([future], "m3", "ACTUAL", False, "2026-11-03")[0] is None


def test_non_ae_missing_waste_does_not_create_total_cost(catalog):
    catalog.wall_systems.loc[catalog.wall_systems.wall_system_id == "W-GN01-220", "norm_code"] = ""
    catalog.materials.loc[catalog.materials.material_id == "GN01", "waste_pct"] = None
    line = brick(catalog)
    assert line.quantity is not None and line.best_price == 1500
    assert line.est_cost is None and "hao hụt thi công (%)" in line.missing


def test_selected_mortar_grade_is_preserved_with_volume_not_wrong_package(catalog):
    group = WallGroup(wall_type="220", role="envelope", length_m=10, gross_area_m2=30, opening_area_m2=0,
                      net_area_m2=30, min_confidence=1, design_wall_system_id="W-GN01-220")
    group = group.model_copy(update={"design_mortar_material_id": "VU01"})
    mortar = next(b for b in pricing.bill_of_materials([group], catalog) if b.kind == "mortar")
    assert mortar.material_id == "VU01" and mortar.quantity == pytest.approx(round(30 * 0.22 * 0.29, 3))
    catalog.materials.loc[catalog.materials.material_id == "VU01", "unit"] = "bao"
    mortar = next(b for b in pricing.bill_of_materials([group], catalog) if b.kind == "mortar")
    assert mortar.quantity is None and mortar.est_cost is None and any("cách đổi" in r for r in mortar.missing)


def test_missing_mortar_identity_or_norm_stays_visible(catalog):
    group = WallGroup(wall_type="220", role="envelope", length_m=10, gross_area_m2=30, opening_area_m2=0,
                      net_area_m2=30, min_confidence=1, design_wall_system_id="W-GN01-220")
    selected = catalog.wall_systems.wall_system_id == "W-GN01-220"
    catalog.wall_systems.loc[selected, "mortar_m3_per_m3"] = None
    mortar = next(b for b in pricing.bill_of_materials([group], catalog) if b.kind == "mortar")
    assert mortar.quantity is None and mortar.missing
    catalog.wall_systems.loc[selected, "mortar_material_id"] = None
    mortar = next(b for b in pricing.bill_of_materials([group], catalog) if b.kind == "mortar")
    assert mortar.material_id is None and mortar.quantity is None and mortar.missing


def test_mortar_tons_use_only_density_for_same_material(catalog):
    group = WallGroup(wall_type="220", role="envelope", length_m=10, gross_area_m2=30, opening_area_m2=0,
                      net_area_m2=30, min_confidence=1, design_wall_system_id="W-GN01-220")
    catalog.materials.loc[catalog.materials.material_id == "VU02", "unit"] = "tấn"
    mortar = next(b for b in pricing.bill_of_materials([group], catalog) if b.kind == "mortar")
    assert mortar.quantity == pytest.approx(round(30 * 0.22 * 0.29 * 1800 / 1000, 3))
    catalog.materials.loc[catalog.materials.material_id == "VU01", "unit"] = "tấn"
    group = group.model_copy(update={"design_mortar_material_id": "VU01"})
    mortar = next(b for b in pricing.bill_of_materials([group], catalog) if b.kind == "mortar")
    assert mortar.quantity is None and any("thể tích" in r for r in mortar.missing)


def test_site_mix_mortar_is_intermediate_not_a_finished_product_purchase(catalog, monkeypatch):
    offer = pricing.PriceOffer(supplier_id="VUA", supplier_data_kind="ACTUAL", price=500000, unit="m³",
                              price_level="DEALER", price_date="2026-11-01", data_kind="ACTUAL")
    monkeypatch.setattr(pricing, "_latest_price_records", lambda ids: {"VU02": [offer]})
    group = WallGroup(wall_type="220", role="envelope", length_m=10, gross_area_m2=30, opening_area_m2=0,
                      net_area_m2=30, min_confidence=1, design_wall_system_id="W-GN01-220")
    mortar = next(b for b in pricing.bill_of_materials([group], catalog, actual_only=True) if b.kind == "mortar")
    assert mortar.is_intermediate and mortar.quantity is not None
    assert mortar.best_offer is None and mortar.best_price is None and mortar.est_cost is None
    assert "xi măng, cát" in mortar.price_note
    assert any("chi phí thành phần" in m for m in mortar.missing)
    assert len(mortar.offers) == 1 and not mortar.offers[0].eligible
    assert offer.eligible is False and offer.rejection_reasons == []


@pytest.mark.parametrize("source", [None, "", "ACTUAL", "SAMPLE", "UNKNOWN", "https://www.google.com/maps?q=1,2",
                                    "https://maps.app.goo.gl/abc", "https://www.openstreetmap.org/way/1"])
def test_actual_source_is_price_evidence_not_map_or_kind(source):
    offer = pricing.PriceOffer(supplier_id="S1", supplier_data_kind="ACTUAL", price=100, unit="viên", price_level="QUOTE",
                              price_date="2026-11-01", source_detail=source, url=source or "", data_kind="ACTUAL")
    best, checked = pricing.select_best_offer([offer], "viên", "ACTUAL", True, as_of="2026-11-03")
    assert best is None and any("chứng từ" in r for r in checked[0].rejection_reasons)


@pytest.mark.parametrize("expiry,eligible", [("2026-11-02", False), ("2026-11-03", True), ("2026-11-04", True),
                                             ("2026-11-03broken", False), ("không rõ", False), (None, True)])
def test_supplied_expiry_is_enforced_without_inventing_missing_validity(expiry, eligible):
    offer = pricing.PriceOffer(supplier_id="S1", supplier_data_kind="ACTUAL", price=100, unit="viên", price_level="QUOTE",
                              price_date="2026-11-01", source_detail="Báo giá fixture BG-02/2026", valid_until=expiry,
                              vat_included="YES", transport_included="NO", data_kind="ACTUAL")
    best, checked = pricing.select_best_offer([offer], "viên", "ACTUAL", True, as_of="2026-11-03")
    assert (best is not None) is eligible
    if not eligible:
        assert any("hiệu lực" in r for r in checked[0].rejection_reasons)


def test_supplier_profile_source_never_substitutes_for_quote_document(catalog):
    catalog.supplier_materials = catalog.supplier_materials.drop(columns="quote_reference")
    catalog.suppliers["source"] = "Trang Vàng: danh bạ NCC, không phải bảng giá"
    catalog.suppliers["maps_url"] = "https://www.google.com/maps?q=1,2"
    line = brick(catalog, True)
    assert line.best_offer is None and all(o.source_detail is None for o in line.offers)
    assert any("chứng từ" in r for o in line.offers for r in o.rejection_reasons)
    catalog.supplier_materials["product_url"] = "https://dealer.invalid/bao-gia/gach-GN01"
    line = brick(catalog, True)
    assert line.best_offer.price == 1500


def test_product_price_source_and_raw_expiry_are_carried_to_selector(catalog):
    catalog.supplier_materials["valid_until"] = "2026-11-03broken"
    line = brick(catalog, True)
    assert line.best_offer is None
    assert all(o.valid_until == "2026-11-03broken" for o in line.offers)
    assert any("hiệu lực" in r for o in line.offers for r in o.rejection_reasons)


def test_source_helper_accepts_document_or_price_page_but_not_arbitrary_url_text():
    assert pricing.has_price_source("Báo giá fixture BG-03/2026")
    assert pricing.has_price_source(price_url="https://dealer.invalid/bao-gia/03")
    assert not pricing.has_price_source(price_url="Báo giá không phải URL")
    assert not pricing.has_price_source(price_url="http://[invalid")
    assert not pricing.has_price_source(price_url="https://bad host/price")
    assert not pricing.has_price_source(price_url="https://dealer.invalid:invalid/price")


@pytest.mark.parametrize("field,raw,label", [("vat_included", "UNKNOWN", "VAT"), ("transport_included", None, "giao hàng")])
def test_unknown_terms_preserve_raw_quote_but_block_cost(catalog, field, raw, label):
    catalog.supplier_materials[field] = raw
    line = brick(catalog, True)
    assert line.best_offer is None and line.est_cost is None
    quote = next(o for o in line.offers if o.unit == "viên")
    assert getattr(quote, field) == raw and quote.price == 1500
    assert any(label in reason for reason in quote.rejection_reasons)


@pytest.mark.parametrize("field", ["vat_included", "transport_included"])
def test_different_known_terms_cannot_compete_on_price(catalog, field):
    quotes = catalog.supplier_materials
    quotes.loc[0, ["sale_unit", "base_price"]] = ["viên", 50]
    quotes.loc[0, field] = "NO" if quotes.loc[1, field] == "YES" else "YES"
    line = brick(catalog, True)
    assert line.best_offer is None and line.est_cost is None
    assert all(any("cùng điều kiện" in reason for reason in o.rejection_reasons) for o in line.offers)
    quotes.loc[0, field] = quotes.loc[1, field]
    best = brick(catalog, True).best_offer
    assert best.price == 50 and best.vat_included == "YES" and best.transport_included == "NO"


def test_unknown_bulletins_can_be_read_but_not_ranked_against_each_other():
    first = pricing.PriceOffer(price=100, unit="tấn", source="price_records", source_detail="Công bố fixture",
                               data_kind="ACTUAL", price_date="2026-01-03", price_level="BULLETIN", vat_included="YES")
    best, _ = pricing.select_best_offer([first], "tấn", "ACTUAL", True, "2026-11-03")
    assert best.is_reference and best.transport_included is None
    best, raw = pricing.select_best_offer([first, first.model_copy(update={"price": 80})], "tấn", "ACTUAL", True, "2026-11-03")
    assert best is None and all(o.is_reference for o in raw)


def test_old_dealer_record_is_not_a_current_quote():
    historical = pricing.PriceOffer(price=100, unit="tấn", source="price_records", source_detail="Phiếu giá cũ",
                                    supplier_id="S", supplier_data_kind="ACTUAL", data_kind="ACTUAL", price_date="2026-01-03",
                                    price_level="DEALER", vat_included="YES", transport_included="YES")
    best, raw = pricing.select_best_offer([historical], "tấn", "ACTUAL", True, "2026-11-03")
    assert best is None and any("lịch sử" in reason for reason in raw[0].rejection_reasons)
    assert not pricing.has_price_source("ftp://maps.invalid/x")
