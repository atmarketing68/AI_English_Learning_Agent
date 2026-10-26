"""G8 · Thi thử IELTS/TOEIC, hỏi Bo, báo cáo nhóm CSV, hoá đơn VAT, kênh FCM."""
import dataclasses
import json

import pytest

from app.agents import orchestrator
from app.core.config import settings
from app.models.device_token import DeviceToken
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import fcm, mock_exams as bank, reminders

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


# ── Thi thử ──────────────────────────────────────────────────────────────────
def test_exam_bank_grading_and_estimates():
    assert [e["id"] for e in bank.list_exams()] == ["ielts-listening-1", "ielts-reading-1", "toeic-listening-1", "toeic-reading-1"]
    for e in bank.list_exams():
        ids = [q["id"] for s in e["sections"] for q in s["questions"]]
        assert len(ids) == len(set(ids)) and bank.question_count(e) >= 10
        for s in e["sections"]:
            for q in s["questions"]:
                assert q["type"] in ("mc", "gap", "tfng") and q["explanation_vi"]
                if q["type"] != "gap":
                    assert 0 <= q["answer"] < len(q["options"])
    exam = bank.get_exam("ielts-listening-1")
    public = bank.public_exam(exam)
    assert all("answer" not in q for s in public["sections"] for q in s["questions"])
    perfect = {q["id"]: (q["answer"][0] if q["type"] == "gap" else q["answer"]) for s in exam["sections"] for q in s["questions"]}
    res = bank.grade(exam, perfect)
    assert res["correct"] == res["total"] == 10 and res["estimate"] == 9.0
    # gap answers are normalised (case, spaces, punctuation); mc answers must be the index
    res = bank.grade(exam, {"q1": "  mitchell. ", "q3": "thursday", "q6": "0", "q7": 2})
    by_id = {d["id"]: d for d in res["details"]}
    assert by_id["q1"]["correct"] and by_id["q3"]["correct"] and by_id["q6"]["correct"] and not by_id["q7"]["correct"]
    assert by_id["q7"]["given"] == "a study room with 40 desks" and by_id["q7"]["expected"] == "a café and a meeting room"
    assert bank.estimate_score(bank.get_exam("toeic-reading-1"), 100) == 495 and bank.estimate_score(bank.get_exam("toeic-reading-1"), 0) == 5
    assert bank.estimate_score(bank.get_exam("ielts-reading-1"), 50) == 5.5     # 20/40 → 5.5


def test_take_exam_free_limit_and_history(client, db_session, demo):
    headers = _auth(client, "exam1@example.com")
    cat = client.get(f"{API}/exams", headers=headers).json()
    assert len(cat["exams"]) == 4 and cat["can_start"] is True and cat["attempts_today"] == 0 and cat["is_premium"] is False
    test = client.get(f"{API}/exams/toeic-reading-1", headers=headers)
    assert test.status_code == 200 and "answer" not in test.json()["sections"][0]["questions"][0]
    assert client.get(f"{API}/exams/nope", headers=headers).status_code == 404

    exam = bank.get_exam("toeic-reading-1")
    answers = {q["id"]: q["answer"] for s in exam["sections"] for q in s["questions"]}
    answers["q1"] = 0                                             # one wrong
    r = client.post(f"{API}/exams/toeic-reading-1/submit", json={"answers": answers, "seconds": 600}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["correct"] == 12 and body["total"] == 13 and body["xp_earned"] == 36 and body["gems_earned"] == bank.GEMS_GOOD_SCORE
    assert body["estimate"] > 400 and len(body["details"]) == 13 and body["sections"][0]["correct"] == 5
    wrong = next(d for d in body["details"] if d["id"] == "q1")
    assert wrong["correct"] is False and wrong["expected"] == "will present" and "tương lai" in wrong["explanation_vi"]

    # Free: one test a day
    cat = client.get(f"{API}/exams", headers=headers).json()
    assert cat["attempts_today"] == 1 and cat["can_start"] is False
    assert client.get(f"{API}/exams/ielts-reading-1", headers=headers).status_code == 403
    assert client.post(f"{API}/exams/ielts-reading-1/submit", json={"answers": {}}, headers=headers).status_code == 403
    hist = client.get(f"{API}/exams/history", headers=headers).json()
    assert len(hist) == 1 and hist[0]["title"].startswith("TOEIC Reading")
    best = next(e for e in cat["exams"] if e["id"] == "toeic-reading-1")
    assert best["attempts"] == 1 and best["best_pct"] == body["pct"]

    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "exam1@example.com").one()
    assert learner.total_xp == 36 and learner.gems == bank.GEMS_GOOD_SCORE and learner.reading_score > 0

    # Premium: unlimited
    assert client.post(f"{API}/billing/upgrade", json={"months": 1}, headers=headers).status_code == 200
    assert client.get(f"{API}/exams/ielts-reading-1", headers=headers).status_code == 200
    empty = client.post(f"{API}/exams/ielts-reading-1/submit", json={"answers": {}}, headers=headers).json()
    assert empty["correct"] == 0 and empty["xp_earned"] == 0 and empty["gems_earned"] == 0 and empty["estimate"] == 2.0


