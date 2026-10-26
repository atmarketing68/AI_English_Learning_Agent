"""G9 · Thi thử Speaking, đề AI sinh + duyệt, kế hoạch ôn thi, kênh Zalo OA."""
import dataclasses
import hashlib
import json
from datetime import timedelta

import pytest

from app.agents import orchestrator
from app.core.config import settings
from app.core.timeutil import local_today
from app.models.app_config import AppConfig
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import mock_exams, reminders, speaking_exams as sbank, zalo
from app.services.exam_generator import ExamGenerationError, normalize_paper

API = "/api/v1"


def _auth(client, email, role="learner", age=20, name=None):
    body = {"email": email, "password": "Strong123", "full_name": name or email.split("@")[0], "display_name": name or email.split("@")[0], "role": role}
    if role == "learner":
        body["age"] = age
    r = client.post(f"{API}/auth/register", json=body)
    assert r.status_code in (200, 201), r.text
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def demo(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_UPGRADE", True)
    monkeypatch.setattr(settings, "VNPAY_TMN_CODE", "")
    monkeypatch.setattr(settings, "MOMO_PARTNER_CODE", "")


def _swap_agent(monkeypatch, name, handler):
    patched = dict(orchestrator.AGENT_SPECS)
    patched[name] = dataclasses.replace(orchestrator.AGENT_SPECS[name], handler=handler)
    monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)


# ── G9.1 Speaking mock test ──────────────────────────────────────────────────
EVAL = {
    "exam": "ielts", "overall": 6.5,
    "criteria": {"fluency_coherence": 6.5, "lexical_resource": 6.0, "grammatical_range": 6.5, "pronunciation": 6.5},
    "task_feedback": [{"task_id": "t1", "comment_vi": "Trả lời đủ ý, mạch lạc.", "corrections": [{"original": "I living in Hanoi", "corrected": "I live in Hanoi"}]},
                      {"task_id": "t4", "comment_vi": "Dùng đủ 4 gợi ý.", "corrections": []}],
    "strengths": ["Tự tin"], "improvements": ["Dùng thêm từ nối"], "next_band_tips": ["Luyện Part 2 với đồng hồ"],
}


def test_speaking_exam_bank_and_heuristic():
    assert [e["id"] for e in sbank.list_exams()] == ["ielts-speaking-1", "toeic-speaking-1"]
    for e in sbank.list_exams():
        ids = [t["id"] for t in e["tasks"]]
        assert len(ids) == len(set(ids)) and all(t["answer_seconds"] > 0 for t in e["tasks"])
    toeic = sbank.get_exam("toeic-speaking-1")
    assert sum(1 for t in toeic["tasks"] if t["kind"] == "read_aloud" and t["reference"]) == 2
    ielts = sbank.get_exam("ielts-speaking-1")
    empty = sbank.heuristic_estimate(ielts, [])
    assert empty["overall"] == 3.0 and empty["exam"] == "ielts"
    full = sbank.heuristic_estimate(ielts, [{"task_id": t["id"], "transcript": "word " * (t["answer_seconds"] * 2)} for t in ielts["tasks"]])
    assert full["overall"] == 7.0 and len(full["task_feedback"]) == 6
    assert sbank.heuristic_estimate(toeic, [])["overall"] == 40.0
    assert sbank.xp_for([{"transcript": "one two three four five six"}, {"transcript": "hi"}]) == 6


