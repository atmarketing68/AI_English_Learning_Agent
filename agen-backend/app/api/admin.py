"""
AGEN — Admin / Quality API
Read-only views over the AI Evaluation Framework (Master Plan §29).
Access restricted to authenticated users for now; tighten to an admin role later.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, Integer, cast
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.models.agent_trace import AgentTrace
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent

router = APIRouter(prefix="/admin", tags=["Admin / Quality"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class EvalTraceItem(BaseModel):
    trace_id: str
    agent: str
    status: str
    eval_score: Optional[float]
    eval_flags: Optional[list[str]]
    eval_flagged: Optional[bool]
    duration_ms: float
    created_at: datetime


class AgentEvalStat(BaseModel):
    agent: str
    total: int
    flagged: int
    avg_score: Optional[float]


class EvalSummary(BaseModel):
    total_traces: int
    evaluated: int
    flagged: int
    flagged_pct: float
    avg_score: Optional[float]
    per_agent: list[AgentEvalStat]


class PilotMetric(BaseModel):
    value: int | float
    rate: Optional[float] = None


class PilotSummary(BaseModel):
    registered_learners: int
    placement_completed: PilotMetric
    first_lesson_completed: PilotMetric
    d7_retention: PilotMetric
    weekly_habit: PilotMetric
    ai_quality: PilotMetric
    lesson_generation: PilotMetric


def _is_admin(user: User) -> bool:
    """A user is an admin if their email is in the configured ADMIN_EMAILS allowlist."""
    return bool(user.email) and user.email.strip().lower() in settings.admin_emails_list


def _require_admin(user: User) -> None:
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="Không có quyền truy cập.")


class AdminMeOut(BaseModel):
    email: str
    is_admin: bool


@router.get("/me", response_model=AdminMeOut)
def admin_me(current_user: User = Depends(get_current_user)):
    """Let the frontend check whether the current user has admin access."""
    return AdminMeOut(email=current_user.email, is_admin=_is_admin(current_user))


# ── Content Factory (pre-generated curriculum content) ──────────────────────────
class ContentItemOut(BaseModel):
    curriculum_code: str
    level: str
    skill: str
    topic: str
    status: str
    eval_score: Optional[float]
    eval_flagged: Optional[bool]
    total_exercises: int


class BatchGenerateRequest(BaseModel):
    level: str
    force: bool = False
    auto_approve: bool = False
    limit: Optional[int] = None


class ContentStatusRequest(BaseModel):
    status: str  # approved | rejected | draft


@router.get("/content", response_model=list[ContentItemOut])
def list_content(
    level: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List cached curriculum lesson content (optionally by level / status)."""
    _require_admin(current_user)
    from app.models.curriculum_content import CurriculumLessonContent

    q = db.query(CurriculumLessonContent)
    if level:
        q = q.filter(CurriculumLessonContent.level == level)
    if status:
        q = q.filter(CurriculumLessonContent.status == status)
    rows = q.order_by(CurriculumLessonContent.curriculum_code).all()
    return [
        ContentItemOut(
            curriculum_code=r.curriculum_code, level=r.level, skill=r.skill, topic=r.topic,
            status=r.status, eval_score=r.eval_score, eval_flagged=r.eval_flagged,
            total_exercises=r.total_exercises,
        )
        for r in rows
    ]


