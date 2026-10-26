"""Tests for the hardened admin allowlist gate on /admin/* endpoints."""
import pytest

from app.core.config import settings

API = "/api/v1"


@pytest.fixture()
def admin_emails(monkeypatch):
    """Set the ADMIN_EMAILS allowlist for a test (settings is a singleton)."""
    def _set(value: str):
        monkeypatch.setattr(settings, "ADMIN_EMAILS", value)

    return _set


def _register_login(client, email, role="learner"):
    body = {
        "email": email, "password": "Strong123",
        "full_name": "U", "display_name": "U", "role": role,
    }
    if role == "learner":
        body["age"] = 20
    client.post(f"{API}/auth/register", json=body)
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_non_allowlisted_learner_is_forbidden(client, admin_emails):
    admin_emails("boss@example.com")
    headers = _register_login(client, "random@example.com")
    resp = client.get(f"{API}/admin/evaluations/summary", headers=headers)
    assert resp.status_code == 403


def test_allowlisted_user_can_access(client, admin_emails):
    admin_emails("boss@example.com")
    headers = _register_login(client, "boss@example.com")
    resp = client.get(f"{API}/admin/evaluations/summary", headers=headers)
    assert resp.status_code == 200
    assert "evaluated" in resp.json()


def test_empty_allowlist_forbids_everyone(client, admin_emails):
    admin_emails("")
    headers = _register_login(client, "anyone@example.com")
    resp = client.get(f"{API}/admin/evaluations/summary", headers=headers)
    assert resp.status_code == 403


def test_allowlist_is_case_insensitive(client, admin_emails):
    admin_emails("Boss@Example.com")
    headers = _register_login(client, "boss@example.com")
    resp = client.get(f"{API}/admin/evaluations", headers=headers)
    assert resp.status_code == 200


def test_admin_me_reports_status(client, admin_emails):
    admin_emails("boss@example.com,other@example.com")
    admin_headers = _register_login(client, "other@example.com")
    non_headers = _register_login(client, "plain@example.com")

    me_admin = client.get(f"{API}/admin/me", headers=admin_headers)
    assert me_admin.status_code == 200
    assert me_admin.json()["is_admin"] is True
    assert me_admin.json()["email"] == "other@example.com"

    me_non = client.get(f"{API}/admin/me", headers=non_headers)
    assert me_non.status_code == 200
    assert me_non.json()["is_admin"] is False


def test_admin_me_requires_auth(client):
    resp = client.get(f"{API}/admin/me")
    assert resp.status_code == 401


def test_pilot_summary_returns_kpi_shape(client, admin_emails):
    admin_emails("pilot@example.com")
    headers = _register_login(client, "pilot@example.com")
    resp = client.get(f"{API}/admin/pilot/summary", headers=headers)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["registered_learners"] == 1
    assert payload["placement_completed"] == {"value": 0, "rate": 0.0}
    assert payload["ai_quality"] == {"value": 0.0, "rate": 0.0}
