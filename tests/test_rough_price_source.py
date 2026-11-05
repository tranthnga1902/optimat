"""Nguồn giá phần thô: fixture SYNTHETIC trong bộ nhớ, không đọc DB bằng monkeypatch."""
from types import SimpleNamespace

import pandas as pd
import pytest

from optimat.catalog import pricing
from optimat.rough.models import MaterialLine
from optimat.rough.takeoff import attach_prices


@pytest.fixture
def catalog():
    return SimpleNamespace(materials=pd.DataFrame([{"material_id": "M1", "data_kind": "ACTUAL"}]))


def line(**changes):
    return MaterialLine(**({"material_id": "M1", "name": "Vật liệu kiểm thử", "unit": "viên",
                            "quantity": 10, "quantity_with_waste": 11} | changes))


def quote(**changes):
    return pricing.PriceOffer(**({"price": 100, "price_level": "QUOTE", "unit": "viên", "supplier_id": "S1",
                                 "supplier_name": "Nhà cung cấp thử", "supplier_data_kind": "ACTUAL",
                                 "price_date": "2020-01-01", "data_kind": "ACTUAL", "source_detail": "Phiếu thử BG-01",
                                 "vat_included": "YES", "transport_included": "NO"} | changes))


def test_rough_uses_evidence_and_conditions_of_selected_quote(monkeypatch, catalog):
    offers = [quote(price=1, unit="kiện", source_detail="Phiếu sai đơn vị"),
              quote(url="https://example.test/gia-vien")]
    monkeypatch.setattr(pricing, "price_offers", lambda *_: {"M1": offers})
    m = line()
    attach_prices([m], catalog, actual_only=True)
    assert m.best_price == 100 and m.est_cost == 1100
    assert all(s in m.price_source for s in ("QUOTE", "Nhà cung cấp thử", "2020-01-01", "Phiếu thử BG-01",
                                             "https://example.test/gia-vien", "đã gồm VAT", "chưa gồm cước giao hàng"))
    assert "Phiếu sai đơn vị" not in m.price_source


@pytest.mark.parametrize("id_after,offer_after", [
    ("M1", quote(valid_until="2020-02-01")), ("M1", quote(transport_included="UNKNOWN")), (None, None)
])
def test_reselect_drops_old_money_but_retains_work(monkeypatch, catalog, id_after, offer_after):
    rows = {"M1": [quote()]}
    monkeypatch.setattr(pricing, "price_offers", lambda *_: rows)
    m = line()
    attach_prices([m], catalog, actual_only=True)
    assert m.est_cost == 1100
    m.material_id = id_after
    rows["M1"] = [offer_after] if offer_after else []
    preserved = m.model_dump(exclude={"best_price", "price_source", "est_cost"})
    attach_prices([m], catalog, actual_only=True)
    assert (m.best_price, m.price_source, m.est_cost) == (None, None, None)
    assert m.model_dump(exclude={"best_price", "price_source", "est_cost"}) == preserved


def test_reference_price_keeps_missing_data_and_no_partial_total(monkeypatch, catalog):
    reference = quote(price_level="BULLETIN", source="price_records", transport_included="UNKNOWN")
    monkeypatch.setattr(pricing, "price_offers", lambda *_: {"M1": [reference]})
    m = line(status="D", complete=False, missing=["thiếu phần lượng"], quantity_with_waste=None)
    attach_prices([m], catalog, actual_only=True)
    assert m.best_price == 100 and m.est_cost is None and m.status == "D" and m.quantity == 10
    assert m.missing == ["thiếu phần lượng"] and "tham khảo" in m.price_source and "chưa rõ cước" in m.price_source


@pytest.mark.parametrize("kind", ["SAMPLE", "SYNTHETIC"])
def test_scenario_source_retains_kind(monkeypatch, catalog, kind):
    monkeypatch.setattr(pricing, "price_offers", lambda *_: {"M1": [quote(data_kind=kind)]})
    m = line()
    attach_prices([m], catalog, actual_only=False)
    assert kind in m.price_source and m.best_price == 100


@pytest.mark.parametrize("valid_until,expected", [(None, "chưa rõ hiệu lực"), ("2099-12-31", "hiệu lực đến 2099-12-31")])
def test_source_retains_raw_validity_without_inventing_current_quote(monkeypatch, catalog, valid_until, expected):
    monkeypatch.setattr(pricing, "price_offers", lambda *_: {"M1": [quote(valid_until=valid_until)]})
    m = line()
    attach_prices([m], catalog, actual_only=True)
    assert m.best_price == 100 and expected in m.price_source
    assert "báo giá hiện hành" not in m.price_source
    assert "2020-01-01" in m.price_source  # ngày giá không tự thành ngày hết hiệu lực


def test_history_and_unknown_terms_are_labeled_without_touching_quantity(monkeypatch, catalog):
    offer = quote(source="price_records", vat_included="UNKNOWN", transport_included=None)
    monkeypatch.setattr(pricing, "price_offers", lambda *_: {"M1": [offer]})
    m = line()
    attach_prices([m], catalog, actual_only=False)
    assert "giá lịch sử tham khảo" in m.price_source
    assert "chưa rõ VAT" in m.price_source and "chưa rõ cước giao hàng" in m.price_source
    assert m.quantity == 10 and m.quantity_with_waste == 11


def test_d_status_never_gets_cost_even_when_complete_flag_is_true(monkeypatch, catalog):
    monkeypatch.setattr(pricing, "price_offers", lambda *_: {"M1": [quote()]})
    m = line(status="D", complete=True, missing=["chưa rõ phạm vi"])
    preserved = m.model_dump(exclude={"best_price", "price_source", "est_cost"})
    attach_prices([m], catalog, actual_only=True)
    assert m.best_price == 100 and m.est_cost is None
    assert m.model_dump(exclude={"best_price", "price_source", "est_cost"}) == preserved
