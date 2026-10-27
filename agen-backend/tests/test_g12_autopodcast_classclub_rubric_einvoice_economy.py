"""G12 · Podcast tự động, câu lạc bộ nói hằng tuần của lớp, rubric IELTS, hoá đơn điện tử Viettel, chế độ tiết kiệm AI."""
import dataclasses
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import sessionmaker

from app.agents import orchestrator
from app.core.config import settings
from app.core.timeutil import LEARNER_TZ
from app.models.ai_usage import AiUsage
from app.models.generated_episode import GeneratedEpisode
from app.models.learner_profile import LearnerProfile
from app.models.notification import Notification
from app.models.payment_order import PaymentOrder
from app.models.speaking_club import GroupClubSchedule, SpeakingRoom
from app.models.user import User
from app.models.writing import WritingSubmission
from app.services import ai_usage, einvoice, llm_client, podcast_generator, speaking_club
from app.services.groups import ielts_overall

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


EPISODE = {
    "title": "A day at the market", "title_vi": "Một ngày ở chợ", "description_vi": "Hội thoại mua bán ở chợ.", "topic": "Đời sống",
    "lines": [{"speaker": "Lan", "text": t, "vi": "…"} for t in (
        "How much are these mangoes?", "Thirty thousand a kilo.", "Can I have two kilos, please?", "Sure, anything else?",
        "Some herbs for the soup.", "Here you are. Sixty-five thousand altogether.")],
    "vocab": [{"word": "mangoes", "definition": "xoài"}, {"word": "herbs", "definition": "rau thơm"}, {"word": "altogether", "definition": "tổng cộng"}],
    "questions": [
        {"prompt": "What does Lan buy first?", "options": ["mangoes", "apples", "fish"], "answer": 0, "explanation_vi": "\"these mangoes\""},
        {"prompt": "How many kilos?", "options": ["one", "two", "three"], "answer": 1, "explanation_vi": "\"two kilos\""},
        {"prompt": "What is the total?", "options": ["30,000", "60,000", "65,000"], "answer": 2, "explanation_vi": "\"Sixty-five thousand\""},
    ],
}


# ── G12.1 Scheduled podcast drafts ───────────────────────────────────────────
def test_auto_podcast_drafts_top_up_queue(db_session, monkeypatch):
    calls = []
    _swap_agent(monkeypatch, "podcast_generation", lambda **kw: calls.append(kw) or EPISODE)
    assert podcast_generator.run_auto_drafts(db_session) == {"enabled": False, "created": [], "errors": 0}

    monkeypatch.setattr(settings, "PODCAST_AUTO_DRAFTS", 1)
    monkeypatch.setattr(settings, "PODCAST_AUTO_LEVELS", "A2,B1")
    first = podcast_generator.run_auto_drafts(db_session)
    assert len(first["created"]) == 1 and first["created"][0]["level"] == "A2"          # one per run
    assert calls[0]["topic"] in podcast_generator.AUTO_TOPICS
    second = podcast_generator.run_auto_drafts(db_session)
    assert second["created"][0]["level"] == "B1"                                         # A2 already has its draft
    assert podcast_generator.run_auto_drafts(db_session)["created"] == []                # queue full
    rows = db_session.query(GeneratedEpisode).all()
    assert len(rows) == 2 and all(r.auto and r.status == "draft" for r in rows)

    # approving frees the slot, but the 20-hour spacing still holds until tomorrow
    rows[0].status = "approved"
    db_session.commit()
    assert podcast_generator.run_auto_drafts(db_session)["created"] == []
    later = _now() + timedelta(hours=21)
    assert podcast_generator.run_auto_drafts(db_session, now=later)["created"][0]["level"] == rows[0].level

    # an AI failure is counted, never raised
    _swap_agent(monkeypatch, "podcast_generation", lambda **kw: (_ for _ in ()).throw(RuntimeError("down")))
    db_session.query(GeneratedEpisode).update({"status": "approved"})
    db_session.commit()
    out = podcast_generator.run_auto_drafts(db_session, now=_now() + timedelta(days=3))
    assert out["created"] == [] and out["errors"] == 1


def test_content_cron_runs_podcast_hook(client, monkeypatch):
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "cron12")
    monkeypatch.setattr("app.services.curriculum_content_service.generate_missing_content", lambda db, limit=3: {"generated": 0})
    r = client.post(f"{API}/admin/content/cron", headers={"X-Cron-Secret": "cron12"})
    assert r.status_code == 200, r.text
    assert r.json()["podcasts"]["enabled"] is False


