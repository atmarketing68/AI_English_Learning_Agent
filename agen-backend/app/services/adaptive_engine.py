"""
AGEN — Adaptive Learning Engine
Master Plan Giai đoạn 6 + Blueprint Part E.

Deterministic decision engine (no LLM). After each learning interaction it
inspects the outcome and decides the next pedagogical action:

    KEEP_LEVEL       — performing well, continue at current difficulty
    INCREASE         — mastered, push difficulty up
    DECREASE         — struggling, lower difficulty
    REVIEW           — decent but shaky, do a review
    RETEACH          — failed badly, re-teach the concept
    CHANGE_ACTIVITY  — repeated same-skill failures, switch activity/skill

This produces the value stored in LearningEvent.adaptive_decision, which
becomes part of the "Golden Data" that powers analytics and NBL later.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AdaptiveDecision(str, Enum):
    KEEP_LEVEL = "keep_level"
    INCREASE = "increase"
    DECREASE = "decrease"
    REVIEW = "review"
    RETEACH = "reteach"
    CHANGE_ACTIVITY = "change_activity"


# Score thresholds (0–100)
MASTERY = 85          # ≥ → mastered
PASS = 60             # ≥ → acceptable
WEAK = 40             # < → struggling


@dataclass
class AdaptiveInput:
    score: float                    # 0–100 for this activity
    skill: str
    difficulty: int = 1             # 1–5
    correct_ratio: float = 0.0      # fraction of exercises correct (0–1)
    consecutive_failures: int = 0   # prior consecutive low-scores in same skill
    prev_score: Optional[float] = None  # last activity score in same skill
    response_confidence: Optional[float] = None  # 0–1 if available


@dataclass
class AdaptiveResult:
    decision: AdaptiveDecision
    recommended_difficulty: int     # next difficulty (1–5)
    reason_vi: str                  # human-readable reason (Vietnamese)
    reason_en: str


def _clamp_difficulty(d: int) -> int:
    return max(1, min(5, d))


def decide(inp: AdaptiveInput) -> AdaptiveResult:
    """
    Core decision function. Ordered rule cascade — first match wins.
    Designed to be explainable and testable (no randomness, no LLM).
    """
    score = inp.score
    diff = inp.difficulty

    # 1. Repeated failures in the same skill → change activity to break the loop
    if inp.consecutive_failures >= 2 and score < PASS:
        return AdaptiveResult(
            decision=AdaptiveDecision.CHANGE_ACTIVITY,
            recommended_difficulty=_clamp_difficulty(diff - 1),
            reason_vi=f"Bạn gặp khó ở kỹ năng {inp.skill} nhiều lần liên tiếp — hãy thử một dạng hoạt động khác.",
            reason_en=f"Repeated struggles in {inp.skill} — switching activity type.",
        )

    # 2. Very low score → re-teach the concept from the start
    if score < WEAK:
        return AdaptiveResult(
            decision=AdaptiveDecision.RETEACH,
            recommended_difficulty=_clamp_difficulty(diff - 1),
            reason_vi="Kết quả còn thấp — AGEN sẽ dạy lại kiến thức này từ đầu.",
            reason_en="Low score — re-teaching the concept.",
        )

    # 3. Below passing → lower difficulty and try again
    if score < PASS:
        return AdaptiveResult(
            decision=AdaptiveDecision.DECREASE,
            recommended_difficulty=_clamp_difficulty(diff - 1),
            reason_vi="Bài hơi khó — AGEN sẽ giảm độ khó để bạn nắm chắc hơn.",
            reason_en="Below passing — decreasing difficulty.",
        )

    # 4. Mastered → increase difficulty (if not already at max)
    if score >= MASTERY:
        if diff < 5:
            return AdaptiveResult(
                decision=AdaptiveDecision.INCREASE,
                recommended_difficulty=_clamp_difficulty(diff + 1),
                reason_vi="Xuất sắc! AGEN sẽ tăng độ khó để bạn tiến bộ nhanh hơn.",
                reason_en="Mastered — increasing difficulty.",
            )
        return AdaptiveResult(
            decision=AdaptiveDecision.KEEP_LEVEL,
            recommended_difficulty=diff,
            reason_vi="Bạn đã thành thạo ở mức cao nhất — tiếp tục duy trì phong độ!",
            reason_en="Mastered at max difficulty — keeping level.",
        )

    # 5. Passing but not mastered, and dropped vs previous → review
    if inp.prev_score is not None and score < inp.prev_score - 10:
        return AdaptiveResult(
            decision=AdaptiveDecision.REVIEW,
            recommended_difficulty=diff,
            reason_vi="Kết quả giảm so với lần trước — hãy ôn lại một chút nhé.",
            reason_en="Score dropped vs previous — scheduling review.",
        )

    # 6. Solid pass → keep current level
    return AdaptiveResult(
        decision=AdaptiveDecision.KEEP_LEVEL,
        recommended_difficulty=diff,
        reason_vi="Tốt! Bạn đang học ổn định — tiếp tục ở mức hiện tại.",
        reason_en="Solid pass — keeping current level.",
    )


def compute_consecutive_failures(recent_scores: list[float], threshold: float = PASS) -> int:
    """
    Count how many of the MOST RECENT same-skill scores were below threshold,
    stopping at the first score that met threshold.
    recent_scores must be ordered newest → oldest.
    """
    count = 0
    for s in recent_scores:
        if s < threshold:
            count += 1
        else:
            break
    return count
