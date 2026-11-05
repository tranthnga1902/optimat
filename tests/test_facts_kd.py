"""KD02–KD07: kiểm chứng chống bịa, gắn nhãn AI (giả lập, không gọi mạng), quy tắc thông số, hàng chờ duyệt -> CSV,
ánh xạ dự toán. Mọi đề xuất AI sai nhãn/trích đoạn bịa phải bị loại; số luôn do mã đọc từ trích đoạn."""
import csv
import json
import shutil
from types import SimpleNamespace

import pytest

from optimat import config
from optimat.agent import llm
from optimat.drawing import plans
from optimat.facts import ai, estimate, labels, params, review
from optimat.facts.verify import check


@pytest.fixture
def fake_ai(monkeypatch, tmp_path):
    """Bật AI với phản hồi giả; ghi lại các lần gọi và schema đã gửi."""
    calls = []
    monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "khoa-gia")
    monkeypatch.setenv("OPTIMAT_AI_CACHE_DIR", str(tmp_path / "ai"))
    monkeypatch.setenv("OPTIMAT_AI_QUEUE", str(tmp_path / "queue.jsonl"))
    replies = {}

    def chat(messages, tools=None, json_mode=False, schema=None):
        calls.append(schema)
        llm.LAST_USAGE.clear()
        llm.LAST_USAGE.update(total_tokens=10)
        return {"content": json.dumps({"items": replies.get(schema[0], [])})}
    monkeypatch.setattr(llm, "chat_openai", chat)
    return SimpleNamespace(calls=calls, replies=replies)


def test_verify_rejects_fabrication():
    sources = {"t1": "Lớp vữa trát trần #75 dày 15"}
    ok = {"ref": "t1", "label": "plaster_thickness_mm", "excerpt": "trát trần #75 dày 15"}
    assert check(ok, sources, {"plaster_thickness_mm"}) is None
    assert check({**ok, "ref": "t9"}, sources, {"plaster_thickness_mm"}) == "nguồn không tồn tại"
    assert check({**ok, "label": "khac"}, sources, {"plaster_thickness_mm"}) == "nhãn ngoài danh mục"
    assert check({**ok, "excerpt": "trát trần dày 20"}, sources, {"plaster_thickness_mm"}) == "trích đoạn không có trong nguồn"
    assert check({**ok, "excerpt": " "}, sources, {"plaster_thickness_mm"}) == "thiếu trích đoạn"


def test_rules_read_params_without_ai(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "none")
    items = params.candidates([("t0", "- tráT trầN vxm máC 75 dàY 15."), ("t1", "tường xây bằng gạch đặc mác 75 với vữa xi măng mác 50"),
                               ("t2", "bê tông lót b7.5 (m100)"), ("t3", "sàN btct Đổ tạI chỗ máC 200 dàY 120."), ("t4", "12")])
    report = params.extract(items, "kc.dxf", allow_ai=True)
    got = {(f.field, f.value) for f in report.facts}
    assert {("plaster_thickness_mm", 15.0), ("plaster_mortar_grade", "M75"), ("masonry_mortar_grade", "M50"),
            ("lean_concrete_grade", "M100"), ("slab_thickness_mm", 120.0), ("concrete_grade", "M200")} <= got
    assert ("masonry_mortar_grade", "M75") not in got          # mác gạch không bị đọc thành mác vữa
    assert report.ai["status"] == "khong_co_muc" and all(f.method == "rule" and f.status == "B" for f in report.facts)


def test_suggest_keeps_conflicts_for_user():
    facts = params.extract(params.candidates([("t0", "sàn btct dày 100"), ("t1", "bản sàn btct dày 12cm"),
                                              ("t2", "trát tường vxm mác 75 dày 15")]), "kc", False).facts
    suggested, conflicts = params.suggest(facts)
    assert suggested["plaster_thickness_mm"]["value"] == 15.0
    assert "slab_thickness_mm" not in suggested and {o["value"] for o in conflicts["slab_thickness_mm"]} == {100.0, 120.0}


def test_ai_labels_rest_numbers_read_by_code(fake_ai):
    fake_ai.replies["kd_thong_so"] = [
        {"ref": "t0", "label": "lintel_height_mm", "excerpt": "lanh tô cao 200"},          # đúng
        {"ref": "t0", "label": "lintel_bearing_mm", "excerpt": "gối 250"},                   # bịa: không có trong dòng
        {"ref": "t1", "label": "waterproof_upturn_mm", "excerpt": "chống thấm chân tường"},  # không có số: loại
    ]
    items = [{"ref": "t0", "text": "Lanh tô cao 200 đặt trên cửa"}, {"ref": "t1", "text": "Quét chống thấm chân tường WC"}]
    report = params.extract(items, "kt.dxf", allow_ai=True)
    assert [(f.field, f.value, f.method) for f in report.facts] == [("lintel_height_mm", 200.0, "ai_label")]
    assert {r["reason"] for r in report.rejected} == {"trích đoạn không có trong nguồn", "không đọc được số từ trích đoạn"}
    schema = fake_ai.calls[0][1]["properties"]["items"]["items"]
    assert schema["properties"]["ref"]["enum"] == ["t0", "t1"] and "lintel_height_mm" in schema["properties"]["label"]["enum"]
    assert report.ai["status"] == "ok" and report.ai["tokens"] == 10
    params.extract(items, "kt.dxf", allow_ai=True)
    assert len(fake_ai.calls) == 1                                       # lần hai lấy từ cache, không gọi lại
    assert params.extract(items, "kt.dxf", allow_ai=False).ai["status"] == "off"


