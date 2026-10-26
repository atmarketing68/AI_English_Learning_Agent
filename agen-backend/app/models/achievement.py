"""
AGEN — Achievement & Daily Challenge Models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Achievement(Base):
    """Definition of an achievement (global catalog)."""
    __tablename__ = "achievements"

    id          = Column(String, primary_key=True)       # slug: "first_lesson", "streak_7"
    name        = Column(String, nullable=False)          # Display name
    description = Column(String, nullable=False)          # What you need to do
    icon        = Column(String, nullable=False)          # Emoji icon
    category    = Column(String, nullable=False)          # streak / lesson / skill / special
    xp_reward   = Column(Integer, default=0)             # Bonus XP when unlocked
    condition_type  = Column(String, nullable=False)     # lessons_completed / streak_days / skill_score / xp_total
    condition_value = Column(Integer, nullable=False)    # Threshold to unlock


class LearnerAchievement(Base):
    """Records which achievements a learner has earned."""
    __tablename__ = "learner_achievements"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id     = Column(String, ForeignKey("learner_profiles.id"), nullable=False, index=True)
    achievement_id = Column(String, ForeignKey("achievements.id"), nullable=False)
    earned_at      = Column(DateTime, default=datetime.utcnow)
    notified       = Column(Boolean, default=False)      # Whether user has seen the notification

    achievement = relationship("Achievement")


class DailyChallenge(Base):
    """A generated daily challenge for a learner."""
    __tablename__ = "daily_challenges"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id  = Column(String, ForeignKey("learner_profiles.id"), nullable=False, index=True)
    date        = Column(String, nullable=False)          # "YYYY-MM-DD"
    title       = Column(String, nullable=False)
    description = Column(String, nullable=False)
    skill       = Column(String, nullable=False)          # vocabulary/grammar/reading/listening/speaking/writing
    target_type = Column(String, nullable=False)          # complete_lesson / word_count / score_threshold / sessions
    target_value= Column(Integer, nullable=False)
    current_value= Column(Integer, default=0)
    xp_reward   = Column(Integer, default=20)
    is_completed= Column(Boolean, default=False)
    completed_at= Column(DateTime, nullable=True)
