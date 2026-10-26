"""
AGEN — Writing Coach API
Endpoints for writing prompts, submission evaluation, and history.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.writing import WritingSubmission
from app.models.learning_event import LearningEvent
from app.agents.writing_agent import EXAM_GENRES
from app.agents.orchestrator import AgentRequest, execute
from app.services.streak_service import record_activity
from app.services.trace_recorder import record_agent_trace

router = APIRouter(prefix="/writing", tags=["Writing"])

GENRES = ["opinion", "narrative", "descriptive", "email", "ielts_task2", "ielts_task1", "toeic_email", "toeic_essay"]   # G5 · exam genres


# ── Schemas ───────────────────────────────────────────────────────────────────
class PromptRequest(BaseModel):
    genre: Optional[str] = "opinion"


class PromptResponse(BaseModel):
    title: str
    prompt: str
    genre: str
    word_target: str
    guide_steps: list[str]
    useful_phrases: list[str]
    example_opening: str
    level: str
    topic: str


class GrammarError(BaseModel):
    original: str
    corrected: str
    explanation_vi: str


class EvaluationScores(BaseModel):
    grammar: float
    vocabulary: float
    coherence: float
    task_achievement: float


class SubmitRequest(BaseModel):
    prompt_title: str = Field(max_length=200)
    prompt_text: str = Field(max_length=2000)
    genre: str
    user_text: str = Field(max_length=5000)


class ExamBand(BaseModel):
    exam: str                     # ielts | toeic
    overall: float                # IELTS 0–9 · TOEIC 0–200
    criteria: dict[str, float]
    next_band_tips: list[str]


class EvaluationResponse(BaseModel):
    submission_id: str
    overall_score: float
    grade: str
    word_count: int
    scores: EvaluationScores
    grammar_errors: list[GrammarError]
    vocabulary_feedback: str
    coherence_feedback: str
    strengths: list[str]
    improvements: list[str]
    corrected_version: str
    encouragement: str
    xp_earned: int
    exam_band: Optional[ExamBand] = None


class HistoryItem(BaseModel):
    id: str
    prompt_title: str
    genre: str
    level: str
    overall_score: Optional[float]
    grade: Optional[str]
    word_count: int
    xp_earned: int
    created_at: datetime
    # G11 · teacher re-grade (overrides the AI score when present)
    band: Optional[float] = None
    teacher_score: Optional[float] = None
    teacher_band: Optional[float] = None
    teacher_comment: Optional[str] = None
    teacher_scored_at: Optional[datetime] = None


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


def _grade_to_xp(grade: str, score: float) -> int:
    if grade == "S":   return 50
    if grade == "A":   return 35
    if grade == "B":   return 25
    if grade == "C":   return 15
    return 8  # D grade — effort points


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/prompt", response_model=PromptResponse)
def get_writing_prompt(
    payload: PromptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate an AI writing prompt tailored to learner's level and chosen genre."""
    learner = _get_learner(db, current_user.id)

    genre = payload.genre if payload.genre in GENRES else "opinion"

    result = execute(AgentRequest(
        agent="writing_prompt",
        payload={"level": learner.overall_level, "genre": genre},
    ))
    record_agent_trace(db, learner.id, result.trace_id, result, {"genre": genre, "level": learner.overall_level})
    db.commit()

    if result.status == "failed":
        raise HTTPException(
            status_code=429 if result.is_quota_error else 502,
            detail=result.error or "Prompt generation failed",
        )

    return PromptResponse(**result.data)


