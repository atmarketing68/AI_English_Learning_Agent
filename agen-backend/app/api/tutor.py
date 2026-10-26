"""G8 · Hỏi Bo — grammar & usage Q&A chatbot in Vietnamese."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents import tutor_agent
from app.agents.orchestrator import AgentRequest, execute
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timeutil import local_day_start_utc
from app.models.learner_profile import LearnerProfile
from app.models.tutor_message import ROLE_ASSISTANT, ROLE_USER, TutorMessage
from app.models.user import User
from app.services.subscription_service import is_premium
from app.services.trace_recorder import record_agent_trace

router = APIRouter(prefix="/tutor", tags=["Tutor (Bo)"])

SUGGESTED_QUESTIONS = [
    "Khi nào dùng thì hiện tại hoàn thành, khi nào dùng quá khứ đơn?",
    "Phân biệt 'a', 'an' và 'the'?",
    "'Make' và 'do' khác nhau thế nào?",
    "Cách dùng 'since' và 'for'?",
    "Câu điều kiện loại 2 dùng khi nào?",
    "'Although' và 'despite' khác gì nhau?",
]


# ── Schemas ──────────────────────────────────────────────────────────────────
class Example(BaseModel):
    en: str
    vi: str = ""


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    rule: str = ""
    examples: list[Example] = []
    common_mistake: str = ""
    follow_ups: list[str] = []
    fallback: bool = False
    created_at: datetime


class TutorHome(BaseModel):
    messages: list[MessageOut]
    suggested: list[str]
    is_premium: bool
    free_daily_limit: int
    asked_today: int
    remaining_today: Optional[int]        # None = unlimited


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=600)


class AskOut(BaseModel):
    question: MessageOut
    answer: MessageOut
    asked_today: int
    remaining_today: Optional[int]


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


def _out(m: TutorMessage) -> MessageOut:
    extra = m.extra if isinstance(m.extra, dict) else {}
    return MessageOut(
        id=m.id, role=m.role, content=m.content, rule=extra.get("rule", "") or "",
        examples=[Example(**e) for e in extra.get("examples", []) if isinstance(e, dict) and e.get("en")],
        common_mistake=extra.get("common_mistake", "") or "", follow_ups=list(extra.get("follow_ups", []) or []),
        fallback=bool(m.fallback), created_at=m.created_at,
    )


def _asked_today(db: Session, learner_id: str) -> int:
    """Questions that got a real (non-fallback) answer today."""
    return (
        db.query(TutorMessage)
        .filter(TutorMessage.learner_id == learner_id, TutorMessage.role == ROLE_ASSISTANT,
                TutorMessage.fallback.is_(False), TutorMessage.created_at >= local_day_start_utc())
        .count()
    )


def _quota(db: Session, user_id: str, learner_id: str) -> tuple[bool, int, Optional[int]]:
    premium = is_premium(db, user_id)
    asked = _asked_today(db, learner_id)
    remaining = None if premium else max(0, settings.TUTOR_FREE_DAILY_LIMIT - asked)
    return premium, asked, remaining


# ── Endpoints ────────────────────────────────────────────────────────────────
@router.get("", response_model=TutorHome)
def home(limit: int = 40, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    rows = db.query(TutorMessage).filter(TutorMessage.learner_id == learner.id).order_by(TutorMessage.created_at.desc()).limit(min(limit, 200)).all()
    premium, asked, remaining = _quota(db, current_user.id, learner.id)
    return TutorHome(messages=[_out(m) for m in reversed(rows)], suggested=SUGGESTED_QUESTIONS, is_premium=premium,
                     free_daily_limit=settings.TUTOR_FREE_DAILY_LIMIT, asked_today=asked, remaining_today=remaining)


@router.post("/ask", response_model=AskOut)
def ask(payload: AskIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    premium, asked, remaining = _quota(db, current_user.id, learner.id)
    if not premium and remaining == 0:
        raise HTTPException(status_code=403, detail=f"Gói miễn phí hỏi Bo được {settings.TUTOR_FREE_DAILY_LIMIT} câu mỗi ngày. Nâng cấp Premium để hỏi không giới hạn.")

    history = db.query(TutorMessage).filter(TutorMessage.learner_id == learner.id).order_by(TutorMessage.created_at.desc()).limit(tutor_agent.MAX_HISTORY).all()
    question = TutorMessage(learner_id=learner.id, role=ROLE_USER, content=payload.question.strip())
    db.add(question)
    db.flush()

    result = execute(AgentRequest(agent="tutor_answer", payload={
        "question": payload.question.strip(), "history": tutor_agent.history_payload(list(reversed(history))),
        "level": learner.overall_level or "A2", "age": learner.age,
    }))
    record_agent_trace(db, learner.id, result.trace_id, result, {"level": learner.overall_level})
    fallback = result.status != "succeeded"
    data = result.data if not fallback else tutor_agent.fallback_answer(payload.question)
    answer = TutorMessage(
        learner_id=learner.id, role=ROLE_ASSISTANT, content=data["answer_vi"], fallback=fallback,
        extra={k: data.get(k) for k in ("rule", "examples", "common_mistake", "follow_ups", "on_topic")},
    )
    db.add(answer)
    db.commit()
    premium, asked, remaining = _quota(db, current_user.id, learner.id)
    return AskOut(question=_out(question), answer=_out(answer), asked_today=asked, remaining_today=remaining)


@router.delete("", status_code=204)
def clear(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    db.query(TutorMessage).filter(TutorMessage.learner_id == learner.id).delete()
    db.commit()