# ── Hỏi Bo ───────────────────────────────────────────────────────────────────
ANSWER = {
    "answer_vi": "Dùng hiện tại hoàn thành khi hành động có liên hệ với hiện tại.\nQuá khứ đơn khi có mốc thời gian đã kết thúc.",
    "rule": "have/has + V3; quá khứ đơn đi với mốc thời gian cụ thể.",
    "examples": [{"en": "I have lived here for five years.", "vi": "Tôi đã sống ở đây 5 năm."}, {"en": "I lived in Hanoi in 2019.", "vi": "Tôi sống ở Hà Nội năm 2019."}],
    "common_mistake": "Dùng 'since' với khoảng thời gian.",
    "follow_ups": ["Khi nào dùng 'since' và 'for'?"],
    "on_topic": True,
}


def test_tutor_ask_limit_and_fallback(client, db_session, monkeypatch, demo):
    monkeypatch.setattr(settings, "TUTOR_FREE_DAILY_LIMIT", 2)
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return ANSWER
    _swap_agent(monkeypatch, "tutor_answer", fake)

    headers = _auth(client, "tutor1@example.com", age=12)
    home = client.get(f"{API}/tutor", headers=headers).json()
    assert home["messages"] == [] and len(home["suggested"]) >= 3 and home["remaining_today"] == 2

    r = client.post(f"{API}/tutor/ask", json={"question": "Khi nào dùng hiện tại hoàn thành?"}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"]["content"].startswith("Dùng hiện tại hoàn thành") and len(body["answer"]["examples"]) == 2
    assert body["answer"]["fallback"] is False and body["remaining_today"] == 1
    assert seen["age"] == 12 and seen["history"] == [] and seen["level"]

    r = client.post(f"{API}/tutor/ask", json={"question": "Còn 'since' và 'for'?"}, headers=headers).json()
    assert [m["role"] for m in seen["history"]] == ["user", "assistant"]       # previous turn passed as context
    assert r["remaining_today"] == 0
    assert client.post(f"{API}/tutor/ask", json={"question": "Câu thứ ba?"}, headers=headers).status_code == 403

    # Premium → unlimited; LLM down → canned answer, not counted
    assert client.post(f"{API}/billing/upgrade", json={"months": 1}, headers=headers).status_code == 200
    _swap_agent(monkeypatch, "tutor_answer", lambda **kw: (_ for _ in ()).throw(RuntimeError("no LLM")))
    r = client.post(f"{API}/tutor/ask", json={"question": "Bo ơi?"}, headers=headers)
    assert r.status_code == 200 and r.json()["answer"]["fallback"] is True and r.json()["remaining_today"] is None
    home = client.get(f"{API}/tutor", headers=headers).json()
    assert len(home["messages"]) == 6 and home["messages"][0]["role"] == "user" and home["asked_today"] == 2
    assert client.delete(f"{API}/tutor", headers=headers).status_code == 204
    assert client.get(f"{API}/tutor", headers=headers).json()["messages"] == []
    assert client.post(f"{API}/tutor/ask", json={"question": "x"}, headers=headers).status_code == 422


# ── Báo cáo nhóm CSV ─────────────────────────────────────────────────────────
def test_group_report_csv(client):
    teacher = _auth(client, "t8@example.com", role="teacher", name="Thầy Nam")
    an = _auth(client, "an8@example.com", name="An Nguyễn")
    g = client.post(f"{API}/groups", json={"name": "Lớp 8B", "kind": "class"}, headers=teacher).json()
    client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=an)
    client.post(f"{API}/groups/{g['id']}/assignments", json={"title": "Tuần 1", "skill": "grammar", "topic": "past simple"}, headers=teacher)

    r = client.get(f"{API}/groups/{g['id']}/report.csv", headers=teacher)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    text = r.content.decode("utf-8")
    assert text.startswith("﻿") and "Lớp 8B" in text and "An Nguyễn" in text and "Tuần 1" in text
    assert client.get(f"{API}/groups/{g['id']}/report.csv", headers=an).status_code == 403


