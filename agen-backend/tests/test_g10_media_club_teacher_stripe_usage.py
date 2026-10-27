"""G10 · Podcast/video, câu lạc bộ nói, giáo viên xem bài + nhận xét, Stripe + chứng nhận, chi phí AI."""
import dataclasses
import hashlib
import hmac
import json
import time

import pytest
from sqlalchemy.orm import sessionmaker

from app.agents import orchestrator
from app.core.config import settings
from app.core.usage_context import current_feature, current_user_id, feature_from_path
from app.models.ai_usage import AiUsage
from app.models.goal_track import GoalTrackProgress
from app.models.learner_profile import LearnerProfile
from app.models.notification import Notification
from app.models.payment_order import PaymentOrder
from app.models.user import User
from app.services import ai_usage, goal_tracks, llm_client, media_library, payments, speaking_club, tts_service
from app.services.subscription_service import is_premium

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


@pytest.fixture()
def usage_db(db_engine, monkeypatch):
    """AI usage rows go to the test engine instead of the dev database."""
    monkeypatch.setattr(ai_usage, "_session_factory", sessionmaker(autocommit=False, autoflush=False, bind=db_engine))


# ── G10.1 Podcast / video ────────────────────────────────────────────────────
def test_media_library_is_consistent_and_grades():
    eps = media_library.list_episodes()
    assert len(eps) >= 6 and len({e["id"] for e in eps}) == len(eps)
    for e in eps:
        assert e["lines"] and e["questions"] and all(l["text"] and l["vi"] for l in e["lines"])
        for q in e["questions"]:
            assert 0 <= q["answer"] < len(q["options"])
        pub = media_library.public_episode(e)
        assert all("answer" not in q and "explanation_vi" not in q for q in pub["questions"])
    ep = media_library.get_episode("pod-coffee-order")
    res = media_library.grade(ep, {"q1": 1, "q2": "1", "q3": 0, "q4": "x"})
    assert res["correct"] == 2 and res["total"] == 4 and res["pct"] == 50.0
    assert res["details"][2]["expected"] == "by QR code"


def test_media_submit_xp_rules(client, db_session):
    headers = _auth(client, "pod1@example.com")
    lst = client.get(f"{API}/media", headers=headers).json()
    assert lst[0]["completed"] is False and lst[0]["best_score"] is None
    assert client.get(f"{API}/media/nope", headers=headers).status_code == 404
    ep = client.get(f"{API}/media/pod-coffee-order", headers=headers).json()
    assert ep["lines"] and "answer" not in ep["questions"][0]

    r = client.post(f"{API}/media/pod-coffee-order/submit", json={"answers": {"q1": 1, "q2": 1}}, headers=headers).json()
    assert r["correct"] == 2 and r["xp_earned"] == 6 and r["gems_earned"] == 0 and r["best_score"] == 50.0
    # replaying with the same score gives nothing; improving gives a small bonus + gems for 100 %
    again = client.post(f"{API}/media/pod-coffee-order/submit", json={"answers": {"q1": 1, "q2": 1}}, headers=headers).json()
    assert again["xp_earned"] == 0
    perfect = client.post(f"{API}/media/pod-coffee-order/submit", json={"answers": {"q1": 1, "q2": 1, "q3": 2, "q4": 1}}, headers=headers).json()
    assert perfect["pct"] == 100 and perfect["xp_earned"] == media_library.XP_PER_CORRECT and perfect["gems_earned"] == media_library.GEMS_PERFECT
    assert client.post(f"{API}/media/pod-coffee-order/submit", json={"answers": {"q1": 1, "q2": 1, "q3": 2, "q4": 1}}, headers=headers).json()["gems_earned"] == 0
    item = next(e for e in client.get(f"{API}/media", headers=headers).json() if e["id"] == "pod-coffee-order")
    assert item["completed"] is True and item["best_score"] == 100