@router.post("/content/generate")
def batch_generate_content(
    payload: BatchGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pre-generate + cache content for every generatable node in a level.

    Note: this makes one LLM call per node — run it deliberately (subject to
    provider quota). Returns a per-node summary.
    """
    _require_admin(current_user)
    from app.services.curriculum_content_service import batch_generate_level

    return batch_generate_level(
        db, payload.level,
        force=payload.force, auto_approve=payload.auto_approve, limit=payload.limit,
    )


@router.post("/content/{code}/generate", response_model=ContentItemOut)
def generate_single_content(
    code: str,
    force: bool = False,
    auto_approve: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate + cache content for a single curriculum node."""
    _require_admin(current_user)
    from app.services.curriculum_content_service import generate_and_cache, ContentGenerationError

    try:
        row = generate_and_cache(db, code, force=force, auto_approve=auto_approve)
        db.commit()
    except ContentGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ContentItemOut(
        curriculum_code=row.curriculum_code, level=row.level, skill=row.skill, topic=row.topic,
        status=row.status, eval_score=row.eval_score, eval_flagged=row.eval_flagged,
        total_exercises=row.total_exercises,
    )


@router.post("/content/{code}/status", response_model=ContentItemOut)
def set_content_status(
    code: str,
    payload: ContentStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve / reject / reset cached content (review workflow)."""
    _require_admin(current_user)
    from app.services.curriculum_content_service import set_status, ContentGenerationError

    try:
        row = set_status(db, code, payload.status)
        db.commit()
    except ContentGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ContentItemOut(
        curriculum_code=row.curriculum_code, level=row.level, skill=row.skill, topic=row.topic,
        status=row.status, eval_score=row.eval_score, eval_flagged=row.eval_flagged,
        total_exercises=row.total_exercises,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/evaluations", response_model=list[EvalTraceItem])
def list_evaluations(
    flagged_only: bool = False,
    agent: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recent AI evaluation traces (optionally only flagged / by agent)."""
    _require_admin(current_user)
    q = db.query(AgentTrace).filter(AgentTrace.eval_score.isnot(None))
    if flagged_only:
        q = q.filter(AgentTrace.eval_flagged.is_(True))
    if agent:
        q = q.filter(AgentTrace.agent == agent)
    traces = q.order_by(AgentTrace.created_at.desc()).limit(min(limit, 200)).all()
    return [
        EvalTraceItem(
            trace_id=t.trace_id, agent=t.agent, status=t.status,
            eval_score=t.eval_score, eval_flags=t.eval_flags, eval_flagged=t.eval_flagged,
            duration_ms=t.duration_ms, created_at=t.created_at,
        )
        for t in traces
    ]


@router.get("/evaluations/summary", response_model=EvalSummary)
def evaluation_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate quality metrics across all evaluated AI outputs."""
    _require_admin(current_user)

    total = db.query(func.count(AgentTrace.id)).scalar() or 0
    evaluated = db.query(func.count(AgentTrace.id)).filter(AgentTrace.eval_score.isnot(None)).scalar() or 0
    flagged = db.query(func.count(AgentTrace.id)).filter(AgentTrace.eval_flagged.is_(True)).scalar() or 0
    avg_score = db.query(func.avg(AgentTrace.eval_score)).filter(AgentTrace.eval_score.isnot(None)).scalar()

    # Per-agent breakdown
    rows = (
        db.query(
            AgentTrace.agent,
            func.count(AgentTrace.id),
            func.sum(cast(AgentTrace.eval_flagged, Integer)),
            func.avg(AgentTrace.eval_score),
        )
        .filter(AgentTrace.eval_score.isnot(None))
        .group_by(AgentTrace.agent)
        .all()
    )
    per_agent = [
        AgentEvalStat(
            agent=r[0],
            total=int(r[1] or 0),
            flagged=int(r[2] or 0),
            avg_score=round(float(r[3]), 1) if r[3] is not None else None,
        )
        for r in rows
    ]

    return EvalSummary(
        total_traces=total,
        evaluated=evaluated,
        flagged=flagged,
        flagged_pct=round((flagged / evaluated) * 100, 1) if evaluated else 0.0,
        avg_score=round(float(avg_score), 1) if avg_score is not None else None,
        per_agent=per_agent,
    )


@router.get("/pilot/summary", response_model=PilotSummary)
def pilot_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the pilot KPI snapshot from learner, event and agent telemetry."""
    _require_admin(current_user)

    learners = (
        db.query(LearnerProfile)
        .join(User, User.id == LearnerProfile.user_id)
        .filter(User.role == "learner")
        .all()
    )
    learner_ids = {learner.id for learner in learners}
    events = (
        db.query(LearningEvent)
        .filter(LearningEvent.learner_id.in_(learner_ids))
        .order_by(LearningEvent.recorded_at.asc())
        .all()
        if learner_ids else []
    )
    events_by_learner: dict[str, list[LearningEvent]] = {}
    for event in events:
        events_by_learner.setdefault(event.learner_id, []).append(event)

    registered = len(learners)
    placement_ids = {
        learner.id for learner in learners
        if learner.placement_completed == "done"
        or any(e.event_type == "placement_done" for e in events_by_learner.get(learner.id, []))
    }
    first_lesson_ids = {
        learner_id for learner_id, learner_events in events_by_learner.items()
        if any(e.event_type == "lesson_completed" for e in learner_events)
    }

    retained_ids: set[str] = set()
    habitual_ids: set[str] = set()
    for learner_id in placement_ids:
        learner_events = events_by_learner.get(learner_id, [])
        placement_events = [e for e in learner_events if e.event_type == "placement_done"]
        placement_at = placement_events[0].recorded_at if placement_events else None
        if placement_at:
            cutoff = placement_at + timedelta(days=7)
            if any(e.recorded_at >= cutoff for e in learner_events):
                retained_ids.add(learner_id)
        recent_days = {
            e.recorded_at.date() for e in learner_events
            if e.recorded_at >= datetime.utcnow() - timedelta(days=7)
        }
        if len(recent_days) >= 3:
            habitual_ids.add(learner_id)

    evaluated = db.query(AgentTrace).filter(AgentTrace.eval_score.isnot(None)).all()
    clean_evaluated = sum(1 for trace in evaluated if not trace.eval_flagged)
    successful_lessons = db.query(AgentTrace).filter(
        AgentTrace.agent == "lesson",
        AgentTrace.status == "succeeded",
    ).count()
    lesson_traces = db.query(AgentTrace).filter(AgentTrace.agent == "lesson").count()
    avg_ai_score = (
        round(sum(float(t.eval_score) for t in evaluated) / len(evaluated), 1)
        if evaluated else 0.0
    )

    def metric(count: int) -> PilotMetric:
        return PilotMetric(
            value=count,
            rate=round((count / registered) * 100, 1) if registered else 0.0,
        )

    return PilotSummary(
        registered_learners=registered,
        placement_completed=metric(len(placement_ids)),
        first_lesson_completed=metric(len(first_lesson_ids)),
        d7_retention=metric(len(retained_ids)),
        weekly_habit=metric(len(habitual_ids)),
        ai_quality=PilotMetric(
            value=avg_ai_score,
            rate=round((clean_evaluated / len(evaluated)) * 100, 1) if evaluated else 0.0,
        ),
        lesson_generation=PilotMetric(
            value=successful_lessons,
            rate=round((successful_lessons / lesson_traces) * 100, 1) if lesson_traces else 0.0,
        ),
    )