# ── G12.2 Weekly class speaking-club sessions ────────────────────────────────
def test_next_occurrence_is_in_vietnam_time():
    sch = GroupClubSchedule(group_id="g", weekday=2, time_local="19:30")       # Wednesday 19:30 VN
    monday_noon_vn = datetime(2026, 10, 26, 12, 0, tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)
    nxt = speaking_club.next_occurrence(sch, monday_noon_vn)
    assert nxt == datetime(2026, 10, 28, 12, 30)                                    # 19:30 VN = 12:30 UTC
    just_before = datetime(2026, 10, 28, 19, 20, tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)
    assert speaking_club.next_occurrence(sch, just_before) == datetime(2026, 11, 4, 12, 30)   # too close → next week
    with pytest.raises(speaking_club.ClubError):
        speaking_club.parse_time("25:00")


def test_class_club_schedule_flow(client, db_session, monkeypatch):
    _swap_agent(monkeypatch, "club_moderator", lambda **kw: {"feedback_vi": "Tốt.", "corrected": "", "reply": "Next!"})
    teacher = _auth(client, "co12@example.com", role="teacher", name="Cô Lan")
    an = _auth(client, "an12@example.com", name="An")
    binh = _auth(client, "binh12@example.com", name="Bình")
    outsider = _auth(client, "out12@example.com", name="Ngoài")
    g = client.post(f"{API}/groups", json={"name": "Lớp 12A", "kind": "class"}, headers=teacher).json()
    for h in (an, binh):
        client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=h)

    assert client.post(f"{API}/groups/{g['id']}/club-schedules", json={"weekday": 2, "time": "19:30"}, headers=an).status_code == 403
    assert client.post(f"{API}/groups/{g['id']}/club-schedules", json={"weekday": 2, "time": "19:30", "topic_id": "nope"}, headers=teacher).status_code == 400
    r = client.post(f"{API}/groups/{g['id']}/club-schedules", json={"weekday": 2, "time": "19:30", "topic_id": "travel"}, headers=teacher)
    assert r.status_code == 200, r.text
    sch = r.json()
    assert sch["label"] == "Thứ Tư 19:30" and sch["next"]["registered"] == 0 and sch["next"]["topic_title"] == "Chuyện du lịch"
    listing = client.get(f"{API}/groups/{g['id']}/club-schedules", headers=teacher).json()
    assert len(listing["schedules"]) == 1 and len(listing["topics"]) >= 6 and listing["weekdays"][0] == "Thứ Hai"
    an_lid = _learner_id(db_session, "an12@example.com")
    assert db_session.query(Notification).filter(Notification.learner_id == an_lid, Notification.type == "club_scheduled").count() == 1

    # classmates see it under "upcoming"; outsiders neither see nor join it
    lobby = client.get(f"{API}/club", headers=an).json()
    card = next(c for c in lobby["upcoming_rooms"] if c["id"] == sch["next"]["room_id"])
    assert card["group_name"] == "Lớp 12A" and card["host_name"] == "Lớp 12A" and card["registered"] is False
    assert all(c["id"] != card["id"] for c in client.get(f"{API}/club", headers=outsider).json()["upcoming_rooms"])
    assert client.post(f"{API}/club/rooms/join", json={"code": card["code"]}, headers=outsider).status_code == 400

    # first to register hosts it; when everyone leaves before the start the room stays open for the class
    st = client.post(f"{API}/club/rooms/join", json={"code": card["code"]}, headers=an).json()
    assert st["is_host"] is True
    client.post(f"{API}/club/rooms/{card['id']}/leave", headers=an)
    db_session.expire_all()
    room = db_session.query(SpeakingRoom).filter(SpeakingRoom.id == card["id"]).first()
    assert room.status == "waiting" and room.host_learner_id is None
    client.post(f"{API}/club/rooms/join", json={"code": card["code"]}, headers=binh)
    assert client.get(f"{API}/groups/{g['id']}/club-schedules", headers=teacher).json()["schedules"][0]["next"]["registered"] == 1

    # reminder: registered member individually + the rest of the class once
    db_session.expire_all()
    room = db_session.query(SpeakingRoom).filter(SpeakingRoom.id == card["id"]).first()
    stats = speaking_club.run_reminders(db_session, now=room.scheduled_at - timedelta(minutes=15))
    assert stats["reminded"] == 1 and stats["class_reminded"] == 1
    assert speaking_club.run_reminders(db_session, now=room.scheduled_at - timedelta(minutes=8))["class_reminded"] == 0

    # the scheduler does not duplicate rooms; cancelling closes the waiting one
    assert speaking_club.ensure_group_rooms(db_session) == 0
    assert client.delete(f"{API}/groups/{g['id']}/club-schedules/{sch['id']}", headers=teacher).status_code == 204
    db_session.expire_all()
    assert db_session.query(SpeakingRoom).filter(SpeakingRoom.id == card["id"]).first().status == "finished"
    assert client.get(f"{API}/groups/{g['id']}/club-schedules", headers=teacher).json()["schedules"] == []


