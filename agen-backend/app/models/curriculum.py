"""
AGEN — Curriculum Models
Structured hierarchy: Program → Level → Unit → CurriculumLesson

This is the fixed "curriculum map" (the skeleton of the whole system per
Master Plan Phần B). AI generates lesson *content* on demand, but the
sequence, objectives and prerequisites are anchored to this human-designed map.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class CurriculumUnit(Base):
    """
    A thematic unit within a CEFR level (e.g. "Unit 1 - Me & My World").
    Units are ordered and group multiple CurriculumLessons.
    """
    __tablename__ = "curriculum_units"

    id = Column(String(36), primary_key=True, default=_uuid)

    level = Column(String(10), nullable=False, index=True)   # PRE_A1, A1, A2, ...
    order = Column(Integer, nullable=False, default=0)        # position within the level
    code = Column(String(30), nullable=False, unique=True)   # e.g. "A1-U01"
    title = Column(String(150), nullable=False)              # "Me & My World"
    description = Column(Text, nullable=True)
    theme = Column(String(100), nullable=True)               # topic theme
    icon = Column(String(20), nullable=True)                 # emoji

    created_at = Column(DateTime, default=datetime.utcnow)

    lessons = relationship(
        "CurriculumLesson",
        back_populates="unit",
        order_by="CurriculumLesson.order",
        cascade="all, delete-orphan",
    )


class CurriculumLesson(Base):
    """
    A single planned lesson node in the curriculum map with full pedagogical
    metadata (per Master Plan section 6). AI generates the actual exercise
    content, but this node defines WHAT should be taught and in what order.
    """
    __tablename__ = "curriculum_lessons"

    id = Column(String(36), primary_key=True, default=_uuid)
    unit_id = Column(String(36), ForeignKey("curriculum_units.id"), nullable=False, index=True)

    order = Column(Integer, nullable=False, default=0)       # position within the unit
    code = Column(String(40), nullable=False, unique=True)   # e.g. "A1-U01-L03"
    title = Column(String(150), nullable=False)              # "My Family"

    # --- Primary skill & difficulty ---
    skill = Column(String(20), nullable=False)               # vocabulary/grammar/reading/listening/speaking/writing
    difficulty = Column(Integer, default=1)                  # 1 (easy) → 5 (hard)

    # --- Pedagogical metadata ---
    topic = Column(String(100), nullable=False)              # topic passed to AI for content gen
    objective = Column(Text, nullable=True)                  # learning objective (VI/EN)
    vocabulary_focus = Column(JSON, default=list)            # ["hello", "name", ...]
    grammar_focus = Column(String(150), nullable=True)       # "Simple Present: to be"
    cefr_reference = Column(String(20), nullable=True)       # CEFR descriptor code
    vietnam_curriculum_ref = Column(String(100), nullable=True)

    # --- Sequencing ---
    prerequisite_code = Column(String(40), nullable=True)    # code of lesson that must be done first
    is_review = Column(Boolean, default=False)               # True for Review/Assessment nodes
    is_assessment = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("CurriculumUnit", back_populates="lessons")


class LearnerCurriculumProgress(Base):
    """
    Tracks a learner's progress through the curriculum map.
    One row per (learner, curriculum_lesson) once the learner starts it.
    Links the fixed curriculum node to the AI-generated Lesson instance.
    """
    __tablename__ = "learner_curriculum_progress"

    id = Column(String(36), primary_key=True, default=_uuid)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    curriculum_lesson_id = Column(String(36), ForeignKey("curriculum_lessons.id"), nullable=False, index=True)

    # Link to the actual AI-generated Lesson (once generated)
    generated_lesson_id = Column(String(36), nullable=True)

    status = Column(String(20), default="not_started")       # not_started, in_progress, completed
    best_score = Column(Integer, default=0)                  # 0–100
    attempts = Column(Integer, default=0)
    mastered = Column(Boolean, default=False)                # score >= mastery threshold

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
