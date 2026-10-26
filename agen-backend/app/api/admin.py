"""
AGEN — Admin / Quality API
Read-only views over the AI Evaluation Framework (Master Plan §29).
Access restricted to authenticated users for now; tighten to an admin role later.
"""
import hmac
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, Integer, cast
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.models.agent_trace import AgentTrace
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.payment_order import STATUS_FAILED, STATUS_PAID, STATUS_PENDING, PaymentOrder
from app.models.subscription import PLAN_FAMILY, PLAN_PREMIUM, Subscription

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


@router.get("/content/coverage")
def get_content_coverage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """How much of the A1–B1 roadmap has ready (approved) content."""
    _require_admin(current_user)
    from app.services.curriculum_content_service import content_coverage

    return content_coverage(db)


@router.post("/content/cron")
def scheduled_content_factory(
    limit: int = Query(3, ge=1, le=10),
    x_cron_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Scheduled Content Factory run (see .github/workflows/content-factory.yml).

    Generates the next few A1–B1 roadmap lessons that have no content yet, so
    lessons open instantly instead of waiting on the AI. Small batches keep the
    AI provider's daily quota free for learners.
    """
    secret = settings.cron_secret
    if not secret or not hmac.compare_digest(x_cron_secret, secret):
        raise HTTPException(status_code=403, detail="Forbidden")
    from app.services.curriculum_content_service import content_coverage, generate_missing_content

    summary = generate_missing_content(db, limit=limit)
    summary["coverage"] = content_coverage(db)
    return summary


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


# ── G5 · Doanh thu & chuyển đổi ──────────────────────────────────────────────
class RevenueBucket(BaseModel):
    key: str                  # "2026-10" | "vnpay" | "premium·12"
    label: str
    revenue_vnd: int
    orders: int


class RevenueSummary(BaseModel):
    total_vnd: int
    paid_orders: int
    pending_orders: int
    failed_orders: int
    by_month: list[RevenueBucket]        # last 6 months, oldest first
    by_provider: list[RevenueBucket]
    by_plan: list[RevenueBucket]
    active_premium: int                  # learner subscriptions currently paid (own)
    active_family: int                   # parent family subscriptions currently active
    trials_started: int
    trials_converted: int                # trial accounts that later paid
    trial_conversion_pct: float
    guests_now: int
    guests_claimed: int
    registered_learners: int


@router.get("/revenue/summary", response_model=RevenueSummary)
def revenue_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revenue from paid orders (VNPay/MoMo) and the trial → paid / guest → registered funnels."""
    _require_admin(current_user)
    orders = db.query(PaymentOrder).all()
    paid = [o for o in orders if o.status == STATUS_PAID]
    now = datetime.utcnow()

    months: list[str] = []
    y, m = now.year, now.month
    for _ in range(6):
        months.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    by_month = {k: RevenueBucket(key=k, label=f"{k[5:]}/{k[:4]}", revenue_vnd=0, orders=0) for k in months}
    by_provider: dict[str, RevenueBucket] = {}
    by_plan: dict[str, RevenueBucket] = {}
    for o in paid:
        when = o.paid_at or o.created_at
        key = f"{when.year:04d}-{when.month:02d}"
        if key in by_month:
            by_month[key].revenue_vnd += o.amount_vnd
            by_month[key].orders += 1
        prov = by_provider.setdefault(o.provider, RevenueBucket(key=o.provider, label=o.provider.upper(), revenue_vnd=0, orders=0))
        prov.revenue_vnd += o.amount_vnd
        prov.orders += 1
        plan = o.plan or PLAN_PREMIUM
        pk = f"{plan}·{o.months}"
        label = f"{'Gia đình' if plan == PLAN_FAMILY else 'Doanh nghiệp' if plan == 'team' else 'Premium'} {o.months} tháng"
        bucket = by_plan.setdefault(pk, RevenueBucket(key=pk, label=label, revenue_vnd=0, orders=0))
        bucket.revenue_vnd += o.amount_vnd
        bucket.orders += 1

    subs_all = db.query(Subscription).all()
    def _active(sub: Subscription) -> bool:
        return sub.status == "active" and (sub.current_period_end is None or sub.current_period_end >= now)
    active_premium = sum(1 for s in subs_all if s.plan == PLAN_PREMIUM and _active(s) and s.provider != "trial")
    active_family = sum(1 for s in subs_all if s.plan == PLAN_FAMILY and _active(s))
    trial_users = {s.user_id for s in subs_all if s.trial_started_at is not None}
    paid_users = {o.user_id for o in paid}
    trials_converted = len(trial_users & paid_users)

    guests_now = db.query(func.count(User.id)).filter(User.is_guest.is_(True)).scalar() or 0
    guests_claimed = db.query(func.count(User.id)).filter(User.claimed_at.isnot(None)).scalar() or 0
    registered = db.query(func.count(User.id)).filter(User.role == "learner", User.is_guest.is_(False)).scalar() or 0

    return RevenueSummary(
        total_vnd=sum(o.amount_vnd for o in paid),
        paid_orders=len(paid),
        pending_orders=sum(1 for o in orders if o.status == STATUS_PENDING),
        failed_orders=sum(1 for o in orders if o.status == STATUS_FAILED),
        by_month=list(by_month.values()),
        by_provider=sorted(by_provider.values(), key=lambda b: -b.revenue_vnd),
        by_plan=sorted(by_plan.values(), key=lambda b: -b.revenue_vnd),
        active_premium=active_premium,
        active_family=active_family,
        trials_started=len(trial_users),
        trials_converted=trials_converted,
        trial_conversion_pct=round(trials_converted / len(trial_users) * 100, 1) if trial_users else 0.0,
        guests_now=guests_now,
        guests_claimed=guests_claimed,
        registered_learners=registered,
    )


# ── G8 · Đơn hàng & hoá đơn VAT ──────────────────────────────────────────────
class AdminOrder(BaseModel):
    order_id: str
    email: Optional[str]
    role: Optional[str]
    provider: str
    plan: str
    seats: int
    months: int
    amount_vnd: int
    status: str
    invoice: Optional[dict]
    invoice_issued_at: Optional[datetime]
    created_at: datetime
    paid_at: Optional[datetime]


@router.get("/revenue/orders", response_model=list[AdminOrder])
def revenue_orders(
    invoice_only: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recent orders, newest first; `invoice_only` lists the ones that asked for a VAT invoice."""
    _require_admin(current_user)
    q = db.query(PaymentOrder, User.email, User.role).join(User, User.id == PaymentOrder.user_id)
    if invoice_only:
        q = q.filter(PaymentOrder.invoice_info.isnot(None))
    rows = q.order_by(PaymentOrder.created_at.desc()).limit(limit).all()
    return [AdminOrder(order_id=o.id, email=email, role=role, provider=o.provider, plan=o.plan or PLAN_PREMIUM, seats=o.seats or 1, months=o.months,
                       amount_vnd=o.amount_vnd, status=o.status, invoice=o.invoice_info if isinstance(o.invoice_info, dict) else None,
                       invoice_issued_at=o.invoice_issued_at, created_at=o.created_at, paid_at=o.paid_at) for o, email, role in rows]


class InvoiceIssuedIn(BaseModel):
    issued: bool = True


@router.post("/revenue/orders/{order_id}/invoice-issued", response_model=AdminOrder)
def mark_invoice_issued(
    order_id: str,
    payload: InvoiceIssuedIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark the e-invoice for an order as issued (or undo)."""
    _require_admin(current_user)
    row = db.query(PaymentOrder, User.email, User.role).join(User, User.id == PaymentOrder.user_id).filter(PaymentOrder.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")
    o, email, role = row
    o.invoice_issued_at = datetime.utcnow() if payload.issued else None
    db.commit()
    return AdminOrder(order_id=o.id, email=email, role=role, provider=o.provider, plan=o.plan or PLAN_PREMIUM, seats=o.seats or 1, months=o.months,
                      amount_vnd=o.amount_vnd, status=o.status, invoice=o.invoice_info if isinstance(o.invoice_info, dict) else None,
                      invoice_issued_at=o.invoice_issued_at, created_at=o.created_at, paid_at=o.paid_at)


# ── G9 · Đề thi thử do AI sinh (duyệt trước khi phát hành) ────────────────────
class GeneratedExamOut(BaseModel):
    id: str
    public_id: str
    exam: str
    skill: str
    title: str
    topic: Optional[str]
    status: str
    questions: int
    eval_score: Optional[float]
    eval_flagged: Optional[bool]
    created_at: datetime
    approved_at: Optional[datetime]


class GenerateExamIn(BaseModel):
    exam: str = Field(pattern="^(ielts|toeic)$")
    skill: str = Field(pattern="^(listening|reading)$")
    topic: str = Field(default="", max_length=120)
    level: str = Field(default="B1", pattern="^(A2|B1|B2|C1)$")
    auto_approve: bool = False


class ExamStatusIn(BaseModel):
    status: str = Field(pattern="^(draft|approved|rejected)$")


def _gen_out(r) -> GeneratedExamOut:
    from app.services.exam_generator import public_id
    return GeneratedExamOut(id=r.id, public_id=public_id(r), exam=r.exam, skill=r.skill, title=r.title, topic=r.topic, status=r.status,
                            questions=int(r.questions or 0), eval_score=r.eval_score, eval_flagged=r.eval_flagged, created_at=r.created_at, approved_at=r.approved_at)


@router.get("/exams", response_model=list[GeneratedExamOut])
def list_generated_exams(status: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    from app.models.generated_exam import GeneratedExam
    q = db.query(GeneratedExam)
    if status:
        q = q.filter(GeneratedExam.status == status)
    return [_gen_out(r) for r in q.order_by(GeneratedExam.created_at.desc()).limit(200).all()]


@router.post("/exams/generate", response_model=GeneratedExamOut)
def generate_exam(payload: GenerateExamIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """One AI call → one draft paper (or approved straight away with auto_approve)."""
    _require_admin(current_user)
    from app.services.exam_generator import ExamGenerationError, generate_exam_draft
    try:
        row = generate_exam_draft(db, payload.exam, payload.skill, payload.topic, payload.level, payload.auto_approve)
    except ExamGenerationError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc))
    db.commit()
    return _gen_out(row)


@router.get("/exams/{exam_id}")
def get_generated_exam(exam_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Full paper with answers, for review."""
    _require_admin(current_user)
    from app.models.generated_exam import GeneratedExam
    row = db.query(GeneratedExam).filter(GeneratedExam.id == exam_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề.")
    return {"meta": _gen_out(row).model_dump(), "paper": row.content}


@router.post("/exams/{exam_id}/status", response_model=GeneratedExamOut)
def set_generated_exam_status(exam_id: str, payload: ExamStatusIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    from app.models.generated_exam import GeneratedExam
    from app.services.exam_generator import set_status
    row = db.query(GeneratedExam).filter(GeneratedExam.id == exam_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề.")
    set_status(db, row, payload.status)
    db.commit()
    return _gen_out(row)


@router.delete("/exams/{exam_id}", status_code=204)
def delete_generated_exam(exam_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    from app.models.generated_exam import GeneratedExam
    row = db.query(GeneratedExam).filter(GeneratedExam.id == exam_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề.")
    db.delete(row)
    db.commit()


# ── G10 · AI cost tracking ────────────────────────────────────────────────────
@router.get("/ai-usage/summary")
def ai_usage_summary(days: int = 30, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Estimated AI spend (LLM + TTS) per day, feature, provider and top users."""
    _require_admin(current_user)
    from app.services import ai_usage
    return ai_usage.summary(db, days=max(1, min(days, 90)))
