"""Notification service — create in-app notifications for learners.

Kept deterministic and side-effect-light: callers pass an already-open session
and are responsible for committing (so notifications join the caller's transaction).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    learner_id: str,
    *,
    type: str,
    title: str,
    body: str | None = None,
    icon: str | None = None,
) -> Notification:
    """Add a notification row (caller commits)."""
    n = Notification(
        learner_id=learner_id,
        type=type,
        title=title,
        body=body,
        icon=icon,
    )
    db.add(n)
    return n


def notify_achievements(db: Session, learner_id: str, earned: list[dict]) -> int:
    """Create a notification per newly-earned achievement. Returns count created."""
    for ach in earned:
        create_notification(
            db,
            learner_id,
            type="achievement",
            title=f"Huy hiệu mới: {ach.get('name', 'Thành tựu')}",
            body=ach.get("description"),
            icon=ach.get("icon", "🏆"),
        )
    return len(earned)


def notify_streak(db: Session, learner_id: str, streak_days: int) -> Notification | None:
    """Create a milestone streak notification (only at meaningful milestones)."""
    milestones = {3, 7, 14, 30, 60, 100}
    if streak_days not in milestones:
        return None
    return create_notification(
        db,
        learner_id,
        type="streak",
        title=f"🔥 Chuỗi {streak_days} ngày!",
        body=f"Bạn đã học {streak_days} ngày liên tiếp. Tiếp tục giữ vững nhé!",
        icon="🔥",
    )
