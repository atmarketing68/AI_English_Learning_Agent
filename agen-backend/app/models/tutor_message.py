"""G8 · Hỏi đáp ngữ pháp với Bo — chat history, one row per message."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Text

from app.core.database import Base

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"


class TutorMessage(Base):
    __tablename__ = "tutor_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    role = Column(String(10), nullable=False)                 # user | assistant
    content = Column(Text, nullable=False)                    # question, or the answer in Vietnamese
    extra = Column(JSON, nullable=True)                       # assistant: examples, rule, related topics
    fallback = Column(Boolean, nullable=False, default=False) # assistant answer produced without the LLM
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