# ── G12.3 IELTS rubric ───────────────────────────────────────────────────────
def test_ielts_rounding():
    assert ielts_overall([6, 6, 6, 6.5]) == 6.0          # 6.125
    assert ielts_overall([6, 6.5, 6, 6.5]) == 6.5        # 6.25 → 6.5
    assert ielts_overall([6.5, 7, 7, 7]) == 7.0          # 6.875 → 7
    assert ielts_overall([6.5, 6.5, 6.5, 7]) == 6.5      # 6.625
    assert ielts_overall([7, 7, 7, 6.5]) == 7.0          # 6.875
    assert ielts_overall([5.5, 6, 6, 6]) == 6.0          # 5.875 → 6


def test_teacher_rubric_grade(client, db_session):
    teacher = _auth(client, "co12b@example.com", role="teacher", name="Thầy Nam")
    hs = _auth(client, "hs12@example.com", name="Hà")
    g = client.post(f"{API}/groups", json={"name": "IELTS 12", "kind": "class"}, headers=teacher).json()
    client.post(f"{API}/groups/join", json={"code": g["code"]}, headers=hs)
    lid = _learner_id(db_session, "hs12@example.com")
    w = WritingSubmission(learner_id=lid, prompt_title="Traffic", prompt_text="Discuss…", genre="ielts_task2", level="B2",
                          user_text="Traffic is a problem. " * 30, word_count=90, overall_score=60.0, grade="B", evaluation={})
    letter = WritingSubmission(learner_id=lid, prompt_title="Email", prompt_text="Reply…", genre="toeic_email", level="B1",
                               user_text="Dear Sir,", word_count=3, overall_score=55.0, grade="C", evaluation={})
    db_session.add_all([w, letter])
    db_session.commit()
    url = f"{API}/groups/{g['id']}/members/{lid}/writing"

    bad = {"rubric": {"task": 6, "coherence": 6.3, "lexical": 6, "grammar": 6}}
    assert client.post(f"{url}/{w.id}/grade", json=bad, headers=teacher).status_code == 400
    assert client.post(f"{url}/{w.id}/grade", json={"rubric": {"task": 6}}, headers=teacher).status_code == 400
    assert client.post(f"{url}/{letter.id}/grade", json={"rubric": {"task": 6, "coherence": 6, "lexical": 6, "grammar": 6}}, headers=teacher).status_code == 400

    r = client.post(f"{url}/{w.id}/grade", json={"rubric": {"task": 6, "coherence": 6.5, "lexical": 6, "grammar": 6.5}, "comment": "Tốt"}, headers=teacher)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["teacher_band"] == 6.5 and body["teacher_score"] == round(6.5 / 9 * 100) and body["teacher_rubric"]["coherence"] == 6.5
    hist = next(x for x in client.get(f"{API}/writing/history", headers=hs).json() if x["id"] == w.id)
    assert hist["teacher_rubric"] == {"task": 6.0, "coherence": 6.5, "lexical": 6.0, "grammar": 6.5}
    detail = client.get(f"{API}/groups/{g['id']}/members/{lid}", headers=teacher).json()
    assert any("Mạch lạc & liên kết 6.5" in f["text"] for f in detail["feedback"])
    # a plain score afterwards drops the rubric
    plain = client.post(f"{url}/{w.id}/grade", json={"score": 70, "band": 6}, headers=teacher).json()
    assert plain["teacher_rubric"] is None and plain["teacher_band"] == 6