def test_ai_network_error_keeps_rules(monkeypatch, fake_ai):
    def down(*args, **kwargs):
        raise llm.LLMUnavailable("mất mạng")
    monkeypatch.setattr(llm, "chat_openai", down)
    report = params.extract([{"ref": "t0", "text": "trát trần vxm mác 75 dày 15"}, {"ref": "t1", "text": "lanh tô cao 200"}],
                            "kt", allow_ai=True)
    assert report.ai["status"] == "loi" and {f.field for f in report.facts} == {"plaster_thickness_mm", "plaster_mortar_grade"}


@pytest.fixture
def rules_copy(monkeypatch, tmp_path):
    folder = tmp_path / "rules"
    shutil.copytree(config.DATA_DIR / "rules", folder)
    monkeypatch.setattr(review, "RULES", folder)
    monkeypatch.setenv("OPTIMAT_AI_QUEUE", str(tmp_path / "queue.jsonl"))
    return folder


def _rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_review_queue_approve_writes_rule_rows(rules_copy):
    review.enqueue("thong_so", [{"label": "lintel_height_mm", "excerpt": "lanh tô cao 200", "text": "Lanh tô cao 200"}], "a")
    review.enqueue("thong_so", [{"label": "lintel_height_mm", "excerpt": "lanh tô cao 220", "text": "x"}], "b")   # cùng mẫu
    review.enqueue("loai_ban_ve", [{"label": "BV01", "excerpt": "MB BỐ TRÍ TẦNG 2", "text": "MB BỐ TRÍ TẦNG 2"}], "a")
    review.enqueue("ky_hieu", [{"label": "BEAM", "excerpt": "DS12", "text": "DS12"}], "a")
    items = review.pending()
    assert len(items) == 3 and items[0]["seen"] == 2
    by_task = {i["task"]: i for i in items}
    done = review.decide(by_task["thong_so"]["id"], True, "qa@test")
    row = _rows(rules_copy / "ghi_chu_thong_so.csv")[-1]
    assert row["truong"] == "lintel_height_mm" and done["status"] == "da_duyet"
    assert params.re.compile(row["mau"]).search(params.norm("Lanh tô cao 180"))   # số thay bằng \d+
    review.decide(by_task["loai_ban_ve"]["id"], True, "qa@test")
    assert _rows(rules_copy / "loai_ban_ve.csv")[-1]["ma"] == "BV01"
    assert _rows(rules_copy / "tieu_de_mat_bang.csv")[-1]["mau"].startswith("^mb")
    review.decide(by_task["ky_hieu"]["id"], False, "qa@test")
    assert not review.pending()
    with pytest.raises(ValueError):
        review.decide(by_task["ky_hieu"]["id"], True, "qa@test")
    with pytest.raises(KeyError):
        review.decide("khong-co", True, "qa@test")


def test_symbol_rule_uses_letter_prefix(rules_copy):
    review.enqueue("ky_hieu", [{"label": "BEAM", "excerpt": "DS7a", "text": "DS7a"}], "a")
    review.decide(review.pending()[0]["id"], True, "qa")
    row = _rows(rules_copy / "ky_hieu_cau_kien.csv")[-1]
    assert row["mau"] == r"ds\d+[a-z]?" and row["vai_tro"] == "BEAM" and row["ten"] == "dầm, đà kiềng, giằng móng"


def test_approved_plan_title_is_recognized(monkeypatch, tmp_path):
    path = tmp_path / "tieu_de_mat_bang.csv"
    path.write_text("ma,mau,ghi_chu\nMB01,^mat bang bo tri tang\\s*\\d+,x\n", encoding="utf-8")
    monkeypatch.setattr(plans, "PLAN_TITLE_FILE", path)
    plans.extra_plan_titles.cache_clear()
    try:
        assert not plans._is_plan_title("CHI TIẾT MẶT BẰNG BỐ TRÍ TẦNG 2")
        assert plans._is_plan_title("MB BỐ TRÍ TẦNG 2")          # "bố trí" là từ loại trừ, nhưng mẫu đã duyệt thắng
    finally:
        plans.extra_plan_titles.cache_clear()