def test_speaking_exam_flow_limit_and_fallback(client, db_session, monkeypatch, demo):
    _swap_agent(monkeypatch, "speaking_exam_evaluation", lambda **kw: EVAL)
    headers = _auth(client, "sp9@example.com")
    cat = client.get(f"{API}/speaking-exams", headers=headers).json()
    assert len(cat["exams"]) == 2 and cat["can_start"] is True

    start = client.post(f"{API}/speaking-exams/ielts-speaking-1/start", headers=headers)
    assert start.status_code == 200, start.text
    aid = start.json()["attempt_id"]
    assert start.json()["exam"]["tasks"][3]["kind"] == "cue_card"
    # restarting the same exam today resumes the open attempt (not a second free attempt)
    assert client.post(f"{API}/speaking-exams/ielts-speaking-1/start", headers=headers).json()["attempt_id"] == aid
    assert client.post(f"{API}/speaking-exams/attempts/{aid}/finish", headers=headers).status_code == 400     # nothing answered yet

    a = client.post(f"{API}/speaking-exams/attempts/{aid}/answer", json={"task_id": "t1", "transcript": "I living in Hanoi and I like the food there", "duration_seconds": 12}, headers=headers)
    assert a.status_code == 200 and a.json()["words"] == 10 and a.json()["answered"] == 1 and a.json()["pronunciation"] is None
    client.post(f"{API}/speaking-exams/attempts/{aid}/answer", json={"task_id": "t4", "transcript": "The skill I learned is cooking " * 5, "duration_seconds": 90}, headers=headers)
    assert client.post(f"{API}/speaking-exams/attempts/{aid}/answer", json={"task_id": "nope", "transcript": "x"}, headers=headers).status_code == 404

    fin = client.post(f"{API}/speaking-exams/attempts/{aid}/finish", headers=headers)
    assert fin.status_code == 200, fin.text
    body = fin.json()
    assert body["overall"] == 6.5 and body["fallback"] is False and body["xp_earned"] == 12 and body["gems_earned"] == sbank.GEMS_GOOD
    t1 = next(t for t in body["tasks"] if t["task_id"] == "t1")
    assert t1["corrections"][0]["corrected"] == "I live in Hanoi" and t1["transcript"].startswith("I living")
    assert next(t for t in body["tasks"] if t["task_id"] == "t2")["comment_vi"] == "Chưa trả lời phần này."
    assert client.post(f"{API}/speaking-exams/attempts/{aid}/finish", headers=headers).json()["overall"] == 6.5       # idempotent
    assert client.get(f"{API}/speaking-exams/attempts/{aid}", headers=headers).json()["criteria"]["pronunciation"] == 6.5
    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "sp9@example.com").one()
    assert learner.total_xp == 12 and learner.speaking_score > 0

    # free: one attempt a day; premium unlimited
    assert client.post(f"{API}/speaking-exams/toeic-speaking-1/start", headers=headers).status_code == 403
    assert client.post(f"{API}/billing/upgrade", json={"months": 1}, headers=headers).status_code == 200
    s2 = client.post(f"{API}/speaking-exams/toeic-speaking-1/start", headers=headers)
    assert s2.status_code == 200
    aid2 = s2.json()["attempt_id"]
    ref = sbank.get_exam("toeic-speaking-1")["tasks"][0]["reference"]
    a = client.post(f"{API}/speaking-exams/attempts/{aid2}/answer", json={"task_id": "t1", "transcript": ref, "duration_seconds": 20}, headers=headers).json()
    assert a["pronunciation"] is not None and a["pronunciation"] > 80      # read-aloud scored against the reference
    _swap_agent(monkeypatch, "speaking_exam_evaluation", lambda **kw: (_ for _ in ()).throw(RuntimeError("no LLM")))
    fin2 = client.post(f"{API}/speaking-exams/attempts/{aid2}/finish", headers=headers).json()
    assert fin2["fallback"] is True and 40 <= fin2["overall"] <= 200 and fin2["exam"] == "toeic"
    hist = client.get(f"{API}/speaking-exams/history", headers=headers).json()
    assert len(hist) == 2 and hist[0]["status"] == "finished"


# ── G9.2 AI-generated exams ──────────────────────────────────────────────────
PAPER = {
    "title": "IELTS Reading · City parks", "description": "Đề đọc về công viên.", "minutes": 12,
    "sections": [{
        "title": "Passage · City parks", "instructions": "Read and answer.",
        "passage": "Parks matter. " * 60,
        "questions": (
            [{"type": "tfng", "prompt": f"Statement {i}", "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": i % 3, "explanation_vi": "Xem đoạn 1."} for i in range(5)]
            + [{"type": "gap", "prompt": "Parks ______.", "answer": ["matter"], "explanation_vi": "Câu đầu."} for _ in range(2)]
            + [{"type": "mc", "prompt": "Main idea?", "options": ["a", "b", "c"], "answer": 1, "explanation_vi": "Đoạn 1."} for _ in range(2)]
        ),
    }],
}


