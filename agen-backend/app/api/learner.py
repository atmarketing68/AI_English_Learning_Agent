from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core import get_db
from app.core.security import get_current_user   # ← checks user.is_active
from app.models import LearnerProfile
from app.models.user import User

router = APIRouter(prefix="/learner", tags=["Learner Profile"])


def get_current_learner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LearnerProfile:
    """
    Resolve the active learner profile.
    Uses get_current_user which already validates JWT + is_active flag.
    """
    profile = db.query(LearnerProfile).filter(
        LearnerProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return profile


# ── Schemas ───────────────────────────────────────────────────────────────────
class LearnerProfileOut(BaseModel):
    id: str
    display_name: str
    age: Optional[int]
    grade: Optional[str]
    overall_level: str
    listening_score: float
    speaking_score: float
    reading_score: float
    writing_score: float
    vocabulary_score: float
    grammar_score: float
    current_streak: int
    total_xp: int
    total_lessons_completed: int
    strengths: List[str]
    weaknesses: List[str]
    placement_completed: str
    learning_goal: Optional[str]
    interests: List[str]
    daily_study_minutes: int        # now exposed so UI can display/edit it
    invite_code: Optional[str]      # code parents use to link to this learner

    @classmethod
    def from_orm_safe(cls, p: LearnerProfile) -> "LearnerProfileOut":
        return cls(
            id=str(p.id),
            display_name=p.display_name,
            age=p.age,
            grade=p.grade,
            overall_level=p.overall_level or "PRE_A1",
            listening_score=p.listening_score or 0.0,
            speaking_score=p.speaking_score or 0.0,
            reading_score=p.reading_score or 0.0,
            writing_score=p.writing_score or 0.0,
            vocabulary_score=p.vocabulary_score or 0.0,
            grammar_score=p.grammar_score or 0.0,
            current_streak=p.current_streak or 0,
            total_xp=p.total_xp or 0,
            total_lessons_completed=p.total_lessons_completed or 0,
            strengths=p.strengths or [],
            weaknesses=p.weaknesses or [],
            placement_completed=p.placement_completed or "none",
            learning_goal=p.learning_goal,
            interests=p.interests or [],
            daily_study_minutes=p.daily_study_minutes or 15,
            invite_code=p.invite_code,
        )

    model_config = {"from_attributes": True}


class LearnerProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    age: Optional[int] = None
    grade: Optional[str] = None
    learning_goal: Optional[str] = None
    daily_study_minutes: Optional[int] = None
    interests: Optional[List[str]] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/me", response_model=LearnerProfileOut)
def get_my_profile(
    learner: LearnerProfile = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    """Get the current learner's full profile (Learner Digital Twin)."""
    # Backfill invite_code for learners created before parent feature existed
    if not learner.invite_code:
        import secrets
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        learner.invite_code = "AGEN-" + "".join(secrets.choice(alphabet) for _ in range(4))
        db.commit()
        db.refresh(learner)
    return LearnerProfileOut.from_orm_safe(learner)


@router.patch("/me", response_model=LearnerProfileOut)
def update_my_profile(
    payload: LearnerProfileUpdate,
    learner: LearnerProfile = Depends(get_current_learner),
    db: Session = Depends(get_db),
):
    """Update learner profile fields (name, goal, interests, daily target, etc.)."""
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(learner, field, value)
    db.commit()
    db.refresh(learner)
    return LearnerProfileOut.from_orm_safe(learner)
