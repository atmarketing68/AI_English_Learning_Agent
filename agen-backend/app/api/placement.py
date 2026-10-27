"""AGEN - Placement Test API."""
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.placement import PlacementSession
from app.models.learning_event import LearningEvent
from app.agents.assessment_agent import (
    build_speaking_question,
    evaluate_answer,
    calculate_final_result,
)
from app.agents.orchestrator import AgentRequest, execute
from app.services.trace_recorder import record_agent_trace

router = APIRouter(prefix="/placement", tags=["Placement Test"])

# G2 · 4 skills: 10 text questions + 3 listening + 1 read-aloud speaking item (last).
TOTAL_QUESTIONS = 14
SKILL_ROTATION = [
    "vocabulary", "grammar", "listening", "vocabulary", "grammar", "reading", "listening",
    "vocabulary", "grammar", "reading", "listening", "vocabulary", "grammar", "speaking",
]

# ─── Schemas ─────────────────────────────────────────────────────────────────
class StartResponse(BaseModel):
    session_id: str
    message: str
    total_questions: int
    assessment_type: str


class QuestionResponse(BaseModel):
    session_id: str
    question_index: int
    total_questions: int
    skill: str
    level: str
    passage: Optional[str]
    question: str
    options: dict[str, str]
    # G2 · listening: the client plays this (TTS) and never shows it before answering.
    audio_text: Optional[str] = None
    # G2 · speaking: sentence to read aloud; the answer is the transcript (or "__skip__").
    target_text: Optional[str] = None
    instruction_vi: Optional[str] = None


class AnswerPayload(BaseModel):
    session_id: str
    answer: str = Field(max_length=2000)  # "A"–"D", or a speech transcript for the speaking item


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
    score_delta: int
    question_index: int
    total_questions: int
    is_finished: bool
    skipped: bool = False
    speaking_score: Optional[float] = None


class FinishResponse(BaseModel):
    assessment_type: str
    overall_level: str
    skill_scores: dict
    total_correct: int
    total_questions: int
    accuracy_percent: float
    recommendations: list[str]
    message: str


