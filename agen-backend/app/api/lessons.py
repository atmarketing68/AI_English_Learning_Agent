"""
AGEN — Lesson API
Endpoints for generating, retrieving, and completing lessons.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.lesson import Lesson, Exercise
from app.models.learning_event import LearningEvent
from app.models.agent_trace import AgentTrace
from app.agents.lesson_agent import compute_lesson_score, TOPIC_BANK
from app.agents.orchestrator import AgentRequest, execute
from app.services.agent_jobs import create_job, get_job, update_job
from app.worker import enqueue_lesson_generation
from app.services.streak_service import record_activity
from app.services.adaptive_engine import (
    decide as adaptive_decide,
    AdaptiveInput,
    compute_consecutive_failures,
    MASTERY,
)
from app.models.curriculum import CurriculumLesson, LearnerCurriculumProgress

router = APIRouter(prefix="/lessons", tags=["Lessons"])
logger = logging.getLogger("agen.lessons")


# ── Schemas ───────────────────────────────────────────────────────────────────
class GenerateLessonRequest(BaseModel):
    skill: str
    topic: str | None = Field(
        default=None,
        max_length=100,
        description="Optional topic — AI picks one if omitted",
    )
    curriculum_code: str | None = Field(
        default=None,
        max_length=40,
        description="Curriculum node code — serve cached content if available",
    )
    background: bool = False


class ExerciseSchema(BaseModel):
    id: str
    order: int
    type: str
    content: dict
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None


class LessonDetailResponse(BaseModel):
    id: str
    skill: str
    topic: str
    level: str
    title: str
    summary: Optional[str]
    content: Optional[dict]   # passage data for reading/listening
    status: str
    score: float
    xp_earned: int
    total_exercises: int
    correct_exercises: int
    exercises: list[ExerciseSchema]
    created_at: datetime
    completed_at: Optional[datetime]


class LessonSummaryResponse(BaseModel):
    id: str
    skill: str
    topic: str
    level: str
    title: str
    status: str
    score: float
    xp_earned: int
    created_at: datetime


class SubmitExercisePayload(BaseModel):
    exercise_id: str
    answer: str  # The user's answer text or option key
    duration_seconds: Optional[float] = None   # time spent on this exercise (client-tracked)
    difficulty: int = 1                          # difficulty of this exercise (1–5)


class SubmitExerciseResponse(BaseModel):
    exercise_id: str
    is_correct: bool
    correct_answer: Optional[str]
    explanation: Optional[str]


class FinishLessonResponse(BaseModel):
    lesson_id: str
    score: float
    grade: str
    correct: int
    total: int
    xp_earned: int
    message: str
    adaptive_decision: Optional[str] = None       # keep_level / increase / ...
    adaptive_reason: Optional[str] = None          # human-readable (Vietnamese)
    recommended_difficulty: Optional[int] = None


class DailyRecommendation(BaseModel):
    skill: str
    topic: str
    reason: str
    icon: str


class LessonGenerationAccepted(BaseModel):
    job_id: str
    trace_id: str
    status: str
    poll_url: str


class LessonGenerationJobResponse(BaseModel):
    job_id: str
    trace_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


_CURRICULUM_MASTERY_THRESHOLD = 75  # score >= → curriculum node mastered


def _update_curriculum_progress(db: Session, learner_id: str, lesson: Lesson, score: float) -> None:
    """
    If this AI-generated lesson corresponds to a curriculum node the learner
    started (matched by generated_lesson_id or by skill+topic), update progress.
    Marks the node completed and mastered when score meets the threshold.
    """
    # Prefer explicit link, else best-effort match on an in-progress node
    progress = db.query(LearnerCurriculumProgress).filter(
        LearnerCurriculumProgress.learner_id == learner_id,
        LearnerCurriculumProgress.generated_lesson_id == lesson.id,
    ).first()

    if not progress:
        # Fallback: match any curriculum node (in_progress OR completed) of same skill+topic
        # This handles re-attempts where the learner replays a lesson to improve their score.
        progress = (
            db.query(LearnerCurriculumProgress)
            .join(CurriculumLesson,
                  CurriculumLesson.id == LearnerCurriculumProgress.curriculum_lesson_id)
            .filter(
                LearnerCurriculumProgress.learner_id == learner_id,
                LearnerCurriculumProgress.status.in_(["in_progress", "completed"]),
                CurriculumLesson.skill == lesson.skill,
                CurriculumLesson.topic == lesson.topic,
            )
            .order_by(LearnerCurriculumProgress.started_at.desc())  # take the most recent
            .first()
        )

    if not progress:
        return

    progress.attempts = (progress.attempts or 0) + 1
    progress.best_score = max(progress.best_score or 0, int(round(score)))
    progress.generated_lesson_id = lesson.id
    progress.status = "completed"
    progress.completed_at = datetime.now(timezone.utc)
    if progress.best_score >= _CURRICULUM_MASTERY_THRESHOLD:
        progress.mastered = True


def _check_exercise_answer(exercise: Exercise, user_answer: str) -> tuple[bool, str, str]:
    """Returns (is_correct, correct_answer, explanation)"""
    content = exercise.content
    ex_type = exercise.type

    if ex_type == "multiple_choice":
        correct = content.get("correct_answer", "")
        is_correct = user_answer.upper().strip() == correct.upper().strip()
        explanation = content.get("explanation", "")
        return is_correct, correct, explanation

    elif ex_type == "fill_blank":
        correct = content.get("blank_word", "")
        is_correct = user_answer.strip().lower() == correct.strip().lower()
        return is_correct, correct, f"The correct word is '{correct}'."

    elif ex_type == "flashcard":
        # Flashcards are always "correct" — they're for study, not grading
        return True, "", ""

    elif ex_type == "writing_prompt":
        # Writing prompts are self-assessed; mark as correct if submitted
        return True, "", "Writing submitted for self-review."

    return False, "", ""


def _persist_generated_lesson(
    db: Session,
    learner: LearnerProfile,
    payload: GenerateLessonRequest,
    lesson_data: dict,
) -> Lesson:
    """Persist validated agent output and return the new lesson."""
    lesson = Lesson(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        skill=payload.skill,
        topic=lesson_data.get("topic", payload.topic or "General"),
        level=learner.overall_level,
        title=lesson_data.get("title", "New Lesson"),
        summary=lesson_data.get("summary", ""),
        status="generated",
        total_exercises=len(lesson_data.get("exercises", [])),
    )
    db.add(lesson)
    db.flush()

    for ex_data in lesson_data.get("exercises", []):
        db.add(Exercise(
            id=str(uuid.uuid4()),
            lesson_id=lesson.id,
            order=ex_data.get("order", 0),
            type=ex_data.get("type", "multiple_choice"),
            content=ex_data.get("content", {}),
        ))

    if payload.skill == "vocabulary" and "vocabulary" in lesson_data:
        lesson.content = {"vocabulary": lesson_data["vocabulary"]}
    elif payload.skill in ("reading", "listening") and "passage" in lesson_data:
        lesson.content = lesson_data["passage"]

    return lesson


def _lesson_detail(lesson: Lesson) -> LessonDetailResponse:
    return LessonDetailResponse(
        id=lesson.id,
        skill=lesson.skill,
        topic=lesson.topic,
        level=lesson.level,
        title=lesson.title,
        summary=lesson.summary,
        content=lesson.content,
        status=lesson.status,
        score=lesson.score,
        xp_earned=lesson.xp_earned,
        total_exercises=lesson.total_exercises,
        correct_exercises=lesson.correct_exercises,
        exercises=[ExerciseSchema(
            id=exercise.id,
            order=exercise.order,
            type=exercise.type,
            content=exercise.content,
            user_answer=exercise.user_answer,
            is_correct=exercise.is_correct,
        ) for exercise in lesson.exercises],
        created_at=lesson.created_at,
        completed_at=lesson.completed_at,
    )


def _record_agent_trace(
    db: Session,
    learner_id: str,
    trace_id: str,
    result,
    input_data: dict,
) -> None:
    db.add(AgentTrace(
        trace_id=trace_id,
        learner_id=learner_id,
        agent=result.agent,
        status=result.status,
        duration_ms=result.duration_ms,
        error=result.error,
        input_data=input_data,
        eval_score=getattr(result, "eval_score", None),
        eval_flags=getattr(result, "eval_flags", None),
        eval_flagged=getattr(result, "eval_flagged", False),
        completed_at=result.completed_at,
    ))


def _run_lesson_generation_job(
    job_id: str,
    trace_id: str,
    learner_id: str,
    payload_data: dict,
) -> None:
    """Run lesson generation after the HTTP response has been returned."""
    db = SessionLocal()
    input_data = {"skill": payload_data["skill"], "topic": payload_data.get("topic")}
    try:
        update_job(db, job_id, "running")
        db.commit()
        learner = db.query(LearnerProfile).filter(LearnerProfile.id == learner_id).first()
        if not learner:
            raise ValueError("Learner profile not found")

        result = execute(AgentRequest(
            agent="lesson",
            trace_id=trace_id,
            payload={
                "skill": payload_data["skill"],
                "level": learner.overall_level,
                "topic": payload_data.get("topic"),
                "learner_age": learner.age,
            },
        ))
        _record_agent_trace(db, learner.id, trace_id, result, input_data)
        if result.status == "failed":
            update_job(
                db,
                job_id,
                "failed",
                error=result.error or "Lesson generation failed",
            )
            db.commit()
            return

        lesson = _persist_generated_lesson(db, learner, GenerateLessonRequest(**payload_data), result.data or {})
        # ── Link the generated lesson to the curriculum progress row ──
        curriculum_code = payload_data.get("curriculum_code")
        if curriculum_code:
            from app.models.curriculum import CurriculumLesson, LearnerCurriculumProgress
            curr_lesson = db.query(CurriculumLesson).filter(CurriculumLesson.code == curriculum_code).first()
            if curr_lesson:
                prog = db.query(LearnerCurriculumProgress).filter(
                    LearnerCurriculumProgress.learner_id == learner.id,
                    LearnerCurriculumProgress.curriculum_lesson_id == curr_lesson.id,
                ).first()
                if prog:
                    prog.generated_lesson_id = lesson.id
        update_job(db, job_id, "succeeded", result={"lesson_id": lesson.id})
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Background lesson generation failed: job_id=%s trace_id=%s", job_id, trace_id)
        try:
            update_job(db, job_id, "failed", error="Lesson generation failed")
            db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/generate", response_model=LessonDetailResponse | LessonGenerationAccepted)
def generate_new_lesson(
    payload: GenerateLessonRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI generates a new personalized lesson for the learner."""
    learner = _get_learner(db, current_user.id)

    if payload.skill not in ["vocabulary", "grammar", "reading", "listening"]:
        raise HTTPException(status_code=400, detail=f"Skill '{payload.skill}' not supported. Use: vocabulary, grammar, reading, listening.")

    # Free-tier daily lesson quota gate (premium is unlimited).
    from app.services.subscription_service import check_lesson_quota
    quota = check_lesson_quota(db, current_user.id, learner)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Bạn đã dùng hết {quota['limit']} bài học miễn phí hôm nay. "
                "Nâng cấp Premium để học không giới hạn."
            ),
        )

    # Content Factory: if this curriculum node has approved cached content,
    # serve a copy of it (no LLM call, stable + reviewed content).
    if payload.curriculum_code:
        from app.services.curriculum_content_service import materialize_lesson_for_learner
        cached_lesson = materialize_lesson_for_learner(db, learner, payload.curriculum_code)
        if cached_lesson is not None:
            # ── Link the cached lesson to the curriculum progress row ──
            from app.models.curriculum import CurriculumLesson, LearnerCurriculumProgress
            curr_lesson = db.query(CurriculumLesson).filter(CurriculumLesson.code == payload.curriculum_code).first()
            if curr_lesson:
                prog = db.query(LearnerCurriculumProgress).filter(
                    LearnerCurriculumProgress.learner_id == learner.id,
                    LearnerCurriculumProgress.curriculum_lesson_id == curr_lesson.id,
                ).first()
                if prog:
                    prog.generated_lesson_id = cached_lesson.id
            db.commit()
            db.refresh(cached_lesson)
            logger.info("Served cached content for %s to learner %s", payload.curriculum_code, learner.id)
            return _lesson_detail(cached_lesson)

    trace_id = str(uuid.uuid4())
    input_data = {"skill": payload.skill, "topic": payload.topic}

    if payload.background:
        job = create_job(db, trace_id, "lesson", learner.id)
        db.commit()
        response.status_code = 202
        payload_data = payload.model_dump(exclude={"background"})
        task_id = enqueue_lesson_generation(job["job_id"], trace_id, learner.id, payload_data)
        if not task_id:
            background_tasks.add_task(
                _run_lesson_generation_job,
                job["job_id"], trace_id, learner.id, payload_data,
            )
        return LessonGenerationAccepted(
            job_id=job["job_id"],
            trace_id=trace_id,
            status=job["status"],
            poll_url=f"/api/v1/lessons/generation-jobs/{job['job_id']}",
        )

    result = execute(AgentRequest(
        agent="lesson",
        trace_id=trace_id,
        payload={
            "skill": payload.skill,
            "level": learner.overall_level,
            "topic": payload.topic,
            "learner_age": learner.age,
        },
    ))
    _record_agent_trace(db, learner.id, trace_id, result, input_data)
    if result.status == "failed":
        db.commit()
        status_code = 429 if result.is_quota_error else 502
        raise HTTPException(status_code=status_code, detail=result.error or "AI Lesson generation failed")

    try:
        lesson = _persist_generated_lesson(db, learner, payload, result.data or {})
        # ── Link the generated lesson to the curriculum progress row ──
        if payload.curriculum_code:
            from app.models.curriculum import CurriculumLesson, LearnerCurriculumProgress
            curr_lesson = db.query(CurriculumLesson).filter(CurriculumLesson.code == payload.curriculum_code).first()
            if curr_lesson:
                prog = db.query(LearnerCurriculumProgress).filter(
                    LearnerCurriculumProgress.learner_id == learner.id,
                    LearnerCurriculumProgress.curriculum_lesson_id == curr_lesson.id,
                ).first()
                if prog:
                    prog.generated_lesson_id = lesson.id
        db.commit()
        db.refresh(lesson)
        return _lesson_detail(lesson)
    except Exception:
        db.rollback()
        logger.exception("Lesson persistence failed: trace_id=%s", trace_id)
        raise HTTPException(status_code=500, detail="Lesson could not be saved")


