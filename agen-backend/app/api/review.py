"""
AGEN — Review API (Ôn tập thông minh)
Daily spaced-repetition sessions over the learner's words and past mistakes,
plus the vocabulary / mistake notebook.
"""
import random
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timeutil import local_day_start_utc
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.review_item import ReviewItem
from app.models.user import User
from app.services.srs import MASTERED_STABILITY_DAYS, add_vocab_item, apply_review, is_mastered, strength
from app.services.streak_service import update_streak

router = APIRouter(prefix="/review", tags=["Review"])

XP_PER_CORRECT = 2
DAILY_REVIEW_XP_CAP = 50

# Distractors for learners whose notebook is still too small.
FALLBACK_WORDS = [
    ("apple", "quả táo"), ("book", "quyển sách"), ("house", "ngôi nhà"), ("water", "nước"),
    ("friend", "bạn bè"), ("school", "trường học"), ("happy", "vui vẻ"), ("run", "chạy"),
    ("teacher", "giáo viên"), ("morning", "buổi sáng"), ("city", "thành phố"), ("cheap", "rẻ"),
    ("travel", "du lịch"), ("weather", "thời tiết"), ("family", "gia đình"), ("kitchen", "nhà bếp"),
]


# ── Schemas ───────────────────────────────────────────────────────────────────
PromptType = Literal["meaning", "word", "mistake"]


class ReviewSummary(BaseModel):
    due_count: int
    vocab_total: int
    mistake_total: int
    mastered_count: int
    next_due_at: Optional[datetime]
    xp_today: int


class ReviewQuestion(BaseModel):
    item_id: str
    kind: str
    prompt_type: PromptType
    prompt: str
    hint: Optional[str] = None        # phonetic / example / last wrong answer
    speak: Optional[str] = None       # English text the client can read aloud
    options: list[str]                # empty → free-text answer


class ReviewSession(BaseModel):
    questions: list[ReviewQuestion]
    due_count: int


class ReviewAnswerPayload(BaseModel):
    prompt_type: PromptType
    answer: str = Field(max_length=500)


class ReviewAnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: Optional[str]
    example: Optional[str]
    interval_days: float
    strength: int
    mastered: bool
    xp_earned: int


class NotebookItem(BaseModel):
    id: str
    kind: str
    front: str
    back: str
    phonetic: Optional[str]
    example: Optional[str]
    explanation: Optional[str]
    last_wrong_answer: Optional[str]
    strength: int                     # recall probability right now, 0–100
    mastery: int                      # long-term progress towards "mastered", 0–100
    mastered: bool
    reps: int
    lapses: int
    due_at: datetime
    created_at: datetime


class NotebookPage(BaseModel):
    items: list[NotebookItem]
    total: int


class AddWordPayload(BaseModel):
    """G2 · a word tapped in a listening transcript (or typed by hand)."""
    word: str = Field(min_length=1, max_length=60)
    meaning: str = Field(min_length=1, max_length=300)
    phonetic: Optional[str] = Field(default=None, max_length=100)
    example: Optional[str] = Field(default=None, max_length=300)
    source_lesson_id: Optional[str] = Field(default=None, max_length=36)


class AddWordResponse(BaseModel):
    item: NotebookItem
    created: bool


class WordLookup(BaseModel):
    word: str
    phonetic: str = ""
    part_of_speech: str = ""
    meaning_vi: str
    definition_en: str = ""
    example: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _due_cutoff() -> datetime:
    """Anything due before the next local midnight counts as due today."""
    return (local_day_start_utc() + timedelta(days=1)).replace(tzinfo=None)


def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower()).rstrip(".!?")


def _xp_today(db: Session, learner_id: str) -> int:
    total = (
        db.query(func.coalesce(func.sum(LearningEvent.xp_earned), 0))
        .filter(
            LearningEvent.learner_id == learner_id,
            LearningEvent.event_type == "review_answered",
            LearningEvent.recorded_at >= local_day_start_utc().replace(tzinfo=None),
        )
        .scalar()
    )
    return int(total or 0)


