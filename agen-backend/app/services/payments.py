"""
G3 · Thanh toán thật: VNPay (thẻ nội địa/QR/thẻ quốc tế) và MoMo (ví), cùng gói
dùng thử Premium 7 ngày.

Each gateway is on only when its merchant credentials are set; the mock
upgrade (ALLOW_DEMO_UPGRADE) stays for the pilot. Money is only credited from
the gateway's server-to-server IPN after the signature is verified, never from
the browser redirect.

VNPay: https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html
  - pay URL = sorted params, URL-encoded, HMAC-SHA512(secret) as vnp_SecureHash
  - IPN/return: same params back; verify hash; vnp_ResponseCode "00" = paid
MoMo (v2 captureWallet): https://developers.momo.vn/v3/docs/payment/api/wallet/onetime
  - create: HMAC-SHA256 over the documented key=value&… string (alphabetical)
  - IPN: JSON body with signature over its own documented field order
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment_order import STATUS_FAILED, STATUS_PAID, STATUS_PENDING, PaymentOrder
from app.models.subscription import PLAN_FAMILY, PLAN_PREMIUM, PLAN_TEAM, Subscription
from app.services import subscription_service as subs

logger = logging.getLogger("agen.payments")

# Price list (VND) — mirrors the upgrade page.
PRICES_VND: dict[int, int] = {1: 99_000, 3: 249_000, 12: 799_000}
# G5 · Gói gia đình: one parent pays, up to FAMILY_MAX_CHILDREN linked children are Premium.
FAMILY_PRICES_VND: dict[int, int] = {1: 179_000, 12: 1_490_000}
FAMILY_MAX_CHILDREN = 4
# G7 · Gói doanh nghiệp / lớp học: per seat; group members of the owner are Premium.
TEAM_PRICES_VND: dict[int, int] = {1: 79_000, 12: 690_000}
TEAM_MIN_SEATS = 5
TEAM_MAX_SEATS = 500
TRIAL_DAYS = 7
# G10 · Stripe (international cards), USD cents. Team prices are per seat.
PRICES_USD: dict[int, int] = {1: 499, 3: 1199, 12: 3900}
FAMILY_PRICES_USD: dict[int, int] = {1: 899, 12: 7400}
TEAM_PRICES_USD: dict[int, int] = {1: 399, 12: 3400}
STRIPE_API = "https://api.stripe.com/v1"
STRIPE_SIGNATURE_TOLERANCE_S = 300


def price_for(plan: str, months: int, seats: int = 1) -> int | None:
    if plan == PLAN_TEAM:
        unit = TEAM_PRICES_VND.get(months)
        if unit is None or not (TEAM_MIN_SEATS <= seats <= TEAM_MAX_SEATS):
            return None
        return unit * seats
    table = FAMILY_PRICES_VND if plan == PLAN_FAMILY else PRICES_VND
    return table.get(months)


def price_usd_for(plan: str, months: int, seats: int = 1) -> int | None:
    """USD cents for a Stripe order, None when the plan/months/seats combination is not sold."""
    if plan == PLAN_TEAM:
        unit = TEAM_PRICES_USD.get(months)
        if unit is None or not (TEAM_MIN_SEATS <= seats <= TEAM_MAX_SEATS):
            return None
        return unit * seats
    table = FAMILY_PRICES_USD if plan == PLAN_FAMILY else PRICES_USD
    return table.get(months)


class PaymentError(RuntimeError):
    pass


# ── Availability ─────────────────────────────────────────────────────────────
def vnpay_enabled() -> bool:
    return bool(settings.VNPAY_TMN_CODE and settings.VNPAY_HASH_SECRET)


def momo_enabled() -> bool:
    return bool(settings.MOMO_PARTNER_CODE and settings.MOMO_ACCESS_KEY and settings.MOMO_SECRET_KEY)


def stripe_enabled() -> bool:
    return settings.stripe_enabled


def providers() -> list[str]:
    out = []
    if vnpay_enabled():
        out.append("vnpay")
    if momo_enabled():
        out.append("momo")
    if stripe_enabled():
        out.append("stripe")
    return out


def _plan_label(order: PaymentOrder) -> str:
    if order.plan == PLAN_FAMILY:
        return "Gia dinh"
    if order.plan == PLAN_TEAM:
        return f"Doanh nghiep {order.seats} ghe"
    return "Premium"


# ── Orders ───────────────────────────────────────────────────────────────────
def create_order(db: Session, user_id: str, provider: str, months: int, plan: str = PLAN_PREMIUM, seats: int = 1) -> PaymentOrder:
    seats = seats if plan == PLAN_TEAM else 1
    if provider == "stripe":
        cents = price_usd_for(plan, months, seats)
        amount = cents * settings.USD_TO_VND // 100 if cents is not None else None
    else:
        cents, amount = None, price_for(plan, months, seats)
    if amount is None:
        raise PaymentError("Gói không hợp lệ.")
    if provider not in providers():
        raise PaymentError("Cổng thanh toán này chưa được bật.")
    order = PaymentOrder(user_id=user_id, provider=provider, plan=plan, months=months, seats=seats, amount_vnd=amount,
                         currency="USD" if provider == "stripe" else "VND", amount_foreign=cents)
    db.add(order)
    db.flush()
    return order


def mark_paid(db: Session, order: PaymentOrder, provider_txn: str | None, callback: dict) -> bool:
    """Credit the subscription once; repeated IPNs are ignored. Returns True if newly paid."""
    if order.status == STATUS_PAID:
        return False
    order.status = STATUS_PAID
    order.provider_txn = (provider_txn or "")[:120] or None
    order.callback = callback
    order.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
    sub = subs.upgrade_to_premium(db, order.user_id, months=order.months, plan=order.plan or PLAN_PREMIUM, seats=order.seats or 1)
    sub.provider = order.provider
    sub.provider_ref = order.id
    db.commit()
    return True


def mark_failed(db: Session, order: PaymentOrder, callback: dict) -> None:
    if order.status == STATUS_PENDING:
        order.status = STATUS_FAILED
        order.callback = callback
        db.commit()


# ── 7-day trial ──────────────────────────────────────────────────────────────
def trial_available(db: Session, user_id: str) -> bool:
    sub = subs.get_or_create_subscription(db, user_id)
    return sub.trial_started_at is None and not subs.is_premium(db, user_id)


def start_trial(db: Session, user_id: str) -> Subscription:
    sub = subs.get_or_create_subscription(db, user_id)
    if sub.trial_started_at is not None:
        raise PaymentError("Bạn đã dùng thử Premium rồi.")
    if subs.is_premium(db, user_id):
        raise PaymentError("Bạn đang là Premium.")
    now = datetime.now(timezone.utc)
    sub.plan = PLAN_PREMIUM
    sub.status = "active"
    sub.current_period_end = (now + timedelta(days=TRIAL_DAYS)).replace(tzinfo=None)
    sub.trial_started_at = now.replace(tzinfo=None)
    sub.provider = "trial"
    db.commit()
    db.refresh(sub)
    return sub


# ── VNPay ────────────────────────────────────────────────────────────────────
def _vnpay_sign(params: dict[str, str]) -> str:
    data = "&".join(f"{k}={quote_plus(str(v))}" for k, v in sorted(params.items()) if v not in (None, ""))
    return hmac.new(settings.VNPAY_HASH_SECRET.encode("utf-8"), data.encode("utf-8"), hashlib.sha512).hexdigest()


def vnpay_pay_url(order: PaymentOrder, client_ip: str, return_url: str, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone(timedelta(hours=7)))      # VNPay expects GMT+7 timestamps
    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(order.amount_vnd * 100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order.id,
        "vnp_OrderInfo": f"AGEN {_plan_label(order)} {order.months} thang",
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": return_url,
        "vnp_IpAddr": client_ip or "127.0.0.1",
        "vnp_CreateDate": now.strftime("%Y%m%d%H%M%S"),
        "vnp_ExpireDate": (now + timedelta(minutes=30)).strftime("%Y%m%d%H%M%S"),
    }
    signature = _vnpay_sign(params)
    query = urlencode(sorted(params.items()), quote_via=quote_plus)
    return f"{settings.VNPAY_URL}?{query}&vnp_SecureHashType=HmacSHA512&vnp_SecureHash={signature}"


def vnpay_verify(params: dict[str, str]) -> bool:
    """True when vnp_SecureHash matches the other vnp_* params."""
    received = params.get("vnp_SecureHash", "")
    signed = {k: v for k, v in params.items() if k.startswith("vnp_") and k not in ("vnp_SecureHash", "vnp_SecureHashType")}
    return bool(received) and hmac.compare_digest(_vnpay_sign(signed).lower(), received.lower())


def handle_vnpay_callback(db: Session, params: dict[str, str]) -> tuple[str, str]:
    """Shared by the IPN and the return URL. Returns (RspCode, Message) per VNPay's IPN contract."""
    if not vnpay_enabled():
        return "99", "Unknown error"
    if not vnpay_verify(params):
        return "97", "Invalid signature"
    order = db.query(PaymentOrder).filter(PaymentOrder.id == params.get("vnp_TxnRef", "")).first()
    if not order or order.provider != "vnpay":
        return "01", "Order not found"
    try:
        amount = int(params.get("vnp_Amount", "0")) // 100
    except ValueError:
        amount = -1
    if amount != order.amount_vnd:
        return "04", "Invalid amount"
    if order.status == STATUS_PAID:
        return "02", "Order already confirmed"
    if params.get("vnp_ResponseCode") == "00" and params.get("vnp_TransactionStatus", "00") == "00":
        mark_paid(db, order, params.get("vnp_TransactionNo"), dict(params))
    else:
        mark_failed(db, order, dict(params))
    return "00", "Confirm Success"


