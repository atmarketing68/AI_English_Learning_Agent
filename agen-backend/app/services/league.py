"""
G3/G4 · Giải đấu tuần — Mon–Sun XP leaderboard in small groups with tiers.

Every learner who opens the league (or earns XP) is placed once per ISO week
into a group of up to 30 within their tier (Đồng → Bạc → Vàng → Kim cương).
At the start of a new week last week's standing decides the tier: the top 7
of a group move up, the bottom 5 (of a group with at least 10 members) move
down, and someone who sat out the whole week drops one tier.

Ranking is computed from LearningEvents; only the membership is stored.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.timeutil import LEARNER_TZ, local_today
from app.models.league_membership import LeagueMembership
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.services.engagement import week_key

TIERS = ["Đồng", "Bạc", "Vàng", "Kim cương"]
GROUP_SIZE = 30
PROMOTE_TOP = 7
RELEGATE_BOTTOM = 5
MIN_GROUP_FOR_RELEGATION = 10
BOARD_SIZE = GROUP_SIZE
# rank → XP reward for last week's standing
REWARDS: list[tuple[int, int]] = [(1, 100), (3, 70), (10, 40)]


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


def tier_name(tier: int) -> str:
    return TIERS[max(0, min(tier, len(TIERS) - 1))]


def weekly_xp(db: Session, monday: date, sunday: date, learner_ids: list[str] | None = None) -> dict[str, int]:
    """learner_id → XP earned in the week (only learners with XP > 0)."""
    query = (
        db.query(LearningEvent.learner_id, func.coalesce(func.sum(LearningEvent.xp_earned), 0))
        .filter(
            LearningEvent.recorded_at >= _utc_naive(monday),
            LearningEvent.recorded_at < _utc_naive(sunday + timedelta(days=1)),
            LearningEvent.xp_earned > 0,
        )
    )
    if learner_ids is not None:
        if not learner_ids:
            return {}
        query = query.filter(LearningEvent.learner_id.in_(learner_ids))
    return {lid: int(xp) for lid, xp in query.group_by(LearningEvent.learner_id).all() if xp}


# ── Membership ───────────────────────────────────────────────────────────────
def _members(db: Session, week: str, tier: int, group_no: int) -> list[LeagueMembership]:
    return (
        db.query(LeagueMembership)
        .filter(LeagueMembership.week == week, LeagueMembership.tier == tier, LeagueMembership.group_no == group_no)
        .order_by(LeagueMembership.created_at)
        .all()
    )


def group_ranking(db: Session, week_monday: date, members: list[LeagueMembership]) -> list[tuple[str, int]]:
    """(learner_id, xp) for a group, best first; members without XP come last in join order."""
    ids = [m.learner_id for m in members]
    xp = weekly_xp(db, week_monday, week_monday + timedelta(days=6), ids)
    ranked = sorted(ids, key=lambda lid: (-xp.get(lid, 0), ids.index(lid)))
    return [(lid, xp.get(lid, 0)) for lid in ranked]


def _rank_of(ranking: list[tuple[str, int]], learner_id: str) -> tuple[int | None, int]:
    for i, (lid, xp) in enumerate(ranking, start=1):
        if lid == learner_id:
            return i, xp
    return None, 0


def _next_tier(db: Session, learner: LearnerProfile, prev_week_monday: date) -> tuple[int, str]:
    """Tier for the new week from last week's membership. Returns (tier, reason)."""
    last = (
        db.query(LeagueMembership)
        .filter(LeagueMembership.learner_id == learner.id, LeagueMembership.week == week_key(prev_week_monday))
        .first()
    )
    if not last:
        return 0, "new"
    ranking = group_ranking(db, prev_week_monday, _members(db, last.week, last.tier, last.group_no))
    rank, xp = _rank_of(ranking, learner.id)
    size = len(ranking)
    if xp <= 0:
        return (max(0, last.tier - 1), "inactive") if last.tier > 0 else (0, "stay")
    if rank is not None and rank <= PROMOTE_TOP and last.tier < len(TIERS) - 1:
        return last.tier + 1, "promoted"
    if size >= MIN_GROUP_FOR_RELEGATION and rank is not None and rank > size - RELEGATE_BOTTOM and last.tier > 0:
        return last.tier - 1, "relegated"
    return last.tier, "stay"


