"""G14 · Phân tích giữ chân, bài kiểm tra lặp hằng tháng, sửa chuỗi trong 24 giờ, biểu đồ Speaking, phụ huynh xem bài kiểm tra lớp."""
from datetime import date, datetime, time, timedelta, timezone

from app.core.config import settings
from app.core.timeutil import LEARNER_TZ, local_today
from app.models.group import GroupTest
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.payment_order import PaymentOrder
from app.models.speaking_exam import SpeakingExamAttempt
from app.models.user import User
from app.services import groups, retention
from app.services.streak_service import STREAK_REPAIR_GEMS, update_streak

API = "/api/v1"


def _auth(client, email, role="learner", age=20, name=None, source=None):
    body = {"email": email, "password": "Strong123", "full_name": name or email.split("@")[0], "display_name": name or email.split("@")[0], "role": role}
    if role == "learner":
        body["age"] = age
    if source is not None:
        body["signup_source"] = source
    r = client.post(f"{API}/auth/register", json=body)
    assert r.status_code in (200, 201), r.text
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _learner(db, email) -> LearnerProfile:
    db.expire_all()
    user = db.query(User).filter(User.email == email).first()
    return db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()


def _at(d: date, hour: int = 10) -> datetime:
    """Naive UTC for `hour` o'clock Vietnam time on day d."""
    return datetime.combine(d, time(hour), tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)


# ── G14.4 Retention ──────────────────────────────────────────────────────────
def test_signup_source_is_cleaned_and_stored(client, db_session):
    _auth(client, "src1@example.com", source=" Facebook Ads!! ")
    r = client.post(f"{API}/auth/guest", json={"signup_source": "zalo"})
    assert r.status_code == 201
    client.post(f"{API}/auth/guest")                       # body is optional
    db_session.expire_all()
    assert db_session.query(User).filter(User.email == "src1@example.com").one().signup_source == "facebookads"
    assert db_session.query(User).filter(User.signup_source == "zalo", User.is_guest.is_(True)).count() == 1


