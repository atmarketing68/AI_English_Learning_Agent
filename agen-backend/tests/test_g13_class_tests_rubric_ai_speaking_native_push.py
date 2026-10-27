"""G13 · Bài kiểm tra lớp, biểu đồ rubric, đề Speaking do AI sinh, push gốc cho phụ huynh."""
import dataclasses
from datetime import datetime, timedelta, timezone

from app.agents import orchestrator
from app.core.config import settings
from app.core.timeutil import LEARNER_TZ, local_today
from app.models.exam_attempt import ExamAttempt
from app.models.generated_exam import GeneratedSpeakingExam
from app.models.group import GroupTest
from app.models.learner_profile import LearnerProfile
from app.models.notification import Notification
from app.models.user import User
from app.models.writing import WritingSubmission
from app.services import fcm, groups, mock_exams, parent_digest, speaking_exam_generator

API = "/api/v1"


def _auth(client, email, role="learner", age=20, name=None):
    body = {"email": email, "password": "Strong123", "full_name": name or email.split("@")[0], "display_name": name or email.split("@")[0], "role": role}
    if role == "learner":
        body["age"] = age
    r = client.post(f"{API}/auth/register", json=body)
    assert r.status_code in (200, 201), r.text
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _learner_id(db, email):
    db.expire_all()
    user = db.query(User).filter(User.email == email).first()
    return db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first().id


def _swap_agent(monkeypatch, name, handler):
    patched = dict(orchestrator.AGENT_SPECS)
    patched[name] = dataclasses.replace(orchestrator.AGENT_SPECS[name], handler=handler)
    monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)


def _right_answers(exam_id):
    exam = mock_exams.get_exam(exam_id)
    out = {}
    for s in exam["sections"]:
        for q in s["questions"]:
            out[q["id"]] = q["answer"][0] if isinstance(q["answer"], list) else q["answer"]
    return out


def _class(client, teacher_email, members):
    teacher = _auth(client, teacher_email, role="teacher", name="Cô Mai")
    g = client.post(f"{API}/groups", json={"name": "Lớp 13", "kind": "class"}, headers=teacher).json()
    heads = []
    for email in members:
        h = _auth(client, email, name=email.split("@")[0].capitalize())
        client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=h)
        heads.append(h)
    return teacher, g, heads


