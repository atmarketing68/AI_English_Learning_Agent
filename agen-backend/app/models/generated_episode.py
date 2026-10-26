"""G11 · Tập podcast do AI sinh, admin duyệt rồi mới phát hành (cùng schema với services/media_library.EPISODES)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String

from app.core.database import Base

STATUS_DRAFT = "draft"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


class GeneratedEpisode(Base):
    __tablename__ = "generated_episodes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(String(4), nullable=False)
    topic = Column(String(120), nullable=True)               # what the admin asked for
    title = Column(String(120), nullable=False)
    status = Column(String(12), nullable=False, default=STATUS_DRAFT, index=True)
    content = Column(JSON, nullable=False)                   # full episode incl. answers (media_library schema)
    # Optional matching video (YouTube id + clip window in seconds); the transcript must match it.
    youtube_id = Column(String(20), nullable=True)
    video_start = Column(Integer, nullable=True)
    video_end = Column(Integer, nullable=True)
    auto = Column(Boolean, nullable=False, default=False, server_default="0")   # G12 · made by the scheduled Content Factory
    eval_score = Column(Float, nullable=True)
    eval_flagged = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
