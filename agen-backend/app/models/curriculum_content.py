"""
AGEN — Cached Curriculum Lesson Content.

Implements the "Content Factory" idea (Blueprint Part B §4): AI generates lesson
content ONCE per curriculum node, it is quality-checked + human-approvable, then
every learner is served a copy of the approved content instead of triggering a
fresh LLM call.

Benefits: stable/reviewable content, no per-learner LLM cost, no quota pressure.
Keyed by the curriculum lesson `code` (e.g. "A2-U01-L01").
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text, Boolean

from app.core.database import Base

STATUS_DRAFT = "draft"        # generated, awaiting review
STATUS_APPROVED = "approved"  # reviewed & published — served to learners
STATUS_REJECTED = "rejected"  # rejected — will be regenerated


class CurriculumLessonContent(Base):
    __tablename__ = "curriculum_lesson_content"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Curriculum node this content belongs to.
    curriculum_code = Column(String(40), unique=True, nullable=False, index=True)  # "A2-U01-L01"
    level = Column(String(10), nullable=False, index=True)
    skill = Column(String(20), nullable=False)
    topic = Column(String(100), nullable=False)

    # The AI-generated, validated payload (same shape lesson_agent returns):
    # { title, summary, exercises: [...], vocabulary?/passage?, ... }
    content = Column(JSON, nullable=False)

    # Review workflow.
    status = Column(String(20), default=STATUS_DRAFT, nullable=False, index=True)

    # Quality-gate snapshot (from evaluation_service at generation time).
    eval_score = Column(Float, nullable=True)
    eval_flagged = Column(Boolean, default=False)
    eval_flags = Column(JSON, nullable=True)

    total_exercises = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
