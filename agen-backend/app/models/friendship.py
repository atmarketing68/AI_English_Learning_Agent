"""G6 · Bạn học: one row per pair (a_id < b_id) with the duo-quest claim marks per side."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint

from app.core.database import Base


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("a_id", "b_id", name="uq_friendship_pair"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    a_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    b_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    # ISO week ("2026-W44") in which each side claimed the duo-quest reward.
    a_claimed_week = Column(String(10), nullable=True)
    b_claimed_week = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
