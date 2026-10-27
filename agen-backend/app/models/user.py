import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, false as sa_false
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """Core user account — handles authentication."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(20), default="learner", nullable=False)  # learner | parent
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    # G3 · học thử: created without an email/password; claimed later via /auth/claim.
    is_guest = Column(Boolean, default=False, server_default=sa_false(), nullable=False)
    claimed_at = Column(DateTime, nullable=True)      # G5 · when a guest saved the account (conversion stats)
    signup_source = Column(String(60), nullable=True, index=True)  # G14 · first-touch utm_source / referrer host
    # G9 · Zalo OA: the follower id once the person sent their link code to the OA; the code they must send.
    zalo_user_id = Column(String(40), unique=True, nullable=True)
    zalo_link_code = Column(String(12), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    learner_profile = relationship("LearnerProfile", back_populates="user", uselist=False)