# ── G10.2 Speaking club ──────────────────────────────────────────────────────
MOD = {"feedback_vi": "Tốt lắm, thêm ví dụ nhé.", "corrected": "I like playing football.", "reply": "Nice! Lan, what do you do at weekends?"}


def test_speaking_club_flow(client, db_session, monkeypatch):
    seen = {}

    def fake(**kw):
        seen.update(kw)
        return MOD
    _swap_agent(monkeypatch, "club_moderator", fake)
    an = _auth(client, "club_an@example.com", name="An")
    lan = _auth(client, "club_lan@example.com", name="Lan")
    binh = _auth(client, "club_binh@example.com", name="Binh")

    lobby = client.get(f"{API}/club", headers=an).json()
    assert len(lobby["topics"]) >= 6 and lobby["max_members"] == 4
    assert client.post(f"{API}/club/rooms", json={"topic_id": "nope"}, headers=an).status_code == 400
    room = client.post(f"{API}/club/rooms", json={"topic_id": "hobbies"}, headers=an).json()
    rid, code = room["id"], room["code"]
    assert room["status"] == "waiting" and room["is_host"] is True
    assert any(r["code"] == code for r in client.get(f"{API}/club", headers=lan).json()["open_rooms"])
    assert client.get(f"{API}/club/rooms/{rid}", headers=lan).status_code == 403          # not a member yet

    assert client.post(f"{API}/club/rooms/join", json={"code": code.lower()}, headers=lan).status_code == 200
    assert client.post(f"{API}/club/rooms/{rid}/start", headers=lan).status_code == 400      # only the host starts
    st = client.post(f"{API}/club/rooms/{rid}/start", headers=an).json()
    assert st["status"] == "active" and st["is_my_turn"] is True and st["total_turns"] == 2 * speaking_club.TURNS_PER_MEMBER
    assert st["messages"][-1]["role"] == "ai" and "An" in st["messages"][-1]["text"]
    assert client.post(f"{API}/club/rooms/join", json={"code": code}, headers=binh).status_code == 400   # already started

    assert client.post(f"{API}/club/rooms/{rid}/speak", json={"transcript": "hello"}, headers=lan).status_code == 409
    st = client.post(f"{API}/club/rooms/{rid}/speak", json={"transcript": "I like play football with my friends"}, headers=an).json()
    assert seen["speaker_name"] == "An" and seen["next_name"] == "Lan" and seen["topic"] == "Hobbies & free time"
    mine = [m for m in st["messages"] if m["role"] == "learner"][-1]
    assert mine["feedback_vi"] == MOD["feedback_vi"] and mine["corrected"] == MOD["corrected"]
    assert st["messages"][-1]["text"] == MOD["reply"] and st["is_my_turn"] is False
    lan_state = client.get(f"{API}/club/rooms/{rid}?after={st['last_seq'] - 1}", headers=lan).json()
    assert lan_state["is_my_turn"] is True and len(lan_state["messages"]) == 1

    # LLM down → fallback tip and a scripted question, the club keeps going
    _swap_agent(monkeypatch, "club_moderator", lambda **kw: (_ for _ in ()).throw(RuntimeError("down")))
    st = client.post(f"{API}/club/rooms/{rid}/speak", json={"transcript": "I read books"}, headers=lan).json()
    assert [m for m in st["messages"] if m["role"] == "learner"][-1]["feedback_vi"]
    assert st["current_speaker_id"] == _learner_id(db_session, "club_an@example.com")

    # host can skip; turns run out → finished, XP recorded
    assert client.post(f"{API}/club/rooms/{rid}/skip", headers=lan).status_code == 403
    for _ in range(10):
        st = client.get(f"{API}/club/rooms/{rid}", headers=an).json()
        if st["status"] != "active":
            break
        who = an if st["is_my_turn"] else lan
        client.post(f"{API}/club/rooms/{rid}/speak", json={"transcript": "I really enjoy swimming in summer"}, headers=who)
    assert st["status"] == "finished" and st["turns_taken"] == st["total_turns"]
    assert "see you" in st["messages"][-1]["text"].lower()
    an_member = next(m for m in st["members"] if m["is_me"])
    assert an_member["turns"] == speaking_club.TURNS_PER_MEMBER

    # leaving a waiting room hands the host role over; the last one out closes it
    r2 = client.post(f"{API}/club/rooms", json={"topic_id": "food"}, headers=an).json()
    client.post(f"{API}/club/rooms/join", json={"code": r2["code"]}, headers=binh)
    assert client.post(f"{API}/club/rooms/{r2['id']}/leave", headers=an).status_code == 200
    assert client.get(f"{API}/club/rooms/{r2['id']}", headers=binh).json()["is_host"] is True
    client.post(f"{API}/club/rooms/{r2['id']}/leave", headers=binh)
    assert all(r["id"] != r2["id"] for r in client.get(f"{API}/club", headers=lan).json()["open_rooms"])


