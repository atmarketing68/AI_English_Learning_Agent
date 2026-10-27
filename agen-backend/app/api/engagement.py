"""
AGEN — Engagement API
Streak (with streak freezes), the three daily quests and the weekly goal,
served together so the dashboard needs one request.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timeutil import local_date, local_today
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services.engagement import (
    WEEKLY_GOAL_OPTIONS, WEEKLY_REWARD_XP, ClaimError, claim_quest, claim_weekly_reward,
    day_metrics, quest_view, todays_quests, weekly_progress,
)
from app.services.streak_service import MAX_STREAK_FREEZES, StreakRepairError, repair_offer, repair_streak, streak_state
from app.services import league as league_service

router = APIRouter(prefix="/engagement", tags=["Engagement"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class StreakOut(BaseModel):
    current: int
    longest: int
    studied_today: bool
    freezes: int
    max_freezes: int
    protected: bool                  # missed days are covered by freezes
    missed_days: int
    freeze_used_today: bool          # a freeze saved the streak on today's first activity
    repair: Optional[dict] = None    # G14 · {lost, restored, cost} when the streak can be bought back today


class QuestOut(BaseModel):
    id: str
    code: str
    title: str
    icon: str
    progress: int
    target: int
    xp_reward: int
    completed: bool
    claimed: bool


class WeekDayOut(BaseModel):
    date: str
    label: str
    done: bool
    is_today: bool
    is_future: bool


class WeeklyOut(BaseModel):
    goal_days: int
    options: list[int]
    days_done: int
    days: list[WeekDayOut]
    completed: bool
    claimed: bool
    reward_xp: int


class EngagementOut(BaseModel):
    total_xp: int
    streak: StreakOut
    quests: list[QuestOut]
    weekly: WeeklyOut


class ClaimOut(BaseModel):
    xp_awarded: int
    freeze_awarded: bool = False
    state: EngagementOut


class WeeklyGoalIn(BaseModel):
    days: int


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


def _freeze_used_today(used_at: Optional[datetime]) -> bool:
    return used_at is not None and local_date(used_at) == local_today()


def _state(db: Session, learner: LearnerProfile) -> EngagementOut:
    today = local_today()
    s = streak_state(learner, today)
    metrics = day_metrics(db, learner.id, today)
    weekly = weekly_progress(db, learner, today)
    return EngagementOut(
        total_xp=learner.total_xp or 0,
        streak=StreakOut(
            current=s.current,
            longest=learner.longest_streak or 0,
            studied_today=s.studied_today,
            freezes=learner.streak_freezes or 0,
            max_freezes=MAX_STREAK_FREEZES,
            protected=s.protected,
            missed_days=s.missed_days,
            freeze_used_today=_freeze_used_today(learner.streak_freeze_used_at),
            repair=repair_offer(learner, today),
        ),
        quests=[QuestOut(**quest_view(q, metrics)) for q in todays_quests(db, learner, today)],
        weekly=WeeklyOut(
            goal_days=weekly.goal_days,
            options=list(WEEKLY_GOAL_OPTIONS),
            days_done=weekly.days_done,
            days=[WeekDayOut(**d) for d in weekly.days],
            completed=weekly.completed,
            claimed=weekly.claimed,
            reward_xp=WEEKLY_REWARD_XP,
        ),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/today", response_model=EngagementOut)
def get_today(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _state(db, _get_learner(db, current_user.id))


@router.post("/streak/repair", response_model=EngagementOut)
def streak_repair(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """G14 · Sửa chuỗi trong 24 giờ bằng đá quý."""
    learner = _get_learner(db, current_user.id)
    try:
        repair_streak(learner)
    except StreakRepairError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return _state(db, learner)


@router.post("/quests/{quest_id}/claim", response_model=ClaimOut)
def claim_daily_quest(
    quest_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(db, current_user.id)
    try:
        xp = claim_quest(db, learner, quest_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Quest not found.")
    except ClaimError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return ClaimOut(xp_awarded=xp, state=_state(db, learner))


@router.post("/weekly/claim", response_model=ClaimOut)
def claim_weekly(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _get_learner(db, current_user.id)
    try:
        result = claim_weekly_reward(db, learner)
    except ClaimError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return ClaimOut(xp_awarded=result["xp_awarded"], freeze_awarded=result["freeze_awarded"], state=_state(db, learner))


@router.put("/weekly-goal", response_model=EngagementOut)
def set_weekly_goal(
    payload: WeeklyGoalIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.days not in WEEKLY_GOAL_OPTIONS:
        raise HTTPException(status_code=422, detail=f"Mục tiêu tuần phải là một trong {list(WEEKLY_GOAL_OPTIONS)} ngày.")
    learner = _get_learner(db, current_user.id)
    learner.weekly_goal_days = payload.days
    db.commit()
    return _state(db, learner)


# ── G3/G4 · Giải đấu tuần (bảng 30 người, thăng/hạng hạng) ──────────────────
class LeagueEntry(BaseModel):
    rank: int
    learner_id: str
    display_name: str
    level: str
    avatar: dict = {}
    xp: int
    is_me: bool
    zone: str                 # promote | stay | relegate


class LeagueMe(BaseModel):
    rank: Optional[int]
    xp: int
    participants: int


class LastWeekOut(BaseModel):
    week: str
    rank: Optional[int]
    xp: int
    participants: int
    reward_xp: int
    reward_gems: int
    tier_name: Optional[str]
    movement: str
    claimed: bool
    claimable: bool


class LeagueOut(BaseModel):
    week: str
    starts_on: str
    ends_on: str
    tier: int
    tier_name: str
    tiers: list[str]
    group_no: int
    group_size: int
    promote_top: int
    relegate_bottom: int
    rewards: list[dict]
    entries: list[LeagueEntry]
    me: LeagueMe
    last_week: LastWeekOut


class LeagueClaimOut(BaseModel):
    xp_awarded: int
    gems_awarded: int
    total_xp: int
    gems: int


@router.get("/league", response_model=LeagueOut)
def get_league(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _get_learner(db, current_user.id)
    b = league_service.board(db, learner)
    lw = league_service.last_week(db, learner)
    db.commit()           # membership may have been created
    return LeagueOut(
        week=b.week, starts_on=b.starts_on.isoformat(), ends_on=b.ends_on.isoformat(),
        tier=b.tier, tier_name=b.tier_name, tiers=league_service.TIERS, group_no=b.group_no,
        group_size=league_service.GROUP_SIZE, promote_top=b.promote_top, relegate_bottom=b.relegate_bottom,
        rewards=[{"up_to_rank": upto, "xp": xp} for upto, xp in league_service.REWARDS],
        entries=[LeagueEntry(**e) for e in b.entries],
        me=LeagueMe(rank=b.me.rank, xp=b.me.xp, participants=b.me.participants),
        last_week=LastWeekOut(**lw.__dict__),
    )


@router.post("/league/claim", response_model=LeagueClaimOut)
def claim_league(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _get_learner(db, current_user.id)
    try:
        got = league_service.claim_last_week(db, learner)
    except league_service.LeagueClaimError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return LeagueClaimOut(xp_awarded=got["xp"], gems_awarded=got["gems"], total_xp=learner.total_xp or 0, gems=learner.gems or 0)
