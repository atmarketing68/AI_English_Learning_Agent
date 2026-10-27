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
    # G13 · one column per class test with the counted score
    from app.models.group import GroupTest
    tests = db.query(GroupTest).filter(GroupTest.group_id == group.id).order_by(GroupTest.due_on).all()
    test_scores = {t.id: {lid: _attempt_score(t, a)["estimate"] for lid, a in _test_attempts(db, t).items()} for t in tests}
    w.writerow(["Học viên", "Trình độ", "XP tuần này", "Tổng XP", "Chuỗi ngày", "Bài đã học", "Bài tập đã xong", "Tổng bài tập", "Học hôm nay", "Gói", "Tham gia"]
               + [a.title for a in assignments] + [f"Kiểm tra: {t.title} ({t.due_on.strftime('%d/%m')})" for t in tests])
    for m in member_views(db, group):
        done = done_by.get(m.learner_id, set())
        w.writerow([
            m.display_name, m.level, m.weekly_xp, m.total_xp, m.streak, m.lessons, m.assignments_done, len(assignments),
            "Có" if m.active_today else "Không", "Premium" if m.premium_source else "Miễn phí", m.joined_at.date().isoformat(),
        ] + ["x" if a.id in done else "" for a in assignments]
          + [f"{test_scores[t.id][m.learner_id]:g}" if test_scores[t.id].get(m.learner_id) is not None else "" for t in tests])
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
        "speaking_exams": [{"id": s.id, "title": (speaking_exams.get_exam(s.exam_id, db) or {}).get("title", s.exam_id), "exam": s.exam,
                            "estimate": s.estimate, "created_at": s.created_at} for s in speaking],
        "assignments": [a.__dict__ for a in group_assignments(db, group.id, learner.id)],
        "rubric_history": rubric_history(db, learner.id),
        "speaking_history": speaking_history(db, learner.id),
        "tests": _member_tests(db, group, learner.id),
        "feedback": [{"id": f.id, "target_type": f.target_type, "target_id": f.target_id, "target_label": f.target_label, "text": f.text,
                      "created_at": f.created_at, "read_at": f.read_at} for f in feedback],
    }


AI_CRITERIA_KEYS = {"task": "task_response", "coherence": "coherence_cohesion", "lexical": "lexical_resource", "grammar": "grammatical_range"}
RUBRIC_HISTORY_LIMIT = 20


def rubric_history(db: Session, learner_id: str) -> list[dict]:
    """G13 · IELTS writing bands over time, oldest first: the teacher's rubric when graded, else the AI band.
    Feeds the progress chart on the teacher's member page."""
    from app.agents.writing_agent import EXAM_GENRES
    from app.models.writing import WritingSubmission

    genres = [g for g, v in EXAM_GENRES.items() if v.get("exam") == "ielts"]
    if not genres:
        return []
    rows = (db.query(WritingSubmission).filter(WritingSubmission.learner_id == learner_id, WritingSubmission.genre.in_(genres))
            .order_by(WritingSubmission.created_at.desc()).limit(RUBRIC_HISTORY_LIMIT).all())
    out = []
    for w in reversed(rows):
        if w.teacher_rubric:
            criteria = {k: float(w.teacher_rubric[k]) for k in IELTS_CRITERIA if w.teacher_rubric.get(k) is not None}
            overall, source = w.teacher_band if w.teacher_band is not None else ielts_overall(list(criteria.values())), "teacher"
        else:
            band = (w.evaluation or {}).get("exam_band") if isinstance(w.evaluation, dict) else None
            if not band or band.get("overall") is None:
                continue
            raw = band.get("criteria") or {}
            criteria = {k: float(raw[ai]) for k, ai in AI_CRITERIA_KEYS.items() if raw.get(ai) is not None}
            overall, source = float(band["overall"]), "ai"
            if w.teacher_band is not None:
                overall, source = float(w.teacher_band), "teacher"
        out.append({"submission_id": w.id, "title": w.prompt_title, "created_at": w.created_at, "source": source,
                    "overall": overall, "criteria": criteria})
    return out


SPEAKING_CRITERIA_KEYS = {"fluency": "fluency_coherence", "lexical": "lexical_resource", "grammar": "grammatical_range", "pronunciation": "pronunciation"}


