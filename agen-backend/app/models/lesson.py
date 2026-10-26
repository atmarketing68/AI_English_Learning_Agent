"""
AGEN — Lesson & Exercise Models
Stores AI-generated personalized lessons and individual exercises.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class LessonSkill(str, enum.Enum):
    VOCABULARY = "vocabulary"
    GRAMMAR    = "grammar"
    READING    = "reading"
    WRITING    = "writing"
    LISTENING  = "listening"


class LessonStatus(str, enum.Enum):
    GENERATED   = "generated"    # AI generated, not started
    IN_PROGRESS = "in_progress"  # User started
    COMPLETED   = "completed"    # User finished


class ExerciseType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK      = "fill_blank"
    FLASHCARD       = "flashcard"
    WRITING_PROMPT  = "writing_prompt"


class Lesson(Base):
    __tablename__ = "lessons"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String, ForeignKey("learner_profiles.id"), nullable=False)

    # Content metadata
    skill   = Column(String, nullable=False)          # vocabulary/grammar/reading/writing
    topic   = Column(String, nullable=False)          # e.g. "Daily Routines", "Past Tense"
    level   = Column(String, nullable=False)          # CEFR level at time of creation
    title   = Column(String, nullable=False)
    summary = Column(Text, nullable=True)             # Short AI-written intro
    content = Column(JSON, nullable=True)             # Extra lesson content (passage for reading/listening)

    # Progress tracking
    status    = Column(String, default=LessonStatus.GENERATED)
    score     = Column(Float, default=0.0)            # 0–100
    xp_earned = Column(Integer, default=0)
    total_exercises    = Column(Integer, default=0)
    correct_exercises  = Column(Integer, default=0)

    # Timestamps
    created_at   = Column(DateTime, default=datetime.utcnow)
    started_at   = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    exercises = relationship("Exercise", back_populates="lesson", order_by="Exercise.order")


class Exercise(Base):
    __tablename__ = "exercises"

    id        = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False)
    order     = Column(Integer, nullable=False, default=0)

    # Exercise content (flexible JSON for all types)
    type    = Column(String, nullable=False)   # ExerciseType enum value
    content = Column(JSON, nullable=False)     # Full AI-generated content
    # content schema by type:
    # multiple_choice: { question, passage?, options:{A,B,C,D}, correct_answer, explanation }
    # fill_blank:      { sentence, blank_word, hint?, options:[str] }
    # flashcard:       { word, phonetic?, definition, example, translation, image_hint? }
    # writing_prompt:  { prompt, guide_steps:[str], example_answer? }

    # User response
    user_answer = Column(Text, nullable=True)
    is_correct  = Column(Boolean, nullable=True)
    answered_at = Column(DateTime, nullable=True)

    # Relationship
    lesson = relationship("Lesson", back_populates="exercises")
