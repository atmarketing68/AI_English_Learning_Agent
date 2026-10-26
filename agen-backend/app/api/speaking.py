import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
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
from app.services import speaking_scenarios

router = APIRouter(prefix="/speaking", tags=["Speaking"])


# --- Schemas ---
class Persona(BaseModel):
    name: str
    role_en: str
    role_vi: str
    style: str
    voice: str


class Phrase(BaseModel):
    en: str
    vi: str


class ScenarioSummary(BaseModel):
    id: str
    category: str
    level: str
    emoji: str
    title_vi: str
    title_en: str
    persona: Persona
    learner_role_en: str
    learner_role_vi: str
    goal_en: str
    goal_vi: str
    first_message: str
    phrase_count: int
    recommended: bool


class ScenarioDetail(ScenarioSummary):
    phrases: list[Phrase]


class ScenarioList(BaseModel):
    categories: dict[str, str]
    learner_level: str
    scenarios: list[ScenarioSummary]


class StartRoleplayRequest(BaseModel):
    topic: Optional[str] = Field(default=None, max_length=120)
    scenario_id: Optional[str] = Field(default=None, max_length=60)


class StartRoleplayResponse(BaseModel):
    session_id: str
    topic: str
    system_prompt: str
    ai_first_message: str
    scenario_id: Optional[str] = None
    persona: Optional[Persona] = None


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
    corrected: str = ""
    hint_en: str = ""


class FinishRoleplayRequest(BaseModel):
    session_id: str
    topic: str
    total_turns: int
    average_score: float


class FinishRoleplayResponse(BaseModel):
    xp_earned: int
    message: str
    total_turns: int = 0
    average_score: float = 0.0


