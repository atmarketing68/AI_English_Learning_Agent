"""Database-backed state for asynchronous agent jobs."""
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.agent_job import AgentJob

JobStatus = Literal["queued", "running", "succeeded", "failed"]


def _as_dict(job: AgentJob) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "trace_id": job.trace_id,
        "agent": job.agent,
        "learner_id": job.learner_id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def create_job(db: Session, trace_id: str, agent: str, learner_id: str) -> dict[str, Any]:
    job = AgentJob(
        job_id=str(uuid4()),
        trace_id=trace_id,
        agent=agent,
        learner_id=learner_id,
        status="queued",
    )
    db.add(job)
    db.flush()
    return _as_dict(job)


def update_job(
    db: Session,
    job_id: str,
    status: JobStatus,
    *,
    result: Any = None,
    error: str | None = None,
) -> None:
    job = db.query(AgentJob).filter(AgentJob.job_id == job_id).first()
    if job:
        job.status = status
        job.result = result
        job.error = error
        job.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.flush()


def get_job(db: Session, job_id: str) -> dict[str, Any] | None:
    job = db.query(AgentJob).filter(AgentJob.job_id == job_id).first()
    return _as_dict(job) if job else None
