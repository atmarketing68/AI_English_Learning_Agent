"""G9 · Thi thử Speaking: catalogue, attempt flow (start → answer per task → finish), results and history."""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentRequest, execute
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timeutil import local_day_start_utc
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.speaking_exam import STATUS_FINISHED, STATUS_STARTED, SpeakingExamAttempt
from app.models.user import User
from app.services import speaking_exams as bank
from app.services.shop import award_gems
from app.services.streak_service import record_activity
from app.services.subscription_service import is_premium
from app.services.trace_recorder import record_agent_trace

router = APIRouter(prefix="/speaking-exams", tags=["Speaking mock exams"])


class SpeakingExamSummary(BaseModel):
    id: str
    exam: str
    title: str
    description: str
    minutes: int
    tasks: int
    attempts: int
    best_estimate: Optional[float]
    last_at: Optional[datetime]


class SpeakingCatalogue(BaseModel):
    exams: list[SpeakingExamSummary]
    is_premium: bool
    free_daily_attempts: int
    attempts_today: int
    can_start: bool


class StartOut(BaseModel):
    attempt_id: str
    exam: dict


class AnswerIn(BaseModel):
    task_id: str = Field(min_length=1, max_length=10)
    transcript: str = Field(default="", max_length=4000)
    duration_seconds: Optional[float] = Field(default=None, ge=0, le=600)


class AnswerOut(BaseModel):
    task_id: str
    words: int
    pronunciation: Optional[float] = None
    answered: int
    total: int


class Correction(BaseModel):
    original: str
    corrected: str


class TaskFeedback(BaseModel):
    task_id: str
    part: str
    prompt: str
    transcript: str
    words: int
    pronunciation: Optional[float] = None
    comment_vi: str
    corrections: list[Correction] = []


class ResultOut(BaseModel):
    attempt_id: str
    exam_id: str
    exam: str
    title: str
    overall: float
    criteria: dict[str, float]
    tasks: list[TaskFeedback]
    strengths: list[str]
    improvements: list[str]
    next_band_tips: list[str]
    fallback: bool
    xp_earned: int
    gems_earned: int
    finished_at: Optional[datetime]


class HistoryItem(BaseModel):
    id: str
    exam_id: str
    title: str
    exam: str
    overall: Optional[float]
    status: str
    created_at: datetime


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


def _attempts_today(db: Session, learner_id: str) -> int:
    return db.query(SpeakingExamAttempt).filter(SpeakingExamAttempt.learner_id == learner_id, SpeakingExamAttempt.created_at >= local_day_start_utc()).count()


def _own_attempt(db: Session, learner: LearnerProfile, attempt_id: str) -> SpeakingExamAttempt:
    a = db.query(SpeakingExamAttempt).filter(SpeakingExamAttempt.id == attempt_id, SpeakingExamAttempt.learner_id == learner.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài thi.")
    return a


def _words(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])


