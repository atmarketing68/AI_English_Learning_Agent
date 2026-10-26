"""G8 · Thi thử IELTS / TOEIC — one row per completed mock test."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String

from app.core.database import Base


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    exam_id = Column(String(40), nullable=False, index=True)       # id in services/mock_exams.py
    exam = Column(String(10), nullable=False)                      # ielts | toeic
    skill = Column(String(20), nullable=False)                     # listening | reading

    correct = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False, default=0)
    pct = Column(Float, nullable=False, default=0.0)
    estimate = Column(Float, nullable=False, default=0.0)          # IELTS band (0–9) or TOEIC section score (5–495)
    sections = Column(JSON, nullable=True)                         # [{id, title, correct, total}]
    answers = Column(JSON, nullable=True)                          # {question_id: given answer}
    seconds = Column(Integer, nullable=True)
    xp_earned = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
