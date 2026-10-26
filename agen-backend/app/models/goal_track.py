"""G3 · Progress through a goal track (IELTS / TOEIC / interview), one row per started lesson."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.core.database import Base


class GoalTrackProgress(Base):
    __tablename__ = "goal_track_progress"
    __table_args__ = (UniqueConstraint("learner_id", "lesson_code", name="uq_goal_track_learner_lesson"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    track_id = Column(String(30), nullable=False, index=True)
    lesson_code = Column(String(40), nullable=False)

    generated_lesson_id = Column(String(36), nullable=True)     # the Lesson row made for it
    status = Column(String(20), nullable=False, default="in_progress")   # in_progress | completed
    best_score = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=0)
    mastered = Column(Boolean, nullable=False, default=False)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
