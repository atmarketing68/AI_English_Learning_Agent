"""G5 · Gói gia đình, thống kê doanh thu, chấm band IELTS/TOEIC."""
import dataclasses
from datetime import datetime, timedelta

import pytest

from app.agents import orchestrator
from app.agents import writing_agent
from app.core.config import settings
from app.models.payment_order import PaymentOrder
from app.models.user import User
from app.services import payments
from app.services import subscription_service as subs

API = "/api/v1"


def _auth(client, email, role="learner", age=10):
    body = {"email": email, "password": "Strong123", "full_name": "U", "display_name": email.split("@")[0], "role": role}
    if role == "learner":
        body["age"] = age
    client.post(f"{API}/auth/register", json=body)
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _link(client, parent_headers, child_headers):
    code = client.get(f"{API}/learner/me", headers=child_headers).json()["invite_code"]
    res = client.post(f"{API}/parent/link-child", json={"invite_code": code, "relationship_label": "Mẹ"}, headers=parent_headers)
    assert res.status_code == 200, res.text


@pytest.fixture()
def demo(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_UPGRADE", True)
    monkeypatch.setattr(settings, "VNPAY_TMN_CODE", "")
    monkeypatch.setattr(settings, "MOMO_PARTNER_CODE", "")


# ── Gói gia đình ─────────────────────────────────────────────────────────────
def test_family_plan_covers_linked_children(client, demo):
    mom = _auth(client, "mom@example.com", role="parent")
    kid1 = _auth(client, "kid1@example.com")
    kid2 = _auth(client, "kid2@example.com")
    stranger = _auth(client, "stranger@example.com")
    _link(client, mom, kid1)

    opts = client.get(f"{API}/billing/options", headers=mom).json()
    assert opts["can_buy_family"] is True and {p["months"]: p["amount_vnd"] for p in opts["family_prices"]} == {1: 179000, 12: 1490000}
    assert client.get(f"{API}/billing/options", headers=kid1).json()["can_buy_family"] is False

    # Learners cannot buy the family plan; parents cannot buy the learner plan.
    assert client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "family"}, headers=kid1).status_code == 400
    assert client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "premium"}, headers=mom).status_code == 400

    res = client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "family"}, headers=mom)
    assert res.status_code == 200, res.text
    assert res.json()["plan"] == "family" and res.json()["is_premium"] is True and res.json()["premium_source"] == "own"

    sub1 = client.get(f"{API}/billing/subscription", headers=kid1).json()
    assert sub1["is_premium"] is True and sub1["premium_source"] == "family" and sub1["plan"] == "free"
    assert client.get(f"{API}/billing/quota", headers=kid1).json()["limit"] is None       # unlimited lessons
    assert client.get(f"{API}/billing/subscription", headers=stranger).json()["is_premium"] is False

    # A child linked later is covered too; unlinking removes it.
    _link(client, mom, kid2)
    assert client.get(f"{API}/billing/subscription", headers=kid2).json()["premium_source"] == "family"
    children = client.get(f"{API}/parent/children", headers=mom).json()
    assert {c["display_name"]: c["premium_source"] for c in children} == {"kid1": "family", "kid2": "family"}
    kid2_id = next(c["learner_id"] for c in children if c["display_name"] == "kid2")
    client.delete(f"{API}/parent/children/{kid2_id}", headers=mom)
    assert client.get(f"{API}/billing/subscription", headers=kid2).json()["is_premium"] is False


def test_expired_family_plan_no_longer_covers_children(client, db_session, demo):
    dad = _auth(client, "dad@example.com", role="parent")
    kid = _auth(client, "kid3@example.com")
    _link(client, dad, kid)
    client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "family"}, headers=dad)
    user = db_session.query(User).filter(User.email == "dad@example.com").one()
    sub = subs.get_or_create_subscription(db_session, user.id)
    sub.current_period_end = datetime.utcnow() - timedelta(days=1)
    db_session.commit()
    assert client.get(f"{API}/billing/subscription", headers=kid).json()["is_premium"] is False


def test_family_checkout_uses_family_price_and_label(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "VNPAY_TMN_CODE", "TMN123")
    monkeypatch.setattr(settings, "VNPAY_HASH_SECRET", "vnpaysecret")
    monkeypatch.setattr(settings, "API_PUBLIC_URL", "https://api.example.com")
    mom = _auth(client, "mom2@example.com", role="parent")
    res = client.post(f"{API}/billing/checkout", json={"months": 12, "provider": "vnpay", "plan": "family"}, headers=mom)
    assert res.status_code == 200, res.text
    order = db_session.query(PaymentOrder).filter(PaymentOrder.id == res.json()["order_id"]).one()
    assert order.plan == "family" and order.amount_vnd == 1_490_000
    assert "vnp_Amount=149000000" in res.json()["pay_url"] and "Gia+dinh" in res.json()["pay_url"]
    assert client.get(f"{API}/billing/orders/{order.id}", headers=mom).json()["plan"] == "family"
    # Paying credits a *family* subscription.
    payments.mark_paid(db_session, order, "TXN1", {})
    user = db_session.query(User).filter(User.email == "mom2@example.com").one()
    assert subs.get_or_create_subscription(db_session, user.id).plan == "family"


