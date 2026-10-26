"""
G7 · Nhóm học (lớp / doanh nghiệp): create, join by code, members' progress,
weekly assignments and their completion.
"""
from __future__ import annotations

import csv
import io
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


# ── G8 · Báo cáo nhóm (CSV) ──────────────────────────────────────────────────
def report_csv(db: Session, group: Group) -> str:
    """One row per member with this week's XP, streak, lessons and assignment completion."""
    assignments = group_assignments(db, group.id)
    done_by: dict[str, set[str]] = {}
    if assignments:
        rows = db.query(GroupAssignmentDone).filter(GroupAssignmentDone.assignment_id.in_([a.id for a in assignments]), GroupAssignmentDone.done_at.isnot(None)).all()
        for r in rows:
            done_by.setdefault(r.learner_id, set()).add(r.assignment_id)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Nhóm", group.name, "Mã", group.code, "Xuất ngày", local_today().isoformat()])
    w.writerow([])
    w.writerow(["Học viên", "Trình độ", "XP tuần này", "Tổng XP", "Chuỗi ngày", "Bài đã học", "Bài tập đã xong", "Tổng bài tập", "Học hôm nay", "Gói", "Tham gia"]
               + [a.title for a in assignments])
    for m in member_views(db, group):
        done = done_by.get(m.learner_id, set())
        w.writerow([
            m.display_name, m.level, m.weekly_xp, m.total_xp, m.streak, m.lessons, m.assignments_done, len(assignments),
            "Có" if m.active_today else "Không", "Premium" if m.premium_source else "Miễn phí", m.joined_at.date().isoformat(),
        ] + ["x" if a.id in done else "" for a in assignments])
    return buf.getvalue()


# ── G10 · Chi tiết bài làm của một thành viên + nhận xét ──────────────────────
def member_of(db: Session, group: Group, learner_id: str) -> LearnerProfile:
    if not db.query(GroupMember).filter(GroupMember.group_id == group.id, GroupMember.learner_id == learner_id).first():
        raise GroupError("Học viên không ở trong nhóm này.")
    learner = db.query(LearnerProfile).filter(LearnerProfile.id == learner_id).first()
    if not learner:
        raise GroupError("Không tìm thấy học viên.")
    return learner


def member_detail(db: Session, group: Group, learner: LearnerProfile) -> dict:
    """Recent work across lessons, writing, mock tests and speaking tests, plus assignment status and feedback."""
    from app.models.exam_attempt import ExamAttempt
    from app.models.lesson import Lesson
    from app.models.speaking_exam import STATUS_FINISHED, SpeakingExamAttempt
    from app.models.teacher_feedback import TeacherFeedback
    from app.models.writing import WritingSubmission
    from app.services import mock_exams, speaking_exams
    from app.services.shop import avatar_of

    lessons = (db.query(Lesson).filter(Lesson.learner_id == learner.id, Lesson.status == "completed")
               .order_by(Lesson.completed_at.desc()).limit(15).all())
    writings = db.query(WritingSubmission).filter(WritingSubmission.learner_id == learner.id).order_by(WritingSubmission.created_at.desc()).limit(10).all()
    exams = db.query(ExamAttempt).filter(ExamAttempt.learner_id == learner.id).order_by(ExamAttempt.created_at.desc()).limit(10).all()
    speaking = (db.query(SpeakingExamAttempt).filter(SpeakingExamAttempt.learner_id == learner.id, SpeakingExamAttempt.status == STATUS_FINISHED)
                .order_by(SpeakingExamAttempt.created_at.desc()).limit(10).all())
    feedback = (db.query(TeacherFeedback).filter(TeacherFeedback.group_id == group.id, TeacherFeedback.learner_id == learner.id)
                .order_by(TeacherFeedback.created_at.desc()).limit(50).all())
    today = local_today()
    monday, sunday = week_bounds(today)

    def band(w):
        b = (w.evaluation or {}).get("exam_band") if isinstance(w.evaluation, dict) else None
        return float(b["overall"]) if b and b.get("overall") is not None else None

    return {
        "learner_id": learner.id, "display_name": learner.display_name or "Học viên", "level": learner.overall_level or "A1", "avatar": avatar_of(learner),
        "streak": effective_streak(learner), "total_xp": learner.total_xp or 0, "weekly_xp": weekly_xp(db, monday, sunday, [learner.id]).get(learner.id, 0),
        "lessons_completed": learner.total_lessons_completed or 0,
        "skills": {k: round(getattr(learner, f"{k}_score", 0) or 0) for k in ("listening", "speaking", "reading", "writing", "vocabulary", "grammar")},
        "last_active_at": learner.last_active_at,
        "lessons": [{"id": l.id, "title": l.title, "skill": l.skill, "topic": l.topic, "score": round(l.score or 0), "completed_at": l.completed_at} for l in lessons],
        "writings": [{"id": w.id, "prompt_title": w.prompt_title, "genre": w.genre, "score": w.overall_score, "grade": w.grade, "band": band(w),
                      "teacher_score": w.teacher_score, "teacher_band": w.teacher_band,
                      "word_count": w.word_count or 0, "excerpt": (w.user_text or "")[:160], "created_at": w.created_at} for w in writings],
        "exams": [{"id": e.id, "title": (mock_exams.get_exam(e.exam_id, db) or {}).get("title", e.exam_id), "exam": e.exam, "skill": e.skill,
                   "pct": e.pct, "estimate": e.estimate, "created_at": e.created_at} for e in exams],
        "speaking_exams": [{"id": s.id, "title": (speaking_exams.get_exam(s.exam_id) or {}).get("title", s.exam_id), "exam": s.exam,
                            "estimate": s.estimate, "created_at": s.created_at} for s in speaking],
        "assignments": [a.__dict__ for a in group_assignments(db, group.id, learner.id)],
        "feedback": [{"id": f.id, "target_type": f.target_type, "target_id": f.target_id, "target_label": f.target_label, "text": f.text,
                      "created_at": f.created_at, "read_at": f.read_at} for f in feedback],
    }