def test_speaking_club_leave_mid_session_passes_turn(client, db_session, monkeypatch):
    _swap_agent(monkeypatch, "club_moderator", lambda **kw: MOD)
    a = _auth(client, "cl2a@example.com", name="Ai")
    b = _auth(client, "cl2b@example.com", name="Be")
    c = _auth(client, "cl2c@example.com", name="Ce")
    room = client.post(f"{API}/club/rooms", json={"topic_id": "travel", "is_public": False}, headers=a).json()
    assert all(r["id"] != room["id"] for r in client.get(f"{API}/club", headers=b).json()["open_rooms"])   # private
    for h in (b, c):
        client.post(f"{API}/club/rooms/join", json={"code": room["code"]}, headers=h)
    client.post(f"{API}/club/rooms/{room['id']}/start", headers=a)
    client.post(f"{API}/club/rooms/{room['id']}/speak", json={"transcript": "I went to Hue last year"}, headers=a)
    assert client.get(f"{API}/club/rooms/{room['id']}", headers=b).json()["is_my_turn"] is True
    client.post(f"{API}/club/rooms/{room['id']}/leave", headers=b)
    st = client.get(f"{API}/club/rooms/{room['id']}", headers=c).json()
    assert st["is_my_turn"] is True and len(st["members"]) == 2 and "Ce" in st["messages"][-1]["text"]


