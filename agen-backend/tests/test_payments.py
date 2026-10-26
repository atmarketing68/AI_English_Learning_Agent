"""G3 · Thanh toán thật (VNPay / MoMo signatures + callbacks) và dùng thử 7 ngày."""
import hashlib
import hmac
from urllib.parse import parse_qs, quote_plus, urlparse

import pytest

from app.core.config import settings
from app.models.payment_order import PaymentOrder
from app.services import payments
from app.services import subscription_service as subs

API = "/api/v1"


def _auth(client, email):
    client.post(f"{API}/auth/register", json={"email": email, "password": "Strong123", "full_name": "P", "display_name": "P", "role": "learner", "age": 20})
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def gateways(monkeypatch):
    monkeypatch.setattr(settings, "VNPAY_TMN_CODE", "TMN123")
    monkeypatch.setattr(settings, "VNPAY_HASH_SECRET", "vnpaysecret")
    monkeypatch.setattr(settings, "MOMO_PARTNER_CODE", "MOMOTEST")
    monkeypatch.setattr(settings, "MOMO_ACCESS_KEY", "accesskey")
    monkeypatch.setattr(settings, "MOMO_SECRET_KEY", "momosecret")
    monkeypatch.setattr(settings, "APP_URL", "https://app.example.com")
    monkeypatch.setattr(settings, "API_PUBLIC_URL", "https://api.example.com")
    monkeypatch.setattr(settings, "ALLOW_DEMO_UPGRADE", False)


def _vnpay_sign(params: dict) -> str:
    data = "&".join(f"{k}={quote_plus(str(v))}" for k, v in sorted(params.items()) if v)
    return hmac.new(b"vnpaysecret", data.encode(), hashlib.sha512).hexdigest()


# ── Options / availability ───────────────────────────────────────────────────
def test_options_without_gateways_offers_trial_and_demo(client, monkeypatch):
    monkeypatch.setattr(settings, "VNPAY_TMN_CODE", "")
    monkeypatch.setattr(settings, "MOMO_PARTNER_CODE", "")
    headers = _auth(client, "pay0@example.com")
    body = client.get(f"{API}/billing/options", headers=headers).json()
    assert body["providers"] == [] and body["trial_available"] is True and body["trial_days"] == 7
    assert {p["months"]: p["amount_vnd"] for p in body["prices"]} == {1: 99000, 3: 249000, 12: 799000}
    assert client.post(f"{API}/billing/checkout", json={"months": 1, "provider": "vnpay"}, headers=headers).status_code == 503


