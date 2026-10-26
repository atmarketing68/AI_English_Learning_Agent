"""G11 · Podcast AI sinh + duyệt, phòng nói hẹn giờ + nhắc, giáo viên chấm lại bài viết, hoàn tiền + biên nhận, cảnh báo chi phí AI."""
import dataclasses
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

import pytest

from app.agents import orchestrator
from app.core.config import settings
from app.models.ai_usage import AiUsage
from app.models.learner_profile import LearnerProfile
from app.models.notification import Notification
from app.models.payment_order import PaymentOrder
from app.models.speaking_club import RoomMember, SpeakingRoom
from app.models.subscription import Subscription
from app.models.user import User
from app.models.writing import WritingSubmission
from app.services import ai_usage, payments, podcast_generator, speaking_club
from app.services import subscription_service as subs
from app.services.podcast_generator import PodcastGenerationError, normalize_episode, parse_youtube

API = "/api/v1"


def _auth(client, email, role="learner", age=20, name=None):
    body = {"email": email, "password": "Strong123", "full_name": name or email.split("@")[0], "display_name": name or email.split("@")[0], "role": role}
    if role == "learner":
        body["age"] = age
    r = client.post(f"{API}/auth/register", json=body)
    assert r.status_code in (200, 201), r.text
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _user(db, email) -> User:
    db.expire_all()
    return db.query(User).filter(User.email == email).first()


def _learner_id(db, email):
    return db.query(LearnerProfile).filter(LearnerProfile.user_id == _user(db, email).id).first().id


def _swap_agent(monkeypatch, name, handler):
    patched = dict(orchestrator.AGENT_SPECS)
    patched[name] = dataclasses.replace(orchestrator.AGENT_SPECS[name], handler=handler)
    monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── G11.1 Podcast AI ─────────────────────────────────────────────────────────
EPISODE = {
    "title": "Moving to a new city", "title_vi": "Chuyển đến thành phố mới", "description_vi": "Hội thoại về tìm nhà và làm quen hàng xóm.",
    "topic": "Đời sống",
    "lines": [{"speaker": "Lan", "text": t, "vi": "…"} for t in (
        "I finally moved to Da Nang last month.", "Wow, how do you like your new apartment?", "It is small but very bright and close to the beach.",
        "Did you meet your neighbours yet?", "Yes, an old couple next door brought me some fruit.", "That is so kind. Do you miss Hanoi?",
        "A little, but I love the sea breeze here.")],
    "vocab": [{"word": "apartment", "definition": "căn hộ"}, {"word": "neighbours", "definition": "hàng xóm"}, {"word": "spaceship", "definition": "tàu vũ trụ"}],
    "questions": [
        {"prompt": "Where did Lan move?", "options": ["Hanoi", "Da Nang", "Hue"], "answer": 1, "explanation_vi": "\"I finally moved to Da Nang\"."},
        {"prompt": "What is the apartment like?", "options": ["big and dark", "small but bright", "old and noisy"], "answer": 1, "explanation_vi": "\"small but very bright\"."},
        {"prompt": "What did the neighbours bring?", "options": ["fruit", "flowers", "cake"], "answer": 0, "explanation_vi": "\"brought me some fruit\"."},
    ],
}


