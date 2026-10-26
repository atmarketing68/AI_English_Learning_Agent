"""
Spaced-repetition review items (G1 · Ôn tập thông minh).

One row per thing a learner should remember: a word they studied ("vocab") or a
question they got wrong ("mistake"). Scheduling uses FSRS memory state
(stability / difficulty) — see app/services/srs.py.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint

from app.core.database import Base


class ReviewItem(Base):
    __tablename__ = "review_items"
    __table_args__ = (
        UniqueConstraint("learner_id", "kind", "key", name="uq_review_item_learner_kind_key"),
        Index("ix_review_items_learner_due", "learner_id", "due_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False)

    kind = Column(String(20), nullable=False)    # "vocab" | "mistake"
    key = Column(String(128), nullable=False)    # vocab: lowercased word; mistake: question hash

    # What the learner sees.
    # vocab:   front = word, back = Vietnamese meaning (or English definition)
    # mistake: front = question/sentence, back = correct answer text
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    phonetic = Column(String(100), nullable=True)
    example = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    extra = Column(JSON, nullable=True)           # mistake: {exercise_type, options, last_wrong_answer}
    source_lesson_id = Column(String(36), nullable=True)

    # FSRS memory state. stability is None until the first review.
    state = Column(String(20), nullable=False, default="new")   # new | review | relearning
    stability = Column(Float, nullable=True)
    difficulty = Column(Float, nullable=True)
    reps = Column(Integer, nullable=False, default=0)
    lapses = Column(Integer, nullable=False, default=0)
    due_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_review_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
