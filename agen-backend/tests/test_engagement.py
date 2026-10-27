"""Streak freezes, daily quests and the weekly goal."""
from datetime import date, datetime, time, timedelta, timezone

import app.api.engagement as engagement_api
import app.services.engagement as engagement_service
from app.core.timeutil import LEARNER_TZ, local_today
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.user import User
from app.services.streak_service import streak_state, update_streak

API = "/api/v1"


def _local_noon_utc(d: date) -> datetime:
    return datetime.combine(d, time(12), tzinfo=LEARNER_TZ).astimezone(timezone.utc)


def _make_learner(db_session, email="streak@example.com", **kwargs):
    user = User(email=email, hashed_password="x", full_name="U")
    db_session.add(user)
    db_session.flush()
    learner = LearnerProfile(user_id=user.id, display_name="L", **kwargs)
    db_session.add(learner)
    db_session.flush()
    return learner


# ── Streak freeze ────────────────────────────────────────────────────────────
def test_freeze_covers_one_missed_day(db_session):
    learner = _make_learner(db_session, current_streak=6, longest_streak=6,
                            last_active_at=_local_noon_utc(local_today() - timedelta(days=2)))
    assert learner.streak_freezes == 1            # every learner starts with one
    assert streak_state(learner).protected is True
    assert streak_state(learner).current == 6

    info = update_streak(learner, db_session)
    assert info["current_streak"] == 7
    assert info["freezes_used"] == 1
    assert learner.streak_freezes == 0
    assert learner.streak_freeze_used_at is not None


def test_not_enough_freezes_resets_and_keeps_them(db_session):
    learner = _make_learner(db_session, current_streak=6, longest_streak=6, streak_freezes=1,
                            last_active_at=_local_noon_utc(local_today() - timedelta(days=3)))
    assert streak_state(learner).current == 0     # shown as broken before the next activity
    info = update_streak(learner, db_session)
    assert info["current_streak"] == 1
    assert info["freezes_used"] == 0
    assert learner.streak_freezes == 1


def test_two_freezes_cover_two_missed_days(db_session):
    learner = _make_learner(db_session, current_streak=3, streak_freezes=2,
                            last_active_at=_local_noon_utc(local_today() - timedelta(days=3)))
    assert update_streak(learner, db_session)["current_streak"] == 4
    assert learner.streak_freezes == 0