@router.post("/submit", response_model=EvaluationResponse)
def submit_writing(
    payload: SubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit writing for AI evaluation. Returns detailed multi-dimension feedback."""
    learner = _get_learner(db, current_user.id)

    if len(payload.user_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Writing is too short to evaluate.")

    # AI Evaluation — routed through orchestrator so output passes the quality gate
    result = execute(AgentRequest(
        agent="writing_evaluation",
        payload={
            "prompt_text": payload.prompt_text,
            "user_text": payload.user_text,
            "level": learner.overall_level,
            "genre": payload.genre if payload.genre in GENRES else "opinion",
        },
    ))
    record_agent_trace(db, learner.id, result.trace_id, result, {"genre": payload.genre, "level": learner.overall_level})

    if result.status == "failed":
        db.commit()  # persist the failed trace
        raise HTTPException(
            status_code=429 if result.is_quota_error else 502,
            detail=result.error or "Writing evaluation failed",
        )

    eval_result = result.data
    grade     = eval_result.get("grade", "C")
    score     = eval_result.get("overall_score", 50.0)
    xp        = _grade_to_xp(grade, score)
    word_count = eval_result.get("word_count", len(payload.user_text.split()))

    # Save submission to DB
    submission = WritingSubmission(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        prompt_title=payload.prompt_title,
        prompt_text=payload.prompt_text,
        genre=payload.genre,
        level=learner.overall_level,
        user_text=payload.user_text,
        word_count=word_count,
        overall_score=score,
        grade=grade,
        evaluation=eval_result,
        xp_earned=xp,
        evaluated_at=datetime.now(timezone.utc),
    )
    db.add(submission)

    # Update learner writing score (EMA)
    current_w = learner.writing_score or 0.0
    learner.writing_score = round(current_w * 0.8 + score * 0.2, 1)
    learner.total_xp += xp

    # Record learning event
    event = LearningEvent(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        event_type="writing_submitted",
        skill="writing",
        topic=payload.prompt_title,
        score=score,
        xp_earned=xp,
        extra_data={"grade": grade, "word_count": word_count, "genre": payload.genre},
    )
    db.add(event)

    # Update streak and daily challenge progress
    record_activity(learner, "writing", db)

    db.commit()

    scores_raw = eval_result.get("scores", {})
    return EvaluationResponse(
        submission_id=submission.id,
        overall_score=score,
        grade=grade,
        word_count=word_count,
        scores=EvaluationScores(
            grammar=scores_raw.get("grammar", 0),
            vocabulary=scores_raw.get("vocabulary", 0),
            coherence=scores_raw.get("coherence", 0),
            task_achievement=scores_raw.get("task_achievement", 0),
        ),
        grammar_errors=[GrammarError(**e) for e in eval_result.get("grammar_errors", [])[:5]],
        vocabulary_feedback=eval_result.get("vocabulary_feedback", ""),
        coherence_feedback=eval_result.get("coherence_feedback", ""),
        strengths=eval_result.get("strengths", []),
        improvements=eval_result.get("improvements", []),
        corrected_version=eval_result.get("corrected_version", ""),
        encouragement=eval_result.get("encouragement", "Cố lên nhé!"),
        xp_earned=xp,
        exam_band=ExamBand(**eval_result["exam_band"]) if payload.genre in EXAM_GENRES and eval_result.get("exam_band") else None,
    )


@router.get("/history", response_model=list[HistoryItem])
def get_writing_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get learner's past writing submissions."""
    learner = _get_learner(db, current_user.id)
    submissions = (
        db.query(WritingSubmission)
        .filter(WritingSubmission.learner_id == learner.id)
        .order_by(WritingSubmission.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        HistoryItem(
            id=s.id, prompt_title=s.prompt_title, genre=s.genre or "",
            level=s.level, overall_score=s.overall_score, grade=s.grade,
            word_count=s.word_count, xp_earned=s.xp_earned, created_at=s.created_at,
            band=((s.evaluation or {}).get("exam_band") or {}).get("overall") if isinstance(s.evaluation, dict) else None,
            teacher_score=s.teacher_score, teacher_band=s.teacher_band, teacher_comment=s.teacher_comment,
            teacher_scored_at=s.teacher_scored_at,
        )
        for s in submissions
    ]
