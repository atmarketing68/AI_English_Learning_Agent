"""G10 · Chứng nhận hoàn thành (khoá mục tiêu hoặc do lớp / doanh nghiệp cấp), xác thực công khai bằng mã."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String

from app.core.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(24), nullable=False, unique=True, index=True)      # AGEN-XXXX-XXXX, printed on the certificate
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    kind = Column(String(12), nullable=False)                                # track | group
    ref_id = Column(String(40), nullable=True)                               # track id or group id
    title = Column(String(200), nullable=False)                              # e.g. "Lộ trình IELTS Foundation"
    recipient_name = Column(String(120), nullable=False)
    issuer_name = Column(String(160), nullable=False)                        # "AI AGENT ENGLISH" or the class / company
    note = Column(String(300), nullable=True)
    details = Column(JSON, nullable=True)                                    # level, xp, lessons, hours, skill scores
    issued_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    revoked = Column(Boolean, nullable=False, default=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