def test_estimate_rows_mapped_quantity_from_cells(fake_ai):
    fake_ai.replies["kd_du_toan"] = [{"ref": "r2", "label": "COT", "excerpt": "Đổ trụ đứng BTCT"},
                                     {"ref": "r3", "label": "OUT", "excerpt": "Sơn nước"}]
    cand = [{"fields": {"work": "Xây tường gạch ống 8x8x19 dày 100", "unit": "m3", "quantity": "103,427"}},
            {"fields": {"work": "Bê tông lót móng đá 4x6 M100", "unit": "m3", "quantity": "11.784"}},
            {"fields": {"work": "Đổ trụ đứng BTCT", "unit": "m3", "quantity": "2"}},
            {"fields": {"work": "Sơn nước", "unit": "m2", "quantity": "500"}}]
    out = estimate.map_rows(cand, "dt.xlsx", allow_ai=True)
    assert [r["work_code"] for r in out["rows"]] == ["XAY", "BE_TONG_LOT", "COT", "OUT"]
    assert [r["work_method"] for r in out["rows"]] == ["rule", "rule", "ai_label", "ai_label"]
    assert {(t["code"], t["unit"], t["quantity"]) for t in out["totals"]} == {
        ("XAY", "m³", 103.427), ("BE_TONG_LOT", "m³", 11.784), ("COT", "m³", 2.0)}
    cmp = estimate.compare(out["totals"], [{"code": "XAY", "unit": "m³", "quantity": 90.0}])
    xay = next(c for c in cmp if c["code"] == "XAY")
    assert xay["diff_pct"] == pytest.approx(-13.0, abs=0.1) and next(c for c in cmp if c["code"] == "COT")["note"]


def test_label_drawing_offers_only_unmatched_items(fake_ai):
    T = lambda text, y=0.0, x=0.0, h=2.5: SimpleNamespace(text=text, x=x, y=y, layer="0", encoding="", height=h)  # noqa: E731
    drawing = SimpleNamespace(texts=[T("MẶT BẰNG TẦNG 1"), T("MB BỐ TRÍ CÔNG NĂNG LẦU 2"), T("DS1"), T("DS2"), T("C1"), T("C2")])
    fake_ai.replies["kd_loai_ban_ve"] = [{"ref": "t1", "label": "BV01", "excerpt": "MB BỐ TRÍ CÔNG NĂNG LẦU 2"}]
    fake_ai.replies["kd_ky_hieu"] = [{"ref": "t2", "label": "BEAM", "excerpt": "DS1"}]
    report = labels.label_drawing(drawing, "kt.dxf", allow_ai=True, need_plan=False)
    sent = {name: schema["properties"]["items"]["items"]["properties"]["ref"]["enum"] for name, schema in fake_ai.calls}
    assert sent["kd_loai_ban_ve"] == ["t1"]                  # tiêu đề đã khớp loai_ban_ve không gửi AI
    assert sent["kd_ky_hieu"] == ["t2"]                      # C1/C2 đã có quy tắc; DS gặp 2 lần
    assert {(f.task, f.field) for f in report.facts} == {("loai_ban_ve", "BV01"), ("ky_hieu", "BEAM")}
    assert len(review.pending()) == 2


def test_review_api_lists_and_decides(rules_copy):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from optimat.api.ai_review import router
    app = FastAPI()
    app.include_router(router)
    review.enqueue("tieu_de_bang", [{"label": "duong_kinh", "excerpt": "Ø thép", "text": "Ø thép"}], "kc")
    with TestClient(app) as client:
        items = client.get("/api/admin/ai-proposals").json()["items"]
        assert [i["label"] for i in items] == ["duong_kinh"]
        assert client.post(f"/api/admin/ai-proposals/{items[0]['id']}", json={"approve": True}).json()["status"] == "da_duyet"
        assert client.post(f"/api/admin/ai-proposals/{items[0]['id']}", json={"approve": True}).status_code == 409
        assert client.post("/api/admin/ai-proposals/khong-co", json={"approve": False}).status_code == 404
    assert _rows(rules_copy / "bang_thep.csv")[-1]["khoa"] == "duong_kinh"


def test_door_width_from_leaf_arcs():
    """KD08: block cửa đi không ghi rộng, dự án không có rộng cửa -> rộng = tổng bán kính cung cánh cửa của chính block."""
    from optimat.drawing.takeoff import _opening_size_mm, leaf_width_mm
    from optimat.schemas import OpeningDefaults
    block = SimpleNamespace(name="D8", x=0.0, y=0.0, attribs={})
    arc = lambda r, cx=0.0, src="D8", s=0, e=90: SimpleNamespace(r=r, cx=cx, cy=0.0, source=src, sweep=(e - s) % 360)  # noqa: E731
    assert leaf_width_mm(block, [arc(670)]) == 670
    mid = SimpleNamespace(name="D8", x=771.0, y=0.0, attribs={})
    assert leaf_width_mm(mid, [arc(771), arc(771, cx=1542)]) == 1542              # cánh đôi, điểm chèn giữa cửa
    assert leaf_width_mm(block, [arc(670, src="KHAC"), arc(670, cx=5000), arc(670, e=180)]) is None
    assert _opening_size_mm(block, OpeningDefaults(door_height_mm=2000), [arc(670)]) == (670, 2000)
    assert _opening_size_mm(block, None, [arc(670)]) is None                        # thiếu cao: vẫn không đoán (B7)
