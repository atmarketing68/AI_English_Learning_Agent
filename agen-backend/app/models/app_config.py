"""Small key/value store for runtime state that must survive restarts (e.g. rotated Zalo OA tokens)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.core.database import Base


class AppConfig(Base):
    __tablename__ = "app_config"

    key = Column(String(60), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
