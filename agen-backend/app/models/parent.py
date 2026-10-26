"""
AGEN — Parent models (P5 persona)
A parent account links to one or more learner profiles to monitor progress.
Master Plan §21: parent reports must be easy to read, not turn the child into a scoreboard.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ParentProfile(Base):
    """A parent/guardian account (User.role == 'parent')."""
    __tablename__ = "parent_profiles"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    display_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ParentChildLink(Base):
    """
    Links a parent to a learner. Created when a parent enters a learner's invite code.
    Many-to-many capable: a parent can have several children; a learner can have
    both parents linked.
    """
    __tablename__ = "parent_child_links"

    id = Column(String(36), primary_key=True, default=_uuid)
    parent_id = Column(String(36), ForeignKey("parent_profiles.id"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)

    relationship_label = Column(String(30), nullable=True)  # e.g. "mother", "father"
    created_at = Column(DateTime, default=datetime.utcnow)
