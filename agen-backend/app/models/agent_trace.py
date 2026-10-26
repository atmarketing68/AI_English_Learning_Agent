"""Persistent execution telemetry for AGEN agent calls."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, JSON, String

from app.core.database import Base


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id = Column(String(36), unique=True, nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    agent = Column(String(80), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    duration_ms = Column(Float, nullable=False, default=0.0)
    error = Column(String(255), nullable=True)
    input_data = Column(JSON, nullable=True)
    # ── AI Evaluation Framework (Master Plan §29) ──
    eval_score = Column(Float, nullable=True)          # overall quality 0-100
    eval_flags = Column(JSON, nullable=True)           # list of review flags
    eval_flagged = Column(Boolean, nullable=True, index=True)  # needs human review
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
