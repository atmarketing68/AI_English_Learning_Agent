"""Integration tests for the auth flow and the parent<->child link flow.

Uses the in-memory DB + TestClient fixtures (rate limiting disabled).
"""
import pytest

API = "/api/v1"


# ── Helpers ──────────────────────────────────────────────────────────────────
def _register(client, email, role="learner", **extra):
    body = {
        "email": email,
        "password": "Strong123",
        "full_name": "Test User",
        "display_name": "Tester",
        "role": role,
    }
    body.update(extra)
    return client.post(f"{API}/auth/register", json=body)


def _login(client, email, password="Strong123"):
    return client.post(
        f"{API}/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def _auth_header(client, email, role="learner", **extra):
    _register(client, email, role=role, **extra)
    token = _login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth flow ────────────────────────────────────────────────────────────────
def test_register_learner_returns_role(client):
    resp = _register(client, "learner1@example.com", role="learner", age=12)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "learner1@example.com"
    assert body["role"] == "learner"


def test_register_parent_returns_role(client):
    resp = _register(client, "parent1@example.com", role="parent")
    assert resp.status_code == 201
    assert resp.json()["role"] == "parent"


def test_duplicate_email_rejected(client):
    _register(client, "dup@example.com")
    resp = _register(client, "dup@example.com")
    assert resp.status_code == 400


def test_weak_password_rejected(client):
    resp = client.post(
        f"{API}/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "W",
            "display_name": "W",
            "role": "learner",
        },
    )
    assert resp.status_code == 422


def test_invalid_role_rejected(client):
    resp = client.post(
        f"{API}/auth/register",
        json={
            "email": "badrole@example.com",
            "password": "Strong123",
            "full_name": "B",
            "display_name": "B",
            "role": "admin",
        },
    )
    assert resp.status_code == 422


def test_login_success_and_me(client):
    _register(client, "me@example.com", role="learner")
    login = _login(client, "me@example.com")
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "me@example.com"
    assert me.json()["role"] == "learner"


def test_login_wrong_password_rejected(client):
    _register(client, "wp@example.com")
    resp = _login(client, "wp@example.com", password="WrongPass9")
    assert resp.status_code == 401


def test_me_requires_token(client):
    resp = client.get(f"{API}/auth/me")
    assert resp.status_code == 401


def test_me_rejects_garbage_token(client):
    resp = client.get(f"{API}/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


# ── Parent link flow ─────────────────────────────────────────────────────────
def _learner_invite_code(client, email):
    """Register a learner and fetch their invite code via /learner/me."""
    _register(client, email, role="learner", age=11)
    token = _login(client, email).json()["access_token"]
    resp = client.get(f"{API}/learner/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    return resp.json()["invite_code"]


def test_full_parent_link_flow(client):
    # 1. A learner exists with an invite code
    code = _learner_invite_code(client, "child@example.com")
    assert code and code.startswith("AGEN-")

    # 2. A parent registers and links via the code
    parent_headers = _auth_header(client, "mom@example.com", role="parent")
    link = client.post(
        f"{API}/parent/link-child",
        json={"invite_code": code, "relationship_label": "Mẹ"},
        headers=parent_headers,
    )
    assert link.status_code == 200, link.text
    assert link.json()["relationship_label"] == "Mẹ"
    learner_id = link.json()["learner_id"]

    # 3. Child appears in the parent's children list
    children = client.get(f"{API}/parent/children", headers=parent_headers)
    assert children.status_code == 200
    assert any(c["learner_id"] == learner_id for c in children.json())

    # 4. Parent can fetch a weekly report
    report = client.get(f"{API}/parent/child/{learner_id}/report", headers=parent_headers)
    assert report.status_code == 200
    rep = report.json()
    assert rep["learner_id"] == learner_id
    assert "what_improved" in rep and "what_needs_help" in rep and "what_to_do" in rep
    assert len(rep["skills"]) == 6

    # 5. Unlink removes the child
    unlink = client.delete(f"{API}/parent/children/{learner_id}", headers=parent_headers)
    assert unlink.status_code == 204
    children2 = client.get(f"{API}/parent/children", headers=parent_headers)
    assert all(c["learner_id"] != learner_id for c in children2.json())


def test_link_with_bad_code_returns_404(client):
    parent_headers = _auth_header(client, "dad@example.com", role="parent")
    resp = client.post(
        f"{API}/parent/link-child",
        json={"invite_code": "AGEN-XXXX"},
        headers=parent_headers,
    )
    assert resp.status_code == 404


def test_learner_cannot_use_parent_endpoints(client):
    learner_headers = _auth_header(client, "kid@example.com", role="learner", age=10)
    resp = client.get(f"{API}/parent/children", headers=learner_headers)
    assert resp.status_code == 403


def test_double_link_rejected(client):
    code = _learner_invite_code(client, "child2@example.com")
    parent_headers = _auth_header(client, "mom2@example.com", role="parent")
    first = client.post(
        f"{API}/parent/link-child",
        json={"invite_code": code},
        headers=parent_headers,
    )
    assert first.status_code == 200
    second = client.post(
        f"{API}/parent/link-child",
        json={"invite_code": code},
        headers=parent_headers,
    )
    assert second.status_code == 400
