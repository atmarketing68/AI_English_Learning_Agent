"""Durable state for asynchronous agent jobs."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String

from app.core.database import Base


class AgentJob(Base):
    __tablename__ = "agent_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), unique=True, nullable=False, index=True)
    trace_id = Column(String(36), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    agent = Column(String(80), nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    result = Column(JSON, nullable=True)
    error = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
