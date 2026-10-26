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
# The curriculum is seeded for A1/A2/B1 only. A learner's overall_level can be
# PRE_A1 (new account default) or B2+/C-levels (placement result), so map those
# to the nearest seeded level instead of answering 404.
_SEEDED_LEVELS = {"A1", "A2", "B1"}


def _resolve_level(level: str) -> str:
    level = (level or "A1").upper()
    if level in _SEEDED_LEVELS:
        return level
    return "B1" if level in {"B2", "C1", "C2"} else "A1"


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
    level = _resolve_level(level)
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
    level = _resolve_level(level)
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


# ── G3 · Khoá theo mục tiêu (IELTS / TOEIC / phỏng vấn) ──────────────────────
from app.models.goal_track import GoalTrackProgress
from app.services import goal_tracks


class TrackLessonOut(BaseModel):
    code: str
    title_vi: str
    skill: str
    topic: str
    level: str
    status: str = "not_started"      # not_started | in_progress | completed
    best_score: int = 0
    mastered: bool = False
    locked: bool = False


class TrackModuleOut(BaseModel):
    code: str
    title_vi: str
    lessons: list[TrackLessonOut]
    completed_count: int
    total_count: int


class TrackSummaryOut(BaseModel):
    id: str
    emoji: str
    title_vi: str
    title_en: str
    description_vi: str
    target_level: str
    total_lessons: int
    completed_lessons: int
    progress_pct: float
    recommended: bool
    next_lesson_code: Optional[str]


class TrackDetailOut(TrackSummaryOut):
    modules: list[TrackModuleOut]


class StartTrackLessonRequest(BaseModel):
    code: str


class StartTrackLessonResponse(BaseModel):
    track_id: str
    code: str
    skill: str
    topic: str
    level: str
    status: str


def _track_progress(db: Session, learner_id: str, track_id: str) -> dict[str, GoalTrackProgress]:
    rows = db.query(GoalTrackProgress).filter(
        GoalTrackProgress.learner_id == learner_id, GoalTrackProgress.track_id == track_id,
    ).all()
    return {r.lesson_code: r for r in rows}


def _track_view(track: dict, progress: dict[str, GoalTrackProgress], learning_goal: Optional[str]) -> TrackDetailOut:
    modules: list[TrackModuleOut] = []
    previous_done = True          # the first lesson is always open
    completed = 0
    next_code: Optional[str] = None
    for module in track["modules"]:
        lessons: list[TrackLessonOut] = []
        for spec in module["lessons"]:
            row = progress.get(spec["code"])
            status = row.status if row else "not_started"
            done = status == "completed"
            locked = not previous_done and not row
            if done:
                completed += 1
            elif next_code is None and not locked:
                next_code = spec["code"]
            lessons.append(TrackLessonOut(
                **spec, status=status, best_score=(row.best_score if row else 0),
                mastered=bool(row.mastered) if row else False, locked=locked,
            ))
            previous_done = done
        modules.append(TrackModuleOut(
            code=module["code"], title_vi=module["title_vi"], lessons=lessons,
            completed_count=sum(1 for l in lessons if l.status == "completed"), total_count=len(lessons),
        ))
    total = sum(m.total_count for m in modules)
    return TrackDetailOut(
        id=track["id"], emoji=track["emoji"], title_vi=track["title_vi"], title_en=track["title_en"],
        description_vi=track["description_vi"], target_level=track["target_level"],
        total_lessons=total, completed_lessons=completed,
        progress_pct=round(completed / total * 100, 1) if total else 0.0,
        recommended=track["id"] in goal_tracks.recommended_track_ids(learning_goal),
        next_lesson_code=next_code, modules=modules,
    )


@router.get("/tracks", response_model=list[TrackSummaryOut])
def list_goal_tracks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _get_learner(db, current_user.id)
    out = []
    for track in goal_tracks.list_tracks():
        view = _track_view(track, _track_progress(db, learner.id, track["id"]), learner.learning_goal)
        out.append(TrackSummaryOut(**view.model_dump(exclude={"modules"})))
    out.sort(key=lambda t: (not t.recommended, t.id))
    return out


@router.get("/tracks/{track_id}", response_model=TrackDetailOut)
def get_goal_track(track_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _get_learner(db, current_user.id)
    track = goal_tracks.get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoá học này.")
    return _track_view(track, _track_progress(db, learner.id, track_id), learner.learning_goal)


@router.post("/tracks/{track_id}/start", response_model=StartTrackLessonResponse)
def start_track_lesson(
    track_id: str,
    payload: StartTrackLessonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a track lesson as started; the client then calls /lessons/generate with track_code."""
    learner = _get_learner(db, current_user.id)
    found = goal_tracks.find_lesson(payload.code)
    if not found or found[0]["id"] != track_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài học trong khoá này.")
    track, _, spec = found
    view = _track_view(track, _track_progress(db, learner.id, track_id), learner.learning_goal)
    lesson_view = next(l for m in view.modules for l in m.lessons if l.code == payload.code)
    if lesson_view.locked:
        raise HTTPException(status_code=400, detail="Hãy hoàn thành bài trước đó trước.")

    prog = db.query(GoalTrackProgress).filter(
        GoalTrackProgress.learner_id == learner.id, GoalTrackProgress.lesson_code == payload.code,
    ).first()
    if not prog:
        prog = GoalTrackProgress(learner_id=learner.id, track_id=track_id, lesson_code=payload.code, status="in_progress")
        db.add(prog)
    elif prog.status != "completed":
        prog.status = "in_progress"
    db.commit()
    return StartTrackLessonResponse(
        track_id=track_id, code=spec["code"], skill=spec["skill"], topic=spec["topic"], level=spec["level"], status=prog.status,
    )