# ── MoMo ─────────────────────────────────────────────────────────────────────
def _momo_sign(raw: str) -> str:
    return hmac.new(settings.MOMO_SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()


def momo_create_request(order: PaymentOrder, redirect_url: str, ipn_url: str) -> dict:
    request_id = order.id
    order_info = f"AGEN {_plan_label(order)} {order.months} thang"
    extra = ""
    raw = (
        f"accessKey={settings.MOMO_ACCESS_KEY}&amount={order.amount_vnd}&extraData={extra}"
        f"&ipnUrl={ipn_url}&orderId={order.id}&orderInfo={order_info}&partnerCode={settings.MOMO_PARTNER_CODE}"
        f"&redirectUrl={redirect_url}&requestId={request_id}&requestType=captureWallet"
    )
    return {
        "partnerCode": settings.MOMO_PARTNER_CODE,
        "partnerName": "AI AGENT ENGLISH",
        "storeId": "agen",
        "requestId": request_id,
        "amount": order.amount_vnd,
        "orderId": order.id,
        "orderInfo": order_info,
        "redirectUrl": redirect_url,
        "ipnUrl": ipn_url,
        "lang": "vi",
        "requestType": "captureWallet",
        "autoCapture": True,
        "extraData": extra,
        "signature": _momo_sign(raw),
    }


def momo_pay_url(order: PaymentOrder, redirect_url: str, ipn_url: str) -> str:
    body = momo_create_request(order, redirect_url, ipn_url)
    try:
        res = httpx.post(f"{settings.MOMO_ENDPOINT.rstrip('/')}/v2/gateway/api/create", json=body, timeout=15)
        data = res.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise PaymentError(f"MoMo không phản hồi: {exc}") from exc
    if data.get("resultCode") != 0 or not data.get("payUrl"):
        raise PaymentError(f"MoMo từ chối tạo giao dịch: {data.get('message', data.get('resultCode'))}")
    return data["payUrl"]


def momo_verify(payload: dict) -> bool:
    keys = (
        "accessKey", "amount", "extraData", "message", "orderId", "orderInfo", "orderType",
        "partnerCode", "payType", "requestId", "responseTime", "resultCode", "transId",
    )
    values = dict(payload)
    values["accessKey"] = settings.MOMO_ACCESS_KEY
    raw = "&".join(f"{k}={values.get(k, '')}" for k in keys)
    received = str(payload.get("signature", ""))
    return bool(received) and hmac.compare_digest(_momo_sign(raw), received)


def handle_momo_ipn(db: Session, payload: dict) -> bool:
    """Returns True when the order was credited by this call."""
    if not momo_enabled() or not momo_verify(payload):
        logger.warning("MoMo IPN rejected (signature)")
        return False
    order = db.query(PaymentOrder).filter(PaymentOrder.id == str(payload.get("orderId", ""))).first()
    if not order or order.provider != "momo":
        return False
    try:
        amount = int(payload.get("amount", 0))
    except (TypeError, ValueError):
        amount = -1
    if amount != order.amount_vnd:
        logger.warning("MoMo IPN amount mismatch for %s", order.id)
        return False
    if int(payload.get("resultCode", -1)) == 0:
        return mark_paid(db, order, str(payload.get("transId", "")), payload)
    mark_failed(db, order, payload)
    return False


# ── G10 · Stripe Checkout ────────────────────────────────────────────────────
def stripe_checkout_url(order: PaymentOrder, success_url: str, cancel_url: str) -> str:
    """Create a Checkout Session (one-time payment) and return its hosted URL."""
    if not stripe_enabled():
        raise PaymentError("Thanh toán thẻ quốc tế chưa được bật.")
    form = {
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": order.id,
        "metadata[order_id]": order.id,
        "payment_intent_data[metadata][order_id]": order.id,
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][unit_amount]": str(order.amount_foreign),
        "line_items[0][price_data][product_data][name]": f"AI AGENT ENGLISH {_plan_label(order)} · {order.months} month(s)",
    }
    try:
        resp = httpx.post(f"{STRIPE_API}/checkout/sessions", data=form, auth=(settings.STRIPE_SECRET_KEY, ""), timeout=15)
        data = resp.json()
    except Exception as exc:
        raise PaymentError(f"Stripe không phản hồi: {exc}") from exc
    if resp.status_code >= 400 or not data.get("url"):
        raise PaymentError(f"Stripe từ chối tạo phiên thanh toán: {(data.get('error') or {}).get('message', resp.status_code)}")
    order.provider_txn = (data.get("id") or "")[:120] or None
    return data["url"]