# ── G10.3 Teacher: member detail + feedback, certificates ───────────────────
def test_teacher_member_detail_feedback_and_certificate(client, db_session):
    teacher = _auth(client, "co_mai@example.com", role="teacher", name="Cô Mai")
    hs = _auth(client, "hs10@example.com", name="Hà")
    other = _auth(client, "other10@example.com", role="teacher", name="Thầy B")
    g = client.post(f"{API}/groups", json={"name": "Lớp 10A", "kind": "class"}, headers=teacher).json()
    client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=hs)
    lid = _learner_id(db_session, "hs10@example.com")
    client.post(f"{API}/media/pod-coffee-order/submit", json={"answers": {"q1": 1}}, headers=hs)

    d = client.get(f"{API}/groups/{g['id']}/members/{lid}", headers=teacher)
    assert d.status_code == 200, d.text
    d = d.json()
    assert d["display_name"] == "Hà" and d["group"]["name"] == "Lớp 10A" and d["feedback"] == [] and d["certificates"] == []
    assert {"lessons", "writings", "exams", "speaking_exams", "assignments", "skills"} <= set(d)
    assert client.get(f"{API}/groups/{g['id']}/members/{lid}", headers=other).status_code == 404
    assert client.get(f"{API}/groups/{g['id']}/members/nobody", headers=teacher).status_code == 404
    assert client.get(f"{API}/groups/{g['id']}/members/{lid}/writing/nope", headers=teacher).status_code == 404

    fb = client.post(f"{API}/groups/{g['id']}/members/{lid}/feedback", json={"text": "Phát âm tiến bộ, cần luyện thêm thì quá khứ.", "target_type": "general"}, headers=teacher)
    assert fb.status_code == 200, fb.text
    assert client.post(f"{API}/groups/{g['id']}/members/{lid}/feedback", json={"text": "x", "target_type": "bad"}, headers=teacher).status_code == 422
    assert db_session.query(Notification).filter(Notification.learner_id == lid, Notification.type == "teacher_feedback").count() == 1

    mine = client.get(f"{API}/groups/learner/feedback", headers=hs).json()
    assert len(mine) == 1 and mine[0]["teacher_name"] == "Cô Mai" and mine[0]["group_name"] == "Lớp 10A" and mine[0]["read_at"] is None
    assert client.post(f"{API}/groups/learner/feedback/read", headers=hs).status_code == 204
    assert client.get(f"{API}/groups/learner/feedback", headers=hs).json()[0]["read_at"] is not None
    assert client.delete(f"{API}/groups/{g['id']}/feedback/{fb.json()['id']}", headers=other).status_code == 404
    assert client.delete(f"{API}/groups/{g['id']}/feedback/{fb.json()['id']}", headers=teacher).status_code == 204

    cert = client.post(f"{API}/groups/{g['id']}/members/{lid}/certificate", json={"title": "Hoàn thành khoá Giao tiếp A2", "note": "Học kỳ 1"}, headers=teacher)
    assert cert.status_code == 200, cert.text
    cert = cert.json()
    assert cert["issuer_name"] == "Lớp 10A" and cert["recipient_name"] == "Hà" and cert["code"].startswith("AGEN-")
    again = client.post(f"{API}/groups/{g['id']}/members/{lid}/certificate", json={"title": "Hoàn thành khoá Giao tiếp A2"}, headers=teacher).json()
    assert again["code"] == cert["code"]              # idempotent
    # public verification needs no login
    v = client.get(f"{API}/certificates/verify/{cert['code'].lower()}")
    assert v.status_code == 200 and v.json()["title"] == "Hoàn thành khoá Giao tiếp A2"
    assert client.get(f"{API}/certificates/verify/AGEN-NOPE-NOPE").status_code == 404
    assert client.get(f"{API}/certificates", headers=hs).json()["certificates"][0]["code"] == cert["code"]