def test_trial_once_then_premium_for_seven_days(client, monkeypatch):
    headers = _auth(client, "pay1@example.com")
    resp = client.post(f"{API}/billing/trial", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_premium"] is True and resp.json()["provider"] == "trial"
    assert client.get(f"{API}/billing/options", headers=headers).json()["trial_available"] is False
    again = client.post(f"{API}/billing/trial", headers=headers)
    assert again.status_code == 400
    # Guests must save the account first.
    guest = client.post(f"{API}/auth/guest").json()
    assert client.post(f"{API}/billing/trial", headers={"Authorization": f"Bearer {guest['access_token']}"}).status_code == 403


# ── VNPay ────────────────────────────────────────────────────────────────────
def test_vnpay_checkout_builds_signed_url(client, gateways):
    headers = _auth(client, "pay2@example.com")
    resp = client.post(f"{API}/billing/checkout", json={"months": 3, "provider": "vnpay"}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    url = urlparse(body["pay_url"])
    q = {k: v[0] for k, v in parse_qs(url.query).items()}
    assert url.netloc == "sandbox.vnpayment.vn"
    assert q["vnp_TmnCode"] == "TMN123" and q["vnp_Amount"] == str(249000 * 100) and q["vnp_TxnRef"] == body["order_id"]
    assert q["vnp_ReturnUrl"] == "https://api.example.com/api/v1/billing/vnpay/return"
    signed = {k: v for k, v in q.items() if k.startswith("vnp_") and k not in ("vnp_SecureHash", "vnp_SecureHashType")}
    assert q["vnp_SecureHash"] == _vnpay_sign(signed)
    order = client.get(f"{API}/billing/orders/{body['order_id']}", headers=headers).json()
    assert order["status"] == "pending" and order["months"] == 3


def test_vnpay_ipn_credits_once_and_rejects_bad_signature(client, gateways, db_session):
    headers = _auth(client, "pay3@example.com")
    order_id = client.post(f"{API}/billing/checkout", json={"months": 1, "provider": "vnpay"}, headers=headers).json()["order_id"]
    params = {
        "vnp_TmnCode": "TMN123", "vnp_Amount": "9900000", "vnp_TxnRef": order_id, "vnp_ResponseCode": "00",
        "vnp_TransactionStatus": "00", "vnp_TransactionNo": "14567890", "vnp_BankCode": "NCB", "vnp_PayDate": "20261026120000",
    }
    bad = client.get(f"{API}/billing/vnpay/ipn", params={**params, "vnp_SecureHash": "deadbeef"})
    assert bad.json()["RspCode"] == "97"
    assert client.get(f"{API}/billing/subscription", headers=headers).json()["is_premium"] is False

    good = client.get(f"{API}/billing/vnpay/ipn", params={**params, "vnp_SecureHash": _vnpay_sign(params)})
    assert good.json()["RspCode"] == "00", good.text
    sub = client.get(f"{API}/billing/subscription", headers=headers).json()
    assert sub["is_premium"] is True and sub["provider"] == "vnpay"
    assert client.get(f"{API}/billing/orders/{order_id}", headers=headers).json()["status"] == "paid"

    # Replayed IPN: acknowledged, not credited twice.
    again = client.get(f"{API}/billing/vnpay/ipn", params={**params, "vnp_SecureHash": _vnpay_sign(params)})
    assert again.json()["RspCode"] == "02"
    wrong_amount = {**params, "vnp_Amount": "100", "vnp_TxnRef": order_id}
    assert client.get(f"{API}/billing/vnpay/ipn", params={**wrong_amount, "vnp_SecureHash": _vnpay_sign(wrong_amount)}).json()["RspCode"] == "04"


def test_vnpay_return_redirects_to_app(client, gateways):
    headers = _auth(client, "pay4@example.com")
    order_id = client.post(f"{API}/billing/checkout", json={"months": 1, "provider": "vnpay"}, headers=headers).json()["order_id"]
    params = {"vnp_TmnCode": "TMN123", "vnp_Amount": "9900000", "vnp_TxnRef": order_id, "vnp_ResponseCode": "24", "vnp_TransactionStatus": "02"}
    resp = client.get(f"{API}/billing/vnpay/return", params={**params, "vnp_SecureHash": _vnpay_sign(params)}, follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == f"https://app.example.com/upgrade?status=failed&order={order_id}"
    assert client.get(f"{API}/billing/orders/{order_id}", headers=headers).json()["status"] == "failed"


# ── MoMo ─────────────────────────────────────────────────────────────────────
def test_momo_checkout_signs_request_and_returns_pay_url(client, gateways, monkeypatch):
    captured = {}

    class FakeRes:
        def json(self):
            return {"resultCode": 0, "payUrl": "https://test-payment.momo.vn/pay/abc"}

    def fake_post(url, json=None, timeout=None):
        captured["url"], captured["body"] = url, json
        return FakeRes()
    monkeypatch.setattr(payments.httpx, "post", fake_post)

    headers = _auth(client, "pay5@example.com")
    resp = client.post(f"{API}/billing/checkout", json={"months": 12, "provider": "momo"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["pay_url"] == "https://test-payment.momo.vn/pay/abc"
    body = captured["body"]
    assert captured["url"] == "https://test-payment.momo.vn/v2/gateway/api/create"
    assert body["amount"] == 799000 and body["ipnUrl"] == "https://api.example.com/api/v1/billing/momo/ipn"
    raw = (
        f"accessKey=accesskey&amount=799000&extraData=&ipnUrl={body['ipnUrl']}&orderId={body['orderId']}"
        f"&orderInfo={body['orderInfo']}&partnerCode=MOMOTEST&redirectUrl={body['redirectUrl']}"
        f"&requestId={body['requestId']}&requestType=captureWallet"
    )
    assert body["signature"] == hmac.new(b"momosecret", raw.encode(), hashlib.sha256).hexdigest()


def test_momo_ipn_credits_with_valid_signature(client, gateways, db_session):
    headers = _auth(client, "pay6@example.com")
    user_id = client.get(f"{API}/auth/me", headers=headers).json()["id"]
    order = PaymentOrder(user_id=user_id, provider="momo", months=1, amount_vnd=99000)
    db_session.add(order)
    db_session.commit()
    payload = {
        "partnerCode": "MOMOTEST", "orderId": order.id, "requestId": order.id, "amount": 99000,
        "orderInfo": "AGEN Premium 1 thang", "orderType": "momo_wallet", "transId": 123456789,
        "resultCode": 0, "message": "Successful.", "payType": "qr", "responseTime": 1700000000000, "extraData": "",
    }
    raw = "&".join(f"{k}={payload.get(k, '') if k != 'accessKey' else 'accesskey'}" for k in (
        "accessKey", "amount", "extraData", "message", "orderId", "orderInfo", "orderType",
        "partnerCode", "payType", "requestId", "responseTime", "resultCode", "transId",
    ))
    bad = client.post(f"{API}/billing/momo/ipn", json={**payload, "signature": "nope"})
    assert bad.status_code == 204
    assert client.get(f"{API}/billing/subscription", headers=headers).json()["is_premium"] is False
    good = client.post(f"{API}/billing/momo/ipn", json={**payload, "signature": hmac.new(b"momosecret", raw.encode(), hashlib.sha256).hexdigest()})
    assert good.status_code == 204
    sub = client.get(f"{API}/billing/subscription", headers=headers).json()
    assert sub["is_premium"] is True and sub["provider"] == "momo"
    assert client.get(f"{API}/billing/orders/{order.id}", headers=headers).json()["status"] == "paid"


def test_mark_paid_is_idempotent(db_session, gateways):
    from app.models.user import User
    user = User(email="idem@example.com", hashed_password="x")
    db_session.add(user)
    db_session.flush()
    order = payments.create_order(db_session, user.id, "vnpay", 1)
    assert payments.mark_paid(db_session, order, "t1", {}) is True
    end1 = subs.get_or_create_subscription(db_session, user.id).current_period_end
    assert payments.mark_paid(db_session, order, "t1", {}) is False
    assert subs.get_or_create_subscription(db_session, user.id).current_period_end == end1
