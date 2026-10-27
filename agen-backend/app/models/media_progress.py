"""G10 · Học qua podcast / video: one row per (learner, episode)."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.core.database import Base


class MediaProgress(Base):
    __tablename__ = "media_progress"
    __table_args__ = (UniqueConstraint("learner_id", "episode_id", name="uq_media_progress"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    episode_id = Column(String(40), nullable=False)
    best_score = Column(Float, nullable=False, default=0.0)        # % of questions right
    attempts = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime, nullable=True)                 # first time all questions were submitted
    last_at = Column(DateTime, default=datetime.utcnow, nullable=False)
