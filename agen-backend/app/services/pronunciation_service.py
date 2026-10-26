"""
AGEN — Speech practice scoring (transcript-based).

The client captures speech with the browser Web Speech API (STT) and sends the
recognized transcript plus the target sentence. This service scores transcript
alignment as a speaking-practice proxy; it does not measure phoneme-level
pronunciation accuracy.

Dimensions (0-100):
  - accuracy : word-level similarity between transcript and target (order-aware)
  - coverage : fraction of target words the learner actually produced
  - fluency  : words-per-minute vs an expected band (if duration provided)

Deterministic, no LLM.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field


def _normalize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into word tokens."""
    cleaned = re.sub(r"[^a-z0-9'\s]", " ", (text or "").lower())
    return [w for w in cleaned.split() if w]


@dataclass
class PronunciationResult:
    overall_score: float
    accuracy: float
    coverage: float
    fluency: float
    target_word_count: int
    said_word_count: int
    missed_words: list[str] = field(default_factory=list)
    extra_words: list[str] = field(default_factory=list)
    feedback_vi: str = ""

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 1),
            "accuracy": round(self.accuracy, 1),
            "coverage": round(self.coverage, 1),
            "fluency": round(self.fluency, 1),
            "target_word_count": self.target_word_count,
            "said_word_count": self.said_word_count,
            "missed_words": self.missed_words,
            "extra_words": self.extra_words,
            "feedback_vi": self.feedback_vi,
        }


# Expected comfortable speaking pace band (words per minute).
_WPM_MIN = 60
_WPM_IDEAL_LOW = 90
_WPM_IDEAL_HIGH = 160


def _fluency_score(said_words: int, duration_seconds: float | None) -> float:
    if not duration_seconds or duration_seconds <= 0 or said_words == 0:
        return 100.0  # no timing info → don't penalise
    wpm = said_words / (duration_seconds / 60.0)
    if _WPM_IDEAL_LOW <= wpm <= _WPM_IDEAL_HIGH:
        return 100.0
    if wpm < _WPM_IDEAL_LOW:
        # Linear from _WPM_MIN (50) up to ideal-low (100).
        if wpm <= _WPM_MIN:
            return 50.0
        return 50.0 + (wpm - _WPM_MIN) / (_WPM_IDEAL_LOW - _WPM_MIN) * 50.0
    # Too fast: gentle penalty, floor 70.
    over = wpm - _WPM_IDEAL_HIGH
    return max(70.0, 100.0 - over * 0.5)


def score_pronunciation(
    target_text: str,
    transcript: str,
    duration_seconds: float | None = None,
) -> PronunciationResult:
    """Score a spoken attempt against a target sentence."""
    target = _normalize(target_text)
    said = _normalize(transcript)

    if not target:
        return PronunciationResult(
            overall_score=0.0, accuracy=0.0, coverage=0.0, fluency=0.0,
            target_word_count=0, said_word_count=len(said),
            feedback_vi="Không có câu mẫu để so sánh.",
        )

    # Accuracy: order-aware similarity ratio over word sequences.
    matcher = difflib.SequenceMatcher(a=target, b=said, autojunk=False)
    accuracy = matcher.ratio() * 100.0

    # Coverage + missed/extra words via set difference (case/punct-normalized).
    target_set = set(target)
    said_set = set(said)
    matched = target_set & said_set
    coverage = (len(matched) / len(target_set)) * 100.0
    missed_words = [w for w in target if w not in said_set]
    # Preserve order + dedupe for missed
    seen: set[str] = set()
    missed_words = [w for w in missed_words if not (w in seen or seen.add(w))]
    extra_words = [w for w in said if w not in target_set]
    seen2: set[str] = set()
    extra_words = [w for w in extra_words if not (w in seen2 or seen2.add(w))]

    fluency = _fluency_score(len(said), duration_seconds)

    overall = accuracy * 0.55 + coverage * 0.30 + fluency * 0.15

    # Simple Vietnamese feedback.
    if overall >= 85:
        feedback = "Tuyệt vời! Phát âm của bạn rất rõ và chính xác."
    elif overall >= 70:
        feedback = "Tốt! Hãy chú ý phát âm rõ hơn một vài từ còn thiếu."
    elif overall >= 50:
        feedback = "Khá ổn. Hãy luyện lại và nói chậm, rõ từng từ."
    else:
        feedback = "Hãy thử lại — đọc to, chậm và rõ từng từ trong câu mẫu."
    if missed_words:
        preview = ", ".join(missed_words[:5])
        feedback += f" Từ cần luyện thêm: {preview}."

    return PronunciationResult(
        overall_score=overall,
        accuracy=accuracy,
        coverage=coverage,
        fluency=fluency,
        target_word_count=len(target),
        said_word_count=len(said),
        missed_words=missed_words,
        extra_words=extra_words,
        feedback_vi=feedback,
    )
