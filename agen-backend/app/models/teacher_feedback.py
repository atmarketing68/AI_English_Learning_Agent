"""G10 · Nhận xét của giáo viên / HR cho một học viên trong nhóm (chung hoặc gắn với một bài làm)."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.core.database import Base


class TeacherFeedback(Base):
    __tablename__ = "teacher_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("groups.id"), nullable=False, index=True)
    teacher_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    target_type = Column(String(20), nullable=False, default="general")   # general | lesson | writing | exam | speaking_exam
    target_id = Column(String(36), nullable=True)
    target_label = Column(String(200), nullable=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
