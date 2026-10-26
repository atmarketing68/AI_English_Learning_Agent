"""
Daily quests (G1 · 3 nhiệm vụ mỗi ngày).

Three quests are picked per learner per local day. Progress is computed from
that day's LearningEvents, so no activity endpoint needs to know about quests;
the row only pins the day's targets and records when the reward was claimed.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.core.database import Base


class DailyQuest(Base):
    __tablename__ = "daily_quests"
    __table_args__ = (
        UniqueConstraint("learner_id", "date", "code", name="uq_daily_quest_learner_date_code"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False)       # local "YYYY-MM-DD"
    slot = Column(Integer, nullable=False)          # display order 0–2
    code = Column(String(20), nullable=False)       # see QUEST_CATALOG in app/services/engagement.py
    target = Column(Integer, nullable=False)
    xp_reward = Column(Integer, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
