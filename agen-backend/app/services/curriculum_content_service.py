"""
AGEN — Curriculum Content Factory service.

Generates lesson content once per curriculum node, caches + quality-checks it,
and materializes learner-owned Lesson rows from the approved cache WITHOUT any
further LLM calls.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentRequest, execute
from app.models.curriculum import CurriculumLesson
from app.models.curriculum_content import (
    STATUS_APPROVED,
    STATUS_DRAFT,
    STATUS_REJECTED,
    CurriculumLessonContent,
)
from app.models.lesson import Exercise, Lesson
from app.models.learner_profile import LearnerProfile


class ContentGenerationError(RuntimeError):
    """Raised when content could not be generated for a curriculum node."""


def get_cached_content(db: Session, code: str) -> CurriculumLessonContent | None:
    return (
        db.query(CurriculumLessonContent)
        .filter(CurriculumLessonContent.curriculum_code == code)
        .first()
    )


def _curriculum_node(db: Session, code: str) -> CurriculumLesson:
    node = db.query(CurriculumLesson).filter(CurriculumLesson.code == code).first()
    if not node:
        raise ContentGenerationError(f"Curriculum node '{code}' not found.")
    return node


def generate_and_cache(
    db: Session,
    code: str,
    *,
    force: bool = False,
    auto_approve: bool = False,
) -> CurriculumLessonContent:
    """Generate + cache content for a curriculum node (one LLM call).

    - Skips generation if cached content already exists (unless force=True).
    - Runs through the orchestrator so the AI Evaluation quality gate applies.
    - Stores as draft (or approved when auto_approve=True).
    Caller commits.
    """
    node = _curriculum_node(db, code)
    existing = get_cached_content(db, code)
    if existing and not force:
        return existing

    # Speaking/writing curriculum nodes aren't "lesson" content; only the four
    # lesson-generatable skills are pre-generated here.
    if node.skill not in ("vocabulary", "grammar", "reading", "listening"):
        raise ContentGenerationError(
            f"Skill '{node.skill}' is not pre-generatable as lesson content."
        )

    result = execute(AgentRequest(
        agent="lesson",
        payload={
            "skill": node.skill,
            "level": node.cefr_reference or node.code.split("-")[0],
            "topic": node.topic,
        },
    ))
    if result.status != "succeeded" or not result.data:
        raise ContentGenerationError(result.error or "Lesson generation failed.")

    payload = result.data
    exercises = payload.get("exercises", [])

    row = existing or CurriculumLessonContent(curriculum_code=code)
    row.level = node.cefr_reference or node.code.split("-")[0]
    row.skill = node.skill
    row.topic = node.topic
    row.content = payload
    row.total_exercises = len(exercises)
    row.eval_score = getattr(result, "eval_score", None)
    row.eval_flagged = bool(getattr(result, "eval_flagged", False))
    row.eval_flags = getattr(result, "eval_flags", None)
    row.status = STATUS_APPROVED if auto_approve else STATUS_DRAFT
    if auto_approve:
        row.approved_at = datetime.now(timezone.utc)
    if existing is None:
        db.add(row)

    return row


def set_status(db: Session, code: str, status: str) -> CurriculumLessonContent:
    """Approve or reject cached content. Caller commits."""
    if status not in (STATUS_APPROVED, STATUS_REJECTED, STATUS_DRAFT):
        raise ContentGenerationError(f"Invalid status '{status}'.")
    row = get_cached_content(db, code)
    if not row:
        raise ContentGenerationError(f"No cached content for '{code}'.")
    row.status = status
    row.approved_at = datetime.now(timezone.utc) if status == STATUS_APPROVED else None
    return row


def materialize_lesson_for_learner(
    db: Session,
    learner: LearnerProfile,
    code: str,
    *,
    require_approved: bool = True,
) -> Lesson | None:
    """Create a learner-owned Lesson from APPROVED cached content — no LLM call.

    Returns the new Lesson, or None if there is no usable cached content
    (caller may then fall back to live generation). Caller commits.
    """
    cached = get_cached_content(db, code)
    if not cached:
        return None
    if require_approved and cached.status != STATUS_APPROVED:
        return None

    data = cached.content or {}
    lesson = Lesson(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        skill=cached.skill,
        topic=data.get("topic", cached.topic),
        level=cached.level,
        title=data.get("title", "Lesson"),
        summary=data.get("summary", ""),
        status="generated",
        total_exercises=len(data.get("exercises", [])),
    )
    db.add(lesson)
    db.flush()

    for ex in data.get("exercises", []):
        db.add(Exercise(
            id=str(uuid.uuid4()),
            lesson_id=lesson.id,
            order=ex.get("order", 0),
            type=ex.get("type", "multiple_choice"),
            content=ex.get("content", {}),
        ))

    if cached.skill == "vocabulary" and "vocabulary" in data:
        lesson.content = {"vocabulary": data["vocabulary"]}
    elif cached.skill in ("reading", "listening") and "passage" in data:
        lesson.content = data["passage"]
    elif cached.skill == "grammar" and isinstance(data.get("explanation"), dict):
        lesson.content = {"explanation": data["explanation"]}

    return lesson


def batch_generate_level(
    db: Session,
    level: str,
    *,
    force: bool = False,
    auto_approve: bool = False,
    limit: int | None = None,
) -> dict:
    """Generate + cache content for every generatable node in a level.

    Returns a summary: {level, attempted, generated, skipped, failed, errors}.
    Caller commits (this commits per node to persist partial progress).
    """
    nodes = (
        db.query(CurriculumLesson)
        .filter(
            CurriculumLesson.cefr_reference == level,
            CurriculumLesson.skill.in_(["vocabulary", "grammar", "reading", "listening"]),
        )
        .order_by(CurriculumLesson.code)
        .all()
    )
    summary = {"level": level, "attempted": 0, "generated": 0, "skipped": 0, "failed": 0, "errors": []}
    for node in nodes:
        if limit is not None and summary["generated"] >= limit:
            break
        existing = get_cached_content(db, node.code)
        if existing and not force:
            summary["skipped"] += 1
            continue
        summary["attempted"] += 1
        try:
            generate_and_cache(db, node.code, force=force, auto_approve=auto_approve)
            db.commit()
            summary["generated"] += 1
        except Exception as exc:  # noqa: BLE001 — collect per-node failures
            db.rollback()
            summary["failed"] += 1
            summary["errors"].append({"code": node.code, "error": str(exc)})
    return summary


LESSON_SKILLS = ("vocabulary", "grammar", "reading", "listening")
# Levels pre-generated by the scheduled Content Factory run.
FACTORY_LEVELS = ("A1", "A2", "B1")


def generate_missing_content(db: Session, levels: tuple[str, ...] = FACTORY_LEVELS, limit: int = 3) -> dict:
    """Generate the next `limit` curriculum nodes that have no cached content yet.

    Nodes are taken in roadmap order (level, then code) so learners' next
    lessons become instant first. Content that passes the AI quality gate is
    approved straight away; anything the evaluator flags stays a draft for an
    admin to review in /admin. Commits per node so partial progress is kept.
    """
    summary: dict = {"generated": 0, "approved": 0, "flagged": 0, "failed": 0, "remaining": 0, "errors": []}
    cached_codes = {code for (code,) in db.query(CurriculumLessonContent.curriculum_code).all()}
    nodes = (
        db.query(CurriculumLesson)
        .filter(CurriculumLesson.cefr_reference.in_(levels), CurriculumLesson.skill.in_(LESSON_SKILLS))
        .all()
    )
    order = {lvl: i for i, lvl in enumerate(levels)}
    missing = sorted((n for n in nodes if n.code not in cached_codes), key=lambda n: (order[n.cefr_reference], n.code))
    for node in missing[:limit]:
        try:
            row = generate_and_cache(db, node.code)
            if not row.eval_flagged:
                row.status = STATUS_APPROVED
                row.approved_at = datetime.now(timezone.utc)
                summary["approved"] += 1
            else:
                summary["flagged"] += 1
            db.commit()
            summary["generated"] += 1
        except Exception as exc:  # noqa: BLE001 — keep going; report per node
            db.rollback()
            summary["failed"] += 1
            summary["errors"].append({"code": node.code, "error": str(exc)[:300]})
            # A quota error will fail every following node too.
            if "quota" in str(exc).lower() or "giới hạn" in str(exc).lower():
                break
    summary["remaining"] = max(0, len(missing) - summary["generated"])
    return summary


def content_coverage(db: Session, levels: tuple[str, ...] = FACTORY_LEVELS) -> list[dict]:
    """Per level: how many lesson nodes exist and how many are approved / drafts."""
    out = []
    for level in levels:
        codes = [
            c for (c,) in db.query(CurriculumLesson.code)
            .filter(CurriculumLesson.cefr_reference == level, CurriculumLesson.skill.in_(LESSON_SKILLS))
            .all()
        ]
        rows = db.query(CurriculumLessonContent.status).filter(CurriculumLessonContent.curriculum_code.in_(codes)).all() if codes else []
        out.append({
            "level": level,
            "total": len(codes),
            "approved": sum(1 for (s,) in rows if s == STATUS_APPROVED),
            "draft": sum(1 for (s,) in rows if s == STATUS_DRAFT),
        })
    return out


def pick_practice_content(db: Session, learner: LearnerProfile, skill: str, topic: str | None = None) -> str | None:
    """Pick approved cached content for a free-practice lesson, so it opens instantly.

    Prefers the learner's level and topics they have not studied yet; returns
    the curriculum code to materialize, or None to fall back to live generation.
    """
    import random

    level = learner.overall_level or "A1"
    if level not in FACTORY_LEVELS:
        level = "A1" if level == "PRE_A1" else level
    query = db.query(CurriculumLessonContent).filter(
        CurriculumLessonContent.status == STATUS_APPROVED,
        CurriculumLessonContent.skill == skill,
        CurriculumLessonContent.level == level,
    )
    rows = query.all()
    if topic:
        wanted = topic.strip().lower()
        rows = [r for r in rows if (r.topic or "").strip().lower() == wanted]
    done = {
        (t or "").strip().lower()
        for (t,) in db.query(Lesson.topic).filter(Lesson.learner_id == learner.id, Lesson.skill == skill).all()
    }
    fresh = [r for r in rows if (r.topic or "").strip().lower() not in done]
    return random.choice(fresh).curriculum_code if fresh else None
