"""AGEN — Billing / Subscription API.

Plan + daily quota, the pilot's mock upgrade (ALLOW_DEMO_UPGRADE), and from G3
real checkouts through VNPay / MoMo (each on only when its merchant keys are
set), their callbacks, and a 7-day Premium trial.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import client_ip
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.payment_order import PaymentOrder
from app.services import payments
from app.services import subscription_service as subs

router = APIRouter(prefix="/billing", tags=["Billing"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class SubscriptionOut(BaseModel):
    plan: str
    status: str
    is_premium: bool
    current_period_end: datetime | None
    provider: str | None = None


class QuotaOut(BaseModel):
    plan: str
    is_premium: bool
    used_today: int
    limit: int | None
    remaining: int | None
    allowed: bool


class UpgradeRequest(BaseModel):
    months: int = Field(default=1, ge=1, le=12)


class PriceOut(BaseModel):
    months: int
    amount_vnd: int


class BillingOptions(BaseModel):
    prices: list[PriceOut]
    providers: list[str]          # "vnpay" | "momo" that are configured
    demo_enabled: bool            # pilot mock upgrade
    trial_available: bool
    trial_days: int


class CheckoutRequest(BaseModel):
    months: int = Field(ge=1, le=12)
    provider: str = Field(pattern="^(vnpay|momo)$")


class CheckoutOut(BaseModel):
    order_id: str
    provider: str
    pay_url: str


class OrderOut(BaseModel):
    order_id: str
    provider: str
    months: int
    amount_vnd: int
    status: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _sub_out(db: Session, user_id: str) -> SubscriptionOut:
    sub = subs.get_or_create_subscription(db, user_id)
    return SubscriptionOut(
        plan=sub.plan, status=sub.status,
        is_premium=subs.is_premium(db, user_id),
        current_period_end=sub.current_period_end,
        provider=sub.provider,
    )


def _api_base(request: Request) -> str:
    if settings.API_PUBLIC_URL:
        return settings.API_PUBLIC_URL.rstrip("/")
    return str(request.base_url).rstrip("/")


def _app_redirect(status: str, order_id: str) -> RedirectResponse:
    return RedirectResponse(url=f"{settings.app_url}/upgrade?status={status}&order={order_id}", status_code=303)


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/subscription", response_model=SubscriptionOut)
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Current subscription state."""
    return _sub_out(db, current_user.id)


@router.get("/quota", response_model=QuotaOut)
def get_quota(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Today's lesson quota for the current learner."""
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return QuotaOut(**subs.check_lesson_quota(db, current_user.id, learner))


@router.get("/options", response_model=BillingOptions)
def billing_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """What the upgrade page can offer this learner."""
    return BillingOptions(
        prices=[PriceOut(months=m, amount_vnd=a) for m, a in payments.PRICES_VND.items()],
        providers=payments.providers(),
        demo_enabled=settings.demo_upgrade_enabled,
        trial_available=payments.trial_available(db, current_user.id),
        trial_days=payments.TRIAL_DAYS,
    )


@router.post("/trial", response_model=SubscriptionOut)
def start_trial(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """G3 · 7 days of Premium, once per account."""
    if current_user.is_guest:
        raise HTTPException(status_code=403, detail="Hãy lưu tài khoản trước khi dùng thử Premium.")
    try:
        payments.start_trial(db, current_user.id)
    except payments.PaymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _sub_out(db, current_user.id)


@router.post("/checkout", response_model=CheckoutOut)
def checkout(
    payload: CheckoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """G3 · Create an order and return the gateway's pay URL."""
    if current_user.is_guest:
        raise HTTPException(status_code=403, detail="Hãy lưu tài khoản trước khi thanh toán.")
    try:
        order = payments.create_order(db, current_user.id, payload.provider, payload.months)
        base = _api_base(request)
        if payload.provider == "vnpay":
            pay_url = payments.vnpay_pay_url(order, client_ip(request), f"{base}/api/v1/billing/vnpay/return")
        else:
            pay_url = payments.momo_pay_url(order, f"{settings.app_url}/upgrade?order={order.id}", f"{base}/api/v1/billing/momo/ipn")
    except payments.PaymentError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc))
    order.pay_url = pay_url
    db.commit()
    return CheckoutOut(order_id=order.id, provider=order.provider, pay_url=pay_url)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return OrderOut(order_id=order.id, provider=order.provider, months=order.months, amount_vnd=order.amount_vnd, status=order.status)


# ── Gateway callbacks (no login) ──────────────────────────────────────────────
@router.get("/vnpay/ipn")
def vnpay_ipn(request: Request, db: Session = Depends(get_db)):
    """VNPay server-to-server confirmation (the one that credits the order)."""
    code, message = payments.handle_vnpay_callback(db, dict(request.query_params))
    return {"RspCode": code, "Message": message}


@router.get("/vnpay/return")
def vnpay_return(request: Request, db: Session = Depends(get_db)):
    """Browser comes back here after paying; verify, credit if the IPN has not yet, then show the app."""
    params = dict(request.query_params)
    code, _ = payments.handle_vnpay_callback(db, params)
    order_id = params.get("vnp_TxnRef", "")
    if code in ("00", "02") and params.get("vnp_ResponseCode") == "00":
        return _app_redirect("success", order_id)
    return _app_redirect("failed", order_id)


@router.post("/momo/ipn", status_code=204)
async def momo_ipn(request: Request, db: Session = Depends(get_db)):
    """MoMo server-to-server notification (JSON)."""
    try:
        payload = await request.json()
    except ValueError:
        return Response(status_code=204)
    payments.handle_momo_ipn(db, payload if isinstance(payload, dict) else {})
    return Response(status_code=204)


# ── Pilot mock upgrade / cancel ───────────────────────────────────────────────
@router.post("/upgrade", response_model=SubscriptionOut)
def upgrade(
    payload: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upgrade to premium (pilot: no real charge)."""
    if not settings.demo_upgrade_enabled:
        raise HTTPException(
            status_code=403,
            detail="Thanh toán trực tuyến đang được tích hợp. Vui lòng quay lại sau.",
        )
    subs.upgrade_to_premium(db, current_user.id, months=payload.months)
    return _sub_out(db, current_user.id)


@router.post("/cancel", response_model=SubscriptionOut)
def cancel(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel premium (pilot: reverts to free immediately)."""
    subs.cancel_subscription(db, current_user.id)
    return _sub_out(db, current_user.id)