# --- Helpers ---
def _learner_or_404(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


def _detail(scenario: dict, learner_level: str) -> dict:
    data = {k: v for k, v in scenario.items()}
    data["phrase_count"] = len(scenario["phrases"])
    data["recommended"] = speaking_scenarios._recommended(scenario["level"], learner_level)
    return data


# --- Endpoints ---
@router.get("/scenarios", response_model=ScenarioList)
def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """G2 · Curated roleplay scenarios with Vietnamese context (no LLM call)."""
    learner = _learner_or_404(db, current_user)
    level = learner.overall_level or "A1"
    return ScenarioList(
        categories=speaking_scenarios.CATEGORIES,
        learner_level=level,
        scenarios=speaking_scenarios.list_scenarios(level),
    )


@router.get("/scenarios/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _learner_or_404(db, current_user)
    scenario = speaking_scenarios.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return ScenarioDetail(**_detail(scenario, learner.overall_level or "A1"))


@router.post("/start", response_model=StartRoleplayResponse)
def start_roleplay(
    payload: StartRoleplayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _learner_or_404(db, current_user)
    level = learner.overall_level or "A1"

    if payload.scenario_id:
        # Curated scenario: persona + opening line are ready, no LLM round-trip.
        scenario = speaking_scenarios.get_scenario(payload.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found.")
        topic = scenario["title_en"]
        system_prompt = speaking_scenarios.build_system_prompt(scenario, level)
        first_message = scenario["first_message"]
        persona = Persona(**scenario["persona"])
    else:
        if not (payload.topic or "").strip():
            raise HTTPException(status_code=422, detail="topic or scenario_id is required.")
        topic = payload.topic.strip()
        result = execute(AgentRequest(
            agent="roleplay_scenario",
            payload={"level": level, "topic": topic},
        ))
        record_agent_trace(db, learner.id, result.trace_id, result, {"topic": topic, "level": level})
        db.commit()
        if result.status == "failed":
            raise HTTPException(
                status_code=429 if result.is_quota_error else 502,
                detail=result.error or "Failed to generate scenario",
            )
        scenario_out = result.data
        system_prompt = scenario_out.get("system_prompt", "")
        first_message = scenario_out.get("ai_first_message", "Hello!")
        persona = None

    roleplay = RoleplaySession(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        topic=topic,
        system_prompt=system_prompt,
        history=[{"role": "ai", "content": first_message}],
    )
    db.add(roleplay)
    db.commit()

    return StartRoleplayResponse(
        session_id=roleplay.id,
        topic=topic,
        system_prompt=roleplay.system_prompt,
        ai_first_message=first_message,
        scenario_id=payload.scenario_id,
        persona=persona,
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
            "level": learner.overall_level or "A2",
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
        corrected=evaluation.get("corrected", "") or "",
        hint_en=evaluation.get("hint_en", "") or "",
    )


class PronunciationRequest(BaseModel):
    target_text: str = Field(min_length=1, max_length=1000)
    transcript: str = Field(default="", max_length=2000)
    duration_seconds: float | None = None
    # Optional context so the learning event can say where the attempt came from.
    source: str = Field(default="practice", max_length=40)


class PhonemeVerdict(BaseModel):
    phoneme: str
    score: Optional[float] = None


class WordVerdict(BaseModel):
    word: str
    status: str           # ok | wrong | missed
    heard: Optional[str] = None
    score: Optional[float] = None               # phoneme mode only (0–100)
    phonemes: list[PhonemeVerdict] = []         # phoneme mode only


class SoundTip(BaseModel):
    sound: str
    tip_vi: str
    words: list[str]


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
    words: list[WordVerdict] = []
    sound_tips: list[SoundTip] = []
    xp_earned: int
    # G2 · 9: "phoneme" when Azure scored the audio, "transcript" otherwise.
    mode: str = "transcript"
    completeness: Optional[float] = None
    prosody: Optional[float] = None
    recognized_text: Optional[str] = None


class PronunciationStatus(BaseModel):
    phoneme_enabled: bool
    provider: Optional[str] = None


def _award_pronunciation(db: Session, learner: LearnerProfile, overall: float, target_text: str, source: str,
                         extra: dict) -> int:
    """XP + profile + learning event shared by both scoring modes."""
    xp = 5 + int((overall / 100) * 15)      # read-aloud is a lighter activity than roleplay
    learner.total_xp = (learner.total_xp or 0) + xp
    current_speaking = learner.speaking_score or 0.0
    learner.speaking_score = round((current_speaking * 0.85) + (overall * 0.15), 1)
    db.add(LearningEvent(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        event_type="pronunciation_practice",
        skill="speaking",
        topic=target_text[:80],
        score=overall,
        xp_earned=xp,
        extra_data={"source": source, **extra},
    ))
    record_activity(learner, "speaking", db)
    db.commit()
    return xp


def _score_transcript(db: Session, learner: LearnerProfile, target_text: str, transcript: str,
                      duration_seconds: float | None, source: str) -> PronunciationResponse:
    from app.services.pronunciation_service import score_pronunciation
    result = score_pronunciation(target_text=target_text, transcript=transcript, duration_seconds=duration_seconds)
    xp = _award_pronunciation(db, learner, result.overall_score, target_text, source, {
        "mode": "transcript",
        "accuracy": round(result.accuracy, 1),
        "coverage": round(result.coverage, 1),
        "missed_words": result.missed_words[:10],
        "sounds": [t["sound"] for t in result.sound_tips],
    })
    return PronunciationResponse(**result.to_dict(), xp_earned=xp, mode="transcript")


@router.get("/pronunciation/status", response_model=PronunciationStatus)
def pronunciation_status(current_user: User = Depends(get_current_user)):
    """Whether the client should record audio for phoneme-level scoring."""
    from app.services import pronunciation_azure
    enabled = pronunciation_azure.is_enabled()
    return PronunciationStatus(phoneme_enabled=enabled, provider="azure" if enabled else None)


@router.post("/pronunciation", response_model=PronunciationResponse)
def score_pronunciation_attempt(
    payload: PronunciationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Score a read-aloud attempt (transcript vs target). No server-side audio.

    The client transcribes speech with the Web Speech API and posts the text here.
    """
    learner = _learner_or_404(db, current_user)
    return _score_transcript(db, learner, payload.target_text, payload.transcript, payload.duration_seconds, payload.source)


@router.post("/pronunciation-audio", response_model=PronunciationResponse)
async def score_pronunciation_audio(
    audio: UploadFile = File(...),
    target_text: str = Form(min_length=1, max_length=1000),
    transcript: str = Form(default="", max_length=2000),
    duration_seconds: Optional[float] = Form(default=None),
    source: str = Form(default="practice", max_length=40),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """G2 · 9 — phoneme-level scoring of a WAV take (Azure). Falls back to the
    transcript scorer when Azure is off or fails, so the learner always gets a result."""
    from app.services import pronunciation_azure

    learner = _learner_or_404(db, current_user)
    wav = await audio.read()
    if len(wav) > pronunciation_azure.MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Đoạn ghi âm quá dài (tối đa khoảng 60 giây).")
    try:
        result = pronunciation_azure.assess(wav, target_text)
    except pronunciation_azure.AzureUnavailable as exc:
        if not pronunciation_azure.is_enabled():
            raise HTTPException(status_code=404, detail="phoneme_disabled")
        import logging
        logging.getLogger("agen.pronunciation.azure").warning("Azure assessment failed, using transcript: %s", exc)
        return _score_transcript(db, learner, target_text, transcript, duration_seconds, source)

    from app.services.pronunciation_service import _normalize
    target_words = _normalize(target_text)
    missed = [w["word"] for w in result.words if w["status"] == "missed"]
    coverage = (sum(1 for w in result.words if w["status"] != "missed") / len(target_words) * 100) if target_words else 0.0
    xp = _award_pronunciation(db, learner, result.overall_score, target_text, source, {
        "mode": "phoneme",
        "accuracy": round(result.accuracy, 1),
        "fluency": round(result.fluency, 1),
        "completeness": round(result.completeness, 1),
        "prosody": result.prosody,
        "missed_words": missed[:10],
        "sounds": [t["sound"] for t in result.sound_tips],
    })
    return PronunciationResponse(
        overall_score=round(result.overall_score, 1),
        accuracy=round(result.accuracy, 1),
        coverage=round(coverage, 1),
        fluency=round(result.fluency, 1),
        target_word_count=len(target_words),
        said_word_count=len(_normalize(result.recognized_text)),
        missed_words=missed,
        extra_words=result.extra_words,
        feedback_vi=_phoneme_feedback(result.overall_score, missed),
        words=[WordVerdict(**w) for w in result.words],
        sound_tips=[SoundTip(**t) for t in result.sound_tips],
        xp_earned=xp,
        mode="phoneme",
        completeness=round(result.completeness, 1),
        prosody=round(result.prosody, 1) if result.prosody is not None else None,
        recognized_text=result.recognized_text,
    )


def _phoneme_feedback(overall: float, missed: list[str]) -> str:
    if overall >= 85:
        text = "Tuyệt vời! Từng âm đều rõ và đúng."
    elif overall >= 70:
        text = "Tốt! Chạm vào từ màu cam để xem âm nào cần sửa."
    elif overall >= 50:
        text = "Khá ổn. Nghe mẫu rồi nói chậm, nhấn rõ các âm được đánh dấu."
    else:
        text = "Hãy thử lại — nghe mẫu kỹ, đọc to và rõ từng từ."
    if missed:
        text += f" Từ chưa nghe thấy: {', '.join(missed[:5])}."
    return text


@router.post("/finish", response_model=FinishRoleplayResponse)
def finish_roleplay(
    payload: FinishRoleplayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _learner_or_404(db, current_user)
    session = db.query(RoleplaySession).filter(
        RoleplaySession.id == payload.session_id,
        RoleplaySession.learner_id == learner.id,
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
        message="Roleplay completed successfully!",
        total_turns=session.total_turns,
        average_score=round(average_score, 1),
    )