def test_normalize_paper_rejects_bad_answers():
    good = normalize_paper("ielts", "reading", PAPER)
    assert [q["id"] for q in good["sections"][0]["questions"]][:3] == ["q1", "q2", "q3"] and good["sections"][0]["id"] == "s1"
    assert good["sections"][0]["questions"][0]["options"] == ["TRUE", "FALSE", "NOT GIVEN"]
    bad = json.loads(json.dumps(PAPER))
    bad["sections"][0]["questions"][7]["answer"] = 5
    with pytest.raises(ExamGenerationError):
        normalize_paper("ielts", "reading", bad)
    short = json.loads(json.dumps(PAPER))
    short["sections"][0]["questions"] = short["sections"][0]["questions"][:3]
    with pytest.raises(ExamGenerationError):
        normalize_paper("ielts", "reading", short)
    listening = json.loads(json.dumps(PAPER))
    listening["sections"][0].pop("passage")
    with pytest.raises(ExamGenerationError):                      # listening needs audio
        normalize_paper("ielts", "listening", listening)


def test_admin_generates_reviews_and_learners_take_generated_exam(client, db_session, monkeypatch, demo):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss9@example.com")
    _swap_agent(monkeypatch, "exam_generation", lambda **kw: PAPER)
    admin = _auth(client, "boss9@example.com")
    learner = _auth(client, "gen9@example.com")
    assert client.post(f"{API}/admin/exams/generate", json={"exam": "ielts", "skill": "reading"}, headers=learner).status_code == 403

    g = client.post(f"{API}/admin/exams/generate", json={"exam": "ielts", "skill": "reading", "topic": "city parks"}, headers=admin)
    assert g.status_code == 200, g.text
    row = g.json()
    assert row["status"] == "draft" and row["questions"] == 9 and row["public_id"].startswith("gen-")
    assert len(client.get(f"{API}/exams", headers=learner).json()["exams"]) == 4                 # drafts are invisible
    assert client.get(f"{API}/exams/{row['public_id']}", headers=learner).status_code == 404

    full = client.get(f"{API}/admin/exams/{row['id']}", headers=admin).json()
    assert full["paper"]["sections"][0]["questions"][0]["answer"] == 0 and full["meta"]["title"].startswith("IELTS Reading")
    assert client.post(f"{API}/admin/exams/{row['id']}/status", json={"status": "approved"}, headers=admin).json()["status"] == "approved"
    cat = client.get(f"{API}/exams", headers=learner).json()["exams"]
    assert len(cat) == 5 and cat[-1]["id"] == row["public_id"] and cat[-1]["questions"] == 9
    paper = client.get(f"{API}/exams/{row['public_id']}", headers=learner).json()
    assert "answer" not in paper["sections"][0]["questions"][0]
    sub = client.post(f"{API}/exams/{row['public_id']}/submit", json={"answers": {"q1": 0, "q2": 1, "q3": 2, "q6": "Matter"}}, headers=learner)
    assert sub.status_code == 200 and sub.json()["correct"] == 4
    assert client.get(f"{API}/exams/history", headers=learner).json()[0]["title"] == "IELTS Reading · City parks"
    assert client.get(f"{API}/admin/exams?status=approved", headers=admin).json()[0]["id"] == row["id"]
    client.post(f"{API}/admin/exams/{row['id']}/status", json={"status": "rejected"}, headers=admin)
    assert len(client.get(f"{API}/exams", headers=learner).json()["exams"]) == 4
    assert client.request("DELETE", f"{API}/admin/exams/{row['id']}", headers=admin).status_code == 204

    _swap_agent(monkeypatch, "exam_generation", lambda **kw: (_ for _ in ()).throw(RuntimeError("no LLM")))
    assert client.post(f"{API}/admin/exams/generate", json={"exam": "toeic", "skill": "listening"}, headers=admin).status_code == 502
    assert mock_exams.get_exam("gen-nope", db_session) is None


