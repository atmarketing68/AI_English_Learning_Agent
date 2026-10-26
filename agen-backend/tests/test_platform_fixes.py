"""Regression tests for login, local-day boundaries, rate-limit keys and the mock upgrade gate."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.core.config import settings
from app.core.ratelimit import client_ip
from app.core.timeutil import local_date
from app.models.learner_profile import LearnerProfile
from app.services.streak_service import update_streak

API = "/api/v1"


def _register(client, email, password="Strong123"):
    return client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": password,
            "full_name": "T", "display_name": "T", "role": "learner", "age": 20,
        },
    )


# ── Login ─────────────────────────────────────────────────────────────────────
def test_login_ignores_email_case_and_whitespace(client):
    assert _register(client, "Case.User@Example.com").status_code in (200, 201)
    res = client.post(
        f"{API}/auth/login",
        data={"username": "  CASE.user@example.COM ", "password": "Strong123"},
    )
    assert res.status_code == 200
    assert res.json()["access_token"]


# ── Local day boundaries ──────────────────────────────────────────────────────
def test_local_date_rolls_over_at_vietnam_midnight():
    late_evening = datetime(2026, 10, 26, 16, 30)   # 23:30 in Vietnam
    early_morning = datetime(2026, 10, 26, 23, 0)   # 06:00 next day in Vietnam
    assert late_evening.date() == early_morning.date()          # same UTC day
    assert (local_date(early_morning) - local_date(late_evening)).days == 1


def test_streak_counts_vietnam_morning_as_next_day():
    learner = LearnerProfile(user_id="u", display_name="L", current_streak=3, longest_streak=3)
    # Last studied at 23:30 yesterday (Vietnam time), i.e. well under 24h ago.
    now_local_day = local_date(datetime.now(timezone.utc))
    yesterday_2330_vn = datetime.combine(
        now_local_day - timedelta(days=1), datetime.min.time()
    ) + timedelta(hours=23, minutes=30) - timedelta(hours=7)   # as naive UTC
    learner.last_active_at = yesterday_2330_vn

    update_streak(learner, db=None)

    assert learner.current_streak == 4


# ── Rate-limit key ────────────────────────────────────────────────────────────
def _request(headers, host="10.0.0.1"):
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))


def test_client_ip_uses_proxy_appended_address(monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    req = _request({"x-forwarded-for": "6.6.6.6, 203.0.113.9"})
    assert client_ip(req) == "203.0.113.9"


def test_client_ip_falls_back_to_socket_address(monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", False)
    req = _request({"x-forwarded-for": "203.0.113.9"})
    assert client_ip(req) == "10.0.0.1"


# ── Mock Premium upgrade gate ─────────────────────────────────────────────────
def _auth_headers(client, email):
    _register(client, email)
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_demo_upgrade_can_be_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_UPGRADE", False)
    headers = _auth_headers(client, "nodemo@example.com")
    res = client.post(f"{API}/billing/upgrade", json={"months": 1}, headers=headers)
    assert res.status_code == 403


def test_demo_upgrade_defaults_off_in_production(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_UPGRADE", None)
    monkeypatch.setattr(settings, "APP_ENV", "production")
    assert settings.demo_upgrade_enabled is False
    monkeypatch.setattr(settings, "APP_ENV", "development")
    assert settings.demo_upgrade_enabled is True
