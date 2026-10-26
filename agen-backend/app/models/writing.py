"""
AGEN — Writing Submission Model
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class WritingSubmission(Base):
    __tablename__ = "writing_submissions"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String, ForeignKey("learner_profiles.id"), nullable=False, index=True)

    # Prompt info
    prompt_title   = Column(String, nullable=False)
    prompt_text    = Column(Text, nullable=False)
    genre          = Column(String, nullable=True)       # opinion/narrative/descriptive/email
    level          = Column(String, nullable=False)
    word_target    = Column(String, nullable=True)

    # Learner's writing
    user_text  = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)

    # AI Evaluation results (stored as JSON)
    overall_score = Column(Float, nullable=True)
    grade         = Column(String, nullable=True)        # S/A/B/C/D
    evaluation    = Column(JSON, nullable=True)          # Full evaluation dict

    # XP
    xp_earned = Column(Integer, default=0)

    created_at   = Column(DateTime, default=datetime.utcnow)
    evaluated_at = Column(DateTime, nullable=True)

    # G11 · a teacher re-grades the piece; shown instead of the AI score where present
    teacher_score     = Column(Float, nullable=True)        # 0–100
    teacher_band      = Column(Float, nullable=True)        # IELTS band / TOEIC score for exam genres
    teacher_comment   = Column(Text, nullable=True)
    teacher_user_id   = Column(String(36), nullable=True)
    teacher_scored_at = Column(DateTime, nullable=True)
