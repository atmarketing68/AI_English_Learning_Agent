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
from app.models.learning_event import LearningEvent
from app.models.roleplay import RoleplaySession
from app.agents.orchestrator import AgentRequest, execute
from app.services.streak_service import record_activity
from app.services.trace_recorder import record_agent_trace

router = APIRouter(prefix="/speaking", tags=["Speaking"])


# --- Schemas ---
class StartRoleplayRequest(BaseModel):
    topic: str


class StartRoleplayResponse(BaseModel):
    session_id: str
    topic: str
    system_prompt: str
    ai_first_message: str


class SpeakingTurnRequest(BaseModel):
    session_id: str
    system_prompt: str = ""  # Kept for backwards compatibility; server state is authoritative.
    history: list[dict] = []  # Kept for backwards compatibility; server state is authoritative.
    user_message: str = Field(min_length=1, max_length=2000)


class SpeakingTurnResponse(BaseModel):
    ai_reply: str
    feedback: str
    is_correct: bool
    score: float


class FinishRoleplayRequest(BaseModel):
    session_id: str
    topic: str
    total_turns: int
    average_score: float


class FinishRoleplayResponse(BaseModel):
    xp_earned: int
    message: str


# --- Endpoints ---
@router.post("/start", response_model=StartRoleplayResponse)
def start_roleplay(
    payload: StartRoleplayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")

    result = execute(AgentRequest(
        agent="roleplay_scenario",
        payload={"level": learner.overall_level, "topic": payload.topic},
    ))
    record_agent_trace(db, learner.id, result.trace_id, result, {"topic": payload.topic, "level": learner.overall_level})
    db.commit()

    if result.status == "failed":
        raise HTTPException(
            status_code=429 if result.is_quota_error else 502,
            detail=result.error or "Failed to generate scenario",
        )

    scenario = result.data
    first_message = scenario.get("ai_first_message", "Hello!")
    roleplay = RoleplaySession(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        topic=payload.topic,
        system_prompt=scenario.get("system_prompt", ""),
        history=[{"role": "ai", "content": first_message}],
    )
    db.add(roleplay)
    db.commit()

    return StartRoleplayResponse(
        session_id=roleplay.id,
        topic=payload.topic,
        system_prompt=roleplay.system_prompt,
        ai_first_message=first_message,
    )


@router.post("/reply", response_model=SpeakingTurnResponse)
def handle_speaking_turn(
    payload: SpeakingTurnRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    session = db.query(RoleplaySession).filter(
        RoleplaySession.id == payload.session_id,
        RoleplaySession.learner_id == learner.id if learner else False,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Roleplay session not found.")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Roleplay session is already completed.")

    server_history = session.history or []
    result = execute(AgentRequest(
        agent="speaking_turn",
        payload={
            "system_prompt": session.system_prompt,
            "history": server_history,
            "user_message": payload.user_message,
        },
    ))
    record_agent_trace(db, learner.id, result.trace_id, result, {"session_id": payload.session_id, "skill": "speaking"})

    if result.status == "failed":
        db.commit()  # persist the failed trace
        raise HTTPException(
            status_code=429 if result.is_quota_error else 502,
            detail=result.error or "AI evaluation failed",
        )

    evaluation = result.data
    score = max(0.0, min(float(evaluation.get("score", 0.0)), 100.0))
    ai_reply = evaluation.get("ai_reply", "Could you repeat that?")
    session.history = [
        *server_history,
        {"role": "user", "content": payload.user_message},
        {"role": "ai", "content": ai_reply},
    ]
    session.total_turns += 1
    session.total_score += score
    db.commit()

    return SpeakingTurnResponse(
        ai_reply=ai_reply,
        feedback=evaluation.get("feedback", ""),
        is_correct=evaluation.get("is_correct", True),
        score=score,
    )


class PronunciationRequest(BaseModel):
    target_text: str = Field(min_length=1, max_length=1000)
    transcript: str = Field(default="", max_length=2000)
    duration_seconds: float | None = None


class PronunciationResponse(BaseModel):
    overall_score: float
    accuracy: float
    coverage: float
    fluency: float
    target_word_count: int
    said_word_count: int
    missed_words: list[str]
    extra_words: list[str]
    feedback_vi: str
    xp_earned: int


@router.post("/pronunciation", response_model=PronunciationResponse)
def score_pronunciation_attempt(
    payload: PronunciationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Score a read-aloud attempt (transcript vs target). No server-side audio.

    The client transcribes speech with the Web Speech API and posts the text here.
    """
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")

    from app.services.pronunciation_service import score_pronunciation
    result = score_pronunciation(
        target_text=payload.target_text,
        transcript=payload.transcript,
        duration_seconds=payload.duration_seconds,
    )

    # XP: scaled by score (read-aloud is a lighter activity than roleplay).
    xp = 5 + int((result.overall_score / 100) * 15)

    learner.total_xp = (learner.total_xp or 0) + xp
    current_speaking = learner.speaking_score or 0.0
    learner.speaking_score = round((current_speaking * 0.85) + (result.overall_score * 0.15), 1)

    db.add(LearningEvent(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        event_type="pronunciation_practice",
        skill="speaking",
        topic=payload.target_text[:80],
        score=result.overall_score,
        xp_earned=xp,
        extra_data={
            "accuracy": round(result.accuracy, 1),
            "coverage": round(result.coverage, 1),
            "missed_words": result.missed_words[:10],
        },
    ))
    record_activity(learner, "speaking", db)
    db.commit()

    return PronunciationResponse(**result.to_dict(), xp_earned=xp)


@router.post("/finish", response_model=FinishRoleplayResponse)
def finish_roleplay(
    payload: FinishRoleplayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")

    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    session = db.query(RoleplaySession).filter(
        RoleplaySession.id == payload.session_id,
        RoleplaySession.learner_id == learner.id if learner else False,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Roleplay session not found.")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Roleplay session is already completed.")

    # Calculate score and XP from server-recorded turns, never from client input.
    average_score = session.total_score / session.total_turns if session.total_turns else 0.0
    base_xp = 20
    bonus_xp = int((average_score / 100) * 20)
    total_xp = base_xp + bonus_xp

    # Update Learner Profile
    learner.total_xp += total_xp
    current_speaking = learner.speaking_score or 0.0
    learner.speaking_score = round((current_speaking * 0.8) + (average_score * 0.2), 1)

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)

    # Record Event
    event = LearningEvent(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        event_type="roleplay_completed",
        skill="speaking",
        topic=payload.topic,
        score=average_score,
        xp_earned=total_xp,
        extra_data={"session_id": payload.session_id, "turns": session.total_turns},
    )
    db.add(event)

    # Update streak and daily challenge progress
    record_activity(learner, "speaking", db)

    db.commit()

    return FinishRoleplayResponse(
        xp_earned=total_xp,
        message="Roleplay completed successfully!"
    )
