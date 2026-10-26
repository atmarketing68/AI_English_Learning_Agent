"""Shared helper to persist an AgentExecutionResult as an AgentTrace row.

Centralises trace + AI-evaluation persistence so every API that runs an agent
through the orchestrator records the same fields (including eval_score /
eval_flags / eval_flagged from the AI Evaluation Framework, Master Plan §29).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.agent_trace import AgentTrace


def record_agent_trace(
    db: Session,
    learner_id: str | None,
    trace_id: str,
    result,
    input_data: dict,
) -> None:
    """Persist an orchestrator result as an AgentTrace (caller commits)."""
    db.add(
        AgentTrace(
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
        )
    )