def test_track_certificate_claim(client, db_session):
    headers = _auth(client, "track10@example.com", name="Tú")
    lid = _learner_id(db_session, "track10@example.com")
    track = goal_tracks.list_tracks()[0]
    mine = client.get(f"{API}/certificates", headers=headers).json()
    assert mine["certificates"] == [] and next(t for t in mine["tracks"] if t["track_id"] == track["id"])["completed"] is False
    assert client.post(f"{API}/certificates/tracks/{track['id']}", headers=headers).status_code == 400
    assert client.post(f"{API}/certificates/tracks/nope", headers=headers).status_code == 400
    for code in goal_tracks.track_lesson_codes(track):
        db_session.add(GoalTrackProgress(learner_id=lid, track_id=track["id"], lesson_code=code, status="completed"))
    db_session.commit()
    r = client.post(f"{API}/certificates/tracks/{track['id']}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["issuer_name"] == "AI AGENT ENGLISH" and r.json()["details"]["level"]
    mine = client.get(f"{API}/certificates", headers=headers).json()
    assert next(t for t in mine["tracks"] if t["track_id"] == track["id"])["claimed_code"] == r.json()["code"]


# ── G10.4 Stripe ─────────────────────────────────────────────────────────────
@pytest.fixture()
def stripe_on(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")


def _sign(body: bytes, secret="whsec_test", ts=None):
    ts = ts or int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_stripe_prices_and_signature(stripe_on):
    assert payments.price_usd_for("premium", 1) == 499
    assert payments.price_usd_for("team", 12, 5) == 5 * payments.TEAM_PRICES_USD[12]
    assert payments.price_usd_for("team", 12, 1) is None and payments.price_usd_for("premium", 7) is None
    body = b'{"x":1}'
    assert payments.stripe_verify(body, _sign(body)) is True
    assert payments.stripe_verify(body, _sign(body, secret="wrong")) is False
    assert payments.stripe_verify(body + b" ", _sign(body)) is False
    assert payments.stripe_verify(body, _sign(body, ts=int(time.time()) - 3600)) is False     # replayed
    assert payments.stripe_verify(body, "") is False


def test_stripe_checkout_and_webhook(client, db_session, monkeypatch, stripe_on):
    headers = _auth(client, "card10@example.com")
    opts = client.get(f"{API}/billing/options", headers=headers).json()
    assert "stripe" in opts["providers"] and opts["prices_usd"][0]["amount_vnd"] == 499

    sent = {}

    class Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"id": "cs_test_123", "url": "https://checkout.stripe.com/c/pay/cs_test_123"}

    def fake_post(url, data=None, auth=None, timeout=None):
        sent.update(url=url, data=data, auth=auth)
        return Resp()
    monkeypatch.setattr(payments.httpx, "post", fake_post)

    r = client.post(f"{API}/billing/checkout", json={"provider": "stripe", "months": 1}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["pay_url"].startswith("https://checkout.stripe.com/")
    assert sent["url"].endswith("/checkout/sessions") and sent["data"]["line_items[0][price_data][unit_amount]"] == "499"
    order_id = r.json()["order_id"]
    order = client.get(f"{API}/billing/orders/{order_id}", headers=headers).json()
    assert order["currency"] == "USD" and order["amount_foreign"] == 499 and order["amount_vnd"] == 499 * settings.USD_TO_VND // 100

    def event(kind, amount=499, status="paid", currency="usd"):
        return json.dumps({"type": kind, "data": {"object": {"id": "cs_test_123", "client_reference_id": order_id, "metadata": {"order_id": order_id},
                                                             "payment_status": status, "amount_total": amount, "currency": currency, "payment_intent": "pi_1"}}}).encode()

    body = event("checkout.session.completed")
    assert client.post(f"{API}/billing/stripe/webhook", content=body, headers={"stripe-signature": _sign(body, secret="bad")}).status_code == 400
    pending = event("checkout.session.completed", status="unpaid")
    assert client.post(f"{API}/billing/stripe/webhook", content=pending, headers={"stripe-signature": _sign(pending)}).json()["result"] == "pending"
    res = client.post(f"{API}/billing/stripe/webhook", content=body, headers={"stripe-signature": _sign(body)})
    assert res.status_code == 200 and res.json()["result"] == "paid"
    assert client.post(f"{API}/billing/stripe/webhook", content=body, headers={"stripe-signature": _sign(body)}).json()["result"] == "already_paid"
    db_session.expire_all()
    user = db_session.query(User).filter(User.email == "card10@example.com").first()
    assert is_premium(db_session, user.id)

    # a tampered amount never credits
    r2 = client.post(f"{API}/billing/checkout", json={"provider": "stripe", "months": 12}, headers=headers).json()
    bad = json.dumps({"type": "checkout.session.completed", "data": {"object": {"metadata": {"order_id": r2["order_id"]}, "payment_status": "paid",
                                                                                "amount_total": 100, "currency": "usd"}}}).encode()
    assert client.post(f"{API}/billing/stripe/webhook", content=bad, headers={"stripe-signature": _sign(bad)}).json()["result"] == "amount_mismatch"
    db_session.expire_all()
    assert db_session.get(PaymentOrder, r2["order_id"]).status == "failed"


def test_stripe_off_without_keys(client, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "")
    headers = _auth(client, "nocard@example.com")
    assert "stripe" not in client.get(f"{API}/billing/options", headers=headers).json()["providers"]
    assert client.post(f"{API}/billing/checkout", json={"provider": "stripe", "months": 1}, headers=headers).status_code in (400, 503)
    assert client.post(f"{API}/billing/stripe/webhook", content=b"{}", headers={"stripe-signature": "t=1,v1=x"}).status_code == 400


# ── G10.5 AI cost tracking ───────────────────────────────────────────────────
def test_feature_from_path():
    assert feature_from_path("/api/v1/lessons/generate") == "lessons"
    assert feature_from_path("/health") == "health"


def test_llm_usage_recorded_and_daily_limit(db_session, usage_db, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "x")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(llm_client, "_call_gemini", lambda prompt: "y" * 400)
    t1, t2 = current_user_id.set("user-1"), current_feature.set("writing_evaluation")
    try:
        assert llm_client.get_llm_response("p" * 4000) == "y" * 400
        row = db_session.query(AiUsage).one()
        assert row.user_id == "user-1" and row.feature == "writing_evaluation" and row.provider == "gemini"
        assert row.input_chars == 4000 and row.output_chars == 400
        expected = (1000 * settings.AI_PRICE_GEMINI_IN + 100 * settings.AI_PRICE_GEMINI_OUT) / 1_000_000
        assert abs(row.cost_usd - expected) < 1e-9

        # limits off by default; once set, a user over the budget gets a quota error (callers fall back)
        assert ai_usage.over_daily_limit() is False
        monkeypatch.setattr(settings, "AI_DAILY_LIMIT_USD_FREE", expected / 2)
        with pytest.raises(llm_client.LLMError) as err:
            llm_client.get_llm_response("again")
        assert err.value.is_quota_error is True
        assert ai_usage.over_daily_limit("someone-else") is False
    finally:
        current_user_id.reset(t1)
        current_feature.reset(t2)


def test_tts_usage_recorded_only_on_cache_miss(db_session, usage_db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "openai", raising=False)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "x")
    monkeypatch.setattr(settings, "TTS_CACHE_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(tts_service, "providers", lambda: ["openai"])
    monkeypatch.setattr(tts_service, "_cache_dir", lambda: tmp_path)
    monkeypatch.setitem(tts_service._CALLERS, "openai", lambda text, voice: (b"ID3audio", "audio/mpeg"))
    assert tts_service.synthesize("Hello there, friend") is not None
    assert tts_service.synthesize("Hello there, friend").cached is True
    rows = db_session.query(AiUsage).all()
    assert len(rows) == 1 and rows[0].feature == "tts" and rows[0].input_chars == len("Hello there, friend")


def test_usage_attributed_to_user_and_agent_and_admin_summary(client, db_session, usage_db, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss10@example.com")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "x")
    monkeypatch.setattr(llm_client, "_call_gemini", lambda prompt: "answer text")

    def tutor(**kw):
        llm_client.get_llm_response("question prompt")
        return {"answer_vi": "Trả lời.", "rule": "r", "examples": [{"en": "I have been here.", "vi": "Tôi đã ở đây."}],
                "common_mistake": "", "follow_ups": [], "on_topic": True}
    _swap_agent(monkeypatch, "tutor_answer", tutor)
    headers = _auth(client, "ai10@example.com")
    r = client.post(f"{API}/tutor/ask", json={"question": "Khi nào dùng since?"}, headers=headers)
    assert r.status_code == 200, r.text
    user = db_session.query(User).filter(User.email == "ai10@example.com").first()
    db_session.expire_all()
    row = db_session.query(AiUsage).one()
    assert row.user_id == user.id and row.feature == "tutor_answer"

    admin = _auth(client, "boss10@example.com")
    assert client.get(f"{API}/admin/ai-usage/summary", headers=headers).status_code == 403
    s = client.get(f"{API}/admin/ai-usage/summary?days=7", headers=admin).json()
    assert s["calls"] == 1 and s["users_with_usage"] == 1 and s["today_usd"] > 0
    assert s["by_feature"][0]["key"] == "tutor_answer" and s["top_users"][0]["email"] == "ai10@example.com"
    assert s["by_day"] and s["by_provider"][0]["key"] == "gemini"
