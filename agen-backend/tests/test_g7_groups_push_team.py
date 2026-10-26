"""G7 · Nhóm học (lớp / doanh nghiệp), bài tập, gói theo ghế, push phụ huynh, bảng xếp hạng bạn bè."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.core.timeutil import LEARNER_TZ, local_today
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.parent import ParentChildLink, ParentProfile
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.services import parent_digest, reminders

API = "/api/v1"


def _auth(client, email, role="learner", age=20, name=None):
    body = {"email": email, "password": "Strong123", "full_name": name or email.split("@")[0], "display_name": name or email.split("@")[0], "role": role}
    if role == "learner":
        body["age"] = age
    r = client.post(f"{API}/auth/register", json=body)
    assert r.status_code in (200, 201), r.text
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _learner(db, email):
    return db.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id).filter(User.email == email).one()


def _xp(db, learner_id, xp, skill="vocabulary"):
    when = datetime.combine(local_today(), datetime.min.time().replace(hour=12), tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)
    db.add(LearningEvent(learner_id=learner_id, event_type="lesson_completed", skill=skill, xp_earned=xp, recorded_at=when))
    db.commit()


# ── Nhóm học ─────────────────────────────────────────────────────────────────
def test_teacher_creates_class_learners_join_and_see_assignments(client, db_session):
    teacher = _auth(client, "teacher@example.com", role="teacher", name="Cô Lan")
    an = _auth(client, "an7@example.com", name="An")
    binh = _auth(client, "binh7@example.com", name="Bình")
    assert client.get(f"{API}/groups/mine", headers=an).status_code == 403          # learners are not owners

    g = client.post(f"{API}/groups", json={"name": "Lớp 7A", "kind": "class"}, headers=teacher)
    assert g.status_code == 200, g.text
    code = g.json()["code"]
    assert code.startswith("LOP-") and g.json()["member_count"] == 0
    assert client.post(f"{API}/groups", json={"name": "Phòng Kinh doanh", "kind": "company"}, headers=teacher).json()["code"].startswith("CTY-")

    assert client.post(f"{API}/groups/join", json={"code": "LOP-NOPE"}, headers=an).status_code == 400
    assert client.post(f"{API}/groups/join", json={"code": code.lower()}, headers=an).status_code == 200
    assert client.post(f"{API}/groups/join", json={"code": code}, headers=an).status_code == 400         # twice
    assert client.post(f"{API}/groups/join", json={"code": code}, headers=binh).status_code == 200

    home = client.get(f"{API}/groups/mine", headers=teacher).json()
    assert home["members_total"] == 2 and home["plan"] == "free" and home["team_prices"][0]["amount_vnd"] == 79000

    a = client.post(f"{API}/groups/{g.json()['id']}/assignments", json={"title": "Tuần 1: Food", "skill": "vocabulary", "topic": "food and drinks", "due_on": str(local_today() + timedelta(days=3))}, headers=teacher)
    assert a.status_code == 200, a.text
    assert client.post(f"{API}/groups/{g.json()['id']}/assignments", json={"title": "x", "skill": "speaking", "topic": "y"}, headers=teacher).status_code == 422

    mine = client.get(f"{API}/groups/learner/mine", headers=an).json()
    assert mine["groups"][0]["group"]["name"] == "Lớp 7A" and mine["groups"][0]["owner_name"] == "Cô Lan"
    task = mine["groups"][0]["assignments"][0]
    assert task["title"] == "Tuần 1: Food" and task["done"] is False and task["started"] is False and task["overdue"] is False

    # Starting returns the spec; finishing a lesson of that skill marks it done.
    start = client.post(f"{API}/groups/assignments/{task['id']}/start", headers=an)
    assert start.status_code == 200 and start.json()["skill"] == "vocabulary" and start.json()["topic"] == "food and drinks"
    assert client.post(f"{API}/groups/assignments/{task['id']}/start", headers=binh).status_code == 200
    stranger = _auth(client, "stranger7@example.com")
    assert client.post(f"{API}/groups/assignments/{task['id']}/start", headers=stranger).status_code == 400

    from app.services.groups import mark_done_on_finish
    an_lp = _learner(db_session, "an7@example.com")
    assert mark_done_on_finish(db_session, an_lp.id, "grammar", "lesson-x", 90) == 0      # wrong skill → nothing
    assert mark_done_on_finish(db_session, an_lp.id, "vocabulary", "lesson-1", 88.4) == 1
    assert mark_done_on_finish(db_session, an_lp.id, "vocabulary", "lesson-2", 50) == 0     # already done
    db_session.commit()
    _xp(db_session, an_lp.id, 40)

    task = client.get(f"{API}/groups/learner/mine", headers=an).json()["groups"][0]["assignments"][0]
    assert task["done"] is True and task["score"] == 88
    detail = client.get(f"{API}/groups/{g.json()['id']}", headers=teacher).json()
    assert detail["assignments"][0]["done_count"] == 1 and detail["assignments"][0]["member_count"] == 2
    assert [m["display_name"] for m in detail["members"]] == ["An", "Bình"]           # An has weekly XP
    assert detail["members"][0]["weekly_xp"] == 40 and detail["members"][0]["assignments_done"] == 1
    assert detail["covered_seats"] == 0

    # Owner removes a member; another teacher cannot see this group.
    other = _auth(client, "teacher2@example.com", role="teacher")
    assert client.get(f"{API}/groups/{g.json()['id']}", headers=other).status_code == 404
    binh_lp = _learner(db_session, "binh7@example.com")
    assert client.delete(f"{API}/groups/{g.json()['id']}/members/{binh_lp.id}", headers=teacher).status_code == 204
    assert client.get(f"{API}/groups/learner/mine", headers=binh).json()["groups"] == []
    assert client.delete(f"{API}/groups/{g.json()['id']}/assignments/{task['id']}", headers=teacher).status_code == 204


def test_lesson_finish_marks_started_assignment(client, db_session, monkeypatch):
    """End-to-end through /lessons: the finish endpoint calls the group hook."""
    import dataclasses
    from app.agents import orchestrator
    lesson_payload = {
        "title": "Food", "summary": "s", "skill": "vocabulary", "topic": "food", "level": "A2",
        "vocabulary": [{"word": "bread", "translation": "bánh mì", "definition": "d", "example": "e"}],
        "exercises": [{"type": "multiple_choice", "order": 0, "content": {"question": "bread?", "options": {"A": "bánh mì", "B": "x", "C": "y", "D": "z"}, "correct_answer": "A", "explanation": "e"}}],
    }
    patched = dict(orchestrator.AGENT_SPECS)
    patched["lesson"] = dataclasses.replace(orchestrator.AGENT_SPECS["lesson"], handler=lambda **kw: lesson_payload)
    monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)
    teacher = _auth(client, "t3@example.com", role="teacher")
    kid = _auth(client, "kid7@example.com", age=12)
    g = client.post(f"{API}/groups", json={"name": "Lớp 6B"}, headers=teacher).json()
    client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=kid)
    a = client.post(f"{API}/groups/{g['id']}/assignments", json={"title": "Food", "skill": "vocabulary", "topic": "food"}, headers=teacher).json()
    spec = client.post(f"{API}/groups/assignments/{a['id']}/start", headers=kid).json()
    lesson = client.post(f"{API}/lessons/generate", json={"skill": spec["skill"], "topic": spec["topic"]}, headers=kid).json()
    ex = lesson["exercises"][0]
    client.post(f"{API}/lessons/{lesson['id']}/submit-exercise", json={"exercise_id": ex["id"], "answer": "A"}, headers=kid)
    assert client.post(f"{API}/lessons/{lesson['id']}/finish", headers=kid).status_code == 200
    task = client.get(f"{API}/groups/learner/mine", headers=kid).json()["groups"][0]["assignments"][0]
    assert task["done"] is True and task["score"] == 100


# ── Gói theo ghế ─────────────────────────────────────────────────────────────
def test_team_plan_covers_first_seats_members(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_UPGRADE", True)
    monkeypatch.setattr(settings, "VNPAY_TMN_CODE", "")
    monkeypatch.setattr(settings, "MOMO_PARTNER_CODE", "")
    hr = _auth(client, "hr@example.com", role="teacher", name="HR")
    staff = [_auth(client, f"s{i}@example.com", age=30, name=f"S{i}") for i in range(6)]
    opts = client.get(f"{API}/billing/options", headers=hr).json()
    assert opts["can_buy_team"] is True and opts["team_min_seats"] == 5 and opts["can_buy_family"] is False
    assert client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "premium"}, headers=hr).status_code == 400
    assert client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "team", "seats": 2}, headers=hr).status_code == 400    # below minimum
    assert client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "team", "seats": 5}, headers=staff[0]).status_code == 400
    res = client.post(f"{API}/billing/upgrade", json={"months": 12, "plan": "team", "seats": 5}, headers=hr)
    assert res.status_code == 200, res.text
    assert res.json()["plan"] == "team" and res.json()["seats"] == 5

    g = client.post(f"{API}/groups", json={"name": "Công ty ABC", "kind": "company"}, headers=hr).json()
    for s in staff:
        client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=s)
    sources = [client.get(f"{API}/billing/subscription", headers=s).json()["premium_source"] for s in staff]
    assert sources == ["team"] * 5 + [None]                       # 6th member is over the seat count
    assert client.get(f"{API}/billing/quota", headers=staff[0]).json()["limit"] is None
    detail = client.get(f"{API}/groups/{g['id']}", headers=hr).json()
    assert detail["covered_seats"] == 5 and sum(1 for m in detail["members"] if m["premium_source"] == "team") == 5
    assert client.get(f"{API}/groups/mine", headers=hr).json()["plan"] == "team"


def test_team_checkout_price_is_per_seat(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "VNPAY_TMN_CODE", "TMN123")
    monkeypatch.setattr(settings, "VNPAY_HASH_SECRET", "vnpaysecret")
    monkeypatch.setattr(settings, "API_PUBLIC_URL", "https://api.example.com")
    hr = _auth(client, "hr2@example.com", role="teacher")
    res = client.post(f"{API}/billing/checkout", json={"months": 1, "provider": "vnpay", "plan": "team", "seats": 10}, headers=hr)
    assert res.status_code == 200, res.text
    order = client.get(f"{API}/billing/orders/{res.json()['order_id']}", headers=hr).json()
    assert order["plan"] == "team" and order["seats"] == 10 and order["amount_vnd"] == 790_000
    assert client.post(f"{API}/billing/checkout", json={"months": 1, "provider": "vnpay", "plan": "team", "seats": 1}, headers=hr).status_code == 503   # PaymentError → 503


# ── Push phụ huynh ───────────────────────────────────────────────────────────
@pytest.fixture()
def push_env(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "", raising=False)
    sent = []
    def fake_send(db, sub, message, tag="daily-reminder"):
        sent.append((sub.user_id or sub.learner_id, message.title, tag))
        return True
    monkeypatch.setattr(reminders, "send_push", fake_send)
    monkeypatch.setattr(parent_digest, "push_to_user", lambda db, user_id, message, tag="parent-alert": reminders.push_to_user(db, user_id, message, tag))
    return sent


def test_parent_push_subscription_and_streak_alert(client, db_session, push_env):
    mom = _auth(client, "mom7@example.com", role="parent", name="Mẹ")
    kid = _auth(client, "kid8@example.com", age=10, name="Tí")
    code = client.get(f"{API}/learner/me", headers=kid).json()["invite_code"]
    client.post(f"{API}/parent/link-child", json={"invite_code": code}, headers=mom)

    s = client.get(f"{API}/parent/settings", headers=mom).json()
    assert s["push_available"] is True and s["push_public_key"] == "pub" and s["push_devices"] == 0
    assert client.post(f"{API}/parent/push-subscriptions", json={"endpoint": "http://x", "keys": {"p256dh": "a", "auth": "b"}}, headers=mom).status_code == 422
    s = client.post(f"{API}/parent/push-subscriptions", json={"endpoint": "https://push.example/abc", "keys": {"p256dh": "a", "auth": "b"}}, headers=mom).json()
    assert s["push_devices"] == 1 and s["push_alerts"] is True
    sub = db_session.query(PushSubscription).one()
    mom_user = db_session.query(User).filter(User.email == "mom7@example.com").one()
    assert sub.user_id == mom_user.id and sub.learner_id is None

    # Child has a 3-day streak but has not studied today → push at 19:30 local, once.
    lp = _learner(db_session, "kid8@example.com")
    lp.current_streak = 3
    lp.last_active_at = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    lp.last_activity_date = (local_today() - timedelta(days=1)).isoformat() if hasattr(lp, "last_activity_date") else None
    db_session.commit()
    evening = datetime.combine(local_today(), datetime.min.time().replace(hour=19, minute=30), tzinfo=LEARNER_TZ).astimezone(timezone.utc)
    stats = parent_digest.run_parent_digests(db_session, evening)
    assert stats["push_enabled"] is True
    titles = [t for _, t, _ in push_env]
    assert any("Chuỗi" in t for t in titles), titles
    again = parent_digest.run_parent_digests(db_session, evening + timedelta(minutes=30))
    assert again["push_sent"] == 0                                              # once per day
    morning = datetime.combine(local_today(), datetime.min.time().replace(hour=9), tzinfo=LEARNER_TZ).astimezone(timezone.utc)
    assert "Chuỗi" not in " ".join(t for _, t, _ in push_env[1:]) and parent_digest.run_parent_digests(db_session, morning)["push_sent"] == 0

    # Turning push off stops alerts; unsubscribing removes the device.
    assert client.put(f"{API}/parent/settings", json={"push_alerts": False}, headers=mom).json()["push_alerts"] is False
    assert client.put(f"{API}/parent/settings", json={"weekly_report_email": True}, headers=mom).json()["push_alerts"] is False
    s = client.request("DELETE", f"{API}/parent/push-subscriptions", json={"endpoint": "https://push.example/abc"}, headers=mom).json()
    assert s["push_devices"] == 0


def test_inactivity_alert_goes_by_push_without_email(client, db_session, push_env):
    dad = _auth(client, "dad7@example.com", role="parent")
    kid = _auth(client, "kid9@example.com", age=9)
    code = client.get(f"{API}/learner/me", headers=kid).json()["invite_code"]
    client.post(f"{API}/parent/link-child", json={"invite_code": code}, headers=dad)
    client.post(f"{API}/parent/push-subscriptions", json={"endpoint": "https://push.example/dad", "keys": {"p256dh": "a", "auth": "b"}}, headers=dad)
    lp = _learner(db_session, "kid9@example.com")
    lp.last_active_at = (datetime.now(timezone.utc) - timedelta(days=3)).replace(tzinfo=None)
    db_session.commit()
    noon = datetime.combine(local_today(), datetime.min.time().replace(hour=12), tzinfo=LEARNER_TZ).astimezone(timezone.utc)
    stats = parent_digest.run_parent_digests(db_session, noon)
    assert stats["email_enabled"] is False and stats["push_sent"] == 1 and stats["alerts_sent"] == 0
    assert any("nghỉ học" in t for _, t, _ in push_env)
    link = db_session.query(ParentChildLink).one()
    assert link.last_inactivity_alert_on == local_today().isoformat()
    assert parent_digest.run_parent_digests(db_session, noon)["push_sent"] == 0       # one per quiet spell


# ── Bảng xếp hạng bạn bè ─────────────────────────────────────────────────────
def test_friends_leaderboard_ranks_me_and_friends(client, db_session):
    an = _auth(client, "la@example.com", name="An")
    binh = _auth(client, "lb@example.com", name="Bình")
    chi = _auth(client, "lc@example.com", name="Chi")
    code = client.get(f"{API}/learner/me", headers=an).json()["invite_code"]
    client.post(f"{API}/friends", json={"code": code}, headers=binh)
    client.post(f"{API}/friends", json={"code": code}, headers=chi)
    _xp(db_session, _learner(db_session, "lb@example.com").id, 120)
    _xp(db_session, _learner(db_session, "la@example.com").id, 80)
    board = client.get(f"{API}/friends/leaderboard", headers=an).json()
    assert [(r["rank"], r["display_name"], r["weekly_xp"], r["is_me"]) for r in board] == [(1, "Bình", 120, False), (2, "An", 80, True), (3, "Chi", 0, False)]
    # Chi only sees An (not Bình, who is An's friend but not Chi's).
    assert [r["display_name"] for r in client.get(f"{API}/friends/leaderboard", headers=chi).json()] == ["An", "Chi"]