@router.get("", response_model=SpeakingCatalogue)
def catalogue(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    rows = db.query(SpeakingExamAttempt).filter(SpeakingExamAttempt.learner_id == learner.id, SpeakingExamAttempt.status == STATUS_FINISHED).all()
    by_exam: dict[str, list[SpeakingExamAttempt]] = {}
    for r in rows:
        by_exam.setdefault(r.exam_id, []).append(r)
    premium = is_premium(db, current_user.id)
    today = _attempts_today(db, learner.id)
    return SpeakingCatalogue(
        exams=[SpeakingExamSummary(
            id=e["id"], exam=e["exam"], title=e["title"], description=e["description"], minutes=e["minutes"], tasks=bank.task_count(e),
            attempts=len(by_exam.get(e["id"], [])),
            best_estimate=max((r.estimate for r in by_exam.get(e["id"], []) if r.estimate is not None), default=None),
            last_at=max((r.created_at for r in by_exam.get(e["id"], [])), default=None),
        ) for e in bank.list_exams()],
        is_premium=premium, free_daily_attempts=bank.FREE_DAILY_ATTEMPTS, attempts_today=today, can_start=premium or today < bank.FREE_DAILY_ATTEMPTS,
    )


@router.get("/history", response_model=list[HistoryItem])
def history(limit: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    rows = db.query(SpeakingExamAttempt).filter(SpeakingExamAttempt.learner_id == learner.id).order_by(SpeakingExamAttempt.created_at.desc()).limit(min(limit, 100)).all()
    return [HistoryItem(id=r.id, exam_id=r.exam_id, title=(bank.get_exam(r.exam_id) or {}).get("title", r.exam_id), exam=r.exam, overall=r.estimate, status=r.status, created_at=r.created_at) for r in rows]


@router.post("/{exam_id}/start", response_model=StartOut)
def start(exam_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    exam = bank.get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi.")
    # An unfinished attempt of the same exam started today is resumed instead of counted again.
    open_attempt = (
        db.query(SpeakingExamAttempt)
        .filter(SpeakingExamAttempt.learner_id == learner.id, SpeakingExamAttempt.exam_id == exam_id,
                SpeakingExamAttempt.status == STATUS_STARTED, SpeakingExamAttempt.created_at >= local_day_start_utc())
        .order_by(SpeakingExamAttempt.created_at.desc()).first()
    )
    if open_attempt:
        return StartOut(attempt_id=open_attempt.id, exam=bank.public_exam(exam))
    if not is_premium(db, current_user.id) and _attempts_today(db, learner.id) >= bank.FREE_DAILY_ATTEMPTS:
        raise HTTPException(status_code=403, detail=f"Gói miễn phí thi thử Speaking {bank.FREE_DAILY_ATTEMPTS} lần mỗi ngày. Nâng cấp Premium để thi không giới hạn.")
    attempt = SpeakingExamAttempt(learner_id=learner.id, exam_id=exam_id, exam=exam["exam"], responses=[])
    db.add(attempt)
    db.commit()
    return StartOut(attempt_id=attempt.id, exam=bank.public_exam(exam))


@router.post("/attempts/{attempt_id}/answer", response_model=AnswerOut)
def answer(attempt_id: str, payload: AnswerIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    attempt = _own_attempt(db, learner, attempt_id)
    if attempt.status != STATUS_STARTED:
        raise HTTPException(status_code=400, detail="Bài thi đã nộp.")
    exam = bank.get_exam(attempt.exam_id)
    task = next((t for t in exam["tasks"] if t["id"] == payload.task_id), None) if exam else None
    if not task:
        raise HTTPException(status_code=404, detail="Không có phần thi này.")
    transcript = payload.transcript.strip()
    pron: Optional[float] = None
    if task.get("reference") and transcript:
        from app.services.pronunciation_service import score_pronunciation
        pron = round(score_pronunciation(target_text=task["reference"], transcript=transcript, duration_seconds=payload.duration_seconds).overall_score, 1)
    responses = [r for r in (attempt.responses or []) if r.get("task_id") != payload.task_id]
    responses.append({"task_id": payload.task_id, "transcript": transcript, "duration": payload.duration_seconds, "words": _words(transcript), "pronunciation": pron})
    responses.sort(key=lambda r: [t["id"] for t in exam["tasks"]].index(r["task_id"]) if r["task_id"] in [t["id"] for t in exam["tasks"]] else 99)
    attempt.responses = responses
    db.commit()
    return AnswerOut(task_id=payload.task_id, words=_words(transcript), pronunciation=pron, answered=len(responses), total=len(exam["tasks"]))


def _result_out(attempt: SpeakingExamAttempt, gems: int = 0) -> ResultOut:
    exam = bank.get_exam(attempt.exam_id) or {"title": attempt.exam_id, "tasks": []}
    fb = attempt.feedback or {}
    by_task = {r["task_id"]: r for r in (attempt.responses or [])}
    fb_by_task = {t.get("task_id"): t for t in fb.get("task_feedback", [])}
    tasks = []
    for t in exam["tasks"]:
        r = by_task.get(t["id"], {})
        f = fb_by_task.get(t["id"], {})
        tasks.append(TaskFeedback(
            task_id=t["id"], part=t["part"], prompt=t["prompt"], transcript=r.get("transcript", ""), words=r.get("words", 0), pronunciation=r.get("pronunciation"),
            comment_vi=f.get("comment_vi", "Chưa trả lời phần này." if not r.get("transcript") else ""),
            corrections=[Correction(**c) for c in f.get("corrections", []) if c.get("original") and c.get("corrected")],
        ))
    return ResultOut(
        attempt_id=attempt.id, exam_id=attempt.exam_id, exam=attempt.exam, title=exam["title"], overall=attempt.estimate or 0.0,
        criteria={k: float(v) for k, v in (attempt.criteria or {}).items()}, tasks=tasks,
        strengths=list(fb.get("strengths", [])), improvements=list(fb.get("improvements", [])), next_band_tips=list(fb.get("next_band_tips", [])),
        fallback=bool(attempt.fallback), xp_earned=attempt.xp_earned, gems_earned=gems, finished_at=attempt.finished_at,
    )


@router.post("/attempts/{attempt_id}/finish", response_model=ResultOut)
def finish(attempt_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    attempt = _own_attempt(db, learner, attempt_id)
    if attempt.status == STATUS_FINISHED:
        return _result_out(attempt)
    exam = bank.get_exam(attempt.exam_id)
    responses = attempt.responses or []
    if not any(_words(r.get("transcript", "")) >= 3 for r in responses):
        raise HTTPException(status_code=400, detail="Hãy trả lời ít nhất một phần trước khi nộp.")

    result = execute(AgentRequest(agent="speaking_exam_evaluation", payload={"exam": exam["exam"], "tasks": exam["tasks"], "responses": responses, "level": learner.overall_level or "B1"}))
    record_agent_trace(db, learner.id, result.trace_id, result, {"exam": exam["id"], "level": learner.overall_level})
    fallback = result.status != "succeeded"
    data: dict[str, Any] = result.data if not fallback else bank.heuristic_estimate(exam, responses)

    overall = float(data["overall"])
    xp = bank.xp_for(responses)
    gems = award_gems(learner, bank.GEMS_GOOD) if bank.good_score(exam["exam"], overall) else 0
    attempt.status = STATUS_FINISHED
    attempt.estimate = overall
    attempt.criteria = data.get("criteria", {})
    attempt.feedback = {k: data.get(k, []) for k in ("task_feedback", "strengths", "improvements", "next_band_tips")}
    attempt.fallback = 1 if fallback else 0
    attempt.xp_earned = xp
    attempt.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
    learner.total_xp = (learner.total_xp or 0) + xp
    pct = overall / 9 * 100 if exam["exam"] == "ielts" else overall / 2
    learner.speaking_score = round((learner.speaking_score or 0) * 0.8 + pct * 0.2, 1)
    db.add(LearningEvent(
        learner_id=learner.id, event_type="speaking_exam_completed", skill="speaking", topic=exam["title"], activity_type="mock_exam",
        correct=bank.good_score(exam["exam"], overall), score=pct, xp_earned=xp,
        extra_data={"exam": exam["exam"], "exam_id": exam["id"], "estimate": overall, "fallback": fallback, "answered": len(responses)},
    ))
    record_activity(learner, "speaking", db)
    db.commit()
    return _result_out(attempt, gems)


@router.get("/attempts/{attempt_id}", response_model=ResultOut)
def result(attempt_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    attempt = _own_attempt(db, learner, attempt_id)
    if attempt.status != STATUS_FINISHED:
        raise HTTPException(status_code=400, detail="Bài thi chưa nộp.")
    return _result_out(attempt)
