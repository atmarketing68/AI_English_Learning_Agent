"""
G7 · Nhóm học (lớp / doanh nghiệp): create, join by code, members' progress,
weekly assignments and their completion.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.timeutil import local_day_start_utc, local_today
from app.models.group import KIND_CLASS, KIND_COMPANY, Group, GroupAssignment, GroupAssignmentDone, GroupMember
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.user import User
from app.services.league import week_bounds, weekly_xp
from app.services.streak_service import effective_streak

MAX_GROUPS_PER_OWNER = 20
MAX_MEMBERS = 200
ASSIGNMENT_SKILLS = ("vocabulary", "grammar", "reading", "listening")
CODE_PREFIX = {KIND_CLASS: "LOP", KIND_COMPANY: "CTY"}


class GroupError(ValueError):
    pass


def _new_code(db: Session, kind: str) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(20):
        code = f"{CODE_PREFIX.get(kind, 'LOP')}-" + "".join(secrets.choice(alphabet) for _ in range(4))
        if not db.query(Group).filter(Group.code == code).first():
            return code
    raise GroupError("Không tạo được mã nhóm, thử lại.")


def create_group(db: Session, owner: User, name: str, kind: str) -> Group:
    if owner.role != "teacher":
        raise GroupError("Chỉ tài khoản giáo viên / doanh nghiệp mới tạo được nhóm.")
    kind = kind if kind in (KIND_CLASS, KIND_COMPANY) else KIND_CLASS
    name = (name or "").strip()
    if not name:
        raise GroupError("Nhóm cần có tên.")
    if db.query(Group).filter(Group.owner_user_id == owner.id).count() >= MAX_GROUPS_PER_OWNER:
        raise GroupError(f"Tối đa {MAX_GROUPS_PER_OWNER} nhóm cho một tài khoản.")
    group = Group(owner_user_id=owner.id, name=name[:100], kind=kind, code=_new_code(db, kind))
    db.add(group)
    db.flush()
    return group


def owned_groups(db: Session, owner: User) -> list[Group]:
    return db.query(Group).filter(Group.owner_user_id == owner.id).order_by(Group.created_at).all()


def get_owned(db: Session, owner: User, group_id: str) -> Group:
    group = db.query(Group).filter(Group.id == group_id, Group.owner_user_id == owner.id).first()
    if not group:
        raise GroupError("Không tìm thấy nhóm.")
    return group


def join_group(db: Session, learner: LearnerProfile, code: str) -> Group:
    code = (code or "").strip().upper()
    group = db.query(Group).filter(Group.code == code).first()
    if not group:
        raise GroupError("Mã nhóm không đúng.")
    if db.query(GroupMember).filter(GroupMember.group_id == group.id, GroupMember.learner_id == learner.id).first():
        raise GroupError("Bạn đã ở trong nhóm này rồi.")
    if db.query(GroupMember).filter(GroupMember.group_id == group.id).count() >= MAX_MEMBERS:
        raise GroupError("Nhóm đã đầy.")
    db.add(GroupMember(group_id=group.id, learner_id=learner.id))
    db.flush()
    return group


def leave_group(db: Session, learner_id: str, group_id: str) -> bool:
    row = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.learner_id == learner_id).first()
    if not row:
        return False
    db.delete(row)
    db.flush()
    return True


def members_in_order(db: Session, group_id: str) -> list[GroupMember]:
    return db.query(GroupMember).filter(GroupMember.group_id == group_id).order_by(GroupMember.joined_at, GroupMember.id).all()


def learner_groups(db: Session, learner_id: str) -> list[Group]:
    return (
        db.query(Group).join(GroupMember, GroupMember.group_id == Group.id)
        .filter(GroupMember.learner_id == learner_id).order_by(GroupMember.joined_at).all()
    )


# ── Views ────────────────────────────────────────────────────────────────────
@dataclass
class MemberView:
    learner_id: str
    display_name: str
    level: str
    avatar: dict
    streak: int
    weekly_xp: int
    total_xp: int
    lessons: int
    active_today: bool
    assignments_done: int
    premium_source: str | None
    joined_at: datetime


@dataclass
class AssignmentView:
    id: str
    title: str
    skill: str
    topic: str
    note: str | None
    due_on: date | None
    created_at: datetime
    done_count: int = 0
    member_count: int = 0
    # learner-side
    started: bool = False
    done: bool = False
    score: int | None = None
    overdue: bool = False


def _assignment_view(a: GroupAssignment, rows: list[GroupAssignmentDone], member_count: int, learner_id: str | None, today: date) -> AssignmentView:
    mine = next((r for r in rows if r.learner_id == learner_id), None) if learner_id else None
    done = mine is not None and mine.done_at is not None
    return AssignmentView(
        id=a.id, title=a.title, skill=a.skill, topic=a.topic, note=a.note, due_on=a.due_on, created_at=a.created_at,
        done_count=sum(1 for r in rows if r.done_at is not None), member_count=member_count,
        started=mine is not None, done=done, score=mine.score if mine else None,
        overdue=bool(a.due_on and a.due_on < today and not done),
    )


def group_assignments(db: Session, group_id: str, learner_id: str | None = None) -> list[AssignmentView]:
    today = local_today()
    member_count = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
    out = []
    for a in db.query(GroupAssignment).filter(GroupAssignment.group_id == group_id).order_by(GroupAssignment.created_at.desc()).all():
        rows = db.query(GroupAssignmentDone).filter(GroupAssignmentDone.assignment_id == a.id).all()
        out.append(_assignment_view(a, rows, member_count, learner_id, today))
    return out


def member_views(db: Session, group: Group) -> list[MemberView]:
    from app.services.shop import avatar_of
    from app.services.subscription_service import premium_source

    members = members_in_order(db, group.id)
    ids = [m.learner_id for m in members]
    if not ids:
        return []
    today = local_today()
    monday, sunday = week_bounds(today)
    xp = weekly_xp(db, monday, sunday, ids)
    profiles = {p.id: p for p in db.query(LearnerProfile).filter(LearnerProfile.id.in_(ids)).all()}
    active = {lid for (lid,) in db.query(LearningEvent.learner_id).filter(LearningEvent.learner_id.in_(ids), LearningEvent.recorded_at >= local_day_start_utc()).distinct().all()}
    assignment_ids = [aid for (aid,) in db.query(GroupAssignment.id).filter(GroupAssignment.group_id == group.id).all()]
    done_counts: dict[str, int] = {}
    if assignment_ids:
        for (lid,) in db.query(GroupAssignmentDone.learner_id).filter(GroupAssignmentDone.assignment_id.in_(assignment_ids), GroupAssignmentDone.done_at.isnot(None)).all():
            done_counts[lid] = done_counts.get(lid, 0) + 1
    out = []
    for m in members:
        p = profiles.get(m.learner_id)
        if not p:
            continue
        out.append(MemberView(
            learner_id=p.id, display_name=p.display_name or "Học viên", level=p.overall_level or "A1", avatar=avatar_of(p),
            streak=effective_streak(p), weekly_xp=xp.get(p.id, 0), total_xp=p.total_xp or 0,
            lessons=p.total_lessons_completed or 0, active_today=p.id in active,
            assignments_done=done_counts.get(p.id, 0), premium_source=premium_source(db, p.user_id), joined_at=m.joined_at,
        ))
    out.sort(key=lambda v: (-v.weekly_xp, v.display_name))
    return out


# ── Assignments ──────────────────────────────────────────────────────────────
def create_assignment(db: Session, group: Group, title: str, skill: str, topic: str, due_on: date | None, note: str | None) -> GroupAssignment:
    if skill not in ASSIGNMENT_SKILLS:
        raise GroupError("Kỹ năng không hợp lệ.")
    title, topic = (title or "").strip(), (topic or "").strip()
    if not title or not topic:
        raise GroupError("Bài tập cần tiêu đề và chủ đề.")
    a = GroupAssignment(group_id=group.id, title=title[:140], skill=skill, topic=topic[:100], note=(note or "").strip()[:500] or None, due_on=due_on)
    db.add(a)
    db.flush()
    return a


def delete_assignment(db: Session, group: Group, assignment_id: str) -> bool:
    a = db.query(GroupAssignment).filter(GroupAssignment.id == assignment_id, GroupAssignment.group_id == group.id).first()
    if not a:
        return False
    db.query(GroupAssignmentDone).filter(GroupAssignmentDone.assignment_id == a.id).delete(synchronize_session=False)
    db.delete(a)
    db.flush()
    return True


def start_assignment(db: Session, learner: LearnerProfile, assignment_id: str) -> GroupAssignment:
    """The learner opens an assignment: returns its spec and records the start."""
    a = db.query(GroupAssignment).filter(GroupAssignment.id == assignment_id).first()
    if not a:
        raise GroupError("Không tìm thấy bài tập.")
    if not db.query(GroupMember).filter(GroupMember.group_id == a.group_id, GroupMember.learner_id == learner.id).first():
        raise GroupError("Bạn không ở trong nhóm này.")
    row = db.query(GroupAssignmentDone).filter(GroupAssignmentDone.assignment_id == a.id, GroupAssignmentDone.learner_id == learner.id).first()
    if not row:
        db.add(GroupAssignmentDone(assignment_id=a.id, learner_id=learner.id))
        db.flush()
    return a


def mark_done_on_finish(db: Session, learner_id: str, lesson_skill: str, lesson_id: str, score: float) -> int:
    """Called when a lesson is finished: the oldest started, unfinished assignment of that skill is done."""
    rows = (
        db.query(GroupAssignmentDone).join(GroupAssignment, GroupAssignment.id == GroupAssignmentDone.assignment_id)
        .filter(GroupAssignmentDone.learner_id == learner_id, GroupAssignmentDone.done_at.is_(None), GroupAssignment.skill == lesson_skill)
        .order_by(GroupAssignmentDone.started_at).all()
    )
    if not rows:
        return 0
    row = rows[0]
    row.done_at = datetime.now(timezone.utc).replace(tzinfo=None)
    row.lesson_id = lesson_id
    row.score = int(round(score))
    db.flush()
    return 1


def pending_assignments(db: Session, learner_id: str) -> list[tuple[Group, AssignmentView]]:
    """Open assignments across the learner's groups, soonest due first."""
    today = local_today()
    out: list[tuple[Group, AssignmentView]] = []
    for group in learner_groups(db, learner_id):
        for view in group_assignments(db, group.id, learner_id):
            if not view.done:
                out.append((group, view))
    out.sort(key=lambda gv: (gv[1].due_on or date.max, gv[1].created_at))
    return out