# ── G13.1 Bài kiểm tra lớp ───────────────────────────────────────────────────
def test_class_mock_test_flow(client, db_session):
    teacher, g, (an, binh) = _class(client, "co13@example.com", ["an13@example.com", "binh13@example.com"])
    today = local_today()
    cat = client.get(f"{API}/groups/tests/catalogue", headers=teacher).json()
    assert {"mock", "speaking"} <= {c["kind"] for c in cat} and any(c["id"] == "ielts-reading-1" for c in cat)
    assert client.get(f"{API}/groups/tests/catalogue", headers=an).status_code == 403

    base = f"{API}/groups/{g['id']}/tests"
    assert client.post(base, json={"kind": "mock", "exam_id": "nope", "due_on": today.isoformat()}, headers=teacher).status_code == 400
    assert client.post(base, json={"kind": "mock", "exam_id": "ielts-reading-1", "due_on": (today - timedelta(days=1)).isoformat()}, headers=teacher).status_code == 400
    assert client.post(base, json={"kind": "mock", "exam_id": "ielts-reading-1", "due_on": (today + timedelta(days=90)).isoformat()}, headers=teacher).status_code == 400
    r = client.post(base, json={"kind": "mock", "exam_id": "ielts-reading-1", "due_on": (today + timedelta(days=3)).isoformat(), "note": "Kiểm tra tháng 10"}, headers=teacher)
    assert r.status_code == 200, r.text
    test = r.json()
    assert test["status"] == "open" and test["title"].startswith("IELTS") and test["member_count"] == 2 and test["done_count"] == 0
    an_id = _learner_id(db_session, "an13@example.com")
    assert db_session.query(Notification).filter(Notification.learner_id == an_id, Notification.type == "group_test").count() == 1

    # An already used the free daily attempt — the class test still opens and is counted
    first = client.post(f"{API}/exams/toeic-reading-1/submit", json={"answers": {}}, headers=an)
    assert first.status_code == 200
    assert client.get(f"{API}/exams/ielts-reading-1", headers=an).status_code == 403
    paper = client.get(f"{API}/exams/ielts-reading-1?test={test['id']}", headers=an)
    assert paper.status_code == 200 and paper.json()["class_test"]["id"] == test["id"]
    sub = client.post(f"{API}/exams/ielts-reading-1/submit", json={"answers": _right_answers("ielts-reading-1"), "seconds": 600, "group_test_id": test["id"]}, headers=an)
    assert sub.status_code == 200, sub.text
    assert sub.json()["class_test"] is True and sub.json()["pct"] == 100
    # a class attempt does not use up the free daily attempt of a learner who has not practised yet
    client.post(f"{API}/exams/ielts-reading-1/submit", json={"answers": {}, "group_test_id": test["id"]}, headers=binh)
    assert client.get(f"{API}/exams", headers=binh).json()["attempts_today"] == 0
    # the counted attempt is the first one; a retake goes through the normal limit
    assert client.get(f"{API}/exams/ielts-reading-1?test={test['id']}", headers=an).status_code == 403

    res = client.get(f"{base}/{test['id']}", headers=teacher).json()
    assert res["done_count"] == 2 and res["results"][0]["display_name"] == "An13" and res["results"][0]["pct"] == 100
    assert res["max_estimate"] >= res["min_estimate"] and res["avg_pct"] == 50.0
    mine = next(t for t in client.get(f"{API}/groups/learner/mine", headers=an).json()["groups"][0]["tests"] if t["id"] == test["id"])
    assert mine["mine"]["done"] is True and mine["mine"]["pct"] == 100
    csv_text = client.get(f"{API}/groups/{g['id']}/report.csv", headers=teacher).text
    assert "Kiểm tra: " in csv_text
    detail = client.get(f"{API}/groups/{g['id']}/members/{an_id}", headers=teacher).json()
    assert detail["tests"][0]["mine"]["done"] is True

    # deleting the test keeps the attempts in the learners' history
    assert client.delete(f"{base}/{test['id']}", headers=teacher).status_code == 204
    db_session.expire_all()
    assert db_session.query(ExamAttempt).filter(ExamAttempt.learner_id == an_id).count() == 2
    assert all(a.group_test_id is None for a in db_session.query(ExamAttempt).all())


def test_closed_or_foreign_tests_do_not_waive_the_limit(client, db_session):
    teacher, g, (an,) = _class(client, "co13b@example.com", ["an13b@example.com"])
    outsider = _auth(client, "out13@example.com")
    today = local_today()
    t = client.post(f"{API}/groups/{g['id']}/tests", json={"kind": "mock", "exam_id": "toeic-listening-1", "opens_on": (today + timedelta(days=2)).isoformat(),
                                                            "due_on": (today + timedelta(days=5)).isoformat()}, headers=teacher).json()
    assert t["status"] == "upcoming"
    client.post(f"{API}/exams/ielts-reading-1/submit", json={"answers": {}}, headers=an)
    client.post(f"{API}/exams/ielts-reading-1/submit", json={"answers": {}}, headers=outsider)
    assert client.get(f"{API}/exams/toeic-listening-1?test={t['id']}", headers=an).status_code == 403          # not open yet
    db_session.query(GroupTest).filter(GroupTest.id == t["id"]).update({"opens_on": today})
    db_session.commit()
    assert client.get(f"{API}/exams/toeic-listening-1?test={t['id']}", headers=an).status_code == 200
    assert client.get(f"{API}/exams/toeic-listening-1?test={t['id']}", headers=outsider).status_code == 403     # not a member
    assert client.get(f"{API}/exams/toeic-reading-1?test={t['id']}", headers=an).status_code == 403              # other exam


