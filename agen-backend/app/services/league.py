"""
G3 · Giải đấu tuần — a Mon–Sun leaderboard of XP earned, computed from
LearningEvents (no new rows while the week runs). Last week's result is
derived the same way, so a learner can claim one reward per week.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.timeutil import LEARNER_TZ, local_today
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.services.engagement import week_key

BOARD_SIZE = 30
# rank → XP reward for last week's standing
REWARDS: list[tuple[int, int]] = [(1, 100), (3, 70), (10, 40)]
TIERS: list[tuple[int, str]] = [(1, "Vàng"), (3, "Bạc"), (10, "Đồng")]


def _utc_naive(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def week_bounds(today: date) -> tuple[date, date]:
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def reward_for(rank: int | None) -> int:
    if not rank:
        return 0
    for upto, xp in REWARDS:
        if rank <= upto:
            return xp
    return 0


def tier_for(rank: int | None) -> str | None:
    if not rank:
        return None
    for upto, name in TIERS:
        if rank <= upto:
            return name
    return None


def weekly_xp(db: Session, monday: date, sunday: date) -> list[tuple[str, int]]:
    """(learner_id, xp) for everyone who earned XP in the week, best first."""
    rows = (
        db.query(LearningEvent.learner_id, func.coalesce(func.sum(LearningEvent.xp_earned), 0))
        .filter(
            LearningEvent.recorded_at >= _utc_naive(monday),
            LearningEvent.recorded_at < _utc_naive(sunday + timedelta(days=1)),
            LearningEvent.xp_earned > 0,
        )
        .group_by(LearningEvent.learner_id)
        .all()
    )
    return sorted(((lid, int(xp)) for lid, xp in rows if xp), key=lambda r: -r[1])


@dataclass
class Standing:
    rank: int | None
    xp: int
    participants: int


@dataclass
class Board:
    week: str
    starts_on: date
    ends_on: date
    entries: list[dict] = field(default_factory=list)
    me: Standing = field(default_factory=lambda: Standing(None, 0, 0))


def _rank_of(ranking: list[tuple[str, int]], learner_id: str) -> tuple[int | None, int]:
    for i, (lid, xp) in enumerate(ranking, start=1):
        if lid == learner_id:
            return i, xp
    return None, 0


def board(db: Session, learner: LearnerProfile, today: date | None = None) -> Board:
    today = today or local_today()
    monday, sunday = week_bounds(today)
    ranking = weekly_xp(db, monday, sunday)
    top = ranking[:BOARD_SIZE]
    names = {
        lp.id: lp
        for lp in db.query(LearnerProfile).filter(LearnerProfile.id.in_([lid for lid, _ in top] or [""])).all()
    }
    entries = []
    for i, (lid, xp) in enumerate(top, start=1):
        lp = names.get(lid)
        entries.append({
            "rank": i,
            "learner_id": lid,
            "display_name": (lp.display_name if lp else "Học viên") or "Học viên",
            "level": (lp.overall_level if lp else None) or "A1",
            "xp": xp,
            "is_me": lid == learner.id,
            "tier": tier_for(i),
        })
    rank, xp = _rank_of(ranking, learner.id)
    return Board(
        week=week_key(today), starts_on=monday, ends_on=sunday, entries=entries,
        me=Standing(rank=rank, xp=xp, participants=len(ranking)),
    )


@dataclass
class LastWeek:
    week: str
    rank: int | None
    xp: int
    participants: int
    reward_xp: int
    tier: str | None
    claimed: bool
    claimable: bool


def last_week(db: Session, learner: LearnerProfile, today: date | None = None) -> LastWeek:
    today = today or local_today()
    monday, sunday = week_bounds(today - timedelta(days=7))
    ranking = weekly_xp(db, monday, sunday)
    rank, xp = _rank_of(ranking, learner.id)
    key = week_key(monday)
    reward = reward_for(rank)
    claimed = learner.league_reward_claimed_week == key
    return LastWeek(
        week=key, rank=rank, xp=xp, participants=len(ranking), reward_xp=reward,
        tier=tier_for(rank), claimed=claimed, claimable=reward > 0 and not claimed,
    )


class LeagueClaimError(ValueError):
    pass


def claim_last_week(db: Session, learner: LearnerProfile, today: date | None = None) -> int:
    result = last_week(db, learner, today)
    if result.claimed:
        raise LeagueClaimError("Bạn đã nhận thưởng giải đấu tuần trước rồi.")
    if result.reward_xp <= 0:
        raise LeagueClaimError("Tuần trước bạn chưa vào top 10.")
    learner.league_reward_claimed_week = result.week
    learner.total_xp = (learner.total_xp or 0) + result.reward_xp
    return result.reward_xp
