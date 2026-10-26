"""
AGEN — Gamification API
Endpoints for achievements and daily challenges.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.achievement import Achievement, LearnerAchievement, DailyChallenge
from app.services.gamification import check_and_award_achievements, get_or_create_daily_challenge
from app.services.streak_service import effective_streak, record_activity

router = APIRouter(prefix="/gamification", tags=["Gamification"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class AchievementSchema(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    category: str
    xp_reward: int
    condition_type: str
    condition_value: int
    earned: bool
    earned_at: Optional[datetime] = None


class DailyChallengeSchema(BaseModel):
    id: str
    title: str
    description: str
    skill: str
    target_value: int
    current_value: int
    xp_reward: int
    is_completed: bool
    progress_pct: float


# ── Helper ────────────────────────────────────────────────────────────────────
def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/achievements", response_model=list[AchievementSchema])
def get_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all achievements with earned status for the current learner."""
    learner = _get_learner(db, current_user.id)

    # Auto-check for any newly earned achievements
    check_and_award_achievements(learner, db)

    all_achievements = db.query(Achievement).all()
    earned_map = {
        la.achievement_id: la.earned_at
        for la in db.query(LearnerAchievement).filter(LearnerAchievement.learner_id == learner.id).all()
    }

    result = []
    for ach in all_achievements:
        result.append(AchievementSchema(
            id=ach.id,
            name=ach.name,
            description=ach.description,
            icon=ach.icon,
            category=ach.category,
            xp_reward=ach.xp_reward,
            condition_type=ach.condition_type,
            condition_value=ach.condition_value,
            earned=ach.id in earned_map,
            earned_at=earned_map.get(ach.id),
        ))

    # Sort: earned first, then by category
    result.sort(key=lambda a: (not a.earned, a.category))
    return result


@router.get("/daily-challenge", response_model=DailyChallengeSchema)
def get_daily_challenge(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns today's daily challenge for the learner."""
    learner = _get_learner(db, current_user.id)
    challenge = get_or_create_daily_challenge(learner, db)

    target = challenge.target_value or 1
    current = challenge.current_value or 0
    pct = min(round((current / target) * 100, 1), 100.0)

    return DailyChallengeSchema(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        skill=challenge.skill,
        target_value=target,
        current_value=current,
        xp_reward=challenge.xp_reward,
        is_completed=challenge.is_completed,
        progress_pct=pct,
    )


@router.post("/check-achievements", response_model=list[dict])
def trigger_achievement_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger achievement check (called after lesson/writing/speaking completion).
    Returns list of newly earned achievements.
    """
    learner = _get_learner(db, current_user.id)
    newly_earned = check_and_award_achievements(learner, db)
    return newly_earned


# ── Schemas ───────────────────────────────────────────────────────────────────
class ActivityUpdateRequest(BaseModel):
    skill: str  # the skill of the completed activity: vocabulary/grammar/reading/listening/speaking/writing


class ActivityUpdateResponse(BaseModel):
    current_streak: int
    longest_streak: int
    daily_challenge_completed: bool
    newly_earned_achievements: list[dict]


@router.post("/activity-completed", response_model=ActivityUpdateResponse)
def on_activity_completed(
    payload: ActivityUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Called after any learning activity is completed (lesson, writing, speaking).
    Updates streak, daily challenge progress, and checks for new achievements.
    Returns fresh streak data + any newly earned achievements.
    """
    learner = _get_learner(db, current_user.id)

    # Update streak + daily challenge
    activity_result = record_activity(learner, payload.skill, db)

    # Check and award any newly unlocked achievements
    newly_earned = check_and_award_achievements(learner, db)

    db.commit()

    return ActivityUpdateResponse(
        current_streak=learner.current_streak or 0,
        longest_streak=learner.longest_streak or 0,
        daily_challenge_completed=activity_result["daily_challenge_completed"],
        newly_earned_achievements=newly_earned,
    )


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_active_at: Optional[datetime]


@router.get("/streak", response_model=StreakResponse)
def get_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current streak info for the learner."""
    learner = _get_learner(db, current_user.id)
    return StreakResponse(
        current_streak=effective_streak(learner),
        longest_streak=learner.longest_streak or 0,
        last_active_at=learner.last_active_at,
    )
