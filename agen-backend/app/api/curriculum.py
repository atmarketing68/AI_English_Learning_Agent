"""
AGEN — Curriculum API
Exposes the fixed curriculum map and the learner's roadmap position.

Master Plan Phần B: learners follow a structured Program→Level→Unit→Lesson
path. The "Next Best Lesson" here is roadmap-driven (first unmastered lesson
whose prerequisite is satisfied), not free LLM choice.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.curriculum import CurriculumUnit, CurriculumLesson, LearnerCurriculumProgress

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

MASTERY_THRESHOLD = 75   # score >= this counts as "mastered"


# ── Schemas ───────────────────────────────────────────────────────────────────
class CurriculumLessonOut(BaseModel):
    id: str
    code: str
    order: int
    title: str
    skill: str
    difficulty: int
    topic: str
    objective: Optional[str]
    grammar_focus: Optional[str]
    is_review: bool
    is_assessment: bool
    # learner progress overlay
    status: str = "not_started"
    best_score: int = 0
    mastered: bool = False
    locked: bool = False           # True if prerequisite not yet met


class CurriculumUnitOut(BaseModel):
    id: str
    code: str
    order: int
    title: str
    theme: Optional[str]
    icon: Optional[str]
    description: Optional[str]
    lessons: list[CurriculumLessonOut]
    completed_count: int
    total_count: int


class CurriculumMapOut(BaseModel):
    level: str
    units: list[CurriculumUnitOut]
    total_lessons: int
    completed_lessons: int
    progress_pct: float


class NextLessonOut(BaseModel):
    code: str
    title: str
    skill: str
    topic: str
    difficulty: int
    unit_title: str
    objective: Optional[str]
    reason: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


def _progress_map(db: Session, learner_id: str) -> dict[str, LearnerCurriculumProgress]:
    """Return {curriculum_lesson_id: progress} for a learner."""
    rows = db.query(LearnerCurriculumProgress).filter(
        LearnerCurriculumProgress.learner_id == learner_id
    ).all()
    return {r.curriculum_lesson_id: r for r in rows}


def _mastered_codes(db: Session, learner_id: str) -> set[str]:
    """Set of curriculum lesson codes the learner has mastered."""
    rows = (
        db.query(CurriculumLesson.code)
        .join(LearnerCurriculumProgress,
              LearnerCurriculumProgress.curriculum_lesson_id == CurriculumLesson.id)
        .filter(
            LearnerCurriculumProgress.learner_id == learner_id,
            LearnerCurriculumProgress.mastered == True,  # noqa: E712
        )
        .all()
    )
    return {r.code for r in rows}


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/map", response_model=CurriculumMapOut)
def get_curriculum_map(
    level: str = "A1",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the full curriculum map for a level, with the learner's progress overlaid."""
    learner = _get_learner(db, current_user.id)
    units = (
        db.query(CurriculumUnit)
        .filter(CurriculumUnit.level == level)
        .order_by(CurriculumUnit.order)
        .all()
    )
    if not units:
        raise HTTPException(status_code=404, detail=f"No curriculum found for level {level}.")

    progress = _progress_map(db, learner.id)
    mastered = _mastered_codes(db, learner.id)

    units_out: list[CurriculumUnitOut] = []
    total_lessons = 0
    completed_lessons = 0

    for unit in units:
        lessons_out: list[CurriculumLessonOut] = []
        unit_completed = 0
        for lesson in unit.lessons:
            total_lessons += 1
            prog = progress.get(lesson.id)
            status = prog.status if prog else "not_started"
            best = prog.best_score if prog else 0
            is_mastered = prog.mastered if prog else False
            if status == "completed":
                unit_completed += 1
                completed_lessons += 1
            # Locked if prerequisite not yet mastered
            locked = bool(lesson.prerequisite_code) and lesson.prerequisite_code not in mastered
            lessons_out.append(CurriculumLessonOut(
                id=lesson.id, code=lesson.code, order=lesson.order, title=lesson.title,
                skill=lesson.skill, difficulty=lesson.difficulty, topic=lesson.topic,
                objective=lesson.objective, grammar_focus=lesson.grammar_focus,
                is_review=lesson.is_review, is_assessment=lesson.is_assessment,
                status=status, best_score=best, mastered=is_mastered, locked=locked,
            ))
        units_out.append(CurriculumUnitOut(
            id=unit.id, code=unit.code, order=unit.order, title=unit.title,
            theme=unit.theme, icon=unit.icon, description=unit.description,
            lessons=lessons_out, completed_count=unit_completed, total_count=len(unit.lessons),
        ))

    pct = round((completed_lessons / total_lessons) * 100, 1) if total_lessons else 0.0
    return CurriculumMapOut(
        level=level, units=units_out,
        total_lessons=total_lessons, completed_lessons=completed_lessons, progress_pct=pct,
    )


