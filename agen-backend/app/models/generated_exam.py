"""G9 · Đề thi thử do AI sinh, admin duyệt rồi mới phát hành (cùng schema với services/mock_exams.EXAMS)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, JSON, String

from app.core.database import Base

STATUS_DRAFT = "draft"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


class GeneratedExam(Base):
    __tablename__ = "generated_exams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exam = Column(String(10), nullable=False)                      # ielts | toeic
    skill = Column(String(20), nullable=False)                     # listening | reading
    title = Column(String(140), nullable=False)
    topic = Column(String(120), nullable=True)
    status = Column(String(12), nullable=False, default=STATUS_DRAFT, index=True)
    content = Column(JSON, nullable=False)                         # full paper incl. answers (mock_exams schema)
    questions = Column(Float, nullable=False, default=0)
    eval_score = Column(Float, nullable=True)
    eval_flagged = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