def test_class_speaking_test_and_due_reminder(client, db_session, monkeypatch):
    _swap_agent(monkeypatch, "speaking_exam_evaluation", lambda **kw: (_ for _ in ()).throw(RuntimeError("down")))
    teacher, g, (an, binh) = _class(client, "co13c@example.com", ["an13c@example.com", "binh13c@example.com"])
    today = local_today()
    t = client.post(f"{API}/groups/{g['id']}/tests", json={"kind": "speaking", "exam_id": "ielts-speaking-1", "due_on": today.isoformat()}, headers=teacher).json()
    assert t["skill"] == "speaking"
    # a normal attempt today, then the class one is still allowed and counted
    client.post(f"{API}/speaking-exams/toeic-speaking-1/start", headers=an)
    assert client.post(f"{API}/speaking-exams/ielts-speaking-1/start", headers=an).status_code == 403
    st = client.post(f"{API}/speaking-exams/ielts-speaking-1/start?test={t['id']}", headers=an)
    assert st.status_code == 200
    attempt = st.json()["attempt_id"]
    assert client.post(f"{API}/speaking-exams/ielts-speaking-1/start?test={t['id']}", headers=an).json()["attempt_id"] == attempt   # resumed
    client.post(f"{API}/speaking-exams/attempts/{attempt}/answer", json={"task_id": "t1", "transcript": "I live in Hanoi and I love the food there very much"}, headers=an)
    fin = client.post(f"{API}/speaking-exams/attempts/{attempt}/finish", headers=an)
    assert fin.status_code == 200 and fin.json()["fallback"] is True
    res = client.get(f"{API}/groups/{g['id']}/tests/{t['id']}", headers=teacher).json()
    assert res["done_count"] == 1 and res["results"][0]["estimate"] == fin.json()["overall"]

    # due-day reminder: only Bình (not done), once, and not before 8:00
    early = datetime.combine(today, datetime.min.time().replace(hour=6), tzinfo=LEARNER_TZ).astimezone(timezone.utc)
    assert groups.remind_due_tests(db_session, early)["notified"] == 0
    nine = datetime.combine(today, datetime.min.time().replace(hour=9), tzinfo=LEARNER_TZ).astimezone(timezone.utc)
    stats = groups.remind_due_tests(db_session, nine)
    assert stats == {"tests": 1, "notified": 1, "push": 0}
    assert groups.remind_due_tests(db_session, nine + timedelta(hours=2))["notified"] == 0
    binh_id = _learner_id(db_session, "binh13c@example.com")
    assert db_session.query(Notification).filter(Notification.learner_id == binh_id, Notification.title.like("Hôm nay hết hạn%")).count() == 1


# ── G13.2 Rubric history ─────────────────────────────────────────────────────
def test_rubric_history_for_teacher(client, db_session):
    teacher, g, (ha,) = _class(client, "co13d@example.com", ["ha13@example.com"])
    lid = _learner_id(db_session, "ha13@example.com")
    t0 = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=10)
    ai = {"exam_band": {"exam": "ielts", "overall": 5.5, "criteria": {"task_response": 5.5, "coherence_cohesion": 5.5, "lexical_resource": 5, "grammatical_range": 6}}}
    rows = [
        WritingSubmission(learner_id=lid, prompt_title="Cities", prompt_text="…", genre="ielts_task2", level="B1", user_text="x", word_count=1,
                          overall_score=55, grade="C", evaluation=ai, created_at=t0),
        WritingSubmission(learner_id=lid, prompt_title="Chart", prompt_text="…", genre="ielts_task1", level="B1", user_text="x", word_count=1,
                          overall_score=60, grade="B", evaluation={}, teacher_rubric={"task": 6, "coherence": 6, "lexical": 6.5, "grammar": 6},
                          teacher_band=6.0, created_at=t0 + timedelta(days=3)),
        WritingSubmission(learner_id=lid, prompt_title="Story", prompt_text="…", genre="story", level="B1", user_text="x", word_count=1,
                          overall_score=70, grade="B", evaluation={}, created_at=t0 + timedelta(days=4)),
        WritingSubmission(learner_id=lid, prompt_title="No band", prompt_text="…", genre="ielts_task2", level="B1", user_text="x", word_count=1,
                          overall_score=40, grade="D", evaluation={}, created_at=t0 + timedelta(days=5)),
    ]
    db_session.add_all(rows)
    db_session.commit()
    hist = client.get(f"{API}/groups/{g['id']}/members/{lid}", headers=teacher).json()["rubric_history"]
    assert [(h["title"], h["source"], h["overall"]) for h in hist] == [("Cities", "ai", 5.5), ("Chart", "teacher", 6.0)]
    assert hist[0]["criteria"] == {"task": 5.5, "coherence": 5.5, "lexical": 5.0, "grammar": 6.0}
    assert hist[1]["criteria"]["lexical"] == 6.5