@router.get("/generation-jobs/{job_id}", response_model=LessonGenerationJobResponse)
def get_lesson_generation_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll an asynchronous lesson generation job owned by the current learner."""
    learner = _get_learner(db, current_user.id)
    job = get_job(db, job_id)
    if not job or job.get("learner_id") != learner.id:
        raise HTTPException(status_code=404, detail="Generation job not found")

    return LessonGenerationJobResponse(
        job_id=job["job_id"],
        trace_id=job["trace_id"],
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@router.get("/me", response_model=list[LessonSummaryResponse])
def get_my_lessons(
    limit: int = 20,
    skill: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the learner's lesson history."""
    learner = _get_learner(db, current_user.id)
    query = db.query(Lesson).filter(Lesson.learner_id == learner.id)
    if skill:
        query = query.filter(Lesson.skill == skill)
    lessons = query.order_by(Lesson.created_at.desc()).limit(limit).all()

    return [
        LessonSummaryResponse(
            id=l.id, skill=l.skill, topic=l.topic, level=l.level,
            title=l.title, status=l.status, score=l.score,
            xp_earned=l.xp_earned, created_at=l.created_at,
        )
        for l in lessons
    ]


@router.get("/daily", response_model=list[DailyRecommendation])
def get_daily_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get today's recommended lessons based on learner's weak skills."""
    learner = _get_learner(db, current_user.id)

    # Prioritize weak skills
    skills_ranked = sorted([
        ("vocabulary", learner.vocabulary_score or 0),
        ("grammar",    learner.grammar_score or 0),
        ("reading",    learner.reading_score or 0),
        ("listening",  learner.listening_score or 0),
    ], key=lambda x: x[1])  # weakest first

    import random
    SKILL_ICONS = {"vocabulary": "📚", "grammar": "📝", "reading": "📖", "listening": "🎧"}
    REASONS = {
        "vocabulary": "Mở rộng vốn từ giúp bạn giao tiếp tự nhiên hơn",
        "grammar":    "Ngữ pháp vững chắc giúp câu văn chính xác hơn",
        "reading":    "Đọc hiểu tốt giúp bạn học nhanh hơn",
        "listening":  "Nghe hiểu giúp bạn tự tin giao tiếp thực tế",
    }

    recs = []
    for skill, score in skills_ranked[:3]:
        topics = TOPIC_BANK.get(skill, ["General English"])
        recs.append(DailyRecommendation(
            skill=skill,
            topic=random.choice(topics),
            reason=REASONS.get(skill, "Luyện tập đều đặn"),
            icon=SKILL_ICONS.get(skill, "📌"),
        ))
    return recs


@router.get("/{lesson_id}", response_model=LessonDetailResponse)
def get_lesson_detail(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full lesson details including all exercises."""
    learner = _get_learner(db, current_user.id)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.learner_id == learner.id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")

    # Mark as in_progress if not started
    if lesson.status == "generated":
        lesson.status = "in_progress"
        lesson.started_at = datetime.now(timezone.utc)
        db.commit()

    return LessonDetailResponse(
        id=lesson.id, skill=lesson.skill, topic=lesson.topic, level=lesson.level,
        title=lesson.title, summary=lesson.summary, content=lesson.content, status=lesson.status,
        score=lesson.score, xp_earned=lesson.xp_earned,
        total_exercises=lesson.total_exercises, correct_exercises=lesson.correct_exercises,
        exercises=[
            ExerciseSchema(id=e.id, order=e.order, type=e.type, content=e.content,
                           user_answer=e.user_answer, is_correct=e.is_correct)
            for e in lesson.exercises
        ],
        created_at=lesson.created_at, completed_at=lesson.completed_at,
    )


