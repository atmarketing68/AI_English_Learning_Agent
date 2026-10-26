"""G10 · Câu lạc bộ nói: phòng 2–4 học viên, AI làm người dẫn, lần lượt từng người nói."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint

from app.core.database import Base

ROOM_WAITING = "waiting"
ROOM_ACTIVE = "active"
ROOM_FINISHED = "finished"


class SpeakingRoom(Base):
    __tablename__ = "speaking_rooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(12), nullable=False, unique=True, index=True)
    topic_id = Column(String(40), nullable=False)
    host_learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False)
    status = Column(String(12), nullable=False, default=ROOM_WAITING, index=True)
    is_public = Column(Integer, nullable=False, default=1)          # listed in the lobby while waiting
    question_index = Column(Integer, nullable=False, default=0)     # next topic question to ask
    turn_index = Column(Integer, nullable=False, default=0)         # index into members (join order)
    turns_taken = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RoomMember(Base):
    __tablename__ = "room_members"
    __table_args__ = (UniqueConstraint("room_id", "learner_id", name="uq_room_member"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String(36), ForeignKey("speaking_rooms.id"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    turns = Column(Integer, nullable=False, default=0)
    words = Column(Integer, nullable=False, default=0)
    xp_earned = Column(Integer, nullable=False, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    left_at = Column(DateTime, nullable=True)


class RoomMessage(Base):
    __tablename__ = "room_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String(36), ForeignKey("speaking_rooms.id"), nullable=False, index=True)
    seq = Column(Integer, nullable=False)                           # 1, 2, 3… per room (clients poll with after=seq)
    role = Column(String(10), nullable=False)                       # ai | learner | system
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=True)
    text = Column(Text, nullable=False)
    extra = Column(JSON, nullable=True)                             # ai: {feedback_vi, corrected, to_learner_id}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