def _distractors(pool: list[tuple[str, str]], item: ReviewItem, use_back: bool, k: int = 3) -> list[str]:
    target = _norm(item.back if use_back else item.front)
    seen = {target}
    picks: list[str] = []
    candidates = pool[:]
    random.shuffle(candidates)
    for front, back in candidates + FALLBACK_WORDS:
        text = back if use_back else front
        if _norm(text) in seen:
            continue
        seen.add(_norm(text))
        picks.append(text)
        if len(picks) == k:
            break
    return picks


def _question(item: ReviewItem, pool: list[tuple[str, str]]) -> ReviewQuestion:
    if item.kind == "mistake":
        extra = item.extra or {}
        options = [o for o in extra.get("options") or [] if o]
        if options and _norm(item.back) not in {_norm(o) for o in options}:
            options.append(item.back)
        random.shuffle(options)
        last_wrong = extra.get("last_wrong_answer")
        return ReviewQuestion(
            item_id=item.id, kind=item.kind, prompt_type="mistake", prompt=item.front,
            hint=f"Lần trước bạn chọn: {last_wrong}" if last_wrong else None,
            options=options if len(options) >= 2 else [],
        )

    # Alternate direction so both recognition and recall get practised.
    ask_meaning = (item.reps or 0) % 2 == 0
    options = _distractors(pool, item, use_back=ask_meaning) + [item.back if ask_meaning else item.front]
    random.shuffle(options)
    if ask_meaning:
        return ReviewQuestion(
            item_id=item.id, kind=item.kind, prompt_type="meaning", prompt=item.front,
            hint=item.phonetic, speak=item.front, options=options,
        )
    return ReviewQuestion(
        item_id=item.id, kind=item.kind, prompt_type="word", prompt=item.back,
        hint=None, options=options,
    )


