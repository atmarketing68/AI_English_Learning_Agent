import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class LearnerProfile(Base):
    """
    AGEN Learner Digital Twin.
    The heart of the personalization system.
    """
    __tablename__ = "learner_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    # Short code a parent enters to link to this learner (e.g. "AGEN-7K2P")
    invite_code = Column(String(20), unique=True, index=True, nullable=True)

    # --- Identity ---
    display_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    grade = Column(String(20), nullable=True)   # e.g. "grade_5", "grade_10", "adult"
    avatar_url = Column(String(500), nullable=True)

    # --- Language Profile (0.0 - 100.0 score) ---
    overall_level = Column(String(10), default="PRE_A1")  # PRE_A1, A1, A2, B1, B2, C1, C2
    listening_score = Column(Float, default=0.0)
    speaking_score = Column(Float, default=0.0)
    reading_score = Column(Float, default=0.0)
    writing_score = Column(Float, default=0.0)
    vocabulary_score = Column(Float, default=0.0)
    grammar_score = Column(Float, default=0.0)

    # --- Goals ---
    learning_goal = Column(String(255), nullable=True)  # "giao_tiep", "thi_dau_vao", "ielts", etc.
    target_level = Column(String(10), nullable=True)
    target_date = Column(DateTime, nullable=True)

    # --- Preferences ---
    interests = Column(JSON, default=list)          # ["music", "sport", "tech"]
    daily_study_minutes = Column(Integer, default=15)

    # --- Learning Intelligence (updated by Analytics Agent) ---
    strengths = Column(JSON, default=list)          # ["reading", "vocabulary"]
    weaknesses = Column(JSON, default=list)         # ["speaking", "past_tense"]
    knowledge_gaps = Column(JSON, default=list)     # ["irregular_verbs", "pronunciation_th"]
    error_patterns = Column(JSON, default=dict)     # {"grammar": 12, "pronunciation": 8}

    # --- Behavior & Engagement ---
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    total_lessons_completed = Column(Integer, default=0)
    total_study_minutes = Column(Integer, default=0)
    last_active_at = Column(DateTime, nullable=True)
    # Streak freeze: each one covers a single missed day (max 2 held at once).
    streak_freezes = Column(Integer, default=1, server_default="1", nullable=False)
    streak_freeze_used_at = Column(DateTime, nullable=True)
    # Weekly goal: number of study days per Mon–Sun week; reward claimed once per ISO week.
    weekly_goal_days = Column(Integer, default=5, server_default="5", nullable=False)
    weekly_goal_claimed_week = Column(String(10), nullable=True)   # e.g. "2026-W44"

    # --- Placement ---
    placement_completed = Column(String(10), default="none")  # none, partial, done

    # --- Metadata ---
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="learner_profile")
    learning_events = relationship("LearningEvent", back_populates="learner", cascade="all, delete-orphan")
