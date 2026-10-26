"""Subscription / plan state for a learner.

Pilot scope: models the plan (free/premium) and gating limits. There is NO real
payment gateway integration — the upgrade endpoint records intent so the gating
logic and UI can be built and tested. A Stripe/VNPay integration can later set
`status`/`current_period_end` from webhook events without schema changes.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base

PLAN_FREE = "free"
PLAN_PREMIUM = "premium"
PLAN_FAMILY = "family"          # G5 · a parent pays; linked children are Premium
PLAN_TEAM = "team"              # G7 · a teacher/company pays per seat; group members are Premium
PAID_PLANS = (PLAN_PREMIUM, PLAN_FAMILY, PLAN_TEAM)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)

    plan = Column(String(20), default=PLAN_FREE, nullable=False)     # free | premium
    status = Column(String(20), default="active", nullable=False)    # active | canceled | expired

    # For premium: when the current paid period ends (None for free / perpetual).
    current_period_end = Column(DateTime, nullable=True)

    # Payment provider linkage: pilot_manual | trial | vnpay | momo, and the order id.
    provider = Column(String(30), nullable=True)
    provider_ref = Column(String(120), nullable=True)

    # G3 · 7-day Premium trial, once per account.
    trial_started_at = Column(DateTime, nullable=True)

    # G7 · team plan: how many group members this subscription covers.
    seats = Column(Integer, nullable=False, default=1, server_default="1")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
