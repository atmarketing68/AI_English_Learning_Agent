"""
G6 · Thử thách bạn bè — add a friend by their code and clear a weekly duo quest.

Each pair shares one quest per ISO week: together earn DUO_GOAL_XP, with each
side contributing at least DUO_MIN_EACH (so one learner cannot carry the other).
When it is done, each side claims its own reward once.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.timeutil import local_today
from app.models.friendship import Friendship
from app.models.learner_profile import LearnerProfile
from app.services.engagement import week_key
from app.services.league import week_bounds, weekly_xp
from app.services.streak_service import effective_streak

DUO_GOAL_XP = 200
DUO_MIN_EACH = 50
DUO_REWARD_XP = 30
DUO_REWARD_GEMS = 10
MAX_FRIENDS = 10


class FriendError(ValueError):
    pass


def _pair(x: str, y: str) -> tuple[str, str]:
    return (x, y) if x < y else (y, x)


def _rows(db: Session, learner_id: str) -> list[Friendship]:
    return (
        db.query(Friendship)
        .filter(or_(Friendship.a_id == learner_id, Friendship.b_id == learner_id))
        .order_by(Friendship.created_at)
        .all()
    )


def add_friend(db: Session, learner: LearnerProfile, code: str) -> Friendship:
    code = (code or "").strip().upper()
    friend = db.query(LearnerProfile).filter(LearnerProfile.invite_code == code).first()
    if not friend:
        raise FriendError("Mã bạn bè không đúng.")
    if friend.id == learner.id:
        raise FriendError("Đây là mã của chính bạn.")
    a, b = _pair(learner.id, friend.id)
    if db.query(Friendship).filter(Friendship.a_id == a, Friendship.b_id == b).first():
        raise FriendError("Hai bạn đã là bạn học rồi.")
    if len(_rows(db, learner.id)) >= MAX_FRIENDS:
        raise FriendError(f"Bạn chỉ thêm được tối đa {MAX_FRIENDS} bạn học.")
    row = Friendship(a_id=a, b_id=b)
    db.add(row)
    db.flush()
    return row


def remove_friend(db: Session, learner: LearnerProfile, friend_id: str) -> bool:
    a, b = _pair(learner.id, friend_id)
    row = db.query(Friendship).filter(Friendship.a_id == a, Friendship.b_id == b).first()
    if not row:
        return False
    db.delete(row)
    db.flush()
    return True


@dataclass
class DuoQuest:
    week: str
    my_xp: int
    friend_xp: int
    goal: int
    min_each: int
    done: bool
    claimed: bool
    claimable: bool
    reward_xp: int = DUO_REWARD_XP
    reward_gems: int = DUO_REWARD_GEMS


@dataclass
class FriendView:
    learner_id: str
    display_name: str
    level: str
    avatar: dict
    streak: int
    studied_today: bool
    quest: DuoQuest


def _quest(row: Friendship, me: str, xp: dict[str, int], week: str) -> DuoQuest:
    other = row.b_id if row.a_id == me else row.a_id
    mine, theirs = xp.get(me, 0), xp.get(other, 0)
    done = mine + theirs >= DUO_GOAL_XP and mine >= DUO_MIN_EACH and theirs >= DUO_MIN_EACH
    claimed = (row.a_claimed_week if row.a_id == me else row.b_claimed_week) == week
    return DuoQuest(week=week, my_xp=mine, friend_xp=theirs, goal=DUO_GOAL_XP, min_each=DUO_MIN_EACH,
                    done=done, claimed=claimed, claimable=done and not claimed)


def list_friends(db: Session, learner: LearnerProfile, today: date | None = None) -> list[FriendView]:
    from app.core.timeutil import local_day_start_utc
    from app.models.learning_event import LearningEvent
    from app.services.shop import avatar_of

    today = today or local_today()
    monday, sunday = week_bounds(today)
    week = week_key(today)
    rows = _rows(db, learner.id)
    ids = {learner.id} | {r.a_id for r in rows} | {r.b_id for r in rows}
    xp = weekly_xp(db, monday, sunday, list(ids))
    profiles = {p.id: p for p in db.query(LearnerProfile).filter(LearnerProfile.id.in_(list(ids))).all()}
    day_start = local_day_start_utc()
    active_today = {
        lid for (lid,) in db.query(LearningEvent.learner_id)
        .filter(LearningEvent.learner_id.in_(list(ids)), LearningEvent.recorded_at >= day_start)
        .distinct().all()
    }
    out = []
    for row in rows:
        other = row.b_id if row.a_id == learner.id else row.a_id
        p = profiles.get(other)
        if not p:
            continue
        out.append(FriendView(
            learner_id=other, display_name=p.display_name or "Bạn học", level=p.overall_level or "A1",
            avatar=avatar_of(p), streak=effective_streak(p), studied_today=other in active_today,
            quest=_quest(row, learner.id, xp, week),
        ))
    return out


def claim(db: Session, learner: LearnerProfile, friend_id: str, today: date | None = None) -> dict:
    from app.services.shop import award_gems

    today = today or local_today()
    a, b = _pair(learner.id, friend_id)
    row = db.query(Friendship).filter(Friendship.a_id == a, Friendship.b_id == b).first()
    if not row:
        raise FriendError("Hai bạn chưa là bạn học.")
    monday, sunday = week_bounds(today)
    week = week_key(today)
    xp = weekly_xp(db, monday, sunday, [learner.id, friend_id])
    quest = _quest(row, learner.id, xp, week)
    if quest.claimed:
        raise FriendError("Bạn đã nhận thưởng thử thách tuần này rồi.")
    if not quest.done:
        raise FriendError(f"Chưa xong: cần tổng {DUO_GOAL_XP} XP và mỗi người ít nhất {DUO_MIN_EACH} XP trong tuần.")
    if row.a_id == learner.id:
        row.a_claimed_week = week
    else:
        row.b_claimed_week = week
    learner.total_xp = (learner.total_xp or 0) + DUO_REWARD_XP
    gems = award_gems(learner, DUO_REWARD_GEMS)
    db.flush()
    return {"xp": DUO_REWARD_XP, "gems": gems, "total_xp": learner.total_xp, "gems_total": learner.gems}


def next_week_starts(today: date | None = None) -> date:
    today = today or local_today()
    return week_bounds(today)[1] + timedelta(days=1)


@dataclass
class LeaderRow:
    learner_id: str
    display_name: str
    avatar: dict
    level: str
    weekly_xp: int
    streak: int
    is_me: bool
    rank: int = 0


def leaderboard(db: Session, learner: LearnerProfile, today: date | None = None) -> list[LeaderRow]:
    """G7 · Me and my friends ranked by this week's XP (ties: longer streak first)."""
    from app.services.shop import avatar_of

    today = today or local_today()
    monday, sunday = week_bounds(today)
    rows = _rows(db, learner.id)
    ids = {learner.id} | {r.a_id for r in rows} | {r.b_id for r in rows}
    xp = weekly_xp(db, monday, sunday, list(ids))
    profiles = db.query(LearnerProfile).filter(LearnerProfile.id.in_(list(ids))).all()
    out = [
        LeaderRow(learner_id=p.id, display_name=p.display_name or "Bạn học", avatar=avatar_of(p), level=p.overall_level or "A1",
                  weekly_xp=xp.get(p.id, 0), streak=effective_streak(p), is_me=p.id == learner.id)
        for p in profiles
    ]
    out.sort(key=lambda r: (-r.weekly_xp, -r.streak, r.display_name))
    for i, r in enumerate(out, start=1):
        r.rank = i
    return out
