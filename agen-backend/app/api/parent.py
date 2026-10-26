"""
AGEN — Parent API (P5 persona)
Parents link to their children via an invite code, then view easy-to-read
weekly progress reports with actionable guidance.

Master Plan §21: report answers "What improved? / What needs help? / What should
parents do?" — NOT a raw scoreboard.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.parent import ParentProfile, ParentChildLink

router = APIRouter(prefix="/parent", tags=["Parent"])

SKILL_LABELS_VI = {
    "vocabulary": "Từ vựng", "grammar": "Ngữ pháp", "reading": "Đọc",
    "listening": "Nghe", "speaking": "Nói", "writing": "Viết",
}


# ── Schemas ───────────────────────────────────────────────────────────────────
class LinkChildRequest(BaseModel):
    invite_code: str = Field(min_length=4, max_length=20)
    relationship_label: str | None = None


class ChildSummary(BaseModel):
    learner_id: str
    display_name: str
    overall_level: str
    total_xp: int
    current_streak: int
    total_lessons_completed: int
    relationship_label: str | None


class SkillImprovement(BaseModel):
    skill: str
    label: str
    score: float


class ChildReport(BaseModel):
    learner_id: str
    display_name: str
    overall_level: str
    # This week (last 7 days)
    sessions_this_week: int
    xp_this_week: int
    study_minutes_estimate: int
    current_streak: int
    accuracy_pct: float
    skills: list[SkillImprovement]
    best_skill: str
    focus_skill: str
    # Human-readable guidance (Master Plan §21)
    what_improved: str
    what_needs_help: str
    what_to_do: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_parent(db: Session, user: User) -> ParentProfile:
    if user.role != "parent":
        raise HTTPException(status_code=403, detail="Tài khoản này không phải phụ huynh.")
    parent = db.query(ParentProfile).filter(ParentProfile.user_id == user.id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ phụ huynh.")
    return parent


def _assert_linked(db: Session, parent_id: str, learner_id: str) -> ParentChildLink:
    link = db.query(ParentChildLink).filter(
        ParentChildLink.parent_id == parent_id,
        ParentChildLink.learner_id == learner_id,
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Bạn chưa liên kết với học viên này.")
    return link


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/link-child", response_model=ChildSummary)
def link_child(
    payload: LinkChildRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link the current parent to a learner using the learner's invite code."""
    parent = _get_parent(db, current_user)
    code = payload.invite_code.strip().upper()

    learner = db.query(LearnerProfile).filter(LearnerProfile.invite_code == code).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Mã liên kết không đúng.")

    existing = db.query(ParentChildLink).filter(
        ParentChildLink.parent_id == parent.id,
        ParentChildLink.learner_id == learner.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bạn đã liên kết với học viên này rồi.")

    link = ParentChildLink(
        parent_id=parent.id,
        learner_id=learner.id,
        relationship_label=payload.relationship_label,
    )
    db.add(link)
    db.commit()

    return ChildSummary(
        learner_id=learner.id,
        display_name=learner.display_name,
        overall_level=learner.overall_level or "PRE_A1",
        total_xp=learner.total_xp or 0,
        current_streak=learner.current_streak or 0,
        total_lessons_completed=learner.total_lessons_completed or 0,
        relationship_label=payload.relationship_label,
    )


@router.get("/children", response_model=list[ChildSummary])
def list_children(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all children linked to the current parent."""
    parent = _get_parent(db, current_user)
    links = db.query(ParentChildLink).filter(ParentChildLink.parent_id == parent.id).all()

    out: list[ChildSummary] = []
    for link in links:
        learner = db.query(LearnerProfile).filter(LearnerProfile.id == link.learner_id).first()
        if not learner:
            continue
        out.append(ChildSummary(
            learner_id=learner.id,
            display_name=learner.display_name,
            overall_level=learner.overall_level or "PRE_A1",
            total_xp=learner.total_xp or 0,
            current_streak=learner.current_streak or 0,
            total_lessons_completed=learner.total_lessons_completed or 0,
            relationship_label=link.relationship_label,
        ))
    return out


@router.delete("/children/{learner_id}", status_code=204)
def unlink_child(
    learner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unlink a child from the current parent."""
    parent = _get_parent(db, current_user)
    link = _assert_linked(db, parent.id, learner_id)
    db.delete(link)
    db.commit()


@router.get("/child/{learner_id}/report", response_model=ChildReport)
def child_report(
    learner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Weekly progress report for a linked child.
    Deterministic (no LLM) — reliable, quota-free, easy to read.
    """
    parent = _get_parent(db, current_user)
    _assert_linked(db, parent.id, learner_id)

    learner = db.query(LearnerProfile).filter(LearnerProfile.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Không tìm thấy học viên.")

    since = datetime.now(timezone.utc) - timedelta(days=7)
    events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.learner_id == learner_id,
            LearningEvent.recorded_at >= since,
            LearningEvent.event_type == "lesson_completed",
        )
        .all()
    )

    sessions = len(events)
    xp_week = sum(e.xp_earned or 0 for e in events)
    # Rough study time estimate: ~6 minutes per completed lesson
    study_minutes = sessions * 6
    scored = [e.score for e in events if e.score is not None]
    accuracy = round(sum(scored) / len(scored), 1) if scored else 0.0

    # Skill snapshot from the profile (current EMA scores)
    skill_scores = {
        "listening": learner.listening_score or 0.0,
        "speaking": learner.speaking_score or 0.0,
        "reading": learner.reading_score or 0.0,
        "writing": learner.writing_score or 0.0,
        "vocabulary": learner.vocabulary_score or 0.0,
        "grammar": learner.grammar_score or 0.0,
    }
    skills = [
        SkillImprovement(skill=s, label=SKILL_LABELS_VI.get(s, s), score=round(v, 1))
        for s, v in skill_scores.items()
    ]
    best_skill = max(skill_scores, key=skill_scores.get)
    focus_skill = min(skill_scores, key=skill_scores.get)
    best_label = SKILL_LABELS_VI[best_skill]
    focus_label = SKILL_LABELS_VI[focus_skill]

    # ── Human-readable guidance (Master Plan §21) ──
    name = learner.display_name
    if sessions == 0:
        what_improved = f"Tuần này {name} chưa có buổi học nào."
        what_needs_help = "Cần tạo thói quen học đều đặn."
        what_to_do = f"Hãy cùng {name} đặt mục tiêu học 3 buổi ngắn (10-15 phút) trong tuần tới."
    else:
        what_improved = (
            f"{name} hoàn thành {sessions} buổi học, kiếm được {xp_week} XP tuần này. "
            f"Kỹ năng mạnh nhất hiện tại là {best_label} ({skill_scores[best_skill]:.0f}%)."
        )
        if accuracy >= 80:
            what_improved += f" Độ chính xác rất tốt ({accuracy:.0f}%)!"
        what_needs_help = (
            f"{focus_label} đang là kỹ năng yếu nhất ({skill_scores[focus_skill]:.0f}%) — cần luyện thêm."
        )
        streak = learner.current_streak or 0
        if streak >= 3:
            what_to_do = (
                f"{name} đang có chuỗi {streak} ngày liên tiếp — hãy động viên con giữ vững! "
                f"Tuần tới ưu tiên 2-3 buổi {focus_label}."
            )
        else:
            what_to_do = (
                f"Hãy khuyến khích {name} học đều mỗi ngày để xây chuỗi streak, "
                f"và tập trung vào {focus_label}."
            )

    return ChildReport(
        learner_id=learner.id,
        display_name=learner.display_name,
        overall_level=learner.overall_level or "PRE_A1",
        sessions_this_week=sessions,
        xp_this_week=xp_week,
        study_minutes_estimate=study_minutes,
        current_streak=learner.current_streak or 0,
        accuracy_pct=accuracy,
        skills=skills,
        best_skill=best_label,
        focus_skill=focus_label,
        what_improved=what_improved,
        what_needs_help=what_needs_help,
        what_to_do=what_to_do,
    )