# ── Hoá đơn VAT ──────────────────────────────────────────────────────────────
INVOICE = {"company_name": "Công ty TNHH ABC", "tax_code": "0312345678", "address": "12 Lê Lợi, Q.1, TP.HCM", "email": "ketoan@abc.vn"}


def test_invoice_request_and_admin_issue(client, monkeypatch, demo):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss@example.com")
    hr = _auth(client, "hr8@example.com", role="teacher")
    bad = client.post(f"{API}/billing/upgrade", json={"months": 12, "plan": "team", "seats": 10, "invoice": {**INVOICE, "tax_code": "abc"}}, headers=hr)
    assert bad.status_code == 422
    ok = client.post(f"{API}/billing/upgrade", json={"months": 12, "plan": "team", "seats": 10, "invoice": INVOICE}, headers=hr)
    assert ok.status_code == 200 and ok.json()["plan"] == "team"
    orders = client.get(f"{API}/billing/orders", headers=hr).json()
    assert len(orders) == 1 and orders[0]["invoice"]["tax_code"] == "0312345678" and orders[0]["amount_vnd"] == 6_900_000 and orders[0]["invoice_issued_at"] is None
    oid = orders[0]["order_id"]
    upd = client.put(f"{API}/billing/orders/{oid}/invoice", json={**INVOICE, "company_name": "Công ty ABC mới"}, headers=hr)
    assert upd.status_code == 200 and upd.json()["invoice"]["company_name"] == "Công ty ABC mới"

    # real checkout also keeps the request
    from app.services import payments
    monkeypatch.setattr(payments, "providers", lambda: ["vnpay"])
    monkeypatch.setattr(payments, "vnpay_pay_url", lambda order, ip, ret: "https://pay.example/x")
    co = client.post(f"{API}/billing/checkout", json={"months": 1, "provider": "vnpay", "plan": "team", "seats": 5, "invoice": INVOICE}, headers=hr)
    assert co.status_code == 200, co.text
    assert client.get(f"{API}/billing/orders/{co.json()['order_id']}", headers=hr).json()["invoice"]["email"] == "ketoan@abc.vn"

    assert client.get(f"{API}/admin/revenue/orders", headers=hr).status_code == 403
    admin = _auth(client, "boss@example.com")
    rows = client.get(f"{API}/admin/revenue/orders?invoice_only=true", headers=admin).json()
    assert len(rows) == 2 and {r["status"] for r in rows} == {"paid", "pending"} and rows[0]["email"] == "hr8@example.com"
    done = client.post(f"{API}/admin/revenue/orders/{oid}/invoice-issued", json={"issued": True}, headers=admin)
    assert done.status_code == 200 and done.json()["invoice_issued_at"]
    assert client.put(f"{API}/billing/orders/{oid}/invoice", json=INVOICE, headers=hr).status_code == 400     # locked once issued


