"""Persisted speaking roleplay sessions."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text

from app.core.database import Base


class RoleplaySession(Base):
    __tablename__ = "roleplay_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=False)
    history = Column(JSON, nullable=False, default=list)
    total_score = Column(Float, nullable=False, default=0.0)
    total_turns = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)