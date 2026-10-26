"""G4 · Weekly league groups: who sits in which tier/group this ISO week."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.core.database import Base


class LeagueMembership(Base):
    __tablename__ = "league_memberships"
    __table_args__ = (UniqueConstraint("learner_id", "week", name="uq_league_membership_learner_week"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    week = Column(String(10), nullable=False, index=True)        # "2026-W44"
    tier = Column(Integer, nullable=False, default=0)            # 0 Đồng · 1 Bạc · 2 Vàng · 3 Kim cương
    group_no = Column(Integer, nullable=False, default=1)        # group number within the tier
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
