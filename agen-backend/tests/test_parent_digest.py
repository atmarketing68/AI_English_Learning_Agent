"""G3 · Phụ huynh chủ động: weekly report e-mail + 2-day inactivity alert, parent settings."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import app.services.reminders as reminders
from app.core.config import settings
from app.core.timeutil import LEARNER_TZ
from app.models.learner_profile import LearnerProfile
from app.models.parent import ParentChildLink, ParentProfile
from app.models.user import User
from app.services.parent_digest import run_parent_digests

API = "/api/v1"
SUNDAY_EVENING = datetime(2026, 11, 1, 19, 0, tzinfo=LEARNER_TZ)      # Sunday 19:00 in Vietnam
TUESDAY_NOON = datetime(2026, 10, 27, 12, 0, tzinfo=LEARNER_TZ)


def _register(client, email, role):
    client.post(f"{API}/auth/register", json={"email": email, "password": "Strong123", "full_name": "N", "display_name": "Bé An" if role == "learner" else "Mẹ An", "role": role, "age": 10})
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def email(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr(settings, "EMAIL_FROM", "AGEN <hi@example.com>")
    monkeypatch.setattr(settings, "APP_URL", "https://app.example.com")
    sent = []

    def fake_post(url, headers=None, json=None, timeout=None):
        sent.append(json)
        return SimpleNamespace(status_code=200, text="ok")
    monkeypatch.setattr(reminders.httpx, "post", fake_post)
    return sent


def _link(client, db_session, parent_email, child_email):
    child_headers = _register(client, child_email, "learner")
    parent_headers = _register(client, parent_email, "parent")
    code = client.get(f"{API}/learner/me", headers=child_headers).json()["invite_code"]
    assert client.post(f"{API}/parent/link-child", json={"invite_code": code}, headers=parent_headers).status_code == 200
    learner = db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id).filter(User.email == child_email).one()
    parent = db_session.query(ParentProfile).join(User, User.id == ParentProfile.user_id).filter(User.email == parent_email).one()
    return parent_headers, learner, parent


def test_nothing_sent_without_email_channel(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    _link(client, db_session, "p0@example.com", "c0@example.com")
    stats = run_parent_digests(db_session, SUNDAY_EVENING.astimezone(timezone.utc))
    assert stats["email_enabled"] is False and stats["weekly_sent"] == 0


def test_weekly_report_goes_out_sunday_evening_once(client, db_session, email):
    _, learner, parent = _link(client, db_session, "p1@example.com", "c1@example.com")
    learner.last_active_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.commit()

    assert run_parent_digests(db_session, TUESDAY_NOON.astimezone(timezone.utc))["weekly_sent"] == 0
    stats = run_parent_digests(db_session, SUNDAY_EVENING.astimezone(timezone.utc))
    assert stats["weekly_sent"] == 1 and stats["parents"] == 1
    mail = email[0]
    assert mail["to"] == ["p1@example.com"]
    assert "Báo cáo tuần của Bé An" in mail["subject"]
    assert "Bố mẹ nên làm" in mail["html"] and "https://app.example.com/parent" in mail["text"]
    db_session.refresh(parent)
    assert parent.last_weekly_report_week == "2026-W44"
    # Same Sunday, next hourly run: not sent again.
    assert run_parent_digests(db_session, (SUNDAY_EVENING + timedelta(hours=1)).astimezone(timezone.utc))["weekly_sent"] == 0


def test_inactivity_alert_once_per_quiet_spell(client, db_session, email):
    _, learner, parent = _link(client, db_session, "p2@example.com", "c2@example.com")
    link = db_session.query(ParentChildLink).filter(ParentChildLink.parent_id == parent.id).one()
    learner.last_active_at = (TUESDAY_NOON - timedelta(days=2)).astimezone(timezone.utc).replace(tzinfo=None)
    db_session.commit()

    stats = run_parent_digests(db_session, TUESDAY_NOON.astimezone(timezone.utc))
    assert stats["alerts_sent"] == 1
    assert email[0]["subject"] == "Bé An đã nghỉ học 2 ngày"
    db_session.refresh(link)
    assert link.last_inactivity_alert_on == "2026-10-27"
    # Next day, still idle: no second e-mail for the same spell.
    assert run_parent_digests(db_session, (TUESDAY_NOON + timedelta(days=1)).astimezone(timezone.utc))["alerts_sent"] == 0
    # Child studies, then goes quiet again → a new alert.
    learner.last_active_at = (TUESDAY_NOON + timedelta(days=2)).astimezone(timezone.utc).replace(tzinfo=None)
    db_session.commit()
    assert run_parent_digests(db_session, (TUESDAY_NOON + timedelta(days=3)).astimezone(timezone.utc))["alerts_sent"] == 0
    assert run_parent_digests(db_session, (TUESDAY_NOON + timedelta(days=4)).astimezone(timezone.utc))["alerts_sent"] == 1


def test_recently_active_child_triggers_nothing(client, db_session, email):
    _, learner, _ = _link(client, db_session, "p3@example.com", "c3@example.com")
    learner.last_active_at = (TUESDAY_NOON - timedelta(days=1)).astimezone(timezone.utc).replace(tzinfo=None)
    db_session.commit()
    assert run_parent_digests(db_session, TUESDAY_NOON.astimezone(timezone.utc))["alerts_sent"] == 0


def test_parent_can_turn_emails_off(client, db_session, email):
    parent_headers, learner, _ = _link(client, db_session, "p4@example.com", "c4@example.com")
    body = client.get(f"{API}/parent/settings", headers=parent_headers).json()
    assert body["weekly_report_email"] is True and body["email_available"] is True
    assert client.put(f"{API}/parent/settings", json={"weekly_report_email": False}, headers=parent_headers).json()["weekly_report_email"] is False
    learner.last_active_at = (TUESDAY_NOON - timedelta(days=5)).astimezone(timezone.utc).replace(tzinfo=None)
    db_session.commit()
    stats = run_parent_digests(db_session, SUNDAY_EVENING.astimezone(timezone.utc))
    assert stats["weekly_sent"] == 0 and stats["alerts_sent"] == 0


def test_child_report_endpoint_still_works(client, db_session):
    parent_headers, learner, _ = _link(client, db_session, "p5@example.com", "c5@example.com")
    resp = client.get(f"{API}/parent/child/{learner.id}/report", headers=parent_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["what_to_do"] and len(resp.json()["skills"]) == 6


def test_cron_includes_parent_stats(client, monkeypatch):
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "s3cret")
    res = client.post(f"{API}/reminders/cron/run", headers={"X-Cron-Secret": "s3cret"})
    assert res.status_code == 200 and "parents" in res.json()