# ── API ──────────────────────────────────────────────────────────────────────
def _auth(client, email):
    client.post(f"{API}/auth/register", json={
        "email": email, "password": "Strong123", "full_name": "Q",
        "display_name": "Q", "role": "learner",
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


def _event(db_session, learner, when, event_type="lesson_completed", **kw):
    db_session.add(LearningEvent(
        learner_id=learner.id, event_type=event_type, skill=kw.pop("skill", "vocabulary"),
        recorded_at=when.astimezone(timezone.utc).replace(tzinfo=None), **kw,
    ))
    db_session.commit()


def test_today_returns_three_quests_and_weekly_goal(client, db_session):
    headers = _auth(client, "quest1@example.com")
    body = client.get(f"{API}/engagement/today", headers=headers).json()
    assert [q["code"] for q in body["quests"]][:2] == ["lesson", "correct"]   # empty notebook → accuracy quest
    assert body["quests"][2]["code"] in ("xp", "perfect", "speaking")
    assert all(q["progress"] == 0 and not q["completed"] for q in body["quests"])
    assert body["weekly"]["goal_days"] == 5 and body["weekly"]["days_done"] == 0
    assert len(body["weekly"]["days"]) == 7
    assert body["streak"] == {
        "current": 0, "longest": 0, "studied_today": False, "freezes": 1, "max_freezes": 2,
        "protected": False, "missed_days": 0, "freeze_used_today": False, "repair": None,
    }
    # Quests are pinned for the day.
    again = client.get(f"{API}/engagement/today", headers=headers).json()
    assert [q["id"] for q in again["quests"]] == [q["id"] for q in body["quests"]]


def test_claim_quest_once_after_completion(client, db_session):
    email = "quest2@example.com"
    headers = _auth(client, email)
    quests = client.get(f"{API}/engagement/today", headers=headers).json()["quests"]
    lesson_q, correct_q = quests[0], quests[1]

    assert client.post(f"{API}/engagement/quests/{lesson_q['id']}/claim", headers=headers).status_code == 400

    learner = _learner(db_session, email)
    _event(db_session, learner, datetime.now(timezone.utc), score=95.0, xp_earned=30)
    state = client.get(f"{API}/engagement/today", headers=headers).json()
    assert state["quests"][0]["completed"] is True
    assert state["quests"][1]["progress"] == 0

    res = client.post(f"{API}/engagement/quests/{lesson_q['id']}/claim", headers=headers)
    assert res.status_code == 200
    assert res.json()["xp_awarded"] == 15
    assert res.json()["state"]["total_xp"] == 15
    assert res.json()["state"]["quests"][0]["claimed"] is True
    assert client.post(f"{API}/engagement/quests/{lesson_q['id']}/claim", headers=headers).status_code == 400
    assert client.post(f"{API}/engagement/quests/{correct_q['id']}/claim", headers=headers).status_code == 400

    other = _auth(client, "quest3@example.com")
    assert client.post(f"{API}/engagement/quests/{lesson_q['id']}/claim", headers=other).status_code == 404


def test_yesterdays_events_do_not_count_today(client, db_session):
    email = "quest4@example.com"
    headers = _auth(client, email)
    learner = _learner(db_session, email)
    _event(db_session, learner, _local_noon_utc(local_today() - timedelta(days=1)), score=100.0)
    quests = client.get(f"{API}/engagement/today", headers=headers).json()["quests"]
    assert quests[0]["progress"] == 0


def test_weekly_goal_claim_gives_xp_and_a_freeze(client, db_session, monkeypatch):
    wednesday = date(2026, 10, 21)
    monkeypatch.setattr(engagement_service, "local_today", lambda: wednesday)
    monkeypatch.setattr(engagement_api, "local_today", lambda: wednesday)
    email = "weekly@example.com"
    headers = _auth(client, email)

    assert client.put(f"{API}/engagement/weekly-goal", headers=headers, json={"days": 4}).status_code == 422
    body = client.put(f"{API}/engagement/weekly-goal", headers=headers, json={"days": 3}).json()
    assert body["weekly"]["goal_days"] == 3

    learner = _learner(db_session, email)
    _event(db_session, learner, _local_noon_utc(date(2026, 10, 18)), "review_answered")   # last Sunday: other week
    _event(db_session, learner, _local_noon_utc(date(2026, 10, 19)), "review_answered")
    _event(db_session, learner, _local_noon_utc(date(2026, 10, 20)), "pronunciation_practice", skill="speaking")
    assert client.post(f"{API}/engagement/weekly/claim", headers=headers).status_code == 400

    _event(db_session, learner, _local_noon_utc(wednesday), "exercise_answered", correct=True)
    weekly = client.get(f"{API}/engagement/today", headers=headers).json()["weekly"]
    assert weekly["days_done"] == 3 and weekly["completed"] is True
    assert [d["done"] for d in weekly["days"]] == [True, True, True, False, False, False, False]
    assert [d["is_future"] for d in weekly["days"]][3:] == [True] * 4

    res = client.post(f"{API}/engagement/weekly/claim", headers=headers).json()
    assert res["xp_awarded"] == 50 and res["freeze_awarded"] is True
    assert res["state"]["streak"]["freezes"] == 2
    assert res["state"]["weekly"]["claimed"] is True
    assert client.post(f"{API}/engagement/weekly/claim", headers=headers).status_code == 400


def test_freeze_cap_on_weekly_reward(client, db_session, monkeypatch):
    wednesday = date(2026, 10, 21)
    monkeypatch.setattr(engagement_service, "local_today", lambda: wednesday)
    email = "weekly2@example.com"
    headers = _auth(client, email)
    client.put(f"{API}/engagement/weekly-goal", headers=headers, json={"days": 3})
    learner = _learner(db_session, email)
    learner.streak_freezes = 2
    db_session.commit()
    for d in (19, 20, 21):
        _event(db_session, learner, _local_noon_utc(date(2026, 10, d)), "review_answered")
    res = client.post(f"{API}/engagement/weekly/claim", headers=headers).json()
    assert res["freeze_awarded"] is False
    assert res["state"]["streak"]["freezes"] == 2


def test_profile_reports_broken_streak_as_zero(client, db_session):
    email = "broken@example.com"
    headers = _auth(client, email)
    learner = _learner(db_session, email)
    learner.current_streak = 9
    learner.streak_freezes = 0
    learner.last_active_at = _local_noon_utc(local_today() - timedelta(days=4)).replace(tzinfo=None)
    db_session.commit()
    assert client.get(f"{API}/learner/me", headers=headers).json()["current_streak"] == 0
