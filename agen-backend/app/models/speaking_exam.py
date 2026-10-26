"""G9 · Thi thử Speaking (IELTS Part 1–3 / TOEIC Speaking) — one row per attempt."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String

from app.core.database import Base

STATUS_STARTED = "started"
STATUS_FINISHED = "finished"


class SpeakingExamAttempt(Base):
    __tablename__ = "speaking_exam_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    exam_id = Column(String(40), nullable=False, index=True)       # id in services/speaking_exams.py
    exam = Column(String(10), nullable=False)                      # ielts | toeic
    status = Column(String(12), nullable=False, default=STATUS_STARTED)

    responses = Column(JSON, nullable=True)                        # [{task_id, transcript, duration, words, pronunciation}]
    estimate = Column(Float, nullable=True)                        # IELTS band 0–9 · TOEIC Speaking 0–200
    criteria = Column(JSON, nullable=True)                         # {fluency: 6.0, ...}
    feedback = Column(JSON, nullable=True)                         # agent output (task feedback, tips) or heuristic
    fallback = Column(Integer, nullable=False, default=0)          # 1 when the band came from the heuristic
    xp_earned = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)
