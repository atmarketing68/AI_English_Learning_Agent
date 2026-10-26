"""
Spaced repetition: FSRS-4.5 scheduler + review-item collection.

FSRS models each memory with a stability S (days until recall probability drops
to 90%) and a difficulty D (1–10). After every review it updates S/D from the
grade and the recall probability at review time, then schedules the next review
when retrievability is expected to hit the target (90%).
Reference: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm

All datetimes here are naive UTC, matching the rest of the models.
"""
import hashlib
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.lesson import Exercise, Lesson
from app.models.review_item import ReviewItem

# FSRS-4.5 default parameters.
W = (
    0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474,
    0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755,
)
DECAY = -0.5
FACTOR = 19 / 81            # makes R(S, S) == 0.9
DESIRED_RETENTION = 0.9
MAX_INTERVAL_DAYS = 365
RELEARN_DELAY = timedelta(minutes=10)
MASTERED_STABILITY_DAYS = 21.0

AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def retrievability(elapsed_days: float, stability: float) -> float:
    """Probability of recall after `elapsed_days` for a memory of `stability`."""
    if stability <= 0:
        return 0.0
    return (1 + FACTOR * max(elapsed_days, 0.0) / stability) ** DECAY


def next_interval_days(stability: float) -> int:
    interval = stability / FACTOR * (DESIRED_RETENTION ** (1 / DECAY) - 1)
    return int(_clamp(round(interval), 1, MAX_INTERVAL_DAYS))


def _init_difficulty(grade: int) -> float:
    return _clamp(W[4] - (grade - 3) * W[5], 1, 10)


def _next_difficulty(d: float, grade: int) -> float:
    d_new = d - W[6] * (grade - 3)
    # Mean reversion towards the initial "Good" difficulty.
    return _clamp(W[7] * _init_difficulty(GOOD) + (1 - W[7]) * d_new, 1, 10)


def _recall_stability(d: float, s: float, r: float, grade: int) -> float:
    hard_penalty = W[15] if grade == HARD else 1.0
    easy_bonus = W[16] if grade == EASY else 1.0
    return s * (
        1
        + math.exp(W[8]) * (11 - d) * s ** (-W[9]) * (math.exp(W[10] * (1 - r)) - 1)
        * hard_penalty * easy_bonus
    )


def _forget_stability(d: float, s: float, r: float) -> float:
    s_forget = W[11] * d ** (-W[12]) * ((s + 1) ** W[13] - 1) * math.exp(W[14] * (1 - r))
    return min(s_forget, s)


@dataclass
class ScheduleResult:
    stability: float
    difficulty: float
    state: str
    due_at: datetime
    interval_days: float


def schedule(
    stability: Optional[float],
    difficulty: Optional[float],
    last_review_at: Optional[datetime],
    grade: int,
    now: datetime,
) -> ScheduleResult:
    """Return the memory state and next due time after a review graded `grade` (1–4)."""
    grade = int(_clamp(grade, AGAIN, EASY))

    if stability is None or difficulty is None:
        s = W[grade - 1]
        d = _init_difficulty(grade)
    else:
        elapsed = (now - last_review_at).total_seconds() / 86400 if last_review_at else 0.0
        r = retrievability(elapsed, stability)
        d = _next_difficulty(difficulty, grade)
        s = _forget_stability(difficulty, stability, r) if grade == AGAIN else _recall_stability(difficulty, stability, r, grade)

    s = max(s, 0.1)
    if grade == AGAIN:
        # Show it again later in the same session/day, like a relearning step.
        return ScheduleResult(s, d, "relearning", now + RELEARN_DELAY, RELEARN_DELAY.total_seconds() / 86400)
    days = next_interval_days(s)
    return ScheduleResult(s, d, "review", now + timedelta(days=days), float(days))


def apply_review(item: ReviewItem, correct: bool, now: datetime) -> ScheduleResult:
    """Grade a review (correct → Good, wrong → Again) and update the item in place."""
    grade = GOOD if correct else AGAIN
    result = schedule(item.stability, item.difficulty, item.last_review_at, grade, now)
    item.stability = result.stability
    item.difficulty = result.difficulty
    item.state = result.state
    item.due_at = result.due_at
    item.last_review_at = now
    item.reps = (item.reps or 0) + 1
    if not correct:
        item.lapses = (item.lapses or 0) + 1
    return result


def strength(item: ReviewItem, now: datetime) -> int:
    """Current recall probability, 0–100 (0 for items never reviewed)."""
    if item.stability is None or item.last_review_at is None:
        return 0
    elapsed = (now - item.last_review_at).total_seconds() / 86400
    return round(retrievability(elapsed, item.stability) * 100)


def is_mastered(item: ReviewItem) -> bool:
    return (item.stability or 0) >= MASTERED_STABILITY_DAYS