def speaking_history(db: Session, learner_id: str) -> list[dict]:
    """G14 · IELTS Speaking bands over time (finished mock tests), oldest first — the teacher's speaking chart."""
    from app.models.speaking_exam import STATUS_FINISHED, SpeakingExamAttempt
    from app.services import speaking_exams

    rows = (db.query(SpeakingExamAttempt)
            .filter(SpeakingExamAttempt.learner_id == learner_id, SpeakingExamAttempt.status == STATUS_FINISHED,
                    SpeakingExamAttempt.exam == "ielts", SpeakingExamAttempt.estimate.isnot(None))
            .order_by(SpeakingExamAttempt.created_at.desc()).limit(RUBRIC_HISTORY_LIMIT).all())
    out = []
    for a in reversed(rows):
        raw = a.criteria or {}
        criteria = {k: float(raw[src]) for k, src in SPEAKING_CRITERIA_KEYS.items() if isinstance(raw.get(src), (int, float))}
        out.append({"submission_id": a.id, "title": (speaking_exams.get_exam(a.exam_id, db) or {}).get("title", a.exam_id),
                    "created_at": a.created_at, "source": "estimate" if a.fallback else "ai", "overall": float(a.estimate), "criteria": criteria})
    return out


def learner_class_tests(db: Session, learner_id: str, limit: int = 20) -> list[dict]:
    """G14 · Class tests across the learner's groups (for the parent report), newest due date first."""
    out = []
    for g in learner_groups(db, learner_id):
        for t in group_tests(db, g.id, learner_id):
            if t["available"] or t["mine"]["done"]:
                out.append({**t, "group_name": g.name})
    out.sort(key=lambda t: t["due_on"], reverse=True)
    return out[:limit]


def _member_tests(db: Session, group: Group, learner_id: str) -> list[dict]:
    member_ids = [m.learner_id for m in members_in_order(db, group.id)]
    from app.models.group import GroupTest
    today = local_today()
    rows = db.query(GroupTest).filter(GroupTest.group_id == group.id).order_by(GroupTest.due_on.desc()).limit(20).all()
    return [test_view(db, t, member_ids, learner_id, today) for t in rows]


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



IELTS_CRITERIA = {"task": "Task Response", "coherence": "Coherence & Cohesion", "lexical": "Lexical Resource", "grammar": "Grammatical Range & Accuracy"}
IELTS_CRITERIA_VI = {"task": "Đáp ứng đề", "coherence": "Mạch lạc & liên kết", "lexical": "Từ vựng", "grammar": "Ngữ pháp"}


def ielts_overall(scores: list[float]) -> float:
    """IELTS rounding of the mean: .25 rounds up to .5, .75 rounds up to the next whole band."""
    import math
    avg = sum(scores) / len(scores)
    base = math.floor(avg)
    frac = avg - base
    return base + (0.0 if frac < 0.25 else 0.5 if frac < 0.75 else 1.0)


def grade_writing(db: Session, group: Group, teacher: User, learner: LearnerProfile, submission, score: float | None,
                  band: float | None = None, comment: str | None = None, rubric: dict | None = None):
    """G11 · Teacher re-grade of one writing piece; score None (and no rubric) clears it.
    G12 · an IELTS rubric (4 criteria, 0–9 in steps of 0.5) sets the band; the /100 score defaults to band/9.
    Notifies the learner through a feedback row."""
    from app.agents.writing_agent import EXAM_GENRES

    exam = (EXAM_GENRES.get(submission.genre or "") or {}).get("exam")
    if rubric:
        if exam != "ielts":
            raise GroupError("Rubric 4 tiêu chí chỉ dùng cho bài IELTS.")
        clean = {}
        for key in IELTS_CRITERIA:
            try:
                v = float(rubric[key])
            except (KeyError, TypeError, ValueError):
                raise GroupError("Cần đủ 4 tiêu chí: đáp ứng đề, mạch lạc, từ vựng, ngữ pháp.")
            if not (0 <= v <= 9 and v * 2 == int(v * 2)):
                raise GroupError("Mỗi tiêu chí từ 0 đến 9, bước 0,5.")
            clean[key] = v
        band = ielts_overall(list(clean.values()))
        if score is None:
            score = round(band / 9 * 100)
        submission.teacher_rubric = clean
    elif score is not None:
        submission.teacher_rubric = None
    if score is None:
        submission.teacher_score = submission.teacher_band = submission.teacher_comment = None
        submission.teacher_user_id = submission.teacher_scored_at = submission.teacher_rubric = None
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
    if submission.teacher_rubric:
        parts.append(", ".join(f"{IELTS_CRITERIA_VI[k]} {v:g}" for k, v in submission.teacher_rubric.items()))
    text = " · ".join(parts) + (f"\n{submission.teacher_comment}" if submission.teacher_comment else "")
    return add_feedback(db, group, teacher, learner, text, "writing", submission.id, submission.prompt_title)