def ensure_membership(db: Session, learner: LearnerProfile, today: date | None = None) -> LeagueMembership:
    """Place the learner in this week's league (idempotent). Caller commits."""
    today = today or local_today()
    week = week_key(today)
    existing = db.query(LeagueMembership).filter(LeagueMembership.learner_id == learner.id, LeagueMembership.week == week).first()
    if existing:
        return existing
    monday, _ = week_bounds(today)
    tier, _reason = _next_tier(db, learner, monday - timedelta(days=7))
    counts = dict(
        db.query(LeagueMembership.group_no, func.count(LeagueMembership.id))
        .filter(LeagueMembership.week == week, LeagueMembership.tier == tier)
        .group_by(LeagueMembership.group_no)
        .all()
    )
    group_no = next((g for g in sorted(counts) if counts[g] < GROUP_SIZE), (max(counts) + 1) if counts else 1)
    membership = LeagueMembership(learner_id=learner.id, week=week, tier=tier, group_no=group_no)
    db.add(membership)
    db.flush()
    return membership


# ── Views ────────────────────────────────────────────────────────────────────
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
    tier: int
    tier_name: str
    group_no: int
    entries: list[dict] = field(default_factory=list)
    me: Standing = field(default_factory=lambda: Standing(None, 0, 0))
    promote_top: int = PROMOTE_TOP
    relegate_bottom: int = RELEGATE_BOTTOM


def board(db: Session, learner: LearnerProfile, today: date | None = None) -> Board:
    from app.services.shop import avatar_of

    today = today or local_today()
    monday, sunday = week_bounds(today)
    membership = ensure_membership(db, learner, today)
    members = _members(db, membership.week, membership.tier, membership.group_no)
    ranking = group_ranking(db, monday, members)
    profiles = {lp.id: lp for lp in db.query(LearnerProfile).filter(LearnerProfile.id.in_([lid for lid, _ in ranking] or [""])).all()}
    size = len(ranking)
    entries = []
    for i, (lid, xp) in enumerate(ranking, start=1):
        lp = profiles.get(lid)
        zone = "promote" if i <= PROMOTE_TOP else ("relegate" if size >= MIN_GROUP_FOR_RELEGATION and i > size - RELEGATE_BOTTOM else "stay")
        entries.append({
            "rank": i,
            "learner_id": lid,
            "display_name": (lp.display_name if lp else "Học viên") or "Học viên",
            "level": (lp.overall_level if lp else None) or "A1",
            "avatar": avatar_of(lp) if lp else {},
            "xp": xp,
            "is_me": lid == learner.id,
            "zone": zone,
        })
    rank, xp = _rank_of(ranking, learner.id)
    return Board(
        week=membership.week, starts_on=monday, ends_on=sunday,
        tier=membership.tier, tier_name=tier_name(membership.tier), group_no=membership.group_no,
        entries=entries, me=Standing(rank=rank, xp=xp, participants=size),
    )


@dataclass
class LastWeek:
    week: str
    rank: int | None
    xp: int
    participants: int
    reward_xp: int
    reward_gems: int
    tier_name: str | None
    movement: str            # new | promoted | relegated | stay | inactive
    claimed: bool
    claimable: bool


def last_week(db: Session, learner: LearnerProfile, today: date | None = None) -> LastWeek:
    from app.services.shop import gems_for_league_rank

    today = today or local_today()
    prev_monday, _ = week_bounds(today - timedelta(days=7))
    key = week_key(prev_monday)
    last = db.query(LeagueMembership).filter(LeagueMembership.learner_id == learner.id, LeagueMembership.week == key).first()
    if not last:
        return LastWeek(key, None, 0, 0, 0, 0, None, "new", False, False)
    ranking = group_ranking(db, prev_monday, _members(db, key, last.tier, last.group_no))
    rank, xp = _rank_of(ranking, learner.id)
    reward = reward_for(rank) if xp > 0 else 0
    _, movement = _next_tier(db, learner, prev_monday)
    claimed = learner.league_reward_claimed_week == key
    return LastWeek(
        week=key, rank=rank if xp > 0 else None, xp=xp, participants=len(ranking),
        reward_xp=reward, reward_gems=gems_for_league_rank(rank) if xp > 0 else 0,
        tier_name=tier_name(last.tier), movement=movement, claimed=claimed, claimable=reward > 0 and not claimed,
    )


class LeagueClaimError(ValueError):
    pass


def claim_last_week(db: Session, learner: LearnerProfile, today: date | None = None) -> dict:
    from app.services.shop import award_gems

    result = last_week(db, learner, today)
    if result.claimed:
        raise LeagueClaimError("Bạn đã nhận thưởng giải đấu tuần trước rồi.")
    if result.reward_xp <= 0:
        raise LeagueClaimError("Tuần trước bạn chưa vào top 10 của bảng.")
    learner.league_reward_claimed_week = result.week
    learner.total_xp = (learner.total_xp or 0) + result.reward_xp
    gems = award_gems(learner, result.reward_gems)
    return {"xp": result.reward_xp, "gems": gems}