def stripe_verify(payload: bytes, signature_header: str, now: int | None = None) -> bool:
    """Stripe-Signature: t=<ts>,v1=<hex hmac-sha256 of "t.payload">; rejects stale timestamps."""
    if not settings.STRIPE_WEBHOOK_SECRET or not signature_header:
        return False
    parts: dict[str, list[str]] = {}
    for item in signature_header.split(","):
        k, _, v = item.strip().partition("=")
        parts.setdefault(k, []).append(v)
    try:
        ts = int(parts.get("t", ["0"])[0])
    except ValueError:
        return False
    import time as _time
    if abs((now if now is not None else int(_time.time())) - ts) > STRIPE_SIGNATURE_TOLERANCE_S:
        return False
    expected = hmac.new(settings.STRIPE_WEBHOOK_SECRET.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in parts.get("v1", []))


def handle_stripe_event(db: Session, event: dict) -> str:
    """Credit a paid Checkout Session; mark expired ones failed. Returns what happened."""
    kind = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}
    order_id = (obj.get("metadata") or {}).get("order_id") or obj.get("client_reference_id")
    if not order_id:
        return "ignored"
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.provider == "stripe").first()
    if not order:
        return "unknown_order"
    if kind in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        if obj.get("payment_status") != "paid":
            return "pending"
        if int(obj.get("amount_total") or 0) != int(order.amount_foreign or -1) or (obj.get("currency") or "").lower() != "usd":
            logger.warning("Stripe amount mismatch for order %s: %s %s", order.id, obj.get("amount_total"), obj.get("currency"))
            mark_failed(db, order, {"stripe_event": kind, "reason": "amount_mismatch"})
            return "amount_mismatch"
        return "paid" if mark_paid(db, order, obj.get("payment_intent") or obj.get("id"), {"stripe_event": kind, "session": obj.get("id")}) else "already_paid"
    if kind in ("checkout.session.expired", "checkout.session.async_payment_failed"):
        mark_failed(db, order, {"stripe_event": kind})
        return "failed"
    return "ignored"


def status_of(order: PaymentOrder) -> str:
    return order.status


def new_id() -> str:
    return str(uuid.uuid4())


__all__ = [
    "PRICES_VND", "FAMILY_PRICES_VND", "FAMILY_MAX_CHILDREN", "TEAM_PRICES_VND", "TEAM_MIN_SEATS", "TEAM_MAX_SEATS", "price_for", "TRIAL_DAYS", "PaymentError", "providers", "vnpay_enabled", "momo_enabled",
    "create_order", "mark_paid", "mark_failed", "trial_available", "start_trial",
    "vnpay_pay_url", "vnpay_verify", "handle_vnpay_callback",
    "momo_create_request", "momo_pay_url", "momo_verify", "handle_momo_ipn", "status_of", "new_id", "json",
    "PRICES_USD", "FAMILY_PRICES_USD", "TEAM_PRICES_USD", "price_usd_for", "stripe_enabled", "stripe_checkout_url", "stripe_verify", "handle_stripe_event",
]