def add_feedback(db: Session, group: Group, teacher: User, learner: LearnerProfile, text: str,
                 target_type: str = "general", target_id: str | None = None, target_label: str | None = None):
    from app.models.teacher_feedback import TeacherFeedback
    from app.services.notification_service import create_notification

    text = (text or "").strip()
    if not text:
        raise GroupError("Nhận xét không được để trống.")
    fb = TeacherFeedback(group_id=group.id, teacher_user_id=teacher.id, learner_id=learner.id, target_type=target_type,
                         target_id=target_id, target_label=(target_label or None) and target_label[:200], text=text[:2000])
    db.add(fb)
    who = teacher.full_name or "Giáo viên"
    about = f" về \"{target_label}\"" if target_label else ""
    create_notification(db, learner.id, type="teacher_feedback", title=f"{who} vừa nhận xét bài của bạn{about}", body=text[:200], icon="💬")
    db.flush()
    return fb



def grade_writing(db: Session, group: Group, teacher: User, learner: LearnerProfile, submission, score: float | None,
                  band: float | None = None, comment: str | None = None):
    """G11 · Teacher re-grade of one writing piece; score None clears it. Notifies the learner through a feedback row."""
    from app.agents.writing_agent import EXAM_GENRES

    exam = (EXAM_GENRES.get(submission.genre or "") or {}).get("exam")
    if score is None:
        submission.teacher_score = submission.teacher_band = submission.teacher_comment = None
        submission.teacher_user_id = submission.teacher_scored_at = None
        return None
    if not 0 <= score <= 100:
        raise GroupError("Điểm phải từ 0 đến 100.")
    if band is not None:
        if exam == "ielts" and not (0 <= band <= 9 and (band * 2) == int(band * 2)):
            raise GroupError("Band IELTS từ 0 đến 9, bước 0,5.")
        if exam == "toeic" and not 0 <= band <= 200:
            raise GroupError("Điểm TOEIC Writing từ 0 đến 200.")
        if not exam:
            band = None
    submission.teacher_score = round(float(score), 1)
    submission.teacher_band = band
    submission.teacher_comment = (comment or "").strip()[:2000] or None
    submission.teacher_user_id = teacher.id
    submission.teacher_scored_at = datetime.now(timezone.utc).replace(tzinfo=None)
    parts = [f"Điểm giáo viên chấm lại: {submission.teacher_score:g}/100"]
    if band is not None:
        parts.append(f"band {band:g}" if exam == "ielts" else f"TOEIC Writing {band:g}/200")
    text = " · ".join(parts) + (f"\n{submission.teacher_comment}" if submission.teacher_comment else "")
    return add_feedback(db, group, teacher, learner, text, "writing", submission.id, submission.prompt_title)