def _notebook_item(item: ReviewItem, now: datetime) -> NotebookItem:
    return NotebookItem(
        id=item.id, kind=item.kind, front=item.front, back=item.back,
        phonetic=item.phonetic, example=item.example, explanation=item.explanation,
        last_wrong_answer=(item.extra or {}).get("last_wrong_answer"),
        strength=strength(item, now),
        mastery=min(100, round((item.stability or 0) / MASTERED_STABILITY_DAYS * 100)),
        mastered=is_mastered(item),
        reps=item.reps or 0, lapses=item.lapses or 0,
        due_at=item.due_at, created_at=item.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/summary", response_model=ReviewSummary)
def review_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _get_learner(db, current_user.id)
    base = db.query(ReviewItem).filter(ReviewItem.learner_id == learner.id)
    counts = dict(
        base.with_entities(ReviewItem.kind, func.count(ReviewItem.id)).group_by(ReviewItem.kind).all()
    )
    cutoff = _due_cutoff()
    next_due = (
        base.filter(ReviewItem.due_at >= cutoff).with_entities(func.min(ReviewItem.due_at)).scalar()
    )
    return ReviewSummary(
        due_count=base.filter(ReviewItem.due_at < cutoff).count(),
        vocab_total=counts.get("vocab", 0),
        mistake_total=counts.get("mistake", 0),
        mastered_count=base.filter(ReviewItem.stability >= MASTERED_STABILITY_DAYS).count(),
        next_due_at=next_due,
        xp_today=_xp_today(db, learner.id),
    )


@router.get("/session", response_model=ReviewSession)
def review_session(
    limit: int = Query(15, ge=1, le=30),
    ahead: bool = Query(False, description="Fill with not-yet-due items (practice ahead)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(db, current_user.id)
    base = db.query(ReviewItem).filter(ReviewItem.learner_id == learner.id)
    cutoff = _due_cutoff()
    due_count = base.filter(ReviewItem.due_at < cutoff).count()

    items = base.filter(ReviewItem.due_at < cutoff).order_by(ReviewItem.due_at).limit(limit).all()
    if ahead and len(items) < limit:
        items += (
            base.filter(ReviewItem.due_at >= cutoff)
            .order_by(ReviewItem.due_at)
            .limit(limit - len(items))
            .all()
        )

    pool = [
        (front, back)
        for front, back in base.filter(ReviewItem.kind == "vocab")
        .with_entities(ReviewItem.front, ReviewItem.back)
        .limit(200)
        .all()
    ]
    questions = [_question(item, pool) for item in items]
    random.shuffle(questions)
    return ReviewSession(questions=questions, due_count=due_count)


@router.post("/items/{item_id}/answer", response_model=ReviewAnswerResponse)
def answer_review(
    item_id: str,
    payload: ReviewAnswerPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(db, current_user.id)
    item = db.query(ReviewItem).filter(ReviewItem.id == item_id, ReviewItem.learner_id == learner.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found.")

    expected = item.front if payload.prompt_type == "word" else item.back
    correct = _norm(payload.answer) == _norm(expected)

    now = _now()
    was_due = item.due_at < _due_cutoff()
    result = apply_review(item, correct, now)

    # XP only for items that were actually due, with a daily cap, so practising
    # ahead or replaying a session can't farm XP.
    xp = 0
    if correct and was_due:
        xp = max(0, min(XP_PER_CORRECT, DAILY_REVIEW_XP_CAP - _xp_today(db, learner.id)))
        learner.total_xp = (learner.total_xp or 0) + xp

    db.add(LearningEvent(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        activity_id=item.id,
        event_type="review_answered",
        skill="vocabulary" if item.kind == "vocab" else "review",
        activity_type=f"review_{item.kind}",
        correct=correct,
        score=100.0 if correct else 0.0,
        xp_earned=xp,
        extra_data={"prompt_type": payload.prompt_type, "interval_days": result.interval_days},
    ))
    # A review counts as studying today, so it keeps the streak alive.
    update_streak(learner, db)
    db.commit()

    return ReviewAnswerResponse(
        correct=correct,
        correct_answer=expected,
        explanation=item.explanation,
        example=item.example,
        interval_days=round(result.interval_days, 3),
        strength=strength(item, now),
        mastered=is_mastered(item),
        xp_earned=xp,
    )


@router.get("/items", response_model=NotebookPage)
def list_notebook(
    kind: Literal["vocab", "mistake"] = "vocab",
    q: Optional[str] = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(db, current_user.id)
    query = db.query(ReviewItem).filter(ReviewItem.learner_id == learner.id, ReviewItem.kind == kind)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(ReviewItem.front.ilike(like) | ReviewItem.back.ilike(like))
    total = query.count()
    rows = query.order_by(ReviewItem.created_at.desc()).offset(offset).limit(limit).all()
    now = _now()
    return NotebookPage(items=[_notebook_item(r, now) for r in rows], total=total)


@router.delete("/items/{item_id}", status_code=204)
def delete_notebook_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(db, current_user.id)
    item = db.query(ReviewItem).filter(ReviewItem.id == item_id, ReviewItem.learner_id == learner.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found.")
    db.delete(item)
    db.commit()


@router.post("/items", response_model=AddWordResponse, status_code=201)
def add_notebook_word(
    payload: AddWordPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """G2 · Add a word to the vocabulary notebook (first review due tomorrow)."""
    learner = _get_learner(db, current_user.id)
    now = _now()
    try:
        item, created = add_vocab_item(
            db, learner.id, payload.word, payload.meaning,
            phonetic=payload.phonetic, example=payload.example,
            source_lesson_id=payload.source_lesson_id, now=now,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    db.commit()
    db.refresh(item)
    return AddWordResponse(item=_notebook_item(item, now), created=created)


@router.get("/lookup", response_model=WordLookup)
def lookup_word_endpoint(
    word: str = Query(min_length=1, max_length=60),
    context: str = Query(default="", max_length=300),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """G2 · Quick bilingual lookup for a word tapped in a transcript."""
    from app.services.dictionary_service import clean_word, lookup_word
    from app.services.llm_client import LLMError

    cleaned = clean_word(word)
    if not cleaned:
        raise HTTPException(status_code=422, detail="Từ không hợp lệ.")
    learner = _get_learner(db, current_user.id)
    try:
        data = lookup_word(cleaned, context.strip(), learner.overall_level or "A2")
    except LLMError as exc:
        raise HTTPException(status_code=429 if exc.is_quota_error else 502, detail=str(exc))
    except ValueError:
        raise HTTPException(status_code=502, detail="Không tra được từ này lúc này. Hãy thử lại.")
    return WordLookup(**data)


# ── G4 · Thử thách 60 giây (blitz) ────────────────────────────────────────────
BLITZ_QUESTIONS = 15
BLITZ_XP_PER_CORRECT = 2
BLITZ_DAILY_XP_CAP = 40


class BlitzQuestion(BaseModel):
    prompt: str              # English word
    options: list[str]       # Vietnamese meanings
    answer: int              # index into options (client checks locally for speed)
    phonetic: Optional[str] = None


class BlitzOut(BaseModel):
    questions: list[BlitzQuestion]
    seconds: int = 60
    from_notebook: int


class BlitzResultIn(BaseModel):
    correct: int = Field(ge=0, le=100)
    answered: int = Field(ge=0, le=100)
    seconds: float = Field(ge=0, le=600)


class BlitzResultOut(BaseModel):
    xp_earned: int
    gems_earned: int
    total_xp: int
    gems: int
    daily_xp_left: int


def _blitz_xp_today(db: Session, learner_id: str) -> int:
    start = local_day_start_utc().replace(tzinfo=None)
    return int(
        db.query(func.coalesce(func.sum(LearningEvent.xp_earned), 0))
        .filter(LearningEvent.learner_id == learner_id, LearningEvent.event_type == "blitz_played", LearningEvent.recorded_at >= start)
        .scalar() or 0
    )


@router.get("/blitz", response_model=BlitzOut)
def blitz_round(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """A 60-second meaning quiz from the learner's own words (filled up with common words)."""
    learner = _get_learner(db, current_user.id)
    rows = db.query(ReviewItem).filter(ReviewItem.learner_id == learner.id, ReviewItem.kind == "vocab").all()
    pool: list[tuple[str, str, Optional[str]]] = [(r.front, r.back, r.phonetic) for r in rows if r.front and r.back]
    from_notebook = min(len(pool), BLITZ_QUESTIONS)
    rng = random.Random()
    rng.shuffle(pool)
    chosen = pool[:BLITZ_QUESTIONS]
    fallback = [(w, m, None) for w, m in FALLBACK_WORDS if w.lower() not in {p[0].lower() for p in pool}]
    rng.shuffle(fallback)
    chosen += fallback[: BLITZ_QUESTIONS - len(chosen)]
    meanings = [m for _, m, _ in pool + fallback]
    questions = []
    for word, meaning, phonetic in chosen:
        others = [m for m in meanings if m != meaning]
        rng.shuffle(others)
        options = others[:3] + [meaning]
        rng.shuffle(options)
        questions.append(BlitzQuestion(prompt=word, options=options, answer=options.index(meaning), phonetic=phonetic))
    return BlitzOut(questions=questions, from_notebook=from_notebook)


@router.post("/blitz/result", response_model=BlitzResultOut)
def blitz_result(payload: BlitzResultIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.shop import GEMS_BLITZ_MAX, GEMS_BLITZ_PER_CORRECT, award_gems

    learner = _get_learner(db, current_user.id)
    correct = min(payload.correct, payload.answered, BLITZ_QUESTIONS)
    left = max(0, BLITZ_DAILY_XP_CAP - _blitz_xp_today(db, learner.id))
    xp = min(correct * BLITZ_XP_PER_CORRECT, left)
    gems = award_gems(learner, min(correct * GEMS_BLITZ_PER_CORRECT, GEMS_BLITZ_MAX))
    learner.total_xp = (learner.total_xp or 0) + xp
    db.add(LearningEvent(
        learner_id=learner.id, event_type="blitz_played", skill="vocabulary", activity_type="game",
        score=round(correct / payload.answered * 100, 1) if payload.answered else 0.0,
        xp_earned=xp, duration_seconds=payload.seconds,
        extra_data={"correct": correct, "answered": payload.answered},
    ))
    update_streak(learner, db)
    db.commit()
    return BlitzResultOut(xp_earned=xp, gems_earned=gems, total_xp=learner.total_xp or 0, gems=learner.gems or 0, daily_xp_left=max(0, left - xp))
