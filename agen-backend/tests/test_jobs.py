from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.agent_jobs import create_job, get_job, update_job


def test_agent_job_lifecycle():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        job = create_job(session, "trace-test", "lesson", "learner-test")
        session.commit()
        assert job["status"] == "queued"

        update_job(session, job["job_id"], "running")
        session.commit()
        assert get_job(session, job["job_id"])["status"] == "running"

        update_job(session, job["job_id"], "succeeded", result={"lesson_id": "lesson-test"})
        session.commit()
        saved = get_job(session, job["job_id"])
        assert saved["status"] == "succeeded"
        assert saved["result"] == {"lesson_id": "lesson-test"}
    finally:
        session.close()
        engine.dispose()