# ── G12.4 Viettel S-Invoice ──────────────────────────────────────────────────
@pytest.fixture()
def viettel_on(monkeypatch):
    for k, v in {"EINVOICE_PROVIDER": "viettel", "VIETTEL_SINVOICE_USERNAME": "0312345678", "VIETTEL_SINVOICE_PASSWORD": "pw",
                 "VIETTEL_SINVOICE_TAX_CODE": "0312345678", "VIETTEL_SINVOICE_TEMPLATE_CODE": "1/001", "VIETTEL_SINVOICE_SERIES": "C26TAA",
                 "EINVOICE_TAX_PERCENT": 8}.items():
        monkeypatch.setattr(settings, k, v)
    einvoice._token.update(value=None, expires=0)


class _Resp:
    def __init__(self, data, status=200):
        self._d, self.status_code = data, status

    def json(self):
        return self._d


def test_split_and_payload():
    assert einvoice.split_amount(108_000, 8) == (100_000, 8_000)
    assert einvoice.split_amount(99_000, -2) == (99_000, 0)
    order = PaymentOrder(id="o1", user_id="u", provider="vnpay", plan="team", months=12, seats=10, amount_vnd=6_900_000, status="paid",
                         invoice_info={"company_name": "Công ty ABC", "tax_code": "0101234567", "address": "Hà Nội", "email": "kt@abc.vn"})
    p = einvoice.build_payload(order, User(full_name="Nguyễn Văn A", email="a@abc.vn"), "txn-1", datetime(2026, 10, 27, 1, 0))
    assert p["generalInvoiceInfo"]["transactionUuid"] == "txn-1" and p["generalInvoiceInfo"]["invoiceIssuedDate"] == 1793062800000
    assert p["buyerInfo"]["buyerLegalName"] == "Công ty ABC" and p["buyerInfo"]["buyerTaxCode"] == "0101234567" and p["buyerInfo"]["buyerEmail"] == "kt@abc.vn"
    item = p["itemInfo"][0]
    assert "10 ghế" in item["itemName"] and item["itemTotalAmountWithTax"] == 6_900_000
    assert p["taxBreakdowns"][0]["taxableAmount"] + p["taxBreakdowns"][0]["taxAmount"] == 6_900_000


def test_issue_einvoice_admin_receipt_and_auto(client, db_session, monkeypatch, viettel_on):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "acc12@example.com")
    admin = _auth(client, "acc12@example.com")
    buyer = _auth(client, "buy12@example.com", name="Khách")
    uid = _user(db_session, "buy12@example.com").id
    o = PaymentOrder(user_id=uid, provider="vnpay", plan="premium", months=12, amount_vnd=799_000, status="paid", paid_at=_now(),
                     invoice_info={"company_name": "Công ty XYZ", "tax_code": "0109999999", "address": "12 Lê Lợi, Quận 1, TP.HCM", "email": "kt@xyz.vn"})
    pending = PaymentOrder(user_id=uid, provider="vnpay", plan="premium", months=1, amount_vnd=99_000, status="pending")
    db_session.add_all([o, pending])
    db_session.commit()

    calls = []

    def fake_post(url, json=None, cookies=None, timeout=None):
        calls.append((url, json, cookies))
        if url.endswith("/auth/login"):
            return _Resp({"access_token": "tok", "expires_in": 3600})
        if len([c for c in calls if "createInvoice" in c[0]]) == 1:
            return _Resp({"code": 400, "data": "Ký hiệu không hợp lệ"}, 400)
        return _Resp({"errorCode": None, "description": None, "result": {"supplierTaxCode": "0312345678", "invoiceNo": "C26TAA12", "reservationCode": "XYZ789"}})
    monkeypatch.setattr(einvoice.httpx, "post", fake_post)

    assert client.get(f"{API}/admin/einvoice/status", headers=admin).json()["enabled"] is True
    assert client.post(f"{API}/admin/revenue/orders/{pending.id}/einvoice", headers=admin).status_code == 400
    first = client.post(f"{API}/admin/revenue/orders/{o.id}/einvoice", headers=admin)
    assert first.status_code == 400 and "Ký hiệu không hợp lệ" in first.json()["detail"]
    db_session.expire_all()
    txn = db_session.get(PaymentOrder, o.id).einvoice_txn
    assert txn and db_session.get(PaymentOrder, o.id).einvoice_error

    ok = client.post(f"{API}/admin/revenue/orders/{o.id}/einvoice", headers=admin)
    assert ok.status_code == 200, ok.text
    assert ok.json()["einvoice_no"] == "C26TAA12" and ok.json()["einvoice_lookup_code"] == "XYZ789" and ok.json()["einvoice_error"] is None
    create_calls = [c for c in calls if "createInvoice" in c[0]]
    assert create_calls[0][0].endswith("/InvoiceAPI/InvoiceWS/createInvoice/0312345678") and create_calls[0][2] == {"access_token": "tok"}
    assert create_calls[0][1]["generalInvoiceInfo"]["transactionUuid"] == create_calls[1][1]["generalInvoiceInfo"]["transactionUuid"] == txn
    assert len([c for c in calls if c[0].endswith("/auth/login")]) == 1                 # token cached
    assert client.post(f"{API}/admin/revenue/orders/{o.id}/einvoice", headers=admin).status_code == 400   # once only

    rec = client.get(f"{API}/billing/orders/{o.id}/receipt", headers=buyer).json()
    assert rec["einvoice"]["number"] == "C26TAA12" and rec["einvoice"]["lookup_code"] == "XYZ789"

    # auto mode: only orders that asked for a VAT invoice ("business"), paid in the last 3 days, not demo
    o2 = PaymentOrder(user_id=uid, provider="momo", plan="premium", months=1, amount_vnd=99_000, status="paid", paid_at=_now(),
                      invoice_info={"company_name": "B", "tax_code": "1", "address": "1 Trần Phú, Hà Nội", "email": "b@b.vn"})
    o3 = PaymentOrder(user_id=uid, provider="momo", plan="premium", months=1, amount_vnd=99_000, status="paid", paid_at=_now())
    db_session.add_all([o2, o3])
    db_session.commit()
    assert einvoice.run_auto(db_session) == {"enabled": False}
    monkeypatch.setattr(settings, "EINVOICE_AUTO", "business")
    out = einvoice.run_auto(db_session)
    assert out == {"enabled": True, "issued": 1, "failed": 0}
    db_session.expire_all()
    assert db_session.get(PaymentOrder, o2.id).einvoice_no and db_session.get(PaymentOrder, o3.id).einvoice_no is None


