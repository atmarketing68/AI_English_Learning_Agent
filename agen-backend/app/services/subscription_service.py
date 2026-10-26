"""Subscription plan logic + free-tier gating.

Free users may complete up to FREE_DAILY_LESSON_LIMIT lessons per day (default 3);
premium users are unlimited. No real payment gateway — upgrade is recorded
directly. A webhook-driven integration can later drive plan/status changes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.learning_event import LearningEvent
from app.models.learner_profile import LearnerProfile
from app.models.subscription import PAID_PLANS, PLAN_FAMILY, PLAN_FREE, PLAN_PREMIUM, PLAN_TEAM, Subscription


def _free_daily_limit() -> int:
    """Free-tier daily lesson allowance, read from config (0 = unlimited)."""
    return settings.FREE_DAILY_LESSON_LIMIT


def get_or_create_subscription(db: Session, user_id: str) -> Subscription:
    """Return the user's subscription, creating a default free one if absent."""
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub is None:
        sub = Subscription(user_id=user_id, plan=PLAN_FREE, status="active")
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


def _active_paid(sub: Subscription) -> bool:
    if sub.plan not in PAID_PLANS or sub.status != "active":
        return False
    if sub.current_period_end is not None:
        end = sub.current_period_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if end < datetime.now(timezone.utc):
            return False
    return True


def family_parent_subscription(db: Session, user_id: str) -> Subscription | None:
    """G5 · The active family subscription of a parent linked to this learner, if any."""
    from app.models.parent import ParentChildLink, ParentProfile

    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        return None
    rows = (
        db.query(Subscription, ParentProfile.id)
        .join(ParentProfile, ParentProfile.user_id == Subscription.user_id)
        .join(ParentChildLink, ParentChildLink.parent_id == ParentProfile.id)
        .filter(ParentChildLink.learner_id == learner.id, Subscription.plan == PLAN_FAMILY)
        .all()
    )
    for sub, parent_id in rows:
        if _active_paid(sub) and learner.id in covered_children(db, parent_id):
            return sub
    return None


def covered_children(db: Session, parent_id: str) -> list[str]:
    """G6 · The first FAMILY_MAX_CHILDREN linked learners (by link date) are the ones a family plan covers."""
    from app.models.parent import ParentChildLink
    from app.services.payments import FAMILY_MAX_CHILDREN

    links = (
        db.query(ParentChildLink.learner_id)
        .filter(ParentChildLink.parent_id == parent_id)
        .order_by(ParentChildLink.created_at, ParentChildLink.id)
        .limit(FAMILY_MAX_CHILDREN)
        .all()
    )
    return [lid for (lid,) in links]


def team_covered_learners(db: Session, owner_user_id: str) -> list[str]:
    """G7 · Learner ids a team plan covers: the owner's group members in join order, up to `seats`."""
    from app.models.group import Group, GroupMember

    sub = get_or_create_subscription(db, owner_user_id)
    if sub.plan != PLAN_TEAM or not _active_paid(sub):
        return []
    rows = (
        db.query(GroupMember.learner_id)
        .join(Group, Group.id == GroupMember.group_id)
        .filter(Group.owner_user_id == owner_user_id)
        .order_by(GroupMember.joined_at, GroupMember.id)
        .all()
    )
    seen: list[str] = []
    for (lid,) in rows:
        if lid not in seen:
            seen.append(lid)
        if len(seen) >= (sub.seats or 0):
            break
    return seen


def team_owner_subscription(db: Session, user_id: str) -> Subscription | None:
    """G7 · An active team plan of a group owner whose seats include this learner."""
    from app.models.group import Group, GroupMember

    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        return None
    owners = {
        oid for (oid,) in db.query(Group.owner_user_id).join(GroupMember, GroupMember.group_id == Group.id)
        .filter(GroupMember.learner_id == learner.id).all()
    }
    for owner_id in owners:
        if learner.id in team_covered_learners(db, owner_id):
            return get_or_create_subscription(db, owner_id)
    return None


def premium_source(db: Session, user_id: str) -> str | None:
    """'own' (paid/trial on this account), 'family' (parent's family plan), 'team' (group owner's plan) or None."""
    sub = get_or_create_subscription(db, user_id)
    if _active_paid(sub):
        return "own"
    if family_parent_subscription(db, user_id) is not None:
        return "family"
    if team_owner_subscription(db, user_id) is not None:
        return "team"
    return None


def is_premium(db: Session, user_id: str) -> bool:
    """True if the user has an active paid plan, or is a child covered by a parent's family plan."""
    return premium_source(db, user_id) is not None


def _lessons_today(db: Session, learner_id: str) -> int:
    from app.core.timeutil import local_day_start_utc
    start = local_day_start_utc()
    return (
        db.query(func.count(LearningEvent.id))
        .filter(
            LearningEvent.learner_id == learner_id,
            LearningEvent.event_type == "lesson_completed",
            LearningEvent.recorded_at >= start,
        )
        .scalar()
    ) or 0


def check_lesson_quota(db: Session, user_id: str, learner: LearnerProfile) -> dict:
    """Return the learner's daily lesson quota status.

    { plan, is_premium, used_today, limit (None if unlimited), remaining (None if unlimited),
      allowed (bool) }
    """
    premium = is_premium(db, user_id)
    used = _lessons_today(db, learner.id)
    limit = _free_daily_limit()
    # Premium, or a configured limit of 0, means unlimited.
    if premium or limit <= 0:
        return {
            "plan": PLAN_PREMIUM if premium else PLAN_FREE, "is_premium": premium,
            "used_today": used, "limit": None, "remaining": None, "allowed": True,
        }
    remaining = max(limit - used, 0)
    return {
        "plan": PLAN_FREE, "is_premium": False,
        "used_today": used, "limit": limit,
        "remaining": remaining, "allowed": remaining > 0,
    }


def upgrade_to_premium(db: Session, user_id: str, months: int = 1, plan: str = PLAN_PREMIUM, seats: int = 1) -> Subscription:
    """Record a paid upgrade (pilot: no real charge).

    Sets plan=premium (or family), active, and extends current_period_end by `months`.
    """
    if plan not in PAID_PLANS:
        raise ValueError("unknown plan")
    sub = get_or_create_subscription(db, user_id)
    now = datetime.now(timezone.utc)
    base = now
    if sub.current_period_end is not None:
        end = sub.current_period_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        base = max(now, end)
    sub.plan = plan
    sub.seats = max(1, int(seats)) if plan == PLAN_TEAM else 1
    sub.status = "active"
    sub.current_period_end = (base + timedelta(days=30 * months)).replace(tzinfo=None)
    sub.provider = "pilot_manual"
    db.commit()
    db.refresh(sub)
    return sub


def cancel_subscription(db: Session, user_id: str) -> Subscription:
    """Cancel premium — reverts to free at period end (pilot: immediate free)."""
    sub = get_or_create_subscription(db, user_id)
    sub.plan = PLAN_FREE
    sub.status = "active"
    sub.current_period_end = None
    db.commit()
    db.refresh(sub)
    return sub