@router.get("/next", response_model=NextLessonOut)
def get_next_lesson(
    level: str = "A1",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Roadmap-driven Next Best Lesson: the first curriculum lesson (in order)
    that is not yet mastered AND whose prerequisite is satisfied.
    """
    learner = _get_learner(db, current_user.id)
    units = (
        db.query(CurriculumUnit)
        .filter(CurriculumUnit.level == level)
        .order_by(CurriculumUnit.order)
        .all()
    )
    if not units:
        raise HTTPException(status_code=404, detail=f"No curriculum found for level {level}.")

    progress = _progress_map(db, learner.id)
    mastered = _mastered_codes(db, learner.id)

    for unit in units:
        for lesson in unit.lessons:
            prog = progress.get(lesson.id)
            already_mastered = prog.mastered if prog else False
            if already_mastered:
                continue
            prereq_ok = (not lesson.prerequisite_code) or (lesson.prerequisite_code in mastered)
            if not prereq_ok:
                continue

            # Determine a friendly reason
            if prog and prog.status == "in_progress":
                reason = "Bạn đang học dở bài này — hãy hoàn thành nhé!"
            elif lesson.is_assessment:
                reason = "Bài đánh giá năng lực — kiểm tra những gì bạn đã học."
            elif lesson.is_review:
                reason = "Bài ôn tập giúp củng cố kiến thức của unit."
            else:
                reason = f"Bài tiếp theo trong lộ trình: {unit.title}."

            return NextLessonOut(
                code=lesson.code, title=lesson.title, skill=lesson.skill,
                topic=lesson.topic, difficulty=lesson.difficulty,
                unit_title=unit.title, objective=lesson.objective, reason=reason,
            )

    raise HTTPException(status_code=404, detail="🎉 Bạn đã hoàn thành toàn bộ lộ trình cấp độ này!")


class StartCurriculumLessonRequest(BaseModel):
    code: str   # curriculum lesson code, e.g. "A1-U01-L03"


class StartCurriculumLessonResponse(BaseModel):
    curriculum_lesson_id: str
    code: str
    skill: str
    topic: str
    status: str


@router.post("/start", response_model=StartCurriculumLessonResponse)
def start_curriculum_lesson(
    payload: StartCurriculumLessonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a curriculum lesson as started (creates/updates progress row).
    The frontend then calls /lessons/generate with this lesson's skill+topic.
    """
    learner = _get_learner(db, current_user.id)
    lesson = db.query(CurriculumLesson).filter(CurriculumLesson.code == payload.code).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Curriculum lesson not found.")

    # Prerequisite gate
    if lesson.prerequisite_code:
        mastered = _mastered_codes(db, learner.id)
        if lesson.prerequisite_code not in mastered:
            raise HTTPException(
                status_code=400,
                detail=f"Bạn cần hoàn thành bài {lesson.prerequisite_code} trước.",
            )

    prog = db.query(LearnerCurriculumProgress).filter(
        LearnerCurriculumProgress.learner_id == learner.id,
        LearnerCurriculumProgress.curriculum_lesson_id == lesson.id,
    ).first()

    if not prog:
        prog = LearnerCurriculumProgress(
            learner_id=learner.id,
            curriculum_lesson_id=lesson.id,
            status="in_progress",
            attempts=0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(prog)
    elif prog.status == "not_started":
        prog.status = "in_progress"
        prog.started_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prog)

    return StartCurriculumLessonResponse(
        curriculum_lesson_id=prog.id,
        code=lesson.code,
        skill=lesson.skill,
        topic=lesson.topic,
        status=prog.status,
    )
