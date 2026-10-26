"""Unit tests for streak_service and lesson score computation.

Streak tests use the in-memory DB fixture; scoring tests are pure functions.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.agents.lesson_agent import compute_lesson_score
from app.models.learner_profile import LearnerProfile
from app.models.achievement import DailyChallenge
from app.services.streak_service import (
    record_activity,
    update_daily_challenge_progress,
    update_streak,
)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _make_learner(db_session, **kwargs):
    from app.models.user import User

    user = User(email=f"u_{id(kwargs)}@example.com", hashed_password="x", full_name="U")
    db_session.add(user)
    db_session.flush()
    learner = LearnerProfile(
        user_id=user.id,
        display_name="Learner",
        **kwargs,
    )
    db_session.add(learner)
    db_session.flush()
    return learner


# ── update_streak ──────────────────────────────────────────────────────────────
def test_first_activity_sets_streak_to_one(db_session):
    learner = _make_learner(db_session, current_streak=0, longest_streak=0)
    info = update_streak(learner, db_session)
    assert info["current_streak"] == 1
    assert info["longest_streak"] == 1
    assert learner.last_active_at is not None


def test_same_day_activity_does_not_increment(db_session):
    now = datetime.now(timezone.utc)
    learner = _make_learner(
        db_session, current_streak=5, longest_streak=5, last_active_at=now
    )
    info = update_streak(learner, db_session)
    assert info["current_streak"] == 5


def test_consecutive_day_increments(db_session):
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    learner = _make_learner(
        db_session, current_streak=3, longest_streak=3, last_active_at=yesterday
    )
    info = update_streak(learner, db_session)
    assert info["current_streak"] == 4
    assert info["longest_streak"] == 4


def test_gap_resets_streak(db_session):
    three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
    learner = _make_learner(
        db_session, current_streak=10, longest_streak=10, last_active_at=three_days_ago
    )
    info = update_streak(learner, db_session)
    assert info["current_streak"] == 1
    # longest is preserved because current (1) < longest (10)
    assert info["longest_streak"] == 10


def test_longest_streak_only_grows(db_session):
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    learner = _make_learner(
        db_session, current_streak=7, longest_streak=20, last_active_at=yesterday
    )
    info = update_streak(learner, db_session)
    assert info["current_streak"] == 8
    assert info["longest_streak"] == 20


def test_naive_last_active_is_handled(db_session):
    # last_active_at stored as naive UTC (as SQLite often does)
    yesterday_naive = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    learner = _make_learner(
        db_session, current_streak=2, longest_streak=2, last_active_at=yesterday_naive
    )
    info = update_streak(learner, db_session)
    assert info["current_streak"] == 3


# ── update_daily_challenge_progress ──────────────────────────────────────────────
def _make_challenge(db_session, learner, **kwargs):
    today = datetime.now(timezone.utc).date().isoformat()
    defaults = dict(
        learner_id=learner.id,
        date=today,
        title="Daily",
        description="Do it",
        skill="vocabulary",
        target_type="complete_lesson",
        target_value=2,
        current_value=0,
        xp_reward=20,
        is_completed=False,
    )
    defaults.update(kwargs)
    ch = DailyChallenge(**defaults)
    db_session.add(ch)
    db_session.flush()
    return ch


def test_challenge_increments_on_skill_match(db_session):
    learner = _make_learner(db_session, total_xp=0)
    ch = _make_challenge(db_session, learner, skill="vocabulary", target_value=2)
    completed = update_daily_challenge_progress(learner, "vocabulary", db_session)
    assert completed is False
    assert ch.current_value == 1
    assert ch.is_completed is False


def test_challenge_completes_and_awards_xp(db_session):
    learner = _make_learner(db_session, total_xp=100)
    ch = _make_challenge(db_session, learner, skill="vocabulary", target_value=1, xp_reward=20)
    completed = update_daily_challenge_progress(learner, "vocabulary", db_session)
    assert completed is True
    assert ch.is_completed is True
    assert ch.completed_at is not None
    assert learner.total_xp == 120


def test_challenge_ignores_non_matching_skill(db_session):
    learner = _make_learner(db_session)
    ch = _make_challenge(db_session, learner, skill="grammar")
    completed = update_daily_challenge_progress(learner, "vocabulary", db_session)
    assert completed is False
    assert ch.current_value == 0


def test_already_completed_challenge_not_reincremented(db_session):
    learner = _make_learner(db_session, total_xp=50)
    ch = _make_challenge(
        db_session, learner, skill="vocabulary", current_value=2,
        target_value=2, is_completed=True,
    )
    completed = update_daily_challenge_progress(learner, "vocabulary", db_session)
    assert completed is False
    assert ch.current_value == 2
    assert learner.total_xp == 50


def test_no_challenge_today_is_noop(db_session):
    learner = _make_learner(db_session)
    completed = update_daily_challenge_progress(learner, "vocabulary", db_session)
    assert completed is False


# ── record_activity (integration of both) ────────────────────────────────────────
def test_record_activity_returns_combined_summary(db_session):
    learner = _make_learner(db_session, current_streak=0)
    _make_challenge(db_session, learner, skill="vocabulary", target_value=1)
    summary = record_activity(learner, "vocabulary", db_session)
    assert summary["streak"]["current_streak"] == 1
    assert summary["daily_challenge_completed"] is True


# ── compute_lesson_score ─────────────────────────────────────────────────────────
def _results(n_correct, n_total):
    return [{"is_correct": i < n_correct} for i in range(n_total)]


def test_perfect_score_grade_s():
    r = compute_lesson_score(_results(10, 10))
    assert r["score"] == 100.0
    assert r["grade"] == "S"
    assert r["xp_earned"] == 30
    assert r["correct"] == 10
    assert r["total"] == 10


def test_grade_boundaries():
    assert compute_lesson_score(_results(9, 10))["grade"] == "S"    # 90
    assert compute_lesson_score(_results(75, 100))["grade"] == "A"  # 75
    assert compute_lesson_score(_results(60, 100))["grade"] == "B"  # 60
    assert compute_lesson_score(_results(45, 100))["grade"] == "C"  # 45
    assert compute_lesson_score(_results(44, 100))["grade"] == "D"  # 44


def test_xp_tiers():
    assert compute_lesson_score(_results(80, 100))["xp_earned"] == 30   # >= 75
    assert compute_lesson_score(_results(50, 100))["xp_earned"] == 15   # >= 45
    assert compute_lesson_score(_results(10, 100))["xp_earned"] == 5    # < 45


def test_empty_results_scores_zero():
    r = compute_lesson_score([])
    assert r["score"] == 0
    assert r["total"] == 0
    assert r["grade"] == "D"
    assert r["xp_earned"] == 5
