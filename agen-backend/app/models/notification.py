"""In-app notifications for learners (achievements, streaks, reminders)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)

    type = Column(String(30), nullable=False)   # achievement | streak | reminder | system
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=True)
    icon = Column(String(20), nullable=True)     # emoji

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
