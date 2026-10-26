"""
Daily quests, weekly goal and streak freezes (G1 · giữ thói quen học).

Quest progress and study days are derived from LearningEvents, so every
activity that already logs an event (lessons, reviews, speaking, writing)
counts without extra hooks. Rewards are claimed explicitly by the learner.
"""
import zlib
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.timeutil import LEARNER_TZ, local_date, local_today
from app.models.daily_quest import DailyQuest
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.review_item import ReviewItem
from app.services.streak_service import MAX_STREAK_FREEZES

# Events that mean "the learner studied today".
STUDY_EVENTS = (
    "exercise_answered", "lesson_completed", "review_answered",
    "writing_submitted", "pronunciation_practice", "roleplay_completed",
)
SPEAKING_EVENTS = ("pronunciation_practice", "roleplay_completed")

WEEKLY_GOAL_OPTIONS = (3, 5, 7)
WEEKLY_REWARD_XP = 50
PERFECT_SCORE = 90

# code → (title, metric, default target, xp reward, icon)
QUEST_CATALOG: dict[str, dict] = {
    "lesson":   {"title": "Hoàn thành {n} bài học",            "metric": "lessons",  "target": 1,  "xp": 15, "icon": "book"},
    "review":   {"title": "Ôn tập {n} từ hoặc lỗi sai",        "metric": "reviews",  "target": 10, "xp": 15, "icon": "brain"},
    "correct":  {"title": "Trả lời đúng {n} câu",              "metric": "correct",  "target": 15, "xp": 15, "icon": "target"},
    "xp":       {"title": "Kiếm {n} XP",                        "metric": "xp",       "target": 50, "xp": 20, "icon": "star"},
    "perfect":  {"title": "Đạt từ 90% trở lên trong {n} bài",   "metric": "perfect",  "target": 1,  "xp": 20, "icon": "trophy"},
    "speaking": {"title": "Luyện nói {n} lần",                  "metric": "speaking", "target": 1,  "xp": 20, "icon": "mic"},
}
ROTATING_QUESTS = ("xp", "perfect", "speaking")


