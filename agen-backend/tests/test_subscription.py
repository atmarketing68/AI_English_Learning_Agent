"""Tests for subscription plans, quota gating, and upgrade/cancel."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.user import User
from app.services import subscription_service as subs

API = "/api/v1"

# Pin the free-tier limit to a small, deterministic value for these tests
# (the production default is intentionally high for the pilot).
TEST_LIMIT = 5


@pytest.fixture(autouse=True)
def _pin_free_limit(monkeypatch):
    monkeypatch.setattr(settings, "FREE_DAILY_LESSON_LIMIT", TEST_LIMIT)


def _learner(db_session, email="sub@example.com"):
    user = User(email=email, hashed_password="x", full_name="U")
    db_session.add(user)
    db_session.flush()
    learner = LearnerProfile(user_id=user.id, display_name="L")
    db_session.add(learner)
    db_session.flush()
    return user, learner


def _add_lessons_today(db_session, learner_id, n):
    for _ in range(n):
        db_session.add(LearningEvent(
            learner_id=learner_id, event_type="lesson_completed", skill="vocabulary",
            recorded_at=datetime.now(timezone.utc),
        ))
    db_session.flush()


# ── Service-level ─────────────────────────────────────────────────────────────
def test_default_plan_is_free(db_session):
    user, _ = _learner(db_session)
    sub = subs.get_or_create_subscription(db_session, user.id)
    assert sub.plan == "free"
    assert subs.is_premium(db_session, user.id) is False


def test_free_quota_counts_down(db_session):
    user, learner = _learner(db_session, "sub2@example.com")
    q0 = subs.check_lesson_quota(db_session, user.id, learner)
    assert q0["remaining"] == TEST_LIMIT
    assert q0["allowed"] is True

    _add_lessons_today(db_session, learner.id, TEST_LIMIT)
    q1 = subs.check_lesson_quota(db_session, user.id, learner)
    assert q1["remaining"] == 0
    assert q1["allowed"] is False


def test_limit_zero_means_unlimited(db_session, monkeypatch):
    monkeypatch.setattr(settings, "FREE_DAILY_LESSON_LIMIT", 0)
    user, learner = _learner(db_session, "sub_unlim@example.com")
    _add_lessons_today(db_session, learner.id, 100)
    q = subs.check_lesson_quota(db_session, user.id, learner)
    assert q["limit"] is None
    assert q["allowed"] is True


def test_premium_is_unlimited(db_session):
    user, learner = _learner(db_session, "sub3@example.com")
    subs.upgrade_to_premium(db_session, user.id)
    _add_lessons_today(db_session, learner.id, 50)
    q = subs.check_lesson_quota(db_session, user.id, learner)
    assert q["is_premium"] is True
    assert q["limit"] is None
    assert q["allowed"] is True


def test_expired_premium_is_not_premium(db_session):
    user, _ = _learner(db_session, "sub4@example.com")
    sub = subs.get_or_create_subscription(db_session, user.id)
    sub.plan = "premium"
    sub.status = "active"
    sub.current_period_end = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    db_session.commit()
    assert subs.is_premium(db_session, user.id) is False


def test_cancel_reverts_to_free(db_session):
    user, _ = _learner(db_session, "sub5@example.com")
    subs.upgrade_to_premium(db_session, user.id)
    assert subs.is_premium(db_session, user.id) is True
    subs.cancel_subscription(db_session, user.id)
    assert subs.is_premium(db_session, user.id) is False


# ── API-level ─────────────────────────────────────────────────────────────────
def _register_login(client, email="subapi@example.com"):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "S", "display_name": "S", "role": "learner", "age": 16,
        },
    )
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_api_default_subscription_and_quota(client):
    headers = _register_login(client, "sa1@example.com")
    sub = client.get(f"{API}/billing/subscription", headers=headers)
    assert sub.status_code == 200
    assert sub.json()["plan"] == "free"
    assert sub.json()["is_premium"] is False

    quota = client.get(f"{API}/billing/quota", headers=headers)
    assert quota.status_code == 200
    assert quota.json()["limit"] == TEST_LIMIT
    assert quota.json()["remaining"] == TEST_LIMIT


def test_api_upgrade_then_cancel(client):
    headers = _register_login(client, "sa2@example.com")
    up = client.post(f"{API}/billing/upgrade", json={"months": 3}, headers=headers)
    assert up.status_code == 200
    assert up.json()["is_premium"] is True
    assert up.json()["current_period_end"] is not None

    cancel = client.post(f"{API}/billing/cancel", headers=headers)
    assert cancel.status_code == 200
    assert cancel.json()["is_premium"] is False