# ── FCM ──────────────────────────────────────────────────────────────────────
def _service_account_json() -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    return json.dumps({"project_id": "agen-test", "client_email": "fcm@agen-test.iam.gserviceaccount.com", "private_key": pem})


class _Resp:
    def __init__(self, status, body=None, text=""):
        self.status_code, self._body, self.text = status, body or {}, text

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_device_tokens_and_fcm_send(client, db_session, monkeypatch):
    headers = _auth(client, "fcm8@example.com")
    parent = _auth(client, "pfcm8@example.com", role="parent")
    assert client.get(f"{API}/notifications/native-push", headers=headers).json() == {"enabled": False}
    assert client.post(f"{API}/notifications/device-tokens", json={"token": "short", "platform": "ios"}, headers=headers).status_code == 422
    r = client.post(f"{API}/notifications/device-tokens", json={"token": "d" * 40, "platform": "ios"}, headers=headers)
    assert r.status_code == 200 and r.json()["platform"] == "ios" and r.json()["native_push_enabled"] is False
    client.post(f"{API}/notifications/device-tokens", json={"token": "d" * 40, "platform": "ios"}, headers=headers)      # idempotent
    client.post(f"{API}/notifications/device-tokens", json={"token": "p" * 40, "platform": "android"}, headers=parent)
    rows = db_session.query(DeviceToken).all()
    assert len(rows) == 2 and {bool(r.learner_id) for r in rows} == {True, False}

    learner = db_session.query(LearnerProfile).join(User).filter(User.email == "fcm8@example.com").one()
    msg = reminders.ReminderMessage(title="Học thôi", body="1 bài ngắn", url="/dashboard")
    assert reminders.push_to_learner(db_session, learner, msg) == 0                      # nothing configured

    calls = []

    def fake_post(url, **kw):
        calls.append((url, kw))
        if url == fcm.TOKEN_URL:
            return _Resp(200, {"access_token": "tok", "expires_in": 3600})
        if "/messages:send" in url:
            if kw["json"]["message"]["token"].startswith("p"):
                return _Resp(404, text='{"error":{"details":[{"errorCode":"UNREGISTERED"}]}}')
            return _Resp(200, {"name": "projects/agen-test/messages/1"})
        raise AssertionError(url)
    monkeypatch.setattr(fcm.httpx, "post", fake_post)
    monkeypatch.setattr(settings, "FIREBASE_SERVICE_ACCOUNT_JSON", _service_account_json())
    fcm._cache.update({"token": None, "exp": 0.0})

    assert reminders.push_to_learner(db_session, learner, msg) == 1
    sent = next(kw for url, kw in calls if "/messages:send" in url)
    assert sent["headers"]["Authorization"] == "Bearer tok" and sent["json"]["message"]["notification"]["title"] == "Học thôi"
    assert "agen-test" in [u for u, _ in calls][-1]
    parent_user = db_session.query(User).filter(User.email == "pfcm8@example.com").one()
    assert reminders.push_to_user(db_session, parent_user.id, msg) == 0                  # UNREGISTERED → row deleted
    db_session.commit()
    assert db_session.query(DeviceToken).count() == 1
    assert sum(1 for u, _ in calls if u == fcm.TOKEN_URL) == 1                           # access token cached

    assert client.request("DELETE", f"{API}/notifications/device-tokens", json={"token": "d" * 40, "platform": "ios"}, headers=headers).status_code == 204
    db_session.expire_all()
    assert db_session.query(DeviceToken).count() == 0
