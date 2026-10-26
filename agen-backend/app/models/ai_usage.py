"""G10 · One row per LLM / TTS call with an estimated cost, so admins see AI spend per feature and per user."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.core.database import Base


class AiUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)        # no FK: usage must never block on user rows
    feature = Column(String(60), nullable=False, index=True)        # agent name or API area (review/lookup, tts…)
    provider = Column(String(20), nullable=False)                   # gemini | openai | voicebox …
    model = Column(String(60), nullable=True)
    input_chars = Column(Integer, nullable=False, default=0)
    output_chars = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)            # estimate from settings.AI_PRICE_*
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
