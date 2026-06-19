from fastapi.testclient import TestClient

from app.main import _requires_verified_session, app
from app.services.session import SessionManager


def test_what_is_my_balance_requires_verification():
    assert _requires_verified_session("what is my balance") is True


def test_minimum_balance_faq_does_not_require_verification():
    assert _requires_verified_session("what is minimum balance") is False


def test_unverified_balance_request_prompts_for_account_number(monkeypatch):
    manager = SessionManager()
    monkeypatch.setattr("app.main.session_manager", manager)

    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"session_id": "verify-test", "message": "what is my balance"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["session_verified"] is False
    assert payload["user_id"] == "unverified"
    assert "account number" in payload["response"].lower()
    assert "Rs." not in payload["response"]


def test_verified_session_returns_customer_specific_balance(monkeypatch):
    manager = SessionManager()
    monkeypatch.setattr("app.main.session_manager", manager)

    client = TestClient(app)
    client.post(
        "/chat",
        json={"session_id": "cust-002-test", "message": "5010007788"},
    )
    response = client.post(
        "/chat",
        json={"session_id": "cust-002-test", "message": "what is my balance"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["session_verified"] is True
    assert payload["user_id"] == "cust_002"
    assert "XXXXXX7788" in payload["response"]