# ── Collecting items from lessons ────────────────────────────────────────────
def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _mistake_key(exercise_type: str, prompt: str) -> str:
    return hashlib.sha1(f"{exercise_type}|{prompt.lower()}".encode("utf-8")).hexdigest()


def _upsert(db: Session, learner_id: str, kind: str, key: str, **fields) -> tuple[ReviewItem, bool]:
    item = (
        db.query(ReviewItem)
        .filter(ReviewItem.learner_id == learner_id, ReviewItem.kind == kind, ReviewItem.key == key)
        .first()
    )
    if item:
        return item, False
    item = ReviewItem(learner_id=learner_id, kind=kind, key=key, **fields)
    db.add(item)
    return item, True


def _lesson_words(lesson: Lesson) -> Iterable[dict]:
    content = lesson.content if isinstance(lesson.content, dict) else {}
    for entry in content.get("vocabulary") or []:
        if isinstance(entry, dict):
            yield entry
    for ex in lesson.exercises:
        if ex.type == "flashcard" and isinstance(ex.content, dict):
            yield ex.content
    for entry in content.get("vocabulary_highlights") or []:
        if isinstance(entry, dict):
            yield entry


def collect_lesson_vocabulary(db: Session, learner_id: str, lesson: Lesson, now: datetime) -> int:
    """Add the lesson's words to the learner's notebook. First review is due tomorrow."""
    added = 0
    seen: set[str] = set()
    for entry in _lesson_words(lesson):
        word = _clean(entry.get("word"))
        meaning = _clean(entry.get("translation") or entry.get("definition"))
        key = word.lower()[:128]
        if not word or not meaning or len(word) > 60 or key in seen:
            continue
        seen.add(key)
        _, created = _upsert(
            db, learner_id, "vocab", key,
            front=word,
            back=meaning,
            phonetic=_clean(entry.get("phonetic"))[:100] or None,
            example=_clean(entry.get("example")) or None,
            explanation=_clean(entry.get("definition")) if entry.get("translation") else None,
            source_lesson_id=lesson.id,
            due_at=now + timedelta(days=1),
        )
        added += int(created)
    return added


def add_vocab_item(
    db: Session,
    learner_id: str,
    word: str,
    meaning: str,
    phonetic: str | None = None,
    example: str | None = None,
    source_lesson_id: str | None = None,
    now: datetime | None = None,
) -> tuple[ReviewItem, bool]:
    """G2 · Save a word the learner tapped (listening transcript) to the notebook."""
    now = now or datetime.utcnow()
    word, meaning = _clean(word)[:60], _clean(meaning)
    if not word or not meaning:
        raise ValueError("word and meaning are required")
    return _upsert(
        db, learner_id, "vocab", word.lower()[:128],
        front=word,
        back=meaning,
        phonetic=(_clean(phonetic)[:100] or None),
        example=(_clean(example) or None),
        source_lesson_id=source_lesson_id,
        due_at=now + timedelta(days=1),
    )


def record_mistake(db: Session, learner_id: str, exercise: Exercise, user_answer: str, now: datetime) -> Optional[ReviewItem]:
    """Save a wrongly answered question so it comes back in the next review."""
    content = exercise.content if isinstance(exercise.content, dict) else {}
    if exercise.type == "multiple_choice":
        prompt = _clean(content.get("question"))
        options = content.get("options") if isinstance(content.get("options"), dict) else {}
        correct_key = _clean(content.get("correct_answer")).upper()
        answer = _clean(options.get(correct_key)) if correct_key in options else ""
        choices = [_clean(v) for v in options.values() if _clean(v)]
        explanation = _clean(content.get("explanation")) or None
        wrong = _clean(options.get(_clean(user_answer).upper(), user_answer))
    elif exercise.type == "fill_blank":
        prompt = _clean(content.get("sentence"))
        answer = _clean(content.get("blank_word"))
        choices = [_clean(v) for v in content.get("options") or [] if _clean(v)]
        explanation = _clean(content.get("hint")) or None
        wrong = _clean(user_answer)
    else:
        return None
    if not prompt or not answer:
        return None

    item, created = _upsert(
        db, learner_id, "mistake", _mistake_key(exercise.type, prompt),
        front=prompt,
        back=answer,
        explanation=explanation,
        extra={"exercise_type": exercise.type, "options": choices},
        source_lesson_id=exercise.lesson_id,
        due_at=now,
    )
    if not created:
        # Missed again in a lesson: bring it straight back.
        item.due_at = min(item.due_at, now)
        item.lapses = (item.lapses or 0) + 1
    extra = dict(item.extra or {})
    extra["last_wrong_answer"] = wrong[:200]
    item.extra = extra
    return item