def _utc_naive(d: date) -> datetime:
    """Local midnight of `d` as a naive UTC datetime (how events are stored)."""
    return datetime.combine(d, time.min, tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def _now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def week_key(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


# ── Metrics ──────────────────────────────────────────────────────────────────
def day_metrics(db: Session, learner_id: str, day: date) -> dict[str, int]:
    events = (
        db.query(LearningEvent.event_type, LearningEvent.correct, LearningEvent.score, LearningEvent.xp_earned)
        .filter(
            LearningEvent.learner_id == learner_id,
            LearningEvent.recorded_at >= _utc_naive(day),
            LearningEvent.recorded_at < _utc_naive(day + timedelta(days=1)),
        )
        .all()
    )
    m = {"lessons": 0, "perfect": 0, "reviews": 0, "correct": 0, "xp": 0, "speaking": 0}
    for event_type, correct, score, xp in events:
        m["xp"] += xp or 0
        if event_type == "lesson_completed":
            m["lessons"] += 1
            if (score or 0) >= PERFECT_SCORE:
                m["perfect"] += 1
        elif event_type == "review_answered":
            m["reviews"] += 1
        elif event_type in SPEAKING_EVENTS:
            m["speaking"] += 1
        if event_type in ("exercise_answered", "review_answered") and correct:
            m["correct"] += 1
    return m


def study_days(db: Session, learner_id: str, start: date, end: date) -> set[date]:
    """Local dates in [start, end] with at least one study event."""
    rows = (
        db.query(LearningEvent.recorded_at)
        .filter(
            LearningEvent.learner_id == learner_id,
            LearningEvent.event_type.in_(STUDY_EVENTS),
            LearningEvent.recorded_at >= _utc_naive(start),
            LearningEvent.recorded_at < _utc_naive(end + timedelta(days=1)),
        )
        .all()
    )
    return {local_date(r[0]) for r in rows}


# ── Daily quests ─────────────────────────────────────────────────────────────
def _pick_quests(db: Session, learner: LearnerProfile, day: date) -> list[tuple[str, int]]:
    """Three (code, target) pairs: a lesson, a review/accuracy quest and a rotating one."""
    notebook = db.query(func.count(ReviewItem.id)).filter(ReviewItem.learner_id == learner.id).scalar() or 0
    if notebook:
        second = ("review", min(QUEST_CATALOG["review"]["target"], max(3, notebook)))
    else:
        second = ("correct", QUEST_CATALOG["correct"]["target"])
    # Deterministic per learner and day, so every learner gets variety.
    rot = ROTATING_QUESTS[(day.toordinal() + zlib.crc32(learner.id.encode())) % len(ROTATING_QUESTS)]
    return [("lesson", QUEST_CATALOG["lesson"]["target"]), second, (rot, QUEST_CATALOG[rot]["target"])]


def todays_quests(db: Session, learner: LearnerProfile, day: date | None = None) -> list[DailyQuest]:
    day = day or local_today()
    key = day.isoformat()
    quests = (
        db.query(DailyQuest)
        .filter(DailyQuest.learner_id == learner.id, DailyQuest.date == key)
        .order_by(DailyQuest.slot)
        .all()
    )
    if quests:
        return quests
    for slot, (code, target) in enumerate(_pick_quests(db, learner, day)):
        db.add(DailyQuest(
            learner_id=learner.id, date=key, slot=slot, code=code,
            target=target, xp_reward=QUEST_CATALOG[code]["xp"],
        ))
    try:
        db.commit()
    except IntegrityError:
        # A parallel request created today's quests first.
        db.rollback()
    return (
        db.query(DailyQuest)
        .filter(DailyQuest.learner_id == learner.id, DailyQuest.date == key)
        .order_by(DailyQuest.slot)
        .all()
    )


def quest_view(quest: DailyQuest, metrics: dict[str, int]) -> dict:
    spec = QUEST_CATALOG[quest.code]
    progress = min(metrics.get(spec["metric"], 0), quest.target)
    return {
        "id": quest.id,
        "code": quest.code,
        "title": spec["title"].format(n=quest.target),
        "icon": spec["icon"],
        "progress": progress,
        "target": quest.target,
        "xp_reward": quest.xp_reward,
        "completed": progress >= quest.target,
        "claimed": quest.claimed_at is not None,
    }


class ClaimError(ValueError):
    pass


def claim_quest(db: Session, learner: LearnerProfile, quest_id: str) -> int:
    """Award a finished quest's XP once. Returns the XP awarded."""
    today = local_today()
    quest = (
        db.query(DailyQuest)
        .filter(DailyQuest.id == quest_id, DailyQuest.learner_id == learner.id)
        .with_for_update()
        .first()
    )
    if not quest:
        raise LookupError("Quest not found.")
    if quest.date != today.isoformat():
        raise ClaimError("Nhiệm vụ này đã hết hạn.")
    if quest.claimed_at is not None:
        raise ClaimError("Bạn đã nhận thưởng nhiệm vụ này rồi.")
    if not quest_view(quest, day_metrics(db, learner.id, today))["completed"]:
        raise ClaimError("Nhiệm vụ chưa hoàn thành.")
    quest.claimed_at = _now_naive()
    learner.total_xp = (learner.total_xp or 0) + quest.xp_reward
    from app.services.shop import GEMS_QUEST, award_gems
    award_gems(learner, GEMS_QUEST)
    return quest.xp_reward


# ── Weekly goal ──────────────────────────────────────────────────────────────
WEEKDAY_LABELS = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")


@dataclass
class WeeklyProgress:
    goal_days: int
    days_done: int
    days: list[dict]
    completed: bool
    claimed: bool


def weekly_progress(db: Session, learner: LearnerProfile, today: date | None = None) -> WeeklyProgress:
    today = today or local_today()
    monday = today - timedelta(days=today.weekday())
    done = study_days(db, learner.id, monday, today)
    goal = learner.weekly_goal_days or 5
    days = [
        {
            "date": (monday + timedelta(days=i)).isoformat(),
            "label": WEEKDAY_LABELS[i],
            "done": (monday + timedelta(days=i)) in done,
            "is_today": monday + timedelta(days=i) == today,
            "is_future": monday + timedelta(days=i) > today,
        }
        for i in range(7)
    ]
    return WeeklyProgress(
        goal_days=goal,
        days_done=len(done),
        days=days,
        completed=len(done) >= goal,
        claimed=learner.weekly_goal_claimed_week == week_key(today),
    )


def claim_weekly_reward(db: Session, learner: LearnerProfile) -> dict:
    today = local_today()
    progress = weekly_progress(db, learner, today)
    if progress.claimed:
        raise ClaimError("Bạn đã nhận thưởng tuần này rồi.")
    if not progress.completed:
        raise ClaimError("Chưa đạt mục tiêu tuần.")
    learner.weekly_goal_claimed_week = week_key(today)
    learner.total_xp = (learner.total_xp or 0) + WEEKLY_REWARD_XP
    from app.services.shop import GEMS_WEEKLY_GOAL, award_gems
    award_gems(learner, GEMS_WEEKLY_GOAL)
    gained_freeze = (learner.streak_freezes or 0) < MAX_STREAK_FREEZES
    if gained_freeze:
        learner.streak_freezes = (learner.streak_freezes or 0) + 1
    return {"xp_awarded": WEEKLY_REWARD_XP, "freeze_awarded": gained_freeze}
