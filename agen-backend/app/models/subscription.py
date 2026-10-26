"""Subscription / plan state for a learner.

Pilot scope: models the plan (free/premium) and gating limits. There is NO real
payment gateway integration — the upgrade endpoint records intent so the gating
logic and UI can be built and tested. A Stripe/VNPay integration can later set
`status`/`current_period_end` from webhook events without schema changes.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.core.database import Base

PLAN_FREE = "free"
PLAN_PREMIUM = "premium"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)

    plan = Column(String(20), default=PLAN_FREE, nullable=False)     # free | premium
    status = Column(String(20), default="active", nullable=False)    # active | canceled | expired

    # For premium: when the current paid period ends (None for free / perpetual).
    current_period_end = Column(DateTime, nullable=True)

    # Payment provider linkage (unused in pilot; reserved for real integration).
    provider = Column(String(30), nullable=True)                     # stripe | vnpay | ...
    provider_ref = Column(String(120), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
