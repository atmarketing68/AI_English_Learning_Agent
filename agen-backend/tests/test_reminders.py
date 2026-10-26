"""Daily reminders: settings, push subscriptions, scheduler run and email opt-out."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest

import app.services.reminders as reminders
from app.core.config import settings
from app.core.timeutil import LEARNER_TZ
from app.models.learner_profile import LearnerProfile
from app.models.notification import Notification
from app.models.push_subscription import PushSubscription
from app.models.review_item import ReviewItem
from app.models.user import User

API = "/api/v1"
# 19:30 in Vietnam
NOW = datetime(2026, 10, 26, 19, 30, tzinfo=LEARNER_TZ)


def _auth(client, email):
    client.post(f"{API}/auth/register", json={
        "email": email, "password": "Strong123", "full_name": "R",
        "display_name": "Lan", "role": "learner",
    })
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Strong123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _learner(db_session, email):
    return (
        db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id)
        .filter(User.email == email).one()
    )


SUB = {"endpoint": "https://fcm.googleapis.com/fcm/send/abc", "keys": {"p256dh": "BPkey", "auth": "authkey"}}


@pytest.fixture()
def channels(monkeypatch):
    """Turn both channels on and capture what would be sent."""
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr(settings, "EMAIL_FROM", "Nhắc học <hi@example.com>")
    monkeypatch.setattr(settings, "APP_URL", "https://app.example.com")
    sent = {"push": [], "email": []}

    def fake_send_push(db, sub, message):
        sent["push"].append((sub.endpoint, message))
        return True

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["email"].append(json)
        return SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr(reminders, "send_push", fake_send_push)
    monkeypatch.setattr(reminders.httpx, "post", fake_post)
    return sent


def test_settings_and_push_subscriptions(client, db_session):
    headers = _auth(client, "rem1@example.com")
    body = client.get(f"{API}/reminders/settings", headers=headers).json()
    assert body["hour"] is None and body["email"] is False and body["push_devices"] == 0
    assert body["push_available"] is False and body["email_available"] is False

    assert client.put(f"{API}/reminders/settings", headers=headers, json={"hour": 25}).status_code == 422
    body = client.put(f"{API}/reminders/settings", headers=headers, json={"hour": 19, "email": True}).json()
    assert body["hour"] == 19 and body["email"] is True

    bad = {**SUB, "endpoint": "http://insecure.example.com"}
    assert client.post(f"{API}/reminders/push-subscriptions", headers=headers, json=bad).status_code == 422
    assert client.post(f"{API}/reminders/push-subscriptions", headers=headers, json=SUB).json()["push_devices"] == 1
    # Re-subscribing the same browser updates the row instead of duplicating it.
    assert client.post(f"{API}/reminders/push-subscriptions", headers=headers, json=SUB).json()["push_devices"] == 1
    body = client.request("DELETE", f"{API}/reminders/push-subscriptions", headers=headers,
                          json={"endpoint": SUB["endpoint"]}).json()
    assert body["push_devices"] == 0


def test_cron_requires_the_shared_secret(client, monkeypatch):
    assert client.post(f"{API}/reminders/cron/run").status_code == 403          # not configured
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "s3cret")
    assert client.post(f"{API}/reminders/cron/run", headers={"X-Cron-Secret": "nope"}).status_code == 403
    res = client.post(f"{API}/reminders/cron/run", headers={"X-Cron-Secret": "s3cret"})
    assert res.status_code == 200 and "reminded" in res.json()


def test_run_reminds_due_learners_once(client, db_session, channels):
    a = "due@example.com"
    a_headers = _auth(client, a)
    client.put(f"{API}/reminders/settings", headers=a_headers, json={"hour": 19, "email": True})
    client.post(f"{API}/reminders/push-subscriptions", headers=a_headers, json=SUB)

    studied = "studied@example.com"
    s_headers = _auth(client, studied)
    client.put(f"{API}/reminders/settings", headers=s_headers, json={"hour": 18})
    learner_s = _learner(db_session, studied)
    learner_s.last_active_at = NOW.replace(hour=10).astimezone(timezone.utc).replace(tzinfo=None)

    morning = "morning@example.com"
    m_headers = _auth(client, morning)
    client.put(f"{API}/reminders/settings", headers=m_headers, json={"hour": 8})
    _auth(client, "off@example.com")                                            # never set a reminder
    db_session.commit()

    stats = reminders.run_due_reminders(db_session, NOW)
    assert stats == {"checked": 2, "reminded": 1, "skipped_studied": 1, "push": 1, "email": 1}
    assert channels["push"][0][0] == SUB["endpoint"]
    mail = channels["email"][0]
    assert mail["to"] == [a]
    assert "https://app.example.com/unsubscribe?token=" in mail["text"]
    learner_a = _learner(db_session, a)
    assert learner_a.last_reminder_on == "2026-10-26"
    assert db_session.query(Notification).filter(Notification.learner_id == learner_a.id, Notification.type == "reminder").count() == 1

    # Same day, next hour: nobody is reminded twice.
    assert reminders.run_due_reminders(db_session, NOW + timedelta(hours=1))["reminded"] == 0
    # 08:00 reminder is outside its window at 19:30; email-only users get no push.
    assert len(channels["push"]) == 1

    # One-click unsubscribe from the email link.
    token = mail["text"].split("token=")[1].split()[0]
    assert client.post(f"{API}/reminders/unsubscribe-email", json={"token": "garbage"}).status_code == 400
    assert client.post(f"{API}/reminders/unsubscribe-email", json={"token": token}).status_code == 200
    db_session.expire_all()
    assert _learner(db_session, a).reminder_email is False


def test_message_prefers_streak_then_due_reviews(client, db_session):
    email = "msg@example.com"
    _auth(client, email)
    learner = _learner(db_session, email)
    assert "Đến giờ học" in reminders.compose_message(db_session, learner, NOW).title

    db_session.add(ReviewItem(learner_id=learner.id, kind="vocab", key="cat", front="cat", back="mèo",
                              due_at=datetime(2026, 1, 1)))
    db_session.commit()
    msg = reminders.compose_message(db_session, learner, NOW)
    assert msg.title.startswith("🧠 1 từ") and msg.url == "/review"

    learner.current_streak = 5
    learner.last_active_at = (NOW - timedelta(days=1)).astimezone(timezone.utc).replace(tzinfo=None)
    msg = reminders.compose_message(db_session, learner, NOW)
    assert "Giữ chuỗi 5 ngày" in msg.title and "1 từ" in msg.body


def test_expired_push_subscription_is_removed(client, db_session, monkeypatch):
    from pywebpush import WebPushException

    email = "gone@example.com"
    headers = _auth(client, email)
    client.post(f"{API}/reminders/push-subscriptions", headers=headers, json=SUB)
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")

    def gone(**kwargs):
        raise WebPushException("Gone", response=SimpleNamespace(status_code=410))

    monkeypatch.setattr("pywebpush.webpush", gone)
    learner = _learner(db_session, email)
    msg = reminders.compose_message(db_session, learner, NOW)
    assert reminders.push_to_learner(db_session, learner, msg) == 0
    db_session.commit()
    assert db_session.query(PushSubscription).count() == 0


def test_test_endpoint_reports_channels(client, db_session, channels):
    headers = _auth(client, "tester@example.com")
    client.put(f"{API}/reminders/settings", headers=headers, json={"hour": 7, "email": True})
    client.post(f"{API}/reminders/push-subscriptions", headers=headers, json=SUB)
    assert client.post(f"{API}/reminders/test", headers=headers).json() == {"push": 1, "email": True}
