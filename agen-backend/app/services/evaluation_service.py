"""
AGEN — AI Evaluation Framework (Master Plan §29)

A deterministic, quota-free quality gate that scores every AI-generated payload
BEFORE it reaches a learner. Complements Pydantic structural validation with
pedagogical / safety / completeness checks.

Dimensions (0-100 each):
  - english_accuracy    : basic English sanity (no empty text, sane length, no obvious junk)
  - age_appropriate     : no unsafe / adult / violent vocabulary (blocklist)
  - completeness        : required content present for the agent type
  - curriculum_alignment: output skill/level matches what was requested

Returns an EvaluationResult with an overall score, per-dimension scores and flags.
A flag means "human should review" — it does NOT block delivery (fail-open) so a
single over-strict rule never breaks the learner experience, but everything is
logged for audit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Words never appropriate for a children's English learning app.
# Kept short & high-signal; expand over time. Matched as whole words, case-insensitive.
_BLOCKLIST = {
    # violence / weapons
    "kill", "murder", "gun", "shoot", "blood", "die", "death", "weapon", "bomb",
    # adult / substances
    "sex", "sexy", "porn", "drug", "cocaine", "beer", "wine", "alcohol", "cigarette",
    "gambling", "casino",
    # profanity (mild set)
    "damn", "hell", "stupid", "idiot", "hate",
}

_ALLOWED_SKILLS = {"vocabulary", "grammar", "reading", "listening", "speaking", "writing"}
_ALLOWED_LEVELS = {"PRE_A1", "A1", "A2", "B1", "B2", "C1", "C2"}

# Weights for the overall score (sum = 1.0)
_WEIGHTS = {
    "english_accuracy": 0.30,
    "age_appropriate": 0.30,
    "completeness": 0.25,
    "curriculum_alignment": 0.15,
}

FLAG_THRESHOLD = 70  # overall score below this → flagged for review


@dataclass
class EvaluationResult:
    overall_score: float
    scores: dict[str, float]
    flags: list[str] = field(default_factory=list)

    @property
    def flagged(self) -> bool:
        return self.overall_score < FLAG_THRESHOLD or len(self.flags) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "scores": {k: round(v, 1) for k, v in self.scores.items()},
            "flags": self.flags,
            "flagged": self.flagged,
        }


# ── Text collectors ─────────────────────────────────────────────────────────
def _collect_text(obj: Any, out: list[str]) -> None:
    """Recursively gather all string values from a nested dict/list payload."""
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_text(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_text(v, out)


# ── Individual checks ─────────────────────────────────────────────────────────
def _check_english_accuracy(texts: list[str], flags: list[str]) -> float:
    score = 100.0
    joined = " ".join(texts).strip()
    if not joined:
        flags.append("english: empty output")
        return 0.0
    # Penalise leftover template placeholders / obvious junk
    if re.search(r"\{\{.*?\}\}|lorem ipsum|TODO|XXX", joined, re.IGNORECASE):
        flags.append("english: placeholder/junk text detected")
        score -= 40
    # Penalise excessive repeated characters (e.g. "aaaaa") indicating garbled output
    if re.search(r"(.)\1{5,}", joined):
        flags.append("english: repeated-character garble")
        score -= 20
    # Penalise unbalanced/empty very short critical texts
    if len(joined) < 10:
        flags.append("english: output suspiciously short")
        score -= 30
    return max(score, 0.0)


def _check_age_appropriate(texts: list[str], flags: list[str]) -> float:
    joined = " ".join(texts).lower()
    hits = sorted({w for w in _BLOCKLIST if re.search(rf"\b{re.escape(w)}\b", joined)})
    if not hits:
        return 100.0
    flags.append(f"age: sensitive words {hits}")
    # Each distinct hit costs 25 points
    return max(100.0 - 25.0 * len(hits), 0.0)


def _check_completeness(agent: str, payload: dict, flags: list[str]) -> float:
    """Agent-specific required-content checks (beyond Pydantic min_length)."""
    if agent == "lesson":
        exercises = payload.get("exercises") or []
        if len(exercises) < 3:
            flags.append(f"completeness: only {len(exercises)} exercises (expect >= 3)")
            return 50.0
        # multiple_choice exercises must have a correct_answer + options
        for ex in exercises:
            content = ex.get("content", {}) if isinstance(ex, dict) else {}
            if ex.get("type") == "multiple_choice":
                if not content.get("correct_answer") or not content.get("options"):
                    flags.append("completeness: MCQ missing correct_answer/options")
                    return 60.0
        return 100.0

    if agent == "placement_question":
        if not payload.get("options") or not payload.get("correct_answer"):
            flags.append("completeness: placement missing options/answer")
            return 50.0
        return 100.0

    if agent == "writing_evaluation":
        if not payload.get("corrected_version"):
            flags.append("completeness: writing eval missing corrected_version")
            return 60.0
        return 100.0

    # Default: structurally validated already → assume complete
    return 100.0


def _check_curriculum_alignment(
    agent: str, payload: dict, expected: dict | None, flags: list[str]
) -> float:
    """Verify skill/level in output matches what was requested (if provided)."""
    if not expected:
        return 100.0
    score = 100.0

    exp_skill = expected.get("skill")
    out_skill = payload.get("skill")
    if exp_skill and out_skill and exp_skill != out_skill:
        flags.append(f"alignment: skill mismatch (want {exp_skill}, got {out_skill})")
        score -= 50

    # Validate skill/level are within known vocab where present
    if out_skill and out_skill not in _ALLOWED_SKILLS:
        flags.append(f"alignment: unknown skill '{out_skill}'")
        score -= 25

    out_level = payload.get("level")
    if out_level and out_level not in _ALLOWED_LEVELS:
        flags.append(f"alignment: unknown level '{out_level}'")
        score -= 25

    return max(score, 0.0)


# ── Public entry point ──────────────────────────────────────────────────────
def evaluate_output(agent: str, payload: dict, expected: dict | None = None) -> EvaluationResult:
    """
    Evaluate an AI agent's validated output payload.
    `expected` may carry {'skill': ..., 'level': ...} that was requested.
    """
    flags: list[str] = []
    texts: list[str] = []
    _collect_text(payload, texts)

    scores = {
        "english_accuracy": _check_english_accuracy(texts, flags),
        "age_appropriate": _check_age_appropriate(texts, flags),
        "completeness": _check_completeness(agent, payload, flags),
        "curriculum_alignment": _check_curriculum_alignment(agent, payload, expected, flags),
    }
    overall = sum(scores[k] * w for k, w in _WEIGHTS.items())
    return EvaluationResult(overall_score=overall, scores=scores, flags=flags)
