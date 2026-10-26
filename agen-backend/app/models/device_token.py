"""
G8 · Native push (FCM) device tokens for the Capacitor app.

One row per device. The learner id is set for learner accounts, the user id
always; parents register with just the user id. Rows are deleted when FCM
reports the token as unregistered.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.core.database import Base


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=True, index=True)
    platform = Column(String(10), nullable=False, default="android")   # android | ios
    token = Column(String(400), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_sent_at = Column(DateTime, nullable=True)
