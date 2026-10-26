"""Privacy consent records for learner data and AI/audio processing."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String

from app.core.database import Base


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(String(80), nullable=False)
    policy_version = Column(String(30), nullable=False)
    granted = Column(Boolean, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
