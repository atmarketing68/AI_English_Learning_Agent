"""Tests for the email verification flow (request token → verify → is_verified)."""
import pytest

API = "/api/v1"


def _register_login(client, email="verify@example.com"):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "V", "display_name": "V", "role": "learner", "age": 20,
        },
    )
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_new_user_is_unverified(client):
    headers = _register_login(client, "u1@example.com")
    me = client.get(f"{API}/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["is_verified"] is False


def test_request_returns_dev_token_outside_production(client):
    headers = _register_login(client, "u2@example.com")
    resp = client.post(f"{API}/auth/request-verification", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["dev_token"]  # present in non-prod


def test_full_verification_flow(client):
    headers = _register_login(client, "u3@example.com")
    token = client.post(f"{API}/auth/request-verification", headers=headers).json()["dev_token"]

    verify = client.post(f"{API}/auth/verify-email", json={"token": token})
    assert verify.status_code == 200
    assert verify.json()["is_verified"] is True

    # /me now reflects verified
    me = client.get(f"{API}/auth/me", headers=headers)
    assert me.json()["is_verified"] is True


def test_token_is_single_use(client):
    headers = _register_login(client, "u4@example.com")
    token = client.post(f"{API}/auth/request-verification", headers=headers).json()["dev_token"]
    client.post(f"{API}/auth/verify-email", json={"token": token})
    # Reusing the same token fails.
    second = client.post(f"{API}/auth/verify-email", json={"token": token})
    assert second.status_code == 400


def test_invalid_token_rejected(client):
    resp = client.post(f"{API}/auth/verify-email", json={"token": "definitely-not-a-real-token"})
    assert resp.status_code == 400


def test_requesting_new_token_invalidates_old(client):
    headers = _register_login(client, "u5@example.com")
    first = client.post(f"{API}/auth/request-verification", headers=headers).json()["dev_token"]
    second = client.post(f"{API}/auth/request-verification", headers=headers).json()["dev_token"]
    assert first != second
    # Old token no longer works.
    assert client.post(f"{API}/auth/verify-email", json={"token": first}).status_code == 400
    # New token works.
    assert client.post(f"{API}/auth/verify-email", json={"token": second}).status_code == 200


def test_already_verified_short_circuits(client):
    headers = _register_login(client, "u6@example.com")
    token = client.post(f"{API}/auth/request-verification", headers=headers).json()["dev_token"]
    client.post(f"{API}/auth/verify-email", json={"token": token})
    # Requesting again when already verified returns no dev_token.
    again = client.post(f"{API}/auth/request-verification", headers=headers)
    assert again.status_code == 200
    assert again.json()["dev_token"] is None
