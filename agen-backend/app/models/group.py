"""
G7 · Nhóm học: lớp học (giáo viên) hoặc doanh nghiệp (HR). The owner is a
`teacher` account; learners join with a short code; the owner assigns weekly
tasks and sees everyone's progress. A team plan on the owner's subscription
makes the first `seats` members Premium.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.core.database import Base

KIND_CLASS = "class"
KIND_COMPANY = "company"


def _uuid() -> str:
    return str(uuid.uuid4())


class Group(Base):
    __tablename__ = "groups"

    id = Column(String(36), primary_key=True, default=_uuid)
    owner_user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    kind = Column(String(20), nullable=False, default=KIND_CLASS)      # class | company
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g. "LOP-7K2P"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "learner_id", name="uq_group_member"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    group_id = Column(String(36), ForeignKey("groups.id"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GroupAssignment(Base):
    __tablename__ = "group_assignments"

    id = Column(String(36), primary_key=True, default=_uuid)
    group_id = Column(String(36), ForeignKey("groups.id"), nullable=False, index=True)
    title = Column(String(140), nullable=False)
    skill = Column(String(20), nullable=False)       # vocabulary | grammar | reading | listening
    topic = Column(String(100), nullable=False)
    note = Column(Text, nullable=True)
    due_on = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GroupAssignmentDone(Base):
    """One row per learner per assignment: created on start, done_at set when the lesson is finished."""
    __tablename__ = "group_assignment_done"
    __table_args__ = (UniqueConstraint("assignment_id", "learner_id", name="uq_assignment_learner"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    assignment_id = Column(String(36), ForeignKey("group_assignments.id"), nullable=False, index=True)
    learner_id = Column(String(36), ForeignKey("learner_profiles.id"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    lesson_id = Column(String(36), nullable=True)
    score = Column(Integer, nullable=True)
    done_at = Column(DateTime, nullable=True)


class GroupTest(Base):
    """G13 · Bài kiểm tra lớp: the owner assigns one mock exam (Listening/Reading) or Speaking exam
    to the whole group for a date window. A member's first attempt inside the window counts as the
    result; it bypasses the free daily limit."""
    __tablename__ = "group_tests"

    id = Column(String(36), primary_key=True, default=_uuid)
    group_id = Column(String(36), ForeignKey("groups.id"), nullable=False, index=True)
    kind = Column(String(12), nullable=False, default="mock")        # mock | speaking
    exam_id = Column(String(40), nullable=False)                     # id in mock_exams / speaking_exams
    title = Column(String(140), nullable=False)
    note = Column(Text, nullable=True)
    opens_on = Column(Date, nullable=False)
    due_on = Column(Date, nullable=False)
    reminded_on = Column(Date, nullable=True)                        # "due today" reminder sent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def today_local() -> date:
    from app.core.timeutil import local_today
    return local_today()
