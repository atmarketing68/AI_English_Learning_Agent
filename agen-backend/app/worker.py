"""Celery application and task entry points for distributed agent execution."""
from app.core.config import settings

Celery = None
if settings.WORKER_MODE == "distributed" and settings.REDIS_URL:
    try:
        from celery import Celery
    except ImportError:  # Development can use the local FastAPI fallback.
        Celery = None  # type: ignore[assignment,misc]

if Celery is not None:
    celery_app = Celery(
        "agen",
        broker=settings.REDIS_URL or "redis://localhost:6379/0",
        backend=settings.REDIS_URL or "redis://localhost:6379/1",
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        result_expires=86400,
    )

    @celery_app.task(
        bind=True,
        autoretry_for=(TimeoutError, ConnectionError),
        retry_backoff=True,
        retry_kwargs={"max_retries": 3},
    )
    def run_lesson_generation(self, job_id: str, trace_id: str, learner_id: str, payload_data: dict) -> None:
        from app.api.lessons import _run_lesson_generation_job

        _run_lesson_generation_job(job_id, trace_id, learner_id, payload_data)
else:
    celery_app = None
    run_lesson_generation = None


def enqueue_lesson_generation(job_id: str, trace_id: str, learner_id: str, payload_data: dict) -> str | None:
    """Queue a job when distributed mode is enabled; return broker task id."""
    if settings.WORKER_MODE != "distributed" or not settings.REDIS_URL or run_lesson_generation is None:
        return None
    task = run_lesson_generation.delay(job_id, trace_id, learner_id, payload_data)
    return task.id