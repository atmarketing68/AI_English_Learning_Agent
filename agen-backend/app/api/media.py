"""G10 · Học qua podcast / video: list, open an episode, submit comprehension answers."""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.media_progress import MediaProgress
from app.models.user import User
from app.services import media_library as lib
from app.services.shop import award_gems
from app.services.streak_service import record_activity

router = APIRouter(prefix="/media", tags=["Podcast & video"])


class EpisodeSummary(BaseModel):
    id: str
    kind: str
    level: str
    minutes: int
    topic: str
    title: str
    title_vi: str
    description_vi: str
    has_video: bool
    best_score: Optional[float]
    completed: bool


class SubmitIn(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)


class QuestionResult(BaseModel):
    id: str
    correct: bool
    expected: str
    explanation_vi: str


class SubmitOut(BaseModel):
    correct: int
    total: int
    pct: float
    details: list[QuestionResult]
    xp_earned: int
    gems_earned: int
    best_score: float


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


@router.get("", response_model=list[EpisodeSummary])
def list_episodes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    progress = {p.episode_id: p for p in db.query(MediaProgress).filter(MediaProgress.learner_id == learner.id).all()}
    out = []
    for e in lib.list_episodes():
        p = progress.get(e["id"])
        out.append(EpisodeSummary(id=e["id"], kind=e["kind"], level=e["level"], minutes=e["minutes"], topic=e["topic"], title=e["title"], title_vi=e["title_vi"],
                                  description_vi=e["description_vi"], has_video=bool(e.get("youtube_id")),
                                  best_score=p.best_score if p else None, completed=bool(p and p.completed_at)))
    return out


@router.get("/{episode_id}")
def get_episode(episode_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _learner(db, current_user)
    ep = lib.get_episode(episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập này.")
    return lib.public_episode(ep)


@router.post("/{episode_id}/submit", response_model=SubmitOut)
def submit(episode_id: str, payload: SubmitIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    ep = lib.get_episode(episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Không tìm thấy tập này.")
    result = lib.grade(ep, payload.answers)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    progress = db.query(MediaProgress).filter(MediaProgress.learner_id == learner.id, MediaProgress.episode_id == episode_id).first()
    first_time = progress is None or progress.completed_at is None
    if progress is None:
        progress = MediaProgress(learner_id=learner.id, episode_id=episode_id)
        db.add(progress)
    previous_best = progress.best_score or 0.0
    progress.attempts = (progress.attempts or 0) + 1
    progress.best_score = max(previous_best, result["pct"])
    progress.last_at = now
    progress.completed_at = progress.completed_at or now
    # XP only for the first completion and for improving the best score, so replays cannot farm XP.
    xp = min(lib.XP_CAP, result["correct"] * lib.XP_PER_CORRECT) if first_time else (lib.XP_PER_CORRECT if result["pct"] > previous_best else 0)
    gems = award_gems(learner, lib.GEMS_PERFECT) if result["pct"] == 100 and previous_best < 100 else 0
    learner.total_xp = (learner.total_xp or 0) + xp
    learner.listening_score = round((learner.listening_score or 0) * 0.85 + result["pct"] * 0.15, 1)
    db.add(LearningEvent(learner_id=learner.id, event_type="media_completed", skill="listening", topic=ep["title"], activity_type="podcast",
                         correct=result["pct"] >= 60, score=result["pct"], xp_earned=xp, extra_data={"episode_id": episode_id, "level": ep["level"]}))
    record_activity(learner, "listening", db)
    db.commit()
    return SubmitOut(correct=result["correct"], total=result["total"], pct=result["pct"], details=[QuestionResult(**d) for d in result["details"]],
                     xp_earned=xp, gems_earned=gems, best_score=progress.best_score)
