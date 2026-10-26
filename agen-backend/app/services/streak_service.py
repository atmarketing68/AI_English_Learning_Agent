"""
AGEN — Streak & Daily Challenge Service

Logic:
- Streak tăng 1 khi learner học ít nhất 1 lần trong ngày (so sánh với last_active_at)
- Streak reset về 0 nếu bỏ qua 1 ngày (gap > 1 ngày)
- longest_streak cập nhật khi current_streak vượt qua
- DailyChallenge.current_value tăng khi loại activity khớp với challenge skill
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.learner_profile import LearnerProfile
from app.models.achievement import DailyChallenge


def update_streak(learner: LearnerProfile, db: Session) -> dict:
    """
    Recalculate current_streak and longest_streak based on today vs last_active_at.

    Rules:
    - Same day as last_active_at  → streak unchanged (already counted today)
    - Yesterday as last_active_at → streak += 1 (consecutive day)
    - Gap > 1 day                 → streak reset to 1 (new streak starts today)
    - Never active before         → streak = 1

    Returns dict with updated streak values.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    last_active = learner.last_active_at
    # Make last_active timezone-aware if stored as naive UTC
    if last_active is not None and last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)

    if last_active is None:
        # First ever activity
        learner.current_streak = 1
    else:
        last_date = last_active.date()
        delta = (today - last_date).days

        if delta == 0:
            # Already counted today — no change
            pass
        elif delta == 1:
            # Consecutive day — extend streak
            learner.current_streak = (learner.current_streak or 0) + 1
        else:
            # Gap detected — reset streak
            learner.current_streak = 1

    # Update longest streak
    if (learner.current_streak or 0) > (learner.longest_streak or 0):
        learner.longest_streak = learner.current_streak

    # Always update last_active_at to now
    learner.last_active_at = now

    return {
        "current_streak": learner.current_streak,
        "longest_streak": learner.longest_streak,
    }


def update_daily_challenge_progress(learner: LearnerProfile, activity_skill: str, db: Session) -> bool:
    """
    Increment DailyChallenge.current_value if today's challenge skill matches activity_skill.
    Marks challenge as completed if current_value >= target_value.

    Returns True if challenge was completed (newly), False otherwise.
    """
    today = datetime.now(timezone.utc).date().isoformat()

    challenge = db.query(DailyChallenge).filter(
        DailyChallenge.learner_id == learner.id,
        DailyChallenge.date == today,
    ).first()

    if not challenge or challenge.is_completed:
        return False

    # Check if this activity counts toward the challenge
    # Speaking activities may be recorded as "speaking", writing as "writing", etc.
    # Vocab/grammar/reading/listening are matched directly
    skill_matches = (challenge.skill == activity_skill)

    if not skill_matches:
        return False

    challenge.current_value = (challenge.current_value or 0) + 1

    newly_completed = False
    if challenge.current_value >= (challenge.target_value or 1):
        challenge.is_completed = True
        challenge.completed_at = datetime.now(timezone.utc)
        # Award XP for completing the challenge
        learner.total_xp = (learner.total_xp or 0) + (challenge.xp_reward or 0)
        newly_completed = True

    return newly_completed


def record_activity(learner: LearnerProfile, activity_skill: str, db: Session) -> dict:
    """
    Convenience function called after any learning completion event.
    Updates streak + daily challenge in one call.

    Returns summary dict for API response augmentation.
    """
    streak_info = update_streak(learner, db)
    challenge_completed = update_daily_challenge_progress(learner, activity_skill, db)

    return {
        "streak": streak_info,
        "daily_challenge_completed": challenge_completed,
    }
