"""Persisted placement test sessions."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String

from app.core.database import Base


class PlacementSession(Base):
    __tablename__ = "placement_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    answers = Column(JSON, nullable=False, default=list)
    current_index = Column(Integer, nullable=False, default=0)
    current_question = Column(JSON, nullable=True)
    last_correct = Column(Boolean, nullable=True)
    level = Column(String(10), nullable=False, default="A1")
    learner_age = Column(Integer, nullable=True)
    learner_grade = Column(String(20), nullable=True)
    assessment_type = Column(String(20), nullable=False, default="baseline")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)