# ── G9.3 Study plan ──────────────────────────────────────────────────────────
def test_study_plan_targets_progress_and_status(client, db_session, monkeypatch, demo):
    headers = _auth(client, "plan9@example.com")
    assert client.get(f"{API}/study-plan", headers=headers).json()["configured"] is False
    soon = (local_today() + timedelta(days=60)).isoformat()
    assert client.put(f"{API}/study-plan", json={"exam": "ielts", "target_score": 6.3, "exam_date": soon}, headers=headers).status_code == 422
    assert client.put(f"{API}/study-plan", json={"exam": "ielts", "target_score": 6.5, "exam_date": local_today().isoformat()}, headers=headers).status_code == 422
    plan = client.put(f"{API}/study-plan", json={"exam": "ielts", "target_score": 6.5, "exam_date": soon}, headers=headers).json()
    assert plan["configured"] and plan["status"] == "no_data" and plan["weeks_left"] == 9 and len(plan["weeks"]) == 9
    assert plan["weeks"][0]["is_current"] and plan["weeks"][-1]["mock_tests"] == 2 and plan["current_overall"] is None
    assert "Chưa đo" in " ".join(plan["advice_vi"])

    # a reading mock test gives a current estimate; lessons this week move the status
    exam = mock_exams.get_exam("ielts-reading-1")
    answers = {q["id"]: q["answer"] if q["type"] != "gap" else q["answer"][0] for s in exam["sections"] for q in s["questions"]}
    client.post(f"{API}/exams/ielts-reading-1/submit", json={"answers": answers}, headers=headers)
    plan = client.get(f"{API}/study-plan", headers=headers).json()
    assert plan["current"]["reading"] == 9.0 and plan["current_overall"] == 9.0 and plan["gap"] == -2.5
    assert plan["this_week"]["mock_tests"] == 1 and plan["status"] in ("on_track", "behind", "ahead")
    assert plan["weeks"][0]["focus"][0] in ("listening", "writing", "speaking")       # unknown skills first

    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "plan9@example.com").one()
    assert learner.exam_target == "ielts" and learner.learning_goal == "luyen_thi"
    assert client.put(f"{API}/study-plan", json={"exam": "toeic", "target_score": 733, "exam_date": soon}, headers=headers).status_code == 422
    toeic = client.put(f"{API}/study-plan", json={"exam": "toeic", "target_score": 750, "exam_date": soon}, headers=headers).json()
    assert toeic["exam"] == "toeic" and toeic["current_overall"] is None
    assert client.request("DELETE", f"{API}/study-plan", headers=headers).json()["configured"] is False


# ── G9.4 Zalo OA ─────────────────────────────────────────────────────────────
class _Resp:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