@router.post("/{lesson_id}/submit-exercise", response_model=SubmitExerciseResponse)
def submit_exercise_answer(
    lesson_id: str,
    payload: SubmitExercisePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit an answer for a single exercise and get immediate feedback."""
    learner = _get_learner(db, current_user.id)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.learner_id == learner.id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")

    exercise = db.query(Exercise).filter(Exercise.id == payload.exercise_id, Exercise.lesson_id == lesson_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found.")

    is_correct, correct_answer, explanation = _check_exercise_answer(exercise, payload.answer)

    exercise.user_answer = payload.answer
    exercise.is_correct = is_correct
    exercise.answered_at = datetime.now(timezone.utc)

    # ── Golden Data: record a per-exercise LearningEvent (Master Plan §30) ──
    # Flashcards are study-only, not graded → skip event to avoid skewing analytics.
    if exercise.type != "flashcard":
        error_type = None
        if not is_correct:
            error_type = f"{exercise.type}_incorrect"
        db.add(LearningEvent(
            id=str(uuid.uuid4()),
            learner_id=learner.id,
            lesson_id=lesson_id,
            activity_id=exercise.id,
            event_type="exercise_answered",
            skill=lesson.skill,
            topic=lesson.topic,
            activity_type=exercise.type,
            correct=is_correct,
            score=100.0 if is_correct else 0.0,
            difficulty=payload.difficulty,
            error_type=error_type,
            duration_seconds=payload.duration_seconds,
            extra_data={"exercise_order": exercise.order},
        ))

    db.commit()

    return SubmitExerciseResponse(
        exercise_id=exercise.id,
        is_correct=is_correct,
        correct_answer=correct_answer if not is_correct else None,
        explanation=explanation if explanation else None,
    )


@router.post("/{lesson_id}/finish", response_model=FinishLessonResponse)
def finish_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Finalize lesson, compute score, award XP, and update learner profile."""
    learner = _get_learner(db, current_user.id)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.learner_id == learner.id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")
    if lesson.status == "completed":
        raise HTTPException(status_code=400, detail="This lesson is already completed.")

    # Collect answered exercises
    answered = [
        {"is_correct": e.is_correct, "type": e.type}
        for e in lesson.exercises
        if e.user_answer is not None and e.type != "flashcard"
    ]

    result = compute_lesson_score(answered)

    # Update Lesson
    lesson.status = "completed"
    lesson.score = result["score"]
    lesson.xp_earned = result["xp_earned"]
    lesson.correct_exercises = result["correct"]
    lesson.completed_at = datetime.now(timezone.utc)

    # Update LearnerProfile XP & skill score
    learner.total_xp += result["xp_earned"]
    learner.total_lessons_completed += 1

    skill_field_map = {
        "vocabulary": "vocabulary_score",
        "grammar":    "grammar_score",
        "reading":    "reading_score",
        "writing":    "writing_score",
        "listening":  "listening_score",
    }
    field = skill_field_map.get(lesson.skill)
    if field:
        current = getattr(learner, field, 0) or 0
        # Exponential moving average: 80% old + 20% new
        new_score = round(current * 0.8 + result["score"] * 0.2, 1)
        setattr(learner, field, new_score)

    # ── Adaptive Engine: decide next pedagogical action (Master Plan §6) ──
    correct_ratio = (result["correct"] / result["total"]) if result["total"] else 0.0
    # Look at recent same-skill lesson scores (newest first) to detect failure streaks
    recent_scores = [
        ev.score for ev in db.query(LearningEvent)
        .filter(
            LearningEvent.learner_id == learner.id,
            LearningEvent.skill == lesson.skill,
            LearningEvent.event_type == "lesson_completed",
            LearningEvent.score.isnot(None),
        )
        .order_by(LearningEvent.recorded_at.desc())
        .limit(5)
        .all()
    ]
    prev_score = recent_scores[0] if recent_scores else None
    consecutive_failures = compute_consecutive_failures(recent_scores)

    adaptive = adaptive_decide(AdaptiveInput(
        score=result["score"],
        skill=lesson.skill,
        difficulty=1,
        correct_ratio=correct_ratio,
        consecutive_failures=consecutive_failures,
        prev_score=prev_score,
    ))

    # ── Record enriched LearningEvent (Golden Data) ──
    event = LearningEvent(
        id=str(uuid.uuid4()),
        learner_id=learner.id,
        lesson_id=lesson_id,
        event_type="lesson_completed",
        skill=lesson.skill,
        topic=lesson.topic,
        activity_type="lesson",
        correct=(result["score"] >= 60),
        score=result["score"],
        xp_earned=result["xp_earned"],
        difficulty=1,
        duration_seconds=None,
        adaptive_decision=adaptive.decision.value,
        extra_data={
            "grade": result["grade"],
            "correct": result["correct"],
            "total": result["total"],
            "recommended_difficulty": adaptive.recommended_difficulty,
            "adaptive_reason": adaptive.reason_vi,
        },
    )
    db.add(event)

    # ── Update curriculum progress if this lesson maps to a curriculum node ──
    _update_curriculum_progress(db, learner.id, lesson, result["score"])

    # Update streak and daily challenge progress
    record_activity(learner, lesson.skill, db)

    db.commit()

    grade_messages = {
        "S": "🌟 Xuất sắc! Bạn thật tuyệt vời!",
        "A": "🎉 Tốt lắm! Cố gắng tiếp tục nhé!",
        "B": "👍 Khá tốt! Ôn lại một chút nữa nhé!",
        "C": "💪 Cố lên! Hãy ôn lại bài này!",
        "D": "📚 Hãy học lại bài này để củng cố kiến thức!",
    }

    return FinishLessonResponse(
        lesson_id=lesson_id,
        score=result["score"],
        grade=result["grade"],
        correct=result["correct"],
        total=result["total"],
        xp_earned=result["xp_earned"],
        message=grade_messages.get(result["grade"], "Hoàn thành bài học!"),
        adaptive_decision=adaptive.decision.value,
        adaptive_reason=adaptive.reason_vi,
        recommended_difficulty=adaptive.recommended_difficulty,
    )


# ── Utility ───────────────────────────────────────────────────────────────────
def json_safe(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)
