"""Unit tests for the deterministic Adaptive Learning Engine.

Exercises every branch of the decision cascade plus difficulty clamping and the
consecutive-failure counter. No LLM / DB required.
"""
from app.services.adaptive_engine import (
    MASTERY,
    PASS,
    WEAK,
    AdaptiveDecision,
    AdaptiveInput,
    compute_consecutive_failures,
    decide,
)


# ── decide(): each branch of the cascade ────────────────────────────────────────
def test_change_activity_on_repeated_failures():
    result = decide(AdaptiveInput(score=45, skill="grammar", difficulty=3, consecutive_failures=2))
    assert result.decision == AdaptiveDecision.CHANGE_ACTIVITY
    assert result.recommended_difficulty == 2


def test_reteach_on_very_low_score():
    result = decide(AdaptiveInput(score=WEAK - 1, skill="grammar", difficulty=3))
    assert result.decision == AdaptiveDecision.RETEACH
    assert result.recommended_difficulty == 2


def test_decrease_when_below_passing():
    result = decide(AdaptiveInput(score=WEAK + 5, skill="grammar", difficulty=3))
    assert result.decision == AdaptiveDecision.DECREASE
    assert result.recommended_difficulty == 2


def test_increase_when_mastered_below_max():
    result = decide(AdaptiveInput(score=MASTERY, skill="grammar", difficulty=3))
    assert result.decision == AdaptiveDecision.INCREASE
    assert result.recommended_difficulty == 4


def test_keep_level_when_mastered_at_max():
    result = decide(AdaptiveInput(score=95, skill="grammar", difficulty=5))
    assert result.decision == AdaptiveDecision.KEEP_LEVEL
    assert result.recommended_difficulty == 5


def test_review_when_score_dropped_vs_previous():
    result = decide(AdaptiveInput(score=65, skill="grammar", difficulty=3, prev_score=80))
    assert result.decision == AdaptiveDecision.REVIEW
    assert result.recommended_difficulty == 3


def test_keep_level_on_solid_pass():
    result = decide(AdaptiveInput(score=75, skill="grammar", difficulty=3, prev_score=72))
    assert result.decision == AdaptiveDecision.KEEP_LEVEL
    assert result.recommended_difficulty == 3


# ── Ordering / precedence ────────────────────────────────────────────────────────
def test_repeated_failures_takes_precedence_over_reteach():
    # score < WEAK would normally be RETEACH, but repeated failures win first.
    result = decide(AdaptiveInput(score=20, skill="grammar", difficulty=3, consecutive_failures=3))
    assert result.decision == AdaptiveDecision.CHANGE_ACTIVITY


def test_single_failure_does_not_trigger_change_activity():
    # Only one prior failure → falls through to the low-score rules instead.
    result = decide(AdaptiveInput(score=30, skill="grammar", difficulty=3, consecutive_failures=1))
    assert result.decision == AdaptiveDecision.RETEACH


# ── Difficulty clamping ──────────────────────────────────────────────────────────
def test_difficulty_never_below_one():
    result = decide(AdaptiveInput(score=10, skill="grammar", difficulty=1))
    assert result.recommended_difficulty == 1


def test_difficulty_never_above_five_on_increase():
    # At diff 5 with mastery, engine keeps level (does not exceed 5).
    result = decide(AdaptiveInput(score=100, skill="grammar", difficulty=5))
    assert result.recommended_difficulty == 5


# ── Boundary values at the thresholds ────────────────────────────────────────────
def test_exactly_pass_is_not_below_passing():
    # score == PASS should NOT be DECREASE/RETEACH (those require strict <).
    result = decide(AdaptiveInput(score=PASS, skill="grammar", difficulty=3))
    assert result.decision in {AdaptiveDecision.KEEP_LEVEL, AdaptiveDecision.REVIEW}


def test_exactly_mastery_triggers_increase():
    result = decide(AdaptiveInput(score=MASTERY, skill="grammar", difficulty=2))
    assert result.decision == AdaptiveDecision.INCREASE


def test_result_has_bilingual_reasons():
    result = decide(AdaptiveInput(score=75, skill="grammar", difficulty=3))
    assert result.reason_vi and isinstance(result.reason_vi, str)
    assert result.reason_en and isinstance(result.reason_en, str)


# ── compute_consecutive_failures ─────────────────────────────────────────────────
def test_consecutive_failures_counts_leading_failures():
    # newest → oldest
    assert compute_consecutive_failures([30, 40, 50, 90]) == 3


def test_consecutive_failures_stops_at_first_pass():
    assert compute_consecutive_failures([90, 30, 30]) == 0


def test_consecutive_failures_all_pass():
    assert compute_consecutive_failures([80, 90, 70]) == 0


def test_consecutive_failures_empty():
    assert compute_consecutive_failures([]) == 0


def test_consecutive_failures_custom_threshold():
    assert compute_consecutive_failures([50, 50, 90], threshold=WEAK) == 0
    assert compute_consecutive_failures([30, 30, 90], threshold=WEAK) == 2