# ── G13.3 AI Speaking exams ──────────────────────────────────────────────────
IELTS_GEN = {
    "title": "IELTS Speaking · Food", "description": "Đề về ẩm thực.",
    "tasks": [
        {"part": "Part 1", "kind": "question", "prompt": "Do you like cooking?", "tip_vi": "Trả lời 2–3 câu."},
        {"part": "Part 1", "kind": "question", "prompt": "What did you eat for breakfast today?"},
        {"part": "Part 2", "kind": "cue_card", "prompt": "Describe a memorable meal.", "cue": ["where it was", "who you were with", "what you ate", "and explain why it was memorable"]},
        {"part": "Part 3", "kind": "question", "prompt": "Why do people eat out more nowadays?"},
    ],
}


def test_normalize_speaking_exam():
    exam = speaking_exam_generator.normalize_exam("ielts", IELTS_GEN)
    assert [t["id"] for t in exam["tasks"]] == ["t1", "t2", "t3", "t4"]
    card = exam["tasks"][2]
    assert card["kind"] == "cue_card" and card["prep_seconds"] == 60 and card["answer_seconds"] == 120 and len(card["cue"]) == 4
    assert exam["tasks"][1]["tip_vi"] and exam["minutes"] == 12
    bad = dict(IELTS_GEN, tasks=IELTS_GEN["tasks"][:2])
    try:
        speaking_exam_generator.normalize_exam("ielts", bad)
        raise AssertionError("expected an error")
    except speaking_exam_generator.SpeakingExamGenerationError:
        pass
    toeic = {"title": "TOEIC Speaking · Office", "description": "Công sở.", "tasks": [
        {"part": "Q1", "kind": "read_aloud", "prompt": "Read the text aloud.", "reference": "Welcome to the Riverside Hotel. Breakfast is served from six thirty to ten in the main dining room, and coffee, tea, and fresh juice are free for all guests."},
        {"part": "Q5", "kind": "question", "prompt": "How often do you travel for work?"},
        {"part": "Q6", "kind": "question", "prompt": "Where do you usually stay?"},
        {"part": "Q7", "kind": "question", "prompt": "What makes a hotel good for business travellers?"},
        {"part": "Q11", "kind": "opinion", "prompt": "Do you agree that companies should pay for employees' gym memberships? Give reasons or examples to support your opinion."},
    ]}
    t = speaking_exam_generator.normalize_exam("toeic", toeic)
    assert [x["part"] for x in t["tasks"]] == ["Q1 · Read aloud", "Q5 · Respond to questions", "Q6 · Respond to questions", "Q7 · Respond to questions", "Q11 · Express an opinion"]
    assert t["tasks"][3]["answer_seconds"] == 30 and t["tasks"][0]["reference"].startswith("Welcome")