def test_einvoice_off_without_config(client, monkeypatch):
    monkeypatch.setattr(settings, "EINVOICE_PROVIDER", "")
    assert einvoice.enabled() is False
    with pytest.raises(einvoice.EInvoiceError):
        einvoice.issue(None, PaymentOrder(status="paid"))


# ── G12.5 Economy mode ───────────────────────────────────────────────────────
def test_economy_mode_switches_model_and_falls_back(db_engine, db_session, monkeypatch):
    monkeypatch.setattr(ai_usage, "_session_factory", sessionmaker(autocommit=False, autoflush=False, bind=db_engine))
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "x")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    used = []

    def fake_gemini(prompt, model=None):
        used.append(model)
        if model == "broken-cheap":
            raise RuntimeError("model not found")
        return "ok"
    monkeypatch.setattr(llm_client, "_call_gemini", fake_gemini)
    monkeypatch.setattr(llm_client.time, "sleep", lambda s: None)

    assert ai_usage.economy_active(force_refresh=True) is False
    llm_client.get_llm_response("hello")
    assert used == [None]                                        # normal model: one-argument call

    monkeypatch.setattr(settings, "AI_ECONOMY_AT_USD", 1.0)
    monkeypatch.setattr(settings, "AI_ECONOMY_GEMINI_MODEL", "gemini-cheap")
    db_session.add(AiUsage(user_id=None, feature="lesson", provider="gemini", cost_usd=1.5, created_at=_now()))
    db_session.commit()
    assert ai_usage.economy_active(force_refresh=True) is True
    llm_client.get_llm_response("hello again")
    assert used[-1] == "gemini-cheap"
    row = db_session.query(AiUsage).filter(AiUsage.model == "gemini-cheap").first()
    assert row is not None

    # a wrong economy model name never breaks learning: it retries on the normal model
    monkeypatch.setattr(settings, "AI_ECONOMY_GEMINI_MODEL", "broken-cheap")
    assert llm_client.get_llm_response("third") == "ok"
    assert used[-2:] == ["broken-cheap", None]

    state = ai_usage.economy_state(db_session)
    assert state["active"] is True and state["models"]["gemini"]["economy"] == "broken-cheap"
