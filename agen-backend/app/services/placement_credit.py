"""
AGEN — Placement Credit

When a placement test places a learner ABOVE A1, the learner has effectively
"tested out" of the lower levels. Without crediting those lower-level curriculum
lessons, the roadmap gate (which requires the previous lesson to be mastered)
would lock every lesson at the placed level — leaving the learner with nothing
to start.

grant_placement_credit marks every curriculum lesson strictly BELOW the placed
level as mastered, so the first lesson of the learner's actual level unlocks
while the roadmap ordering within and above their level is preserved.

Deterministic, no LLM. Idempotent: safe to run on repeated placements.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.curriculum import CurriculumLesson, CurriculumUnit, LearnerCurriculumProgress
from app.models.learner_profile import LearnerProfile

# CEFR ladder (must match assessment_agent.CEFR_LEVELS ordering).
CEFR_ORDER = ["PRE_A1", "A1", "A2", "B1", "B2", "C1", "C2"]

# Score written for auto-credited lessons: at/above the curriculum mastery
# threshold (75) so they count as mastered, and clearly recognisable as a
# placement credit rather than a real attempt.
PLACEMENT_CREDIT_SCORE = 100


def _level_index(level: str | None) -> int:
    try:
        return CEFR_ORDER.index(level) if level else 0
    except ValueError:
        return 0


def grant_placement_credit(db: Session, learner: LearnerProfile, placed_level: str) -> int:
    """Mark all curriculum lessons below `placed_level` as mastered for the learner.

    Returns the number of lessons newly credited. Caller is responsible for
    committing the session.
    """
    placed_idx = _level_index(placed_level)
    if placed_idx <= _level_index("A1"):
        # Placed at A1 (or lower) — nothing below to credit; normal roadmap applies.
        return 0

    lower_levels = CEFR_ORDER[1:placed_idx]  # skip PRE_A1 sentinel, up to (not incl.) placed
    if not lower_levels:
        return 0

    lessons = (
        db.query(CurriculumLesson)
        .join(CurriculumUnit, CurriculumUnit.id == CurriculumLesson.unit_id)
        .filter(CurriculumUnit.level.in_(lower_levels))
        .all()
    )
    if not lessons:
        return 0

    # Existing progress rows for this learner, keyed by curriculum_lesson_id.
    existing = {
        p.curriculum_lesson_id: p
        for p in db.query(LearnerCurriculumProgress).filter(
            LearnerCurriculumProgress.learner_id == learner.id
        ).all()
    }

    now = datetime.now(timezone.utc)
    credited = 0
    for lesson in lessons:
        prog = existing.get(lesson.id)
        if prog is None:
            db.add(
                LearnerCurriculumProgress(
                    learner_id=learner.id,
                    curriculum_lesson_id=lesson.id,
                    status="completed",
                    best_score=PLACEMENT_CREDIT_SCORE,
                    attempts=0,
                    mastered=True,
                    started_at=now,
                    completed_at=now,
                )
            )
            credited += 1
        elif not prog.mastered:
            # Learner had a row but hadn't mastered it — credit it now.
            prog.status = "completed"
            prog.best_score = max(prog.best_score or 0, PLACEMENT_CREDIT_SCORE)
            prog.mastered = True
            prog.completed_at = prog.completed_at or now
            credited += 1
        # else: already mastered — leave it (idempotent).

    return credited