def test_zalo_link_by_webhook_and_reminder_channel(client, db_session, monkeypatch):
    headers = _auth(client, "zalo9@example.com")
    parent = _auth(client, "pzalo9@example.com", role="parent")
    s = client.get(f"{API}/reminders/settings", headers=headers).json()
    assert s["zalo_available"] is False and s["zalo_link_code"] is None
    assert client.post(f"{API}/zalo/webhook", json={"event_name": "user_send_text"}).json()["ok"] is False

    monkeypatch.setattr(settings, "ZALO_APP_ID", "123")
    monkeypatch.setattr(settings, "ZALO_APP_SECRET", "app-secret")
    monkeypatch.setattr(settings, "ZALO_OA_ID", "4567")
    monkeypatch.setattr(settings, "ZALO_OA_REFRESH_TOKEN", "refresh-1")
    monkeypatch.setattr(settings, "ZALO_OA_SECRET_KEY", "oa-secret")
    sent = []

    def fake_post(url, **kw):
        if url == zalo.OAUTH_URL:
            assert kw["data"]["refresh_token"] in ("refresh-1", "refresh-2") and kw["headers"]["secret_key"] == "app-secret"
            return _Resp({"access_token": "acc-" + kw["data"]["refresh_token"], "refresh_token": "refresh-2", "expires_in": 90000})
        if url == zalo.MESSAGE_URL:
            sent.append((kw["json"]["recipient"]["user_id"], kw["json"]["message"]["text"], kw["headers"]["access_token"]))
            return _Resp({"error": 0, "message": "Success"})
        raise AssertionError(url)
    monkeypatch.setattr(zalo.httpx, "post", fake_post)

    s = client.get(f"{API}/reminders/settings", headers=headers).json()
    assert s["zalo_available"] and s["zalo_oa_link"] == "https://zalo.me/4567" and s["zalo_link_code"].startswith("ZL-") and s["zalo_linked"] is False
    ps = client.get(f"{API}/parent/settings", headers=parent).json()
    assert ps["zalo_link_code"].startswith("ZL-") and ps["zalo_link_code"] != s["zalo_link_code"]

    def post_event(event, sign=True):
        body = json.dumps(event)
        ts = "1700000000"
        mac = hashlib.sha256(("123" + body + ts + "oa-secret").encode()).hexdigest()
        h = {"Content-Type": "application/json", "X-ZEvent-Timestamp": ts, "X-ZEvent-Signature": f"mac={mac}" if sign else "mac=bad"}
        return client.post(f"{API}/zalo/webhook", content=body, headers=h)

    assert post_event({"event_name": "user_send_text", "sender": {"id": "z-1"}, "message": {"text": "hello"}}, sign=False).status_code == 403
    assert post_event({"event_name": "follow", "sender": {"id": "z-1"}}).json()["actions"] == ["welcome"]
    r = post_event({"event_name": "user_send_text", "sender": {"id": "z-1"}, "message": {"text": f" {s['zalo_link_code'].lower()} "}})
    assert r.json()["actions"] == ["linked"]
    assert client.get(f"{API}/reminders/settings", headers=headers).json()["zalo_linked"] is True
    assert sent[-1][0] == "z-1" and "Đã kết nối" in sent[-1][1] and sent[-1][2] == "acc-refresh-1"
    assert db_session.query(AppConfig).filter(AppConfig.key == zalo.KEY_REFRESH).one().value == "refresh-2"       # rotated token persisted

    # parent links with the learner's invite code? No — parents use their own ZL code; a learner's AGEN code links the learner.
    assert post_event({"event_name": "user_send_text", "sender": {"id": "z-2"}, "message": {"text": ps["zalo_link_code"]}}).json()["actions"] == ["linked"]
    assert client.get(f"{API}/parent/settings", headers=parent).json()["zalo_linked"] is True
    assert post_event({"event_name": "user_send_text", "sender": {"id": "z-3"}, "message": {"text": "gibberish"}}).json()["actions"] == ["help"]

    # reminder goes out over Zalo as well
    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "zalo9@example.com").one()
    user = db_session.query(User).filter(User.email == "zalo9@example.com").one()
    before = len(sent)
    from datetime import datetime, timezone
    out = reminders.remind(db_session, learner, user, datetime.now(timezone.utc))
    assert out["zalo"] == 1 and sent[-1][0] == "z-1" and "/dashboard" in sent[-1][1] and len(sent) == before + 1

    # "TAT" unlinks; unlink endpoint too
    assert post_event({"event_name": "user_send_text", "sender": {"id": "z-1"}, "message": {"text": "tat"}}).json()["actions"] == ["unlinked"]
    assert client.get(f"{API}/reminders/settings", headers=headers).json()["zalo_linked"] is False
    assert client.post(f"{API}/zalo/unlink", headers=parent).json()["linked"] is False
    db_session.expire_all()
    assert reminders.remind(db_session, learner, user, datetime.now(timezone.utc))["zalo"] == 0