# ── G13 · Bài kiểm tra lớp (thi thử giao cho cả lớp, có hạn) ──────────────────
TEST_KINDS = ("mock", "speaking")
MAX_TEST_WINDOW_DAYS = 60
TEST_REMIND_FROM_HOUR = 8          # giờ VN: nhắc "hôm nay hết hạn" từ 8h sáng


def test_catalogue(db: Session) -> list[dict]:
    """Every published test a teacher can assign: Listening/Reading mock tests + Speaking tests."""
    from app.services import mock_exams, speaking_exams
    out = [{"kind": "mock", "id": e["id"], "exam": e["exam"], "skill": e["skill"], "title": e["title"], "minutes": e["minutes"]}
           for e in mock_exams.list_exams(db)]
    out += [{"kind": "speaking", "id": e["id"], "exam": e["exam"], "skill": "speaking", "title": e["title"], "minutes": e["minutes"]}
            for e in speaking_exams.list_exams(db)]
    return out


def _test_exam(db: Session, kind: str, exam_id: str) -> dict | None:
    from app.services import mock_exams, speaking_exams
    if kind == "speaking":
        return speaking_exams.get_exam(exam_id, db)
    return mock_exams.get_exam(exam_id, db)


def create_test(db: Session, group: Group, kind: str, exam_id: str, opens_on: date | None, due_on: date,
                note: str | None = None, title: str | None = None, repeat: str | None = None):
    from app.models.group import GroupTest
    from app.services.notification_service import create_notification

    if kind not in TEST_KINDS:
        raise GroupError("Loại bài kiểm tra không hợp lệ.")
    exam = _test_exam(db, kind, exam_id)
    if not exam:
        raise GroupError("Không tìm thấy đề thi.")
    today = local_today()
    opens_on = opens_on or today
    if due_on < opens_on or due_on < today:
        raise GroupError("Hạn nộp phải sau ngày mở đề và không ở quá khứ.")
    if (due_on - opens_on).days > MAX_TEST_WINDOW_DAYS:
        raise GroupError(f"Một bài kiểm tra mở tối đa {MAX_TEST_WINDOW_DAYS} ngày.")
    if repeat not in (None, "monthly"):
        raise GroupError("Chỉ hỗ trợ lặp lại hằng tháng.")
    test = GroupTest(group_id=group.id, kind=kind, exam_id=exam_id, title=((title or "").strip() or exam["title"])[:140],
                     note=(note or "").strip()[:500] or None, opens_on=opens_on, due_on=due_on, repeat=repeat)
    db.add(test)
    db.flush()
    when = "từ hôm nay" if opens_on <= today else f"mở ngày {opens_on.strftime('%d/%m')}"
    for m in members_in_order(db, group.id):
        create_notification(db, m.learner_id, type="group_test", title=f"Bài kiểm tra lớp {group.name}: {test.title}",
                            body=f"{when.capitalize()}, hạn {due_on.strftime('%d/%m')}. Bài làm đầu tiên được tính điểm.", icon="📝")
    db.flush()
    return test


def delete_test(db: Session, group: Group, test_id: str) -> bool:
    from app.models.exam_attempt import ExamAttempt
    from app.models.group import GroupTest
    from app.models.speaking_exam import SpeakingExamAttempt

    test = db.query(GroupTest).filter(GroupTest.id == test_id, GroupTest.group_id == group.id).first()
    if not test:
        return False
    # Attempts stay in the learners' history; they just stop pointing at the test.
    for model in (ExamAttempt, SpeakingExamAttempt):
        db.query(model).filter(model.group_test_id == test.id).update({"group_test_id": None}, synchronize_session=False)
    db.delete(test)
    db.flush()
    return True


def _test_status(test, today: date) -> str:
    return "upcoming" if today < test.opens_on else "closed" if today > test.due_on else "open"


def _test_attempts(db: Session, test) -> dict:
    """learner_id → the attempt that counts (first finished one linked to the test)."""
    from app.models.exam_attempt import ExamAttempt
    from app.models.speaking_exam import STATUS_FINISHED, SpeakingExamAttempt

    if test.kind == "speaking":
        rows = (db.query(SpeakingExamAttempt).filter(SpeakingExamAttempt.group_test_id == test.id, SpeakingExamAttempt.status == STATUS_FINISHED)
                .order_by(SpeakingExamAttempt.finished_at).all())
    else:
        rows = db.query(ExamAttempt).filter(ExamAttempt.group_test_id == test.id).order_by(ExamAttempt.created_at).all()
    out: dict = {}
    for r in rows:
        out.setdefault(r.learner_id, r)
    return out


