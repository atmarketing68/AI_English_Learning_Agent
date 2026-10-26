"""Tests for the notifications inbox + achievement->notification hook."""
import pytest

from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services.gamification import seed_achievements, check_and_award_achievements
from app.services.notification_service import create_notification, notify_streak
from app.models.notification import Notification

API = "/api/v1"


def _register_login(client, email="notif@example.com"):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "N", "display_name": "N", "role": "learner", "age": 14,
        },
    )
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _learner(db_session, email="svc@example.com"):
    user = User(email=email, hashed_password="x", full_name="U")
    db_session.add(user)
    db_session.flush()
    learner = LearnerProfile(user_id=user.id, display_name="L")
    db_session.add(learner)
    db_session.flush()
    return learner


# ── Service-level ─────────────────────────────────────────────────────────────
def test_create_notification(db_session):
    learner = _learner(db_session)
    create_notification(db_session, learner.id, type="system", title="Hi", body="Welcome", icon="👋")
    db_session.commit()
    rows = db_session.query(Notification).filter(Notification.learner_id == learner.id).all()
    assert len(rows) == 1
    assert rows[0].title == "Hi"
    assert rows[0].is_read is False


def test_streak_notification_only_at_milestones(db_session):
    learner = _learner(db_session, "svc2@example.com")
    assert notify_streak(db_session, learner.id, 5) is None    # not a milestone
    assert notify_streak(db_session, learner.id, 7) is not None  # milestone
    db_session.commit()
    assert db_session.query(Notification).filter(Notification.learner_id == learner.id).count() == 1


def test_achievement_award_creates_notifications(db_session):
    seed_achievements(db_session)
    learner = _learner(db_session, "svc3@example.com")
    learner.total_lessons_completed = 1
    learner.placement_completed = "done"
    db_session.flush()

    earned = check_and_award_achievements(learner, db_session)
    assert len(earned) >= 1
    notes = db_session.query(Notification).filter(
        Notification.learner_id == learner.id, Notification.type == "achievement"
    ).all()
    assert len(notes) == len(earned)


# ── API-level ─────────────────────────────────────────────────────────────────
def test_list_and_unread_count(client, db_session):
    headers = _register_login(client, "n1@example.com")
    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "n1@example.com").first()
    create_notification(db_session, learner.id, type="system", title="A", icon="⭐")
    create_notification(db_session, learner.id, type="system", title="B", icon="⭐")
    db_session.commit()

    lst = client.get(f"{API}/notifications", headers=headers)
    assert lst.status_code == 200
    assert len(lst.json()) == 2

    count = client.get(f"{API}/notifications/unread-count", headers=headers)
    assert count.json()["unread"] == 2


def test_mark_read_and_read_all(client, db_session):
    headers = _register_login(client, "n2@example.com")
    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "n2@example.com").first()
    create_notification(db_session, learner.id, type="system", title="A")
    create_notification(db_session, learner.id, type="system", title="B")
    db_session.commit()

    first_id = client.get(f"{API}/notifications", headers=headers).json()[0]["id"]
    read = client.post(f"{API}/notifications/{first_id}/read", headers=headers)
    assert read.status_code == 200
    assert read.json()["is_read"] is True
    assert client.get(f"{API}/notifications/unread-count", headers=headers).json()["unread"] == 1

    client.post(f"{API}/notifications/read-all", headers=headers)
    assert client.get(f"{API}/notifications/unread-count", headers=headers).json()["unread"] == 0


def test_unread_only_filter(client, db_session):
    headers = _register_login(client, "n3@example.com")
    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "n3@example.com").first()
    create_notification(db_session, learner.id, type="system", title="A")
    db_session.commit()
    nid = client.get(f"{API}/notifications", headers=headers).json()[0]["id"]
    client.post(f"{API}/notifications/{nid}/read", headers=headers)

    unread = client.get(f"{API}/notifications", params={"unread_only": True}, headers=headers)
    assert unread.json() == []


def test_cannot_read_others_notification(client, db_session):
    headers_a = _register_login(client, "n4a@example.com")
    _register_login(client, "n4b@example.com")
    learner_b = db_session.query(LearnerProfile).join(User).filter(User.email == "n4b@example.com").first()
    create_notification(db_session, learner_b.id, type="system", title="B's note")
    db_session.commit()
    nid = db_session.query(Notification).filter(Notification.learner_id == learner_b.id).first().id

    # User A tries to mark B's notification read → 404 (not visible)
    resp = client.post(f"{API}/notifications/{nid}/read", headers=headers_a)
    assert resp.status_code == 404
