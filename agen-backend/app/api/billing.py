"""AGEN — Billing / Subscription API (pilot).

Exposes the learner's plan + daily quota and a mock upgrade/cancel. No real
payment gateway is integrated in the pilot.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.services import subscription_service as subs

router = APIRouter(prefix="/billing", tags=["Billing"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class SubscriptionOut(BaseModel):
    plan: str
    status: str
    is_premium: bool
    current_period_end: datetime | None


class QuotaOut(BaseModel):
    plan: str
    is_premium: bool
    used_today: int
    limit: int | None
    remaining: int | None
    allowed: bool


class UpgradeRequest(BaseModel):
    months: int = Field(default=1, ge=1, le=12)


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/subscription", response_model=SubscriptionOut)
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Current subscription state."""
    sub = subs.get_or_create_subscription(db, current_user.id)
    return SubscriptionOut(
        plan=sub.plan, status=sub.status,
        is_premium=subs.is_premium(db, current_user.id),
        current_period_end=sub.current_period_end,
    )


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
    sub = subs.upgrade_to_premium(db, current_user.id, months=payload.months)
    return SubscriptionOut(
        plan=sub.plan, status=sub.status,
        is_premium=subs.is_premium(db, current_user.id),
        current_period_end=sub.current_period_end,
    )


@router.post("/cancel", response_model=SubscriptionOut)
def cancel(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel premium (pilot: reverts to free immediately)."""
    sub = subs.cancel_subscription(db, current_user.id)
    return SubscriptionOut(
        plan=sub.plan, status=sub.status,
        is_premium=subs.is_premium(db, current_user.id),
        current_period_end=sub.current_period_end,
    )