def test_normalize_episode_and_youtube_parsing():
    ep = normalize_episode(EPISODE, "B1")
    assert [q["id"] for q in ep["questions"]] == ["q1", "q2", "q3"]
    assert [v["word"] for v in ep["vocab"]] == ["apartment", "neighbours"]          # words not in the transcript are dropped
    assert ep["level"] == "B1" and ep["kind"] == "podcast" and 2 <= ep["minutes"] <= 8
    bad = json.loads(json.dumps(EPISODE))
    bad["questions"][0]["answer"] = 5
    with pytest.raises(PodcastGenerationError):
        normalize_episode(bad, "B1")
    short = dict(EPISODE, lines=EPISODE["lines"][:3])
    with pytest.raises(PodcastGenerationError):
        normalize_episode(short, "B1")
    assert parse_youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=5") == "dQw4w9WgXcQ"
    assert parse_youtube("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert parse_youtube("dQw4w9WgXcQ") == "dQw4w9WgXcQ" and parse_youtube("") is None
    with pytest.raises(PodcastGenerationError):
        parse_youtube("https://vimeo.com/123")


def test_admin_generates_reviews_and_learners_hear_podcast(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss11@example.com")
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return EPISODE
    _swap_agent(monkeypatch, "podcast_generation", fake)
    admin = _auth(client, "boss11@example.com")
    learner = _auth(client, "pod11@example.com")
    assert client.post(f"{API}/admin/podcasts/generate", json={"level": "B1"}, headers=learner).status_code == 403

    g = client.post(f"{API}/admin/podcasts/generate", json={"level": "B1", "topic": "moving house"}, headers=admin)
    assert g.status_code == 200, g.text
    draft = g.json()
    assert draft["status"] == "draft" and draft["lines"] == 7 and draft["questions"] == 3 and seen["topic"] == "moving house"
    pid = draft["public_id"]
    assert all(e["id"] != pid for e in client.get(f"{API}/media", headers=learner).json())      # drafts stay hidden
    assert client.get(f"{API}/media/{pid}", headers=learner).status_code == 404
    full = client.get(f"{API}/admin/podcasts/{draft['id']}", headers=admin).json()
    assert full["episode"]["questions"][0]["answer"] == 1

    assert client.post(f"{API}/admin/podcasts/{draft['id']}/video", json={"youtube": "not a link"}, headers=admin).status_code == 400
    v = client.post(f"{API}/admin/podcasts/{draft['id']}/video", json={"youtube": "https://youtu.be/dQw4w9WgXcQ", "start": 10, "end": 70}, headers=admin)
    assert v.status_code == 200 and v.json()["youtube_id"] == "dQw4w9WgXcQ"
    assert client.post(f"{API}/admin/podcasts/{draft['id']}/status", json={"status": "approved"}, headers=admin).json()["status"] == "approved"

    item = next(e for e in client.get(f"{API}/media", headers=learner).json() if e["id"] == pid)
    assert item["has_video"] is True and item["kind"] == "video" and item["level"] == "B1"
    ep = client.get(f"{API}/media/{pid}", headers=learner).json()
    assert ep["youtube_id"] == "dQw4w9WgXcQ" and ep["start"] == 10 and "answer" not in ep["questions"][0]
    r = client.post(f"{API}/media/{pid}/submit", json={"answers": {"q1": 1, "q2": 1, "q3": 0}}, headers=learner).json()
    assert r["pct"] == 100 and r["xp_earned"] > 0

    # rejecting hides it again; deleting removes progress rows too
    client.post(f"{API}/admin/podcasts/{draft['id']}/status", json={"status": "rejected"}, headers=admin)
    assert all(e["id"] != pid for e in client.get(f"{API}/media", headers=learner).json())
    assert client.delete(f"{API}/admin/podcasts/{draft['id']}", headers=admin).status_code == 204
    assert client.get(f"{API}/admin/podcasts", headers=admin).json() == []

    # LLM down → 502 and no row
    _swap_agent(monkeypatch, "podcast_generation", lambda **kw: (_ for _ in ()).throw(RuntimeError("down")))
    assert client.post(f"{API}/admin/podcasts/generate", json={"level": "A2"}, headers=admin).status_code == 502
    assert client.get(f"{API}/admin/podcasts", headers=admin).json() == []


# ── G11.2 Booked speaking-club sessions ──────────────────────────────────────
def test_scheduled_club_room_booking_reminders_and_expiry(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "cron11")
    host = _auth(client, "host11@example.com", name="Hải")
    guest = _auth(client, "guest11@example.com", name="Gia")
    other = _auth(client, "other11@example.com", name="Ô")

    too_soon = (datetime.now(timezone.utc) + timedelta(minutes=3)).isoformat()
    assert client.post(f"{API}/club/rooms", json={"topic_id": "travel", "scheduled_at": too_soon}, headers=host).status_code == 400
    too_far = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    assert client.post(f"{API}/club/rooms", json={"topic_id": "travel", "scheduled_at": too_far}, headers=host).status_code == 400

    when = datetime.now(timezone.utc) + timedelta(hours=2)
    room = client.post(f"{API}/club/rooms", json={"topic_id": "travel", "scheduled_at": when.isoformat()}, headers=host)
    assert room.status_code == 200, room.text
    room = room.json()
    assert room["scheduled_at"] and room["opens_at"] and "Hẹn bắt đầu lúc" in room["messages"][0]["text"]
    assert client.post(f"{API}/club/rooms/{room['id']}/start", headers=host).status_code == 400          # too early

    lobby = client.get(f"{API}/club", headers=guest).json()
    assert any(r["id"] == room["id"] for r in lobby["upcoming_rooms"]) and all(r["id"] != room["id"] for r in lobby["open_rooms"])
    assert client.post(f"{API}/club/rooms/join", json={"code": room["code"]}, headers=guest).status_code == 200
    assert any(r["id"] == room["id"] for r in client.get(f"{API}/club", headers=guest).json()["my_rooms"])

    # the scheduler: nothing yet two hours ahead, then both members reminded once ~15 min before
    assert client.post(f"{API}/club/cron/remind", headers={"X-Cron-Secret": "wrong"}).status_code == 403
    assert client.post(f"{API}/club/cron/remind", headers={"X-Cron-Secret": "cron11"}).json()["reminded"] == 0
    start_naive = when.astimezone(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
    stats = speaking_club.run_reminders(db_session, now=start_naive - timedelta(minutes=15))
    assert stats["reminded"] == 2
    assert speaking_club.run_reminders(db_session, now=start_naive - timedelta(minutes=8))["reminded"] == 0
    notes = db_session.query(Notification).filter(Notification.type == "club_reminder").all()
    assert len(notes) == 2 and "Chuyện du lịch" in notes[0].body

    # move the booking into the start window → host can open it; it shows in the lobby as open
    r = db_session.query(SpeakingRoom).filter(SpeakingRoom.id == room["id"]).first()
    r.scheduled_at = _now() + timedelta(minutes=5)
    db_session.commit()
    assert any(x["id"] == room["id"] for x in client.get(f"{API}/club", headers=other).json()["open_rooms"])
    assert client.post(f"{API}/club/rooms/{room['id']}/start", headers=host).json()["status"] == "active"

    # a booked room nobody opened is closed two hours after its time
    late = client.post(f"{API}/club/rooms", json={"topic_id": "food", "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}, headers=other).json()
    lr = db_session.query(SpeakingRoom).filter(SpeakingRoom.id == late["id"]).first()
    db_session.expire_all()
    assert speaking_club.run_reminders(db_session, now=lr.scheduled_at + timedelta(minutes=speaking_club.SCHEDULED_EXPIRE_MIN + 1))["expired"] == 1
    db_session.expire_all()
    assert db_session.query(SpeakingRoom).filter(SpeakingRoom.id == late["id"]).first().status == "finished"
    assert db_session.query(RoomMember).filter(RoomMember.room_id == room["id"], RoomMember.reminded_at.isnot(None)).count() == 2


# ── G11.3 Teacher re-grades writing ──────────────────────────────────────────
def test_teacher_regrades_writing(client, db_session):
    teacher = _auth(client, "co11@example.com", role="teacher", name="Cô Hạnh")
    student = _auth(client, "hs11@example.com", name="Minh")
    g = client.post(f"{API}/groups", json={"name": "IELTS 11", "kind": "class"}, headers=teacher).json()
    client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=student)
    lid = _learner_id(db_session, "hs11@example.com")
    w = WritingSubmission(learner_id=lid, prompt_title="Online shopping", prompt_text="Discuss…", genre="ielts_task2", level="B1",
                          user_text="Many people shop online. " * 20, word_count=80, overall_score=62.0, grade="B",
                          evaluation={"exam_band": {"exam": "ielts", "overall": 5.5}})
    free = WritingSubmission(learner_id=lid, prompt_title="My weekend", prompt_text="Describe…", genre="narrative", level="B1",
                             user_text="I went to the beach.", word_count=5, overall_score=70.0, grade="B", evaluation={})
    db_session.add_all([w, free])
    db_session.commit()
    base = f"{API}/groups/{g['id']}/members/{lid}/writing"

    assert client.post(f"{base}/{w.id}/grade", json={"score": 75, "band": 6.3}, headers=teacher).status_code == 400   # not a .5 step
    assert client.post(f"{base}/{w.id}/grade", json={"score": 120}, headers=teacher).status_code == 422
    r = client.post(f"{base}/{w.id}/grade", json={"score": 74, "band": 6.5, "comment": "Lập luận rõ, cần thêm ví dụ."}, headers=teacher)
    assert r.status_code == 200, r.text
    assert r.json()["teacher_score"] == 74 and r.json()["teacher_band"] == 6.5 and r.json()["exam"] == "ielts"
    # band is ignored for a non-exam genre
    assert client.post(f"{base}/{free.id}/grade", json={"score": 80, "band": 7}, headers=teacher).json()["teacher_band"] is None

    detail = client.get(f"{API}/groups/{g['id']}/members/{lid}", headers=teacher).json()
    graded = next(x for x in detail["writings"] if x["id"] == w.id)
    assert graded["teacher_score"] == 74 and graded["teacher_band"] == 6.5
    assert any("74/100" in f["text"] and f["target_type"] == "writing" for f in detail["feedback"])
    hist = client.get(f"{API}/writing/history", headers=student).json()
    mine = next(x for x in hist if x["id"] == w.id)
    assert mine["teacher_score"] == 74 and mine["teacher_comment"].startswith("Lập luận") and mine["band"] == 5.5
    assert db_session.query(Notification).filter(Notification.learner_id == lid, Notification.type == "teacher_feedback").count() == 2

    other = _auth(client, "other-teacher11@example.com", role="teacher")
    assert client.post(f"{base}/{w.id}/grade", json={"score": 10}, headers=other).status_code == 404
    cleared = client.post(f"{base}/{w.id}/grade", json={"score": None}, headers=teacher).json()
    assert cleared["teacher_score"] is None and cleared["teacher_comment"] is None


# ── G11.4 Refunds + receipts ─────────────────────────────────────────────────
def _sign(body: bytes, secret="whsec_test"):
    ts = int(time.time())
    return f"t={ts},v1={hmac.new(secret.encode(), f'{ts}.'.encode() + body, hashlib.sha256).hexdigest()}"


def test_stripe_refund_receipt_and_webhook(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "money11@example.com")
    calls = []

    class Resp:
        def __init__(self, data):
            self.status_code, self._d = 200, data

        def json(self):
            return self._d

    def fake_post(url, data=None, auth=None, timeout=None):
        calls.append((url, data))
        return Resp({"id": "re_123"} if url.endswith("/refunds") else {"id": "cs_1", "url": "https://checkout.stripe.com/c/pay/cs_1"})
    monkeypatch.setattr(payments.httpx, "post", fake_post)

    buyer = _auth(client, "buyer11@example.com")
    stranger = _auth(client, "stranger11@example.com")
    admin = _auth(client, "money11@example.com")
    oid = client.post(f"{API}/billing/checkout", json={"provider": "stripe", "months": 1}, headers=buyer).json()["order_id"]
    assert client.get(f"{API}/billing/orders/{oid}/receipt", headers=buyer).status_code == 400            # not paid yet
    paid = json.dumps({"type": "checkout.session.completed", "data": {"object": {"id": "cs_1", "metadata": {"order_id": oid}, "payment_status": "paid",
                                                                                 "amount_total": 499, "currency": "usd", "payment_intent": "pi_777"}}}).encode()
    assert client.post(f"{API}/billing/stripe/webhook", content=paid, headers={"stripe-signature": _sign(paid)}).json()["result"] == "paid"
    uid = _user(db_session, "buyer11@example.com").id
    assert subs.is_premium(db_session, uid)

    rec = client.get(f"{API}/billing/orders/{oid}/receipt", headers=buyer)
    assert rec.status_code == 200 and rec.json()["number"].startswith("BN-") and rec.json()["seller"]["name"] == "AI AGENT ENGLISH"
    assert rec.json()["order"]["amount_foreign"] == 499 and rec.json()["buyer"]["email"] == "buyer11@example.com"
    assert client.get(f"{API}/billing/orders/{oid}/receipt", headers=stranger).status_code == 404
    assert client.get(f"{API}/billing/orders/{oid}/receipt", headers=admin).status_code == 200

    assert client.post(f"{API}/admin/revenue/orders/{oid}/refund", json={}, headers=buyer).status_code == 403
    r = client.post(f"{API}/admin/revenue/orders/{oid}/refund", json={"note": "Khách đổi ý"}, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "refunded" and r.json()["refund_note"] == "Khách đổi ý"
    assert calls[-1][0].endswith("/refunds") and calls[-1][1]["payment_intent"] == "pi_777"
    db_session.expire_all()
    assert not subs.is_premium(db_session, uid)
    assert client.post(f"{API}/admin/revenue/orders/{oid}/refund", json={}, headers=admin).status_code == 400       # twice
    # Stripe echoes the refund as charge.refunded (no order metadata on the charge) → nothing changes
    echo = json.dumps({"type": "charge.refunded", "data": {"object": {"id": "ch_1", "payment_intent": "pi_777", "refunded": True}}}).encode()
    assert client.post(f"{API}/billing/stripe/webhook", content=echo, headers={"stripe-signature": _sign(echo)}).json()["result"] == "already_refunded"
    assert client.get(f"{API}/billing/orders/{oid}/receipt", headers=buyer).json()["order"]["status"] == "refunded"


def test_dashboard_refund_webhook_and_manual_refund(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "money11b@example.com")
    admin = _auth(client, "money11b@example.com")
    _auth(client, "vn11@example.com")
    uid = _user(db_session, "vn11@example.com").id

    # a Stripe order refunded on the Stripe dashboard arrives as charge.refunded, found by its PaymentIntent
    st = PaymentOrder(user_id=uid, provider="stripe", plan="premium", months=1, amount_vnd=124750, currency="USD", amount_foreign=499,
                      status="paid", provider_txn="pi_dash", paid_at=_now())
    # a VNPay order: the operator refunds on VNPay, then records it here
    vn = PaymentOrder(user_id=uid, provider="vnpay", plan="premium", months=3, amount_vnd=249000, status="paid", provider_txn="1400", paid_at=_now())
    db_session.add_all([st, vn])
    db_session.commit()
    subs.upgrade_to_premium(db_session, uid, months=12)
    end_before = db_session.query(Subscription).filter(Subscription.user_id == uid).first().current_period_end

    ev = json.dumps({"type": "charge.refunded", "data": {"object": {"id": "ch_2", "payment_intent": "pi_dash", "refunded": True,
                                                                     "refunds": {"data": [{"id": "re_dash"}]}}}}).encode()
    assert client.post(f"{API}/billing/stripe/webhook", content=ev, headers={"stripe-signature": _sign(ev)}).json()["result"] == "refunded"
    r = client.post(f"{API}/admin/revenue/orders/{vn.id}/refund", json={"note": "Hoàn trên VNPay ngày 27/10"}, headers=admin)
    assert r.status_code == 200 and r.json()["status"] == "refunded"
    db_session.expire_all()
    sub = db_session.query(Subscription).filter(Subscription.user_id == uid).first()
    assert subs.is_premium(db_session, uid)                                 # 12 months bought, 4 refunded → still Premium
    assert abs((end_before - sub.current_period_end).days - 120) <= 1
    assert db_session.get(PaymentOrder, st.id).refund_txn == "re_dash"
    orders = client.get(f"{API}/admin/revenue/orders", headers=admin).json()
    assert {o["status"] for o in orders if o["order_id"] in (st.id, vn.id)} == {"refunded"}


# ── G11.5 AI cost alerts ─────────────────────────────────────────────────────
def test_ai_cost_alerts_email_once_per_day(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "ops11@example.com,cto11@example.com")
    sent = []
    monkeypatch.setattr("app.services.reminders.deliver_email", lambda to, subject, html_body, text, unsubscribe_url=None: sent.append((to, text)) or True)
    _auth(client, "heavy11@example.com")
    heavy = _user(db_session, "heavy11@example.com").id

    assert ai_usage.check_alerts(db_session) == {"enabled": False}           # thresholds off by default
    monkeypatch.setattr(settings, "AI_ALERT_DAILY_USD", 1.0)
    monkeypatch.setattr(settings, "AI_ALERT_USER_DAILY_USD", 0.5)
    db_session.add_all([AiUsage(user_id=heavy, feature="tutor_answer", provider="gemini", cost_usd=0.6, created_at=_now()),
                        AiUsage(user_id=None, feature="lesson", provider="gemini", cost_usd=0.3, created_at=_now()),
                        AiUsage(user_id=heavy, feature="tts", provider="openai", cost_usd=5.0, created_at=_now() - timedelta(days=2))])
    db_session.commit()
    out = ai_usage.check_alerts(db_session)
    assert out["total_alert"] is False and out["user_alerts"] == 1 and out["emails"] == 2
    assert "heavy11@example.com" in sent[0][1]
    assert ai_usage.check_alerts(db_session)["emails"] == 0                  # same user, same day → no repeat

    db_session.add(AiUsage(user_id=None, feature="podcast_generation", provider="gemini", cost_usd=0.2, created_at=_now()))
    db_session.commit()
    out = ai_usage.check_alerts(db_session)
    assert out["total_alert"] is True and out["user_alerts"] == 0 and "vượt ngưỡng" in sent[-1][1]
    assert ai_usage.check_alerts(db_session)["emails"] == 0

    state = ai_usage.alert_state(db_session)
    assert state["total_over"] is True and state["users_over"][0]["email"] == "heavy11@example.com"
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "ops11@example.com")
    _auth(client, "ops11@example.com")
    s = client.get(f"{API}/admin/ai-usage/summary", headers={"Authorization": "Bearer " + client.post(f"{API}/auth/login", data={"username": "ops11@example.com", "password": "Strong123"}).json()["access_token"]}).json()
    assert s["alerts"]["total_over"] is True and s["alerts"]["users_over"][0]["user_id"] == heavy


def test_hourly_cron_runs_club_and_alert_hooks(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "cron11b")
    monkeypatch.setattr("app.api.reminders.run_due_reminders", lambda db: {"checked": 0})
    monkeypatch.setattr("app.services.parent_digest.run_parent_digests", lambda db: {"parents": 0})
    r = client.post(f"{API}/reminders/cron/run", headers={"X-Cron-Secret": "cron11b"})
    assert r.status_code == 200, r.text
    assert "club" in r.json() and r.json()["ai_alerts"] == {"enabled": False}