def test_admin_generates_and_approves_speaking_exam(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss13@example.com")
    seen = {}
    _swap_agent(monkeypatch, "speaking_exam_generation", lambda **kw: seen.update(kw) or IELTS_GEN)
    admin = _auth(client, "boss13@example.com")
    learner = _auth(client, "sp13@example.com")
    assert client.post(f"{API}/admin/speaking-exams/generate", json={"exam": "ielts"}, headers=learner).status_code == 403
    r = client.post(f"{API}/admin/speaking-exams/generate", json={"exam": "ielts", "topic": "food", "level": "B2"}, headers=admin)
    assert r.status_code == 200, r.text
    draft = r.json()
    assert draft["status"] == "draft" and draft["tasks"] == 4 and seen["topic"] == "food" and seen["level"] == "B2"
    assert all(e["id"] != draft["public_id"] for e in client.get(f"{API}/speaking-exams", headers=learner).json()["exams"])
    assert client.post(f"{API}/speaking-exams/{draft['public_id']}/start", headers=learner).status_code == 404
    full = client.get(f"{API}/admin/speaking-exams/{draft['id']}", headers=admin).json()
    assert full["exam"]["tasks"][2]["cue"][0] == "where it was"

    assert client.post(f"{API}/admin/speaking-exams/{draft['id']}/status", json={"status": "approved"}, headers=admin).json()["status"] == "approved"
    cat = client.get(f"{API}/speaking-exams", headers=learner).json()["exams"]
    assert any(e["id"] == draft["public_id"] and e["tasks"] == 4 for e in cat)
    st = client.post(f"{API}/speaking-exams/{draft['public_id']}/start", headers=learner)
    assert st.status_code == 200 and st.json()["exam"]["title"] == "IELTS Speaking · Food"
    # teachers can assign it as a class test
    teacher = _auth(client, "co13e@example.com", role="teacher")
    assert any(c["id"] == draft["public_id"] for c in client.get(f"{API}/groups/tests/catalogue", headers=teacher).json())

    # a format the normaliser rejects becomes a 502, nothing is stored
    _swap_agent(monkeypatch, "speaking_exam_generation", lambda **kw: dict(IELTS_GEN, tasks=IELTS_GEN["tasks"][:1] * 4))
    assert client.post(f"{API}/admin/speaking-exams/generate", json={"exam": "ielts"}, headers=admin).status_code == 502
    db_session.expire_all()
    assert db_session.query(GeneratedSpeakingExam).count() == 1
    assert client.delete(f"{API}/admin/speaking-exams/{draft['id']}", headers=admin).status_code == 204


# ── G13.4 Phụ huynh dùng app di động (FCM, không cần web push) ─────────────────
def test_parent_alerts_reach_native_app_without_web_push(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "FIREBASE_SERVICE_ACCOUNT_JSON", '{"project_id": "x"}')
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "")
    sent = []
    monkeypatch.setattr(fcm, "send_to_user", lambda db, user_id, title, body, url, tag: sent.append((user_id, title, url)) or 1)
    mom = _auth(client, "mom13@example.com", role="parent")
    kid = _auth(client, "kid13@example.com", age=9)
    code = client.get(f"{API}/learner/me", headers=kid).json()["invite_code"]
    client.post(f"{API}/parent/link-child", json={"invite_code": code}, headers=mom)
    client.post(f"{API}/notifications/device-tokens", json={"token": "m" * 40, "platform": "ios"}, headers=mom)
    prefs = client.get(f"{API}/parent/settings", headers=mom).json()
    assert prefs["native_push_available"] is True and prefs["native_devices"] == 1 and prefs["push_available"] is False

    lid = _learner_id(db_session, "kid13@example.com")
    lp = db_session.query(LearnerProfile).filter(LearnerProfile.id == lid).first()
    lp.last_active_at = (datetime.now(timezone.utc) - timedelta(days=3)).replace(tzinfo=None)
    db_session.commit()
    noon = datetime.combine(local_today(), datetime.min.time().replace(hour=12), tzinfo=LEARNER_TZ).astimezone(timezone.utc)
    stats = parent_digest.run_parent_digests(db_session, noon)
    assert stats["push_sent"] == 1 and sent and "nghỉ học" in sent[0][1] and sent[0][2] == "/parent"