# ── Doanh thu ────────────────────────────────────────────────────────────────
def test_revenue_summary_counts_paid_orders_and_funnels(client, db_session, monkeypatch, demo):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss@example.com")
    boss = _auth(client, "boss@example.com", age=30)
    buyer = _auth(client, "buyer@example.com", age=25)
    buyer_user = db_session.query(User).filter(User.email == "buyer@example.com").one()
    client.post(f"{API}/billing/trial", headers=buyer)                      # trial first…
    paid = PaymentOrder(user_id=buyer_user.id, provider="vnpay", plan="premium", months=3, amount_vnd=249_000, status="paid", paid_at=datetime.utcnow())
    pending = PaymentOrder(user_id=buyer_user.id, provider="momo", plan="premium", months=1, amount_vnd=99_000, status="pending")
    db_session.add_all([paid, pending])
    db_session.commit()
    # …a guest who saved the account
    guest = client.post(f"{API}/auth/guest").json()
    client.post(f"{API}/auth/claim", json={"email": "saved@example.com", "password": "Strong123", "full_name": "S", "display_name": "S"}, headers={"Authorization": f"Bearer {guest['access_token']}"})
    client.post(f"{API}/auth/guest")                                        # one still a guest

    assert client.get(f"{API}/admin/revenue/summary", headers=buyer).status_code == 403
    body = client.get(f"{API}/admin/revenue/summary", headers=boss).json()
    assert body["total_vnd"] == 249_000 and body["paid_orders"] == 1 and body["pending_orders"] == 1
    assert body["by_month"][-1]["revenue_vnd"] == 249_000 and len(body["by_month"]) == 6
    assert body["by_provider"][0]["key"] == "vnpay" and body["by_plan"][0]["label"] == "Premium 3 tháng"
    assert body["trials_started"] == 1 and body["trials_converted"] == 1 and body["trial_conversion_pct"] == 100.0
    assert body["guests_now"] == 1 and body["guests_claimed"] == 1


# ── Band IELTS/TOEIC ─────────────────────────────────────────────────────────
EVAL = {
    "overall_score": 72.0, "grade": "B", "word_count": 260,
    "scores": {"grammar": 70, "vocabulary": 72, "coherence": 75, "task_achievement": 71},
    "grammar_errors": [], "vocabulary_feedback": "Tốt", "coherence_feedback": "Ổn",
    "strengths": ["Rõ ý"], "improvements": ["Thêm ví dụ"], "corrected_version": "…", "encouragement": "Cố lên",
    "exam_band": {"exam": "ielts", "overall": 6.0, "criteria": {"task_response": 6, "coherence_cohesion": 6, "lexical_resource": 5.5, "grammatical_range": 6}, "next_band_tips": ["Dùng câu phức hơn"]},
}


def test_exam_genre_prompt_uses_exam_topics(monkeypatch):
    captured = {}
    def fake_llm(prompt):
        captured["prompt"] = prompt
        return '{"title":"T","prompt":"P","genre":"ielts_task2","word_target":"250+ words","guide_steps":["a","b","c"],"useful_phrases":["x"],"example_opening":"E"}'
    monkeypatch.setattr(writing_agent, "get_llm_response", fake_llm)
    out = writing_agent.generate_writing_prompt.__wrapped__("B1", "ielts_task2") if hasattr(writing_agent.generate_writing_prompt, "__wrapped__") else writing_agent.generate_writing_prompt("B1", "ielts_task2")
    assert "IELTS" in captured["prompt"] and "250+" in captured["prompt"] and out["genre"] == "ielts_task2"
    assert "EXAM BAND" in writing_agent._exam_rubric("ielts_task1") and "TOEIC" in writing_agent._exam_rubric("toeic_email")
    assert writing_agent._exam_rubric("opinion") == ""


def test_submit_exam_writing_returns_band(client, monkeypatch):
    received = {}
    def handler(**kw):
        received.update(kw)
        return EVAL
    patched = dict(orchestrator.AGENT_SPECS)
    patched["writing_evaluation"] = dataclasses.replace(orchestrator.AGENT_SPECS["writing_evaluation"], handler=handler)
    monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)
    headers = _auth(client, "writer@example.com", age=22)
    res = client.post(f"{API}/writing/submit", json={"prompt_title": "T", "prompt_text": "P", "genre": "ielts_task2", "user_text": "word " * 60}, headers=headers)
    assert res.status_code == 200, res.text
    assert received["genre"] == "ielts_task2"
    assert res.json()["exam_band"]["overall"] == 6.0 and res.json()["exam_band"]["criteria"]["lexical_resource"] == 5.5

    # Non-exam genres carry no band even if the model returns one.
    res2 = client.post(f"{API}/writing/submit", json={"prompt_title": "T", "prompt_text": "P", "genre": "opinion", "user_text": "word " * 20}, headers=headers)
    assert res2.status_code == 200 and res2.json()["exam_band"] is None
    assert received["genre"] == "opinion"
