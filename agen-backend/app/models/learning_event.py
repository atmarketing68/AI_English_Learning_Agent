import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class LearningEvent(Base):
    """
    AGEN Golden Data — the atomic unit of learning data.
    Every learner interaction generates a LearningEvent.
    This data powers the Adaptive Engine and NBL Engine.
    """
    __tablename__ = "learning_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String, ForeignKey("learner_profiles.id"), nullable=False, index=True)

    # --- Lesson context ---
    lesson_id = Column(String, nullable=True)
    activity_id = Column(String, nullable=True)

    # --- Event type & Skill ---
    event_type = Column(String, nullable=True)         # lesson_completed, placement_done, streak, etc.
    skill = Column(String, nullable=False)             # listening, speaking, reading, writing, vocab, grammar
    topic = Column(String, nullable=True)
    activity_type = Column(String, nullable=True)

    # --- Performance ---
    correct = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)              # 0.0 to 100.0
    xp_earned = Column(Integer, default=0)
    difficulty = Column(Integer, default=1)           # 1 (easy) to 5 (hard)
    error_type = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # --- AI Analysis ---
    ai_feedback = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)          # Arbitrary extra data (renamed from metadata)
    confidence = Column(Float, nullable=True)
    response_time_seconds = Column(Float, nullable=True)

    # --- Adaptive engine decision ---
    adaptive_decision = Column(String(30), nullable=True)  # keep_level, increase, decrease, review, reteach

    # --- Metadata ---
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    learner = relationship("LearnerProfile", back_populates="learning_events")