# ─── Endpoints ───────────────────────────────────────────────────────────────
@router.post("/start", response_model=StartResponse)
def start_placement(
    assessment_type: Literal["baseline", "followup"] = "baseline",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new placement test session for the current user."""
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")

    session = PlacementSession(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        learner_age=learner.age,
        learner_grade=learner.grade,
        assessment_type=assessment_type,
    )
    db.add(session)
    db.commit()

    return StartResponse(
        session_id=session.id,
        message=f"Bài Placement Test của bạn đã bắt đầu! Hãy trả lời {TOTAL_QUESTIONS} câu hỏi (đọc, nghe và nói) để AI AGENT ENGLISH tìm hiểu trình độ của bạn.",
        total_questions=TOTAL_QUESTIONS,
        assessment_type=assessment_type,
    )


@router.get("/question", response_model=QuestionResponse)
def get_next_question(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the next question in the placement test."""
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    session = db.query(PlacementSession).filter(
        PlacementSession.id == session_id,
        PlacementSession.learner_id == learner.id if learner else False,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session không tồn tại. Hãy bắt đầu bài test mới.")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Bài test đã hoàn thành.")

    idx = session.current_index
    if idx >= TOTAL_QUESTIONS:
        raise HTTPException(status_code=400, detail="Bài test đã hoàn thành. Hãy gọi /finish để xem kết quả.")

    skill = SKILL_ROTATION[idx]
    if skill == "speaking":
        # Read-aloud item: built locally from the adaptive level, no LLM call.
        question = build_speaking_question(session.level, session.id)
        session.current_question = question
        db.commit()
        return QuestionResponse(
            session_id=session_id,
            question_index=idx,
            total_questions=TOTAL_QUESTIONS,
            skill="speaking",
            level=question["effective_level"],
            passage=None,
            question=question["question"],
            options={},
            target_text=question["target_text"],
            instruction_vi=question["instruction_vi"],
        )

    result = execute(AgentRequest(
        agent="placement_question",
        payload={
            "skill": skill,  # assessment_agent.generate_placement_question accepts skill
            "current_level": session.level,
            "question_index": idx,
            "previous_correct": session.last_correct,
            "learner_age": session.learner_age,
            "learner_grade": session.learner_grade,
            "skill_occurrence": SKILL_ROTATION[:idx].count(skill),
        },
    ))
    record_agent_trace(db, session.learner_id, result.trace_id, result, {"skill": skill, "level": session.level})

    if result.status == "failed":
        db.commit()  # persist the failed trace
        raise HTTPException(
            status_code=429 if result.is_quota_error else 502,
            detail=result.error or "Không tạo được câu hỏi. Hãy thử lại.",
        )

    question = result.data
    session.current_question = question
    db.commit()

    return QuestionResponse(
        session_id=session_id,
        question_index=idx,
        total_questions=TOTAL_QUESTIONS,
        skill=question.get("skill", skill),
        level=question.get("effective_level", session.level),
        passage=question.get("passage") or None,
        question=question["question"],
        options=question["options"],
        audio_text=(question.get("audio_text") or None) if skill == "listening" else None,
    )


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(
    payload: AnswerPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit an answer and receive immediate feedback."""
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    session = db.query(PlacementSession).filter(
        PlacementSession.id == payload.session_id,
        PlacementSession.learner_id == learner.id if learner else False,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session không tồn tại.")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Bài test đã hoàn thành.")

    question = session.current_question
    if not question:
        raise HTTPException(status_code=400, detail="Chưa có câu hỏi nào được tải. Hãy gọi /question trước.")

    idx = session.current_index
    result = evaluate_answer(question, payload.answer)

    # Determine max possible score for this level (for final calculation)
    from app.agents.assessment_agent import CEFR_LEVELS
    level = question.get("effective_level", "A1")
    level_idx = CEFR_LEVELS.index(level) if level in CEFR_LEVELS else 1
    max_score_delta = 10 + level_idx * 5

    answer_record = {
        **result,
        "question_index": idx,
        "max_score_delta": max_score_delta,
    }
    session.answers = [*(session.answers or []), answer_record]
    session.last_correct = result["is_correct"]

    # Update adaptive level (a skipped speaking item says nothing about the level)
    if result.get("skipped"):
        pass
    elif result["is_correct"] and level_idx < len(CEFR_LEVELS) - 1:
        session.level = CEFR_LEVELS[level_idx + 1]
    elif not result["is_correct"] and level_idx > 0:
        session.level = CEFR_LEVELS[level_idx - 1]

    session.current_index += 1
    session.current_question = None
    db.commit()

    is_finished = session.current_index >= TOTAL_QUESTIONS

    return AnswerResponse(
        is_correct=result["is_correct"],
        correct_answer=result["correct_answer"],
        explanation=result["explanation"],
        score_delta=result["score_delta"],
        question_index=idx,
        total_questions=TOTAL_QUESTIONS,
        is_finished=is_finished,
        skipped=bool(result.get("skipped")),
        speaking_score=result.get("speaking_score"),
    )


@router.post("/finish", response_model=FinishResponse)
def finish_placement(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Finalize the placement test and update the learner's profile."""
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    session = db.query(PlacementSession).filter(
        PlacementSession.id == session_id,
        PlacementSession.learner_id == learner.id if learner else False,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session không tồn tại.")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Bài test đã hoàn thành.")

    if session.current_index < TOTAL_QUESTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Bài test chưa hoàn thành ({session.current_index}/{TOTAL_QUESTIONS} câu).",
        )

    final = calculate_final_result(session.answers or [])

    # Baseline establishes the learner profile. Follow-up assessments measure
    # change without changing the learner's curriculum level.
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if learner and session.assessment_type == "baseline":
        learner.overall_level = final["overall_level"]
        learner.placement_completed = "done"
        skill_map = {
            "vocabulary": "vocabulary_score",
            "grammar": "grammar_score",
            "reading": "reading_score",
            "listening": "listening_score",
            "speaking": "speaking_score",
        }
        for skill_key, db_field in skill_map.items():
            if skill_key in final["skill_scores"]:
                setattr(learner, db_field, final["skill_scores"][skill_key])

        # Credit lower-level curriculum so a learner placed above A1 isn't locked
        # out of their level's roadmap (they've effectively tested out of below).
        from app.services.placement_credit import grant_placement_credit
        grant_placement_credit(db, learner, final["overall_level"])

        db.commit()

    if learner:
        db.add(LearningEvent(
            learner_id=learner.id,
            event_type=f"{session.assessment_type}_assessment_completed",
            skill="assessment",
            score=final["accuracy_percent"],
            extra_data={
                "assessment_type": session.assessment_type,
                "overall_level": final["overall_level"],
                "skill_scores": final["skill_scores"],
                "total_correct": final["total_correct"],
                "total_questions": final["total_questions"],
            },
        ))
        db.commit()

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()

    return FinishResponse(
        assessment_type=session.assessment_type,
        **final,
        message=f"🎉 Hoàn tất! Trình độ của bạn là {final['overall_level']}. AI AGENT ENGLISH sẽ tạo lộ trình học phù hợp!",
    )