def test_retention_cohorts_funnel_and_sources(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss14@example.com")
    admin = _auth(client, "boss14@example.com")
    learner = _auth(client, "nobody14@example.com")
    assert client.get(f"{API}/admin/retention/summary", headers=learner).status_code == 403

    today = local_today()
    signup = today - timedelta(days=40)
    for i, (src, d1, d7, d30, lessons, paid) in enumerate([
        ("google", True, True, True, 3, True),
        ("google", True, False, False, 1, False),
        (None, False, True, False, 0, False),
    ]):
        email = f"coh{i}@example.com"
        _auth(client, email, source=src)
        lp = _learner(db_session, email)
        user = db_session.query(User).filter(User.id == lp.user_id).one()
        user.created_at = _at(signup)
        lp.total_lessons_completed = lessons
        lp.placement_completed = "done" if lessons else "none"
        for day, hit in ((1, d1), (8, d7), (31, d30)):
            if hit:
                db_session.add(LearningEvent(learner_id=lp.id, event_type="lesson_completed", skill="vocabulary", recorded_at=_at(signup + timedelta(days=day))))
        if paid:
            db_session.add(PaymentOrder(user_id=user.id, provider="vnpay", plan="premium", months=12, amount_vnd=799000, status="paid"))
        db_session.commit()            # _learner() expires the session, so save each learner before the next

    rows = retention.cohorts(db_session, weeks=8, today=today)
    week = signup - timedelta(days=signup.weekday())
    row = next(r for r in rows if r["week_start"] == week.isoformat())
    assert row["signups"] == 3 and row["d1"] == round(2 / 3 * 100, 1) and row["d7"] == round(2 / 3 * 100, 1) and row["d30"] == round(1 / 3 * 100, 1)
    young = rows[0]                       # this week: the windows have not passed yet
    assert young["d30"] is None and young["d30_eligible"] == 0

    f = retention.funnel(db_session, days=60, today=today)
    steps = {s["key"]: s["count"] for s in f["steps"]}
    assert steps["registered"] >= 3 and steps["first_lesson"] >= 2 and steps["paid"] >= 1 and steps["active3"] >= 1

    body = client.get(f"{API}/admin/retention/summary", headers=admin).json()
    google = next(s for s in body["sources"] if s["source"] == "google")
    assert google == {"source": "google", "signups": 2, "activated": 2, "paid": 1, "activation_pct": 100.0, "paid_pct": 50.0}
    assert any(s["source"] == retention.NO_SOURCE for s in body["sources"])
    assert len(body["cohorts"]) == 8 and body["funnel"]["days"] == 30


# ── G14.5 Streak repair ──────────────────────────────────────────────────────
def test_streak_repair_before_studying(client, db_session):
    h = _auth(client, "rep1@example.com")
    lp = _learner(db_session, "rep1@example.com")
    lp.current_streak, lp.longest_streak, lp.streak_freezes, lp.gems = 9, 9, 0, 80
    lp.last_active_at = _at(local_today() - timedelta(days=2))          # missed yesterday only
    db_session.commit()
    streak = client.get(f"{API}/engagement/today", headers=h).json()["streak"]
    assert streak["current"] == 0 and streak["repair"] == {"lost": 9, "restored": 9, "cost": STREAK_REPAIR_GEMS}

    r = client.post(f"{API}/engagement/streak/repair", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["streak"]["current"] == 9 and r.json()["streak"]["repair"] is None
    lp = _learner(db_session, "rep1@example.com")
    assert lp.gems == 80 - STREAK_REPAIR_GEMS
    update_streak(lp, db_session)                    # today's first activity extends the repaired streak
    assert lp.current_streak == 10
    assert client.post(f"{API}/engagement/streak/repair", headers=h).status_code == 400


def test_streak_repair_after_studying_and_limits(client, db_session):
    h = _auth(client, "rep2@example.com")
    lp = _learner(db_session, "rep2@example.com")
    lp.current_streak, lp.streak_freezes, lp.gems = 6, 0, 10
    lp.last_active_at = _at(local_today() - timedelta(days=2))
    update_streak(lp, db_session)                    # studied today first: reset to 1, loss remembered
    db_session.commit()
    assert lp.current_streak == 1 and lp.streak_lost_value == 6
    offer = client.get(f"{API}/engagement/today", headers=h).json()["streak"]["repair"]
    assert offer == {"lost": 6, "restored": 7, "cost": STREAK_REPAIR_GEMS}
    assert "đá quý" in client.post(f"{API}/engagement/streak/repair", headers=h).json()["detail"]   # not enough gems
    lp = _learner(db_session, "rep2@example.com")
    lp.gems = 100
    db_session.commit()
    assert client.post(f"{API}/engagement/streak/repair", headers=h).json()["streak"]["current"] == 7

    # two missed days, or a tiny streak: nothing to repair
    h3 = _auth(client, "rep3@example.com")
    lp3 = _learner(db_session, "rep3@example.com")
    lp3.current_streak, lp3.streak_freezes, lp3.gems = 12, 0, 500
    lp3.last_active_at = _at(local_today() - timedelta(days=3))
    db_session.commit()
    assert client.get(f"{API}/engagement/today", headers=h3).json()["streak"]["repair"] is None


# ── G14.5 Monthly class tests, speaking chart, parent view, score sheet ──────
def _class(client, teacher_email, members):
    teacher = _auth(client, teacher_email, role="teacher", name="Cô Hạnh")
    g = client.post(f"{API}/groups", json={"name": "Lớp 14", "kind": "class"}, headers=teacher).json()
    heads = []
    for email in members:
        h = _auth(client, email, name=email.split("@")[0].capitalize())
        client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=h)
        heads.append(h)
    return teacher, g, heads


def test_add_months_clamps():
    assert groups.add_months(date(2026, 1, 31)) == date(2026, 2, 28)
    assert groups.add_months(date(2026, 12, 15)) == date(2027, 1, 15)
    assert groups.add_months(date(2028, 1, 31)) == date(2028, 2, 29)


def test_monthly_test_rolls_to_next_unused_exam(client, db_session):
    teacher, g, _ = _class(client, "co14@example.com", ["m14@example.com"])
    today = local_today()
    t = client.post(f"{API}/groups/{g['id']}/tests", json={"kind": "mock", "exam_id": "ielts-reading-1", "due_on": (today + timedelta(days=2)).isoformat(),
                                                            "repeat": "monthly"}, headers=teacher).json()
    assert t["repeat"] == "monthly"
    assert groups.roll_recurring_tests(db_session, today)["created"] == 0          # still open
    after = today + timedelta(days=3)
    assert groups.roll_recurring_tests(db_session, after)["created"] == 1
    db_session.expire_all()
    old = db_session.query(GroupTest).filter(GroupTest.id == t["id"]).one()
    nxt = db_session.query(GroupTest).filter(GroupTest.id == old.next_test_id).one()
    assert nxt.repeat == "monthly" and nxt.due_on == groups.add_months(old.due_on) and nxt.opens_on == groups.add_months(old.opens_on)
    assert nxt.exam_id == "ielts-reading-1"          # only one IELTS Reading paper in the bank → reused
    assert groups.roll_recurring_tests(db_session, after)["created"] == 0           # idempotent

    # turning repeat off stops the chain
    r = client.post(f"{API}/groups/{g['id']}/tests/{nxt.id}/repeat", json={"repeat": None}, headers=teacher)
    assert r.status_code == 200 and r.json()["repeat"] is None
    assert groups.roll_recurring_tests(db_session, groups.add_months(after, 1) + timedelta(days=5))["created"] == 0


def test_speaking_history_parent_class_tests_and_sheet(client, db_session):
    teacher, g, (kid,) = _class(client, "co14b@example.com", ["kid14@example.com"])
    lid = _learner(db_session, "kid14@example.com").id
    t0 = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=9)
    for i, band in enumerate((5.0, 5.5, 6.0)):
        db_session.add(SpeakingExamAttempt(learner_id=lid, exam_id="ielts-speaking-1", exam="ielts", status="finished", estimate=band,
                                           criteria={"fluency_coherence": band, "lexical_resource": band - 0.5, "grammatical_range": band, "pronunciation": band + 0.5},
                                           responses=[], created_at=t0 + timedelta(days=3 * i), fallback=1 if i == 0 else 0))
    db_session.add(SpeakingExamAttempt(learner_id=lid, exam_id="toeic-speaking-1", exam="toeic", status="finished", estimate=120, criteria={}, responses=[]))
    db_session.commit()
    detail = client.get(f"{API}/groups/{g['id']}/members/{lid}", headers=teacher).json()
    hist = detail["speaking_history"]
    assert [h["overall"] for h in hist] == [5.0, 5.5, 6.0] and hist[0]["source"] == "estimate"
    assert hist[2]["criteria"] == {"fluency": 6.0, "lexical": 5.5, "grammar": 6.0, "pronunciation": 6.5}

    today = local_today()
    test = client.post(f"{API}/groups/{g['id']}/tests", json={"kind": "mock", "exam_id": "toeic-reading-1", "due_on": (today + timedelta(days=4)).isoformat()},
                       headers=teacher).json()
    client.post(f"{API}/exams/toeic-reading-1/submit", json={"answers": {}, "seconds": 300, "group_test_id": test["id"]}, headers=kid)

    mom = _auth(client, "mom14@example.com", role="parent")
    code = client.get(f"{API}/learner/me", headers=kid).json()["invite_code"]
    client.post(f"{API}/parent/link-child", json={"invite_code": code}, headers=mom)
    report = client.get(f"{API}/parent/child/{lid}/report", headers=mom).json()
    ct = report["class_tests"]
    assert len(ct) == 1 and ct[0]["group_name"] == "Lớp 14" and ct[0]["mine"]["done"] is True

    sheet = client.get(f"{API}/groups/{g['id']}/tests/{test['id']}/sheet", headers=teacher).json()
    assert sheet["group_name"] == "Lớp 14" and sheet["teacher_name"] == "Cô Hạnh" and sheet["results"][0]["done"] is True
    assert client.get(f"{API}/groups/{g['id']}/tests/{test['id']}/sheet", headers=kid).status_code == 403
