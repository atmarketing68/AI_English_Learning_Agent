"""G8 · Thi thử IELTS / TOEIC: catalogue, taking a test, grading and history."""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timeutil import local_day_start_utc
from app.models.exam_attempt import ExamAttempt
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.user import User
from app.services import mock_exams as bank
from app.services.shop import award_gems
from app.services.streak_service import record_activity
from app.services.subscription_service import is_premium

router = APIRouter(prefix="/exams", tags=["Mock exams"])


# ── Schemas ──────────────────────────────────────────────────────────────────
class ExamSummary(BaseModel):
    id: str
    exam: str
    skill: str
    title: str
    description: str
    minutes: int
    questions: int
    attempts: int
    best_pct: Optional[float]
    best_estimate: Optional[float]
    last_at: Optional[datetime]


class ExamCatalogue(BaseModel):
    exams: list[ExamSummary]
    is_premium: bool
    free_daily_attempts: int
    attempts_today: int
    can_start: bool


class SectionResult(BaseModel):
    id: str
    title: str
    correct: int
    total: int


class QuestionResult(BaseModel):
    id: str
    section_id: str
    correct: bool
    given: str
    expected: str
    explanation_vi: str


class SubmitIn(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    seconds: Optional[int] = Field(default=None, ge=0, le=7200)
    group_test_id: Optional[str] = Field(default=None, max_length=36)   # G13 · taken as a class test


class SubmitOut(BaseModel):
    attempt_id: str
    exam: str
    skill: str
    correct: int
    total: int
    pct: float
    estimate: float
    sections: list[SectionResult]
    details: list[QuestionResult]
    xp_earned: int
    gems_earned: int
    best_estimate: float
    class_test: bool = False


class AttemptOut(BaseModel):
    id: str
    exam_id: str
    title: str
    exam: str
    skill: str
    correct: int
    total: int
    pct: float
    estimate: float
    seconds: Optional[int]
    created_at: datetime


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


def _attempts_today(db: Session, learner_id: str) -> int:
    # G13 · class tests do not use up the free daily attempt
    return db.query(ExamAttempt).filter(ExamAttempt.learner_id == learner_id, ExamAttempt.created_at >= local_day_start_utc(),
                                         ExamAttempt.group_test_id.is_(None)).count()


# ── Endpoints ────────────────────────────────────────────────────────────────
@router.get("", response_model=ExamCatalogue)
def catalogue(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    attempts = db.query(ExamAttempt).filter(ExamAttempt.learner_id == learner.id).all()
    by_exam: dict[str, list[ExamAttempt]] = {}
    for a in attempts:
        by_exam.setdefault(a.exam_id, []).append(a)
    out = []
    for e in bank.list_exams(db):
        rows = by_exam.get(e["id"], [])
        out.append(ExamSummary(
            id=e["id"], exam=e["exam"], skill=e["skill"], title=e["title"], description=e["description"], minutes=e["minutes"],
            questions=bank.question_count(e), attempts=len(rows),
            best_pct=max((r.pct for r in rows), default=None),
            best_estimate=max((r.estimate for r in rows), default=None),
            last_at=max((r.created_at for r in rows), default=None),
        ))
    premium = is_premium(db, current_user.id)
    today = _attempts_today(db, learner.id)
    return ExamCatalogue(exams=out, is_premium=premium, free_daily_attempts=bank.FREE_DAILY_ATTEMPTS, attempts_today=today,
                         can_start=premium or today < bank.FREE_DAILY_ATTEMPTS)


@router.get("/history", response_model=list[AttemptOut])
def history(limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    rows = db.query(ExamAttempt).filter(ExamAttempt.learner_id == learner.id).order_by(ExamAttempt.created_at.desc()).limit(min(limit, 100)).all()
    return [AttemptOut(id=r.id, exam_id=r.exam_id, title=(bank.get_exam(r.exam_id, db) or {}).get("title", r.exam_id), exam=r.exam, skill=r.skill,
                       correct=r.correct, total=r.total, pct=r.pct, estimate=r.estimate, seconds=r.seconds, created_at=r.created_at) for r in rows]


def _class_test(db: Session, learner_id: str, test_id: Optional[str], exam_id: str):
    from app.services.groups import open_test_for
    return open_test_for(db, learner_id, test_id, "mock", exam_id)


@router.get("/{exam_id}")
def get_exam(exam_id: str, test: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The test without answers. Free accounts: one test a day — a class test (G13, ?test=<id>) does not count."""
    learner = _learner(db, current_user)
    exam = bank.get_exam(exam_id, db)
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi.")
    class_test = _class_test(db, learner.id, test, exam_id)
    if class_test:
        return {**bank.public_exam(exam), "class_test": {"id": class_test.id, "title": class_test.title, "due_on": class_test.due_on.isoformat()}}
    if not is_premium(db, current_user.id) and _attempts_today(db, learner.id) >= bank.FREE_DAILY_ATTEMPTS:
        raise HTTPException(status_code=403, detail=f"Gói miễn phí làm được {bank.FREE_DAILY_ATTEMPTS} đề thi thử mỗi ngày. Nâng cấp Premium để thi không giới hạn.")
    return bank.public_exam(exam)


@router.post("/{exam_id}/submit", response_model=SubmitOut)
def submit(exam_id: str, payload: SubmitIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    exam = bank.get_exam(exam_id, db)
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi.")
    class_test = _class_test(db, learner.id, payload.group_test_id, exam_id)
    if not class_test and not is_premium(db, current_user.id) and _attempts_today(db, learner.id) >= bank.FREE_DAILY_ATTEMPTS:
        raise HTTPException(status_code=403, detail=f"Gói miễn phí làm được {bank.FREE_DAILY_ATTEMPTS} đề thi thử mỗi ngày. Nâng cấp Premium để thi không giới hạn.")

    result = bank.grade(exam, payload.answers)
    xp = bank.xp_for(result["correct"])
    gems = award_gems(learner, bank.GEMS_GOOD_SCORE) if result["pct"] >= 70 else 0
    attempt = ExamAttempt(
        learner_id=learner.id, exam_id=exam["id"], exam=exam["exam"], skill=exam["skill"],
        correct=result["correct"], total=result["total"], pct=result["pct"], estimate=result["estimate"],
        sections=result["sections"], answers={k: v for k, v in payload.answers.items() if k.startswith("q")}, seconds=payload.seconds, xp_earned=xp,
        group_test_id=class_test.id if class_test else None,
    )
    db.add(attempt)
    learner.total_xp = (learner.total_xp or 0) + xp
    field = f"{exam['skill']}_score"
    current = getattr(learner, field, 0) or 0
    setattr(learner, field, round(current * 0.8 + result["pct"] * 0.2, 1))
    db.add(LearningEvent(
        learner_id=learner.id, event_type="exam_completed", skill=exam["skill"], topic=exam["title"], activity_type="mock_exam",
        correct=result["pct"] >= 60, score=result["pct"], xp_earned=xp, duration_seconds=payload.seconds,
        extra_data={"exam": exam["exam"], "exam_id": exam["id"], "estimate": result["estimate"], "correct": result["correct"], "total": result["total"]},
    ))
    record_activity(learner, exam["skill"], db)
    db.commit()
    best = db.query(ExamAttempt).filter(ExamAttempt.learner_id == learner.id, ExamAttempt.exam_id == exam["id"]).all()
    return SubmitOut(
        attempt_id=attempt.id, exam=exam["exam"], skill=exam["skill"], correct=result["correct"], total=result["total"], pct=result["pct"], estimate=result["estimate"],
        sections=[SectionResult(**s) for s in result["sections"]], details=[QuestionResult(**d) for d in result["details"]],
        xp_earned=xp, gems_earned=gems, best_estimate=max(r.estimate for r in best), class_test=class_test is not None,
    )
