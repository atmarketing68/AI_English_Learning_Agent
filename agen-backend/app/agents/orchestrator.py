"""Deterministic orchestration boundary for AGEN agents."""
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import time
from typing import Any, Callable, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.agents import adaptive_coach, assessment_agent, club_agent, exam_agent, lesson_agent, podcast_agent, speaking_agent, speaking_exam_agent, tutor_agent, writing_agent
from app.agents.contracts import (
    ClubModeratorOutput,
    CoachAdviceOutput,
    GeneratedExamOutput,
    LessonOutput,
    PlacementQuestionOutput,
    PodcastEpisodeOutput,
    RoleplayScenarioOutput,
    SpeakingExamEvaluationOutput,
    SpeakingTurnOutput,
    TutorAnswerOutput,
    WeeklyReportOutput,
    WritingEvaluationOutput,
    WritingPromptOutput,
)

logger = logging.getLogger("agen.orchestrator")

AgentName = Literal[
    "lesson",
    "coach_advice",
    "weekly_report",
    "placement_question",
    "roleplay_scenario",
    "speaking_turn",
    "writing_prompt",
    "writing_evaluation",
    "tutor_answer",
    "speaking_exam_evaluation",
    "exam_generation",
    "club_moderator",
    "podcast_generation",
]


class AgentRequest(BaseModel):
    agent: AgentName
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: str = Field(default_factory=lambda: str(uuid4()))


class AgentExecutionResult(BaseModel):
    trace_id: str
    agent: AgentName
    status: Literal["succeeded", "failed"]
    data: dict[str, Any] | None = None
    error: str | None = None
    is_quota_error: bool = False   # True when failure is due to LLM quota exhaustion
    # ── AI Evaluation Framework (Master Plan §29) ──
    eval_score: float | None = None
    eval_flags: list[str] | None = None
    eval_flagged: bool = False
    duration_ms: float
    completed_at: datetime


@dataclass(frozen=True)
class AgentSpec:
    handler: Callable[..., dict[str, Any]]
    output_model: type[BaseModel]


AGENT_SPECS: dict[AgentName, AgentSpec] = {
    "lesson": AgentSpec(lesson_agent.generate_lesson, LessonOutput),
    "coach_advice": AgentSpec(adaptive_coach.analyze_learner, CoachAdviceOutput),
    "weekly_report": AgentSpec(adaptive_coach.generate_weekly_report, WeeklyReportOutput),
    "placement_question": AgentSpec(assessment_agent.generate_placement_question, PlacementQuestionOutput),
    "roleplay_scenario": AgentSpec(speaking_agent.generate_roleplay_scenario, RoleplayScenarioOutput),
    "speaking_turn": AgentSpec(speaking_agent.evaluate_speaking_turn, SpeakingTurnOutput),
    "writing_prompt": AgentSpec(writing_agent.generate_writing_prompt, WritingPromptOutput),
    "writing_evaluation": AgentSpec(writing_agent.evaluate_writing, WritingEvaluationOutput),
    "tutor_answer": AgentSpec(tutor_agent.answer_question, TutorAnswerOutput),
    "speaking_exam_evaluation": AgentSpec(speaking_exam_agent.evaluate_speaking_exam, SpeakingExamEvaluationOutput),
    "exam_generation": AgentSpec(exam_agent.generate_exam, GeneratedExamOutput),
    "club_moderator": AgentSpec(club_agent.moderate_turn, ClubModeratorOutput),
    "podcast_generation": AgentSpec(podcast_agent.generate_episode, PodcastEpisodeOutput),
}


def execute(request: AgentRequest) -> AgentExecutionResult:
    """Execute one registered agent and return a traceable, validated result.

    Payload keys intentionally map to the existing agent function signatures.
    The orchestrator does not expose provider errors or prompt contents to callers.
    """
    started = time.perf_counter()
    spec = AGENT_SPECS[request.agent]
    from app.core.usage_context import current_feature
    feature_token = current_feature.set(request.agent)   # G10 · AI cost per feature

    try:
        raw_result = spec.handler(**request.payload)
        validated = spec.output_model.model_validate(raw_result).model_dump(exclude_none=True)

        # ── Quality gate: evaluate the validated output (fail-open, always logged) ──
        from app.services.evaluation_service import evaluate_output
        expected = {
            k: request.payload.get(k)
            for k in ("skill", "level")
            if request.payload.get(k) is not None
        }
        try:
            evaluation = evaluate_output(request.agent, validated, expected or None)
            eval_score = evaluation.overall_score
            eval_flags = evaluation.flags
            eval_flagged = evaluation.flagged
            if eval_flagged:
                logger.warning(
                    "AI output flagged: agent=%s trace_id=%s score=%.1f flags=%s",
                    request.agent, request.trace_id, eval_score, eval_flags,
                )
        except Exception:
            # Evaluation must never break delivery
            logger.exception("Evaluation failed (non-blocking): trace_id=%s", request.trace_id)
            eval_score, eval_flags, eval_flagged = None, None, False

        return AgentExecutionResult(
            trace_id=request.trace_id,
            agent=request.agent,
            status="succeeded",
            data=validated,
            eval_score=eval_score,
            eval_flags=eval_flags,
            eval_flagged=eval_flagged,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
            completed_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.exception("Agent execution failed: agent=%s trace_id=%s", request.agent, request.trace_id)
        from app.services.llm_client import LLMError
        is_quota = isinstance(exc, LLMError) and exc.is_quota_error
        return AgentExecutionResult(
            trace_id=request.trace_id,
            agent=request.agent,
            status="failed",
            error=str(exc) if isinstance(exc, LLMError) else f"{type(exc).__name__}: agent execution failed",
            is_quota_error=is_quota,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
            completed_at=datetime.now(timezone.utc),
        )
    finally:
        current_feature.reset(feature_token)