def _attempt_score(test, a) -> dict:
    if a is None:
        return {"done": False, "pct": None, "estimate": None, "seconds": None, "submitted_at": None, "attempt_id": None}
    if test.kind == "speaking":
        return {"done": True, "pct": None, "estimate": a.estimate, "seconds": None, "submitted_at": a.finished_at, "attempt_id": a.id}
    return {"done": True, "pct": a.pct, "estimate": a.estimate, "seconds": a.seconds, "submitted_at": a.created_at, "attempt_id": a.id}


def _avg(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else None


def test_view(db: Session, test, member_ids: list[str], learner_id: str | None = None, today: date | None = None) -> dict:
    exam = _test_exam(db, test.kind, test.exam_id) or {}
    attempts = {lid: a for lid, a in _test_attempts(db, test).items() if lid in member_ids}
    scores = [_attempt_score(test, a) for a in attempts.values()]
    view = {
        "id": test.id, "group_id": test.group_id, "kind": test.kind, "exam_id": test.exam_id, "title": test.title, "note": test.note,
        "exam": exam.get("exam"), "skill": exam.get("skill", "speaking" if test.kind == "speaking" else None), "minutes": exam.get("minutes"),
        "available": bool(exam), "opens_on": test.opens_on, "due_on": test.due_on, "status": _test_status(test, today or local_today()),
        "done_count": len(attempts), "member_count": len(member_ids),
        "avg_pct": _avg([s["pct"] for s in scores]), "avg_estimate": _avg([s["estimate"] for s in scores]), "created_at": test.created_at,
        "repeat": test.repeat, "next_test_id": test.next_test_id,
    }
    if learner_id:
        view["mine"] = _attempt_score(test, attempts.get(learner_id))
    return view


def group_tests(db: Session, group_id: str, learner_id: str | None = None) -> list[dict]:
    from app.models.group import GroupTest
    member_ids = [m.learner_id for m in members_in_order(db, group_id)]
    today = local_today()
    rows = db.query(GroupTest).filter(GroupTest.group_id == group_id).order_by(GroupTest.due_on.desc(), GroupTest.created_at.desc()).all()
    return [test_view(db, t, member_ids, learner_id, today) for t in rows]


def test_results(db: Session, group: Group, test_id: str) -> dict:
    """Teacher table: every member with their counted attempt (or not yet), best first."""
    from app.models.group import GroupTest
    from app.services.shop import avatar_of

    test = db.query(GroupTest).filter(GroupTest.id == test_id, GroupTest.group_id == group.id).first()
    if not test:
        raise GroupError("Không tìm thấy bài kiểm tra.")
    members = members_in_order(db, group.id)
    ids = [m.learner_id for m in members]
    attempts = _test_attempts(db, test)
    profiles = {p.id: p for p in db.query(LearnerProfile).filter(LearnerProfile.id.in_(ids)).all()} if ids else {}
    rows = []
    for lid in ids:
        p = profiles.get(lid)
        if not p:
            continue
        rows.append({"learner_id": lid, "display_name": p.display_name or "Học viên", "level": p.overall_level or "A1", "avatar": avatar_of(p),
                     **_attempt_score(test, attempts.get(lid))})
    rows.sort(key=lambda r: (not r["done"], -(r["estimate"] or 0), r["display_name"]))
    estimates = [r["estimate"] for r in rows if r["done"]]
    view = test_view(db, test, ids)
    view.update({
        "results": rows,
        "min_estimate": min(estimates) if estimates else None,
        "max_estimate": max(estimates) if estimates else None,
    })
    return view


def open_test_for(db: Session, learner_id: str, test_id: str | None, kind: str, exam_id: str):
    """The class test this attempt counts for, or None: the learner is a member, the window is open,
    the exam matches and nothing has been counted yet. Only then is the free daily limit waived."""
    from app.models.group import GroupTest

    if not test_id:
        return None
    test = db.query(GroupTest).filter(GroupTest.id == test_id, GroupTest.kind == kind, GroupTest.exam_id == exam_id).first()
    if not test or _test_status(test, local_today()) != "open":
        return None
    if not db.query(GroupMember).filter(GroupMember.group_id == test.group_id, GroupMember.learner_id == learner_id).first():
        return None
    if learner_id in _test_attempts(db, test):
        return None
    return test


def add_months(d: date, months: int = 1) -> date:
    """Same day next month, clamped to the month's last day (31 Jan → 28/29 Feb)."""
    import calendar
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def set_test_repeat(db: Session, group: Group, test_id: str, repeat: str | None):
    from app.models.group import GroupTest
    if repeat not in (None, "monthly"):
        raise GroupError("Chỉ hỗ trợ lặp lại hằng tháng.")
    test = db.query(GroupTest).filter(GroupTest.id == test_id, GroupTest.group_id == group.id).first()
    if not test:
        raise GroupError("Không tìm thấy bài kiểm tra.")
    test.repeat = repeat
    db.flush()
    return test


def _next_exam_id(db: Session, test) -> str:
    """Rotate to a test of the same kind, exam and skill the class has not had yet; else reuse the same one."""
    from app.models.group import GroupTest
    current = _test_exam(db, test.kind, test.exam_id) or {}
    used = {eid for (eid,) in db.query(GroupTest.exam_id).filter(GroupTest.group_id == test.group_id, GroupTest.kind == test.kind).all()}
    same = [c for c in test_catalogue(db) if c["kind"] == test.kind and c["exam"] == current.get("exam") and c["skill"] == current.get("skill")]
    fresh = [c["id"] for c in same if c["id"] not in used]
    return fresh[0] if fresh else test.exam_id


def roll_recurring_tests(db: Session, today: date | None = None) -> dict:
    """Hourly cron: when a monthly test has closed, create next month's (same window, the next unused exam).
    Catches up if the cron missed whole months, and never creates one whose window is already over."""
    from app.models.group import GroupTest
    today = today or local_today()
    stats = {"created": 0}
    due = db.query(GroupTest).filter(GroupTest.repeat == "monthly", GroupTest.next_test_id.is_(None), GroupTest.due_on < today).all()
    for test in due:
        group = db.query(Group).filter(Group.id == test.group_id).first()
        if not group:
            continue
        opens_on, due_on, months = test.opens_on, test.due_on, 0
        while due_on < today and months < 24:
            months += 1
            opens_on, due_on = add_months(test.opens_on, months), add_months(test.due_on, months)
        exam_id = _next_exam_id(db, test)
        exam = _test_exam(db, test.kind, exam_id)
        if not exam:
            continue
        same_title = test.title == (_test_exam(db, test.kind, test.exam_id) or {}).get("title")
        try:
            nxt = create_test(db, group, test.kind, exam_id, opens_on, due_on, test.note, None if same_title else test.title, repeat="monthly")
        except GroupError:
            continue
        test.next_test_id = nxt.id
        stats["created"] += 1
    db.commit()
    return stats


def remind_due_tests(db: Session, now: datetime | None = None) -> dict:
    """Hourly cron: on the due day (from 8:00 VN), one reminder to members who have not taken the test."""
    from app.core.timeutil import LEARNER_TZ
    from app.models.group import GroupTest
    from app.services.notification_service import create_notification
    from app.services.reminders import ReminderMessage, push_to_learner

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    local = now.astimezone(LEARNER_TZ)
    stats = {"tests": 0, "notified": 0, "push": 0}
    if local.hour < TEST_REMIND_FROM_HOUR:
        return stats
    today = local.date()
    tests = db.query(GroupTest).filter(GroupTest.due_on == today, GroupTest.opens_on <= today).all()
    for test in tests:
        if test.reminded_on == today:
            continue
        test.reminded_on = today
        stats["tests"] += 1
        group = db.query(Group).filter(Group.id == test.group_id).first()
        done = _test_attempts(db, test)
        for m in members_in_order(db, test.group_id):
            if m.learner_id in done:
                continue
            title = f"Hôm nay hết hạn bài kiểm tra: {test.title}"
            body = f"Lớp {group.name if group else ''} — làm ngay để giáo viên có điểm của bạn."
            create_notification(db, m.learner_id, type="group_test", title=title, body=body, icon="⏰")
            stats["notified"] += 1
            learner = db.query(LearnerProfile).filter(LearnerProfile.id == m.learner_id).first()
            if learner:
                try:
                    stats["push"] += push_to_learner(db, learner, ReminderMessage(title=title, body=body, url="/classes"))
                except Exception:   # a push channel must never break the run
                    pass
    db.commit()
    return stats
