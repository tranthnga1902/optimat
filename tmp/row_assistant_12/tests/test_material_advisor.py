"""Kiểm mock staging; không OpenAI, CAD, DB hoặc đổi source chung."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("optimat.agent.material_advisor", ROOT / "agent/material_advisor.py")
advisor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = advisor
spec.loader.exec_module(advisor)

from optimat.catalog.repository import Catalog  # noqa: E402


def request(materials=None, works=None, **extra):
    context = {"binding": {"projectUid": "SYN-project", "drawingId": "SYN-drawing", "reviewId": "SYN-review", "materialRevision": "SYN-materials"},
               "partial": True, "scope": "SYNTHETIC — tầng thử nghiệm", "proposedMaterialIds": [],
               "works": works or [{"rowIndex": 0, "code": "COT", "quantity": 2, "unit": "m³", "status": "C", "checked": True}],
               "materials": materials or [{"lineId": "cement", "material_id": "XM02", "name": "Xi măng", "raw_class": "xi_mang",
                                            "unit": "tấn", "quantity": 1, "quantity_with_waste": None, "complete": True,
                                            "uses": [{"work": "COT", "quantity": 1}]}], **extra}
    raw = json.dumps(context, ensure_ascii=False)
    return advisor.MaterialRequest(question="Ưu tiên đúng quy cách, chỉ ra phần thiếu", contextJson=raw,
                                   contextHash=hashlib.sha256(raw.encode()).hexdigest(), requestId="SYN-request")


@pytest.fixture
def cat(monkeypatch):
    monkeypatch.setattr(advisor, "price_offers", lambda c, ids: {mid: [] for mid in ids})
    return Catalog.from_csv(None)


def mock_chat(messages, **kwargs):
    data = json.loads(messages[1]["content"])
    return {"content": json.dumps({"summary": "Cần giữ đúng thiết kế và kiểm phần còn thiếu.", "advice": [
        {"lineId": r["lineId"], "proposed_material_ids": [o["material_id"] for o in r["options"]],
         "reason": "Kiểm quy cách trước khi chọn nguồn mua.", "checks": ["Xác minh báo giá và kế hoạch cấp vật tư."]}
        for r in data["materials"]]}, ensure_ascii=False)}


def test_hash_and_schema_fail_before_chat(cat):
    req = request().model_copy(update={"contextHash": "0" * 64})
    with pytest.raises(ValueError):
        advisor.advise_materials(req, cat, lambda *a, **k: pytest.fail("Không được gọi OpenAI"))


def test_missing_price_demand_not_purchase_and_no_mutation(cat):
    req = request()
    before = req.model_dump_json()
    result = advisor.advise_materials(req, cat, mock_chat)
    line = result["facts"]["materials"][0]
    assert line["demand_quantity"] == 1 and line["purchase_quantity"] is None
    assert line["options"][0]["offer"] is None and line["options"][0]["canApply"] is False
    assert result["facts"]["coverage"][0]["coverage"] == "mapped_aggregate"
    assert result["provenance"] == "client_snapshot" and result["applied"] is False
    assert req.model_dump_json() == before


def test_multiple_proposals_are_not_approved(cat):
    result = advisor.advise_materials(request(proposedMaterialIds=["XM01"]), cat, mock_chat)
    options = result["facts"]["materials"][0]["options"]
    assert {o["material_id"] for o in options} == {"XM01", "XM02"}
    alternative = next(o for o in options if o["material_id"] == "XM01")
    assert alternative["state"] == "proposed" and alternative["needsDesignReview"] and alternative["needsGeometryReview"]
    assert not alternative["canApply"]


def test_unknown_material_keeps_known_part(cat):
    req = request(materials=[{"lineId": "steel", "material_id": None, "name": "Thép chưa chia đường kính", "raw_class": "thep",
                             "unit": "tấn", "quantity": 1.5, "quantity_with_waste": None, "complete": False,
                             "missing": ["Thiếu đường kính/cấp thép/chiều dài cây"]}])
    result = advisor.advise_materials(req, cat, mock_chat)
    line = result["facts"]["materials"][0]
    assert line["demand_quantity"] == 1.5 and not line["complete"] and not line["options"]
    assert result["facts"]["coverage"][0]["coverage"] == "missing"


def test_no_material_unsupported_missing_and_aggregate_elements(cat):
    works = [{"rowIndex": i, "code": code, "plan": "Tầng thử", "element": f"SYN-{i}", "quantity": 1,
              "unit": "m³", "status": "C", "checked": True, **extra}
             for i, (code, extra) in enumerate([("DAO_DAT", {}), ("CAU_THANG", {"basis": "not_supported"}),
                                                ("COT", {}), ("COT", {}), ("DAM", {"quantity": None})])]
    materials = [{"lineId": "cement", "material_id": "XM02", "name": "Xi măng", "raw_class": "xi_mang", "unit": "tấn",
                  "quantity": 1, "complete": True, "uses": [{"work": "COT", "plan": "Tầng thử", "quantity": 1}]}]
    result = advisor.advise_materials(request(materials, works), cat, mock_chat)
    coverage = result["facts"]["coverage"]
    assert [r["coverage"] for r in coverage] == ["no_purchase_material", "unsupported", "mapped_aggregate", "mapped_aggregate", "missing"]
    assert result["facts"]["materials"][0]["demand_quantity"] == 1  # Không chia đều hoặc cộng lại.
    assert coverage[2]["materialIds"] == coverage[3]["materialIds"] == ["cement"]


@pytest.mark.parametrize("bad", [
    {"summary": "Giá là 100 đồng", "advice": []},
    {"summary": "Gợi ý", "advice": [{"lineId": "cement", "proposed_material_ids": ["FAKE"], "reason": "Kiểm", "checks": []}]},
    {"summary": "Gợi ý", "advice": []},
])
def test_bad_ai_output_is_rejected(cat, bad):
    with pytest.raises(ValueError):
        advisor.advise_materials(request(), cat, lambda *a, **k: {"content": json.dumps(bad)})


def test_refusal_and_payload_allowlist(cat):
    with pytest.raises(ValueError):
        advisor.advise_materials(request(), cat, lambda *a, **k: {"refusal": "refused"})
    def capture(messages, **kwargs):
        payload = messages[1]["content"]
        assert "SYN-project" not in payload and "SYN-drawing" not in payload and "SYN-review" not in payload
        return mock_chat(messages, **kwargs)
    advisor.advise_materials(request(), cat, capture)


def test_all_rough_classes_without_walls_or_optimizer(cat):
    materials, works = [], []
    groups = [("COT", "vua_be_tong"), ("SAN", "xi_mang"), ("SAN", "cat"), ("SAN", "da"),
              ("COT_THEP", "thep"), ("COP_PHA", "cop_pha"), ("XAY", "gach"), ("TRAT", "vua_be_tong"),
              ("CAN_NEN", "xi_mang"), ("CHONG_THAM", "chong_tham"), ("CHONG_THAM", "phu_gia")]
    for i, (code, raw_class) in enumerate(groups):
        rows = cat.materials[cat.materials.raw_class == raw_class]
        assert not rows.empty, raw_class
        mat = rows.iloc[0]
        materials.append({"lineId": f"SYN-line-{i}", "material_id": str(mat.material_id), "name": str(mat["name"]),
                          "raw_class": raw_class, "unit": str(mat.unit), "quantity": 1, "complete": True,
                          "sources": ["SYNTHETIC — fixture kiểm hợp đồng, không phải định mức"],
                          "uses": [{"work": code, "plan": "SYN", "quantity": 1}]})
        works.append({"rowIndex": i, "code": code, "plan": "SYN", "element": f"SYN-{i}",
                      "quantity": 1, "unit": WORK_UNITS[code], "status": "C", "checked": True})
    intermediate = [{"name": "Vữa SYN trung gian", "quantity": 2, "unit": "m³", "complete": True}]
    result = advisor.advise_materials(request(materials, works, intermediates=intermediate), cat, mock_chat)
    assert len(result["facts"]["coverage"]) == len(works)
    assert all(w["coverage"] == "mapped_aggregate" for w in result["facts"]["coverage"])
    assert len(result["ai"]["advice"]) == len(materials)
    assert result["facts"]["intermediates"] == intermediate
    assert all(m["purchase_quantity"] is None for m in result["facts"]["materials"])
    assert all(o["u_value"] is None for m in result["facts"]["materials"] for o in m["options"])


WORK_UNITS = {k: v[1] for k, v in advisor.WORKS.items()}


def test_signed_deduction_and_contribution_preserved(cat):
    req = request(materials=[{"lineId": "deduction", "material_id": None, "name": "Khoản trừ nguồn", "raw_class": "cop_pha",
                             "unit": "m²", "quantity": -0.194, "quantity_with_waste": -0.194, "complete": False,
                             "uses": [{"work": "COP_PHA", "quantity": -0.194, "via": "SYN trừ đáy sàn"}]}],
                  works=[{"rowIndex": 38, "code": "COP_PHA", "element": "trừ đáy sàn trên mặt dầm, đỉnh cột",
                          "quantity": -0.194, "unit": "m²", "status": "C", "checked": False}])
    result = advisor.advise_materials(req, cat, mock_chat)
    work = result["facts"]["coverage"][0]
    assert work["quantity"] == -0.194 and work["quantity_role"] == "deduction"
    line = result["facts"]["materials"][0]
    assert line["demand_quantity"] == -0.194 and line["purchase_quantity"] is None
    assert any("âm" in m for m in line["missing"])


def test_unique_exact_catalog_match_needs_no_manual_candidate(cat):
    mat = cat.materials[cat.materials.material_id == "TH10"].iloc[0]
    req = request(materials=[{"lineId": "wire", "material_id": None, "name": str(mat["name"]), "raw_class": "thep",
                             "unit": str(mat.unit), "quantity": 1, "complete": False}])
    result = advisor.advise_materials(req, cat, mock_chat)
    options = result["facts"]["materials"][0]["options"]
    assert len(options) == 1 and options[0]["material_id"] == "TH10"
    assert options[0]["resolution_source"] == "unique_catalog_name_unit_class"
    assert options[0]["state"] == "current_lookup" and not options[0]["canApply"]


def test_reference_price_is_not_commercial_and_zero_option_name_in_prompt(cat, monkeypatch):
    from datetime import date
    from optimat.catalog.pricing import PriceOffer
    offer = PriceOffer(price=100, unit="kg", price_level="BULLETIN", price_date=date.today().isoformat(),
                       data_kind="ACTUAL", source_detail="SYN công bố giá cho mock")
    monkeypatch.setattr(advisor, "price_offers", lambda c, ids: {mid: [offer] for mid in ids})
    req = request(materials=[
        {"lineId": "wire", "material_id": "TH10", "name": "Dây thép buộc 1 ly", "raw_class": "thep", "unit": "kg", "quantity": 1, "complete": False},
        {"lineId": "steel", "material_id": None, "name": "Thép chịu lực chưa chia đường kính", "raw_class": "thep", "unit": "tấn", "quantity": None, "complete": False}])
    def capture(messages, **kwargs):
        data = json.loads(messages[1]["content"])
        wire, steel = data["materials"]
        assert wire["options"][0]["has_eligible_price"] is False
        assert wire["options"][0]["offer"]["is_reference"] is True
        assert steel["name"] == "Thép chịu lực chưa chia đường kính" and not steel["options"]
        assert data["partial"] is True and "coverage" in data
        return mock_chat(messages, **kwargs)
    advisor.advise_materials(req, cat, capture)


@pytest.mark.parametrize("text,allowed,bad", [
    ("Mã TH10 cần kiểm.", {"TH10"}, False),
    ("(TH10), chưa có giá.", {"TH10"}, False),
    ("Mã TH10", set(), True),
    ("TH100", {"TH10"}, True),
    ("X-TH10", {"TH10"}, True),
    ("TH10-A", {"TH10"}, True),
    ("TH10.5", {"TH10"}, True),
    ("TH10 giá 12 triệu", {"TH10"}, True),
    ("Giao 7 ngày", {"TH10"}, True),
    ("Ngày 03/11/2026", {"TH10"}, True),
    ("U=0.5", {"TH10"}, True),
])
def test_whole_catalog_code_guard(text, allowed, bad):
    assert advisor._unverified_number(text, allowed) is bad


def test_code_allowed_in_own_line_and_summary_but_not_other_line(cat):
    req = request(materials=[
        {"lineId": "m0", "material_id": None, "name": "Thép chịu lực chưa chia đường kính", "raw_class": "thep", "unit": "tấn", "complete": False},
        {"lineId": "m5", "material_id": "TH10", "name": "Dây thép buộc 1 ly", "raw_class": "thep", "unit": "kg", "complete": False}])
    reply = {"summary": "Chỉ TH10 có mã tra được, chưa có giá.", "advice": [
        {"lineId": "m0", "proposed_material_ids": [], "reason": "Chưa rõ quy cách thép chịu lực.", "checks": []},
        {"lineId": "m5", "proposed_material_ids": ["TH10"], "reason": "TH10 là dây buộc, chưa có giá.", "checks": ["Kiểm nguồn TH10."]}]}
    good = advisor.advise_materials(req, cat, lambda *a, **k: {"content": json.dumps(reply)})
    assert good["ai"]["advice"][1]["proposed_material_ids"] == ["TH10"]
    reply["advice"][0]["reason"] = "Dùng TH10 cho thép chịu lực."
    with pytest.raises(ValueError):
        advisor.advise_materials(req, cat, lambda *a, **k: {"content": json.dumps(reply)})


def test_advisory_without_material_revision_and_normalized_binding(cat):
    req = request()
    raw = json.loads(req.contextJson)
    del raw["binding"]["materialRevision"]
    context_json = json.dumps(raw)
    req = req.model_copy(update={"contextJson": context_json, "contextHash": hashlib.sha256(context_json.encode()).hexdigest()})
    result = advisor.advise_materials(req, cat, mock_chat)
    assert result["binding"]["materialRevision"] is None
    assert result["binding"]["reviewId"] == "SYN-review" and result["applied"] is False
    raw["binding"]["materialRevision"] = ""
    with pytest.raises(ValueError):
        advisor.MaterialContext.model_validate(raw)
