"""Router staging: bind phiên/context, không API thật hoặc DB."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from test_material_advisor import advisor, request

from optimat.api import material_advisor as api


@pytest.fixture
def client(monkeypatch):
    api._sessions.clear()
    monkeypatch.setenv("OPTIMAT_ASSISTANT_LOCAL_DEMO", "1")
    monkeypatch.setattr(api, "get_database_url", lambda: None)
    monkeypatch.setattr(api, "llm_available", lambda: True)
    monkeypatch.setattr(api.config, "LLM_PROVIDER", "openai")
    app = FastAPI()
    app.include_router(api.router)
    app.dependency_overrides[api.require_user] = lambda: None
    with TestClient(app, headers={"origin": "http://localhost:3000"}) as c:
        yield c


def test_no_cookie_and_cross_snapshot_never_call_model(client, monkeypatch):
    monkeypatch.setattr(api, "advise_materials", lambda *a: pytest.fail("Không được gọi model"))
    payload = request().model_dump()
    assert client.post("/api/assistant/materials", json=payload).status_code == 401
    assert client.post("/api/assistant/material-session", json=payload).status_code == 200
    other = request(scope="Bản khác")
    assert client.post("/api/assistant/materials", json=other.model_dump()).status_code == 409


def test_missing_key_and_network_errors_are_sanitized(client, monkeypatch):
    payload = request().model_dump()
    client.post("/api/assistant/material-session", json=payload)
    monkeypatch.setattr(api, "llm_available", lambda: False)
    assert client.post("/api/assistant/materials", json=payload).status_code == 503
    monkeypatch.setattr(api, "llm_available", lambda: True)
    monkeypatch.setattr(api.Catalog, "load", lambda: None)
    def fail(*args):
        raise api.LLMUnavailable("SENSITIVE upstream header")
    monkeypatch.setattr(api, "advise_materials", fail)
    response = client.post("/api/assistant/materials", json=payload)
    assert response.status_code == 503 and "SENSITIVE" not in response.text


def test_disabled_local_and_bad_origin(client, monkeypatch):
    payload = request().model_dump()
    monkeypatch.delenv("OPTIMAT_ASSISTANT_LOCAL_DEMO")
    assert client.post("/api/assistant/material-session", json=payload).status_code == 403
    monkeypatch.setenv("OPTIMAT_ASSISTANT_LOCAL_DEMO", "1")
    assert client.post("/api/assistant/material-session", json=payload, headers={"origin": "https://evil.example"}).status_code == 403


def test_cookie_flags_expired_and_payload_hash(client, monkeypatch):
    payload = request().model_dump()
    response = client.post("/api/assistant/material-session", json=payload)
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    for session in api._sessions.values():
        session["expires"] = 0
    assert client.post("/api/assistant/materials", json=payload).status_code == 401
    payload["contextHash"] = "0" * 64
    assert client.post("/api/assistant/material-session", json=payload).status_code == 422


def test_bound_success_no_mutation_and_limit(client, monkeypatch):
    payload = request().model_dump()
    client.post("/api/assistant/material-session", json=payload)
    monkeypatch.setattr(api.Catalog, "load", lambda: None)
    monkeypatch.setattr(api, "advise_materials", lambda req, cat: {"requestId": req.requestId, "applied": False})
    for _ in range(api.MAX_CALLS):
        response = client.post("/api/assistant/materials", json=payload)
        assert response.status_code == 200 and response.json()["applied"] is False
    assert client.post("/api/assistant/materials", json=payload).status_code == 429


def test_different_logged_user_cannot_reuse_session(client, monkeypatch):
    payload = request().model_dump()
    client.post("/api/assistant/material-session", json=payload)
    monkeypatch.setattr(api, "get_database_url", lambda: "configured")
    client.app.dependency_overrides[api.require_user] = lambda: {"user_id": 999}
    monkeypatch.setattr(api, "advise_materials", lambda *a: pytest.fail("Không được gọi model"))
    assert client.post("/api/assistant/materials", json=payload).status_code == 401


def test_optional_revision_session_and_changed_review_is_stale(client, monkeypatch):
    import hashlib
    import json
    payload = request().model_dump()
    raw = json.loads(payload["contextJson"])
    del raw["binding"]["materialRevision"]
    payload["contextJson"] = json.dumps(raw)
    payload["contextHash"] = hashlib.sha256(payload["contextJson"].encode()).hexdigest()
    bound = client.post("/api/assistant/material-session", json=payload)
    assert bound.status_code == 200 and bound.json()["binding"]["materialRevision"] is None
    monkeypatch.setattr(api, "advise_materials", lambda *a: pytest.fail("Không được gọi OpenAI khi stale"))
    for field, value in [("reviewId", "new-review"), ("materialRevision", "new-materials")]:
        changed = json.loads(payload["contextJson"])
        changed["binding"][field] = value
        request_body = {**payload, "contextJson": json.dumps(changed)}
        request_body["contextHash"] = hashlib.sha256(request_body["contextJson"].encode()).hexdigest()
        assert client.post("/api/assistant/materials", json=request_body).status_code == 409


def test_exact_demo_origin_3001_bound_request_and_guards(client, monkeypatch):
    payload = request().model_dump()
    origin = {"origin": "http://127.0.0.1:3001"}
    calls = []
    monkeypatch.setattr(api.Catalog, "load", lambda: None)
    def mock_advice(req, catalog):
        calls.append(req.requestId)
        return {"requestId": req.requestId, "contextHash": req.contextHash, "applied": False}
    monkeypatch.setattr(api, "advise_materials", mock_advice)

    # Origin hợp lệ không thay thế cookie phiên hoặc binding.
    assert client.post("/api/assistant/materials", json=payload, headers=origin).status_code == 401
    session = client.post("/api/assistant/material-session", json=payload, headers=origin)
    assert session.status_code == 200 and session.json()["provenance"] == "client_snapshot"
    answer = client.post("/api/assistant/materials", json=payload, headers=origin)
    assert answer.status_code == 200 and answer.json()["applied"] is False
    assert calls == [payload["requestId"]]

    changed = request(scope="Bản thay đổi").model_dump()
    assert client.post("/api/assistant/materials", json=changed, headers=origin).status_code == 409
    bad_origins = ["http://127.0.0.1:3002", "http://localhost:3001", "https://evil.example", ""]
    for bad_origin in bad_origins:
        for path in ("material-session", "materials"):
            assert client.post(f"/api/assistant/{path}", json=payload, headers={"origin": bad_origin}).status_code == 403
    # Kiểm header thực sự vắng, không chỉ chuỗi Origin rỗng.
    client.headers.pop("origin", None)
    for path in ("material-session", "materials"):
        assert client.post(f"/api/assistant/{path}", json=payload).status_code == 403

    monkeypatch.delenv("OPTIMAT_ASSISTANT_LOCAL_DEMO")
    for path in ("material-session", "materials"):
        assert client.post(f"/api/assistant/{path}", json=payload, headers=origin).status_code == 403
    monkeypatch.setattr(api, "get_database_url", lambda: "configured")
    for path in ("material-session", "materials"):
        assert client.post(f"/api/assistant/{path}", json=payload, headers=origin).status_code == 401
    assert calls == [payload["requestId"]]  # Mọi nhánh bị chặn đều không gọi trợ lý.
