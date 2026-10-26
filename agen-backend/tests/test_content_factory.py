"""Scheduled Content Factory runs and instant free-practice lessons."""
from types import SimpleNamespace

import app.services.curriculum_content_service as factory
from app.core.config import settings
from app.models.curriculum import CurriculumLesson
from app.models.curriculum_content import STATUS_APPROVED, STATUS_DRAFT, CurriculumLessonContent
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services.curriculum_seed import seed_curriculum

API = "/api/v1"


def _fake_execute(flagged_codes=(), fail_with=None):
    calls = []

    def execute(request):
        calls.append(request.payload)
        if fail_with:
            return SimpleNamespace(status="failed", data=None, error=fail_with)
        topic = request.payload["topic"]
        return SimpleNamespace(
            status="succeeded",
            data={"title": f"Lesson {topic}", "summary": "s", "topic": topic,
                  "exercises": [{"type": "multiple_choice", "order": 0,
                                 "content": {"question": "q", "options": {"A": "a", "B": "b"}, "correct_answer": "A"}}]},
            error=None,
            eval_score=90.0,
            eval_flagged=topic in flagged_codes,
            eval_flags=None,
        )
    return execute, calls


def _lesson_nodes(db, level):
    return (
        db.query(CurriculumLesson)
        .filter(CurriculumLesson.cefr_reference == level, CurriculumLesson.skill.in_(factory.LESSON_SKILLS))
        .order_by(CurriculumLesson.code)
        .all()
    )


def test_generates_next_missing_nodes_in_roadmap_order(db_session, monkeypatch):
    seed_curriculum(db_session)
    a1 = _lesson_nodes(db_session, "A1")
    flagged_topic = a1[1].topic
    execute, calls = _fake_execute(flagged_codes={flagged_topic})
    monkeypatch.setattr(factory, "execute", execute)

    summary = factory.generate_missing_content(db_session, limit=3)
    assert summary["generated"] == 3 and summary["approved"] == 2 and summary["flagged"] == 1
    assert [c["topic"] for c in calls] == [n.topic for n in a1[:3]]
    statuses = {r.curriculum_code: r.status for r in db_session.query(CurriculumLessonContent).all()}
    assert statuses[a1[0].code] == STATUS_APPROVED and statuses[a1[1].code] == STATUS_DRAFT

    total = sum(len(_lesson_nodes(db_session, lvl)) for lvl in factory.FACTORY_LEVELS)
    assert summary["remaining"] == total - 3
    # The next run continues where this one stopped.
    factory.generate_missing_content(db_session, limit=2)
    assert calls[3]["topic"] == a1[3].topic

    coverage = {c["level"]: c for c in factory.content_coverage(db_session)}
    assert coverage["A1"]["approved"] == 4 and coverage["A1"]["draft"] == 1


def test_quota_error_stops_the_batch(db_session, monkeypatch):
    seed_curriculum(db_session)
    execute, calls = _fake_execute(fail_with="Hệ thống AI đang bận hoặc đã hết giới hạn sử dụng hôm nay.")
    monkeypatch.setattr(factory, "execute", execute)
    summary = factory.generate_missing_content(db_session, limit=5)
    assert summary["failed"] == 1 and len(calls) == 1
    assert db_session.query(CurriculumLessonContent).count() == 0


def test_cron_endpoint_requires_secret(client, db_session, monkeypatch):
    seed_curriculum(db_session)          # done at app startup in production
    db_session.commit()
    execute, calls = _fake_execute()
    monkeypatch.setattr(factory, "execute", execute)
    assert client.post(f"{API}/admin/content/cron").status_code == 403
    monkeypatch.setattr(settings, "CRON_SECRET", "")
    monkeypatch.setattr(settings, "REMINDER_CRON_SECRET", "shared")   # one secret for every scheduled job
    assert client.post(f"{API}/admin/content/cron", headers={"X-Cron-Secret": "x"}).status_code == 403
    res = client.post(f"{API}/admin/content/cron?limit=2", headers={"X-Cron-Secret": "shared"})
    assert res.status_code == 200
    body = res.json()
    assert body["generated"] == 2 and len(calls) == 2
    assert [c["level"] for c in body["coverage"]] == ["A1", "A2", "B1"]


def _register(client, email):
    client.post(f"{API}/auth/register", json={
        "email": email, "password": "Strong123", "full_name": "P", "display_name": "P", "role": "learner",
    })
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Strong123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_free_practice_is_served_from_cache_instantly(client, db_session, monkeypatch):
    email = "practice@example.com"
    headers = _register(client, email)
    learner = db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id).filter(User.email == email).one()
    assert learner.overall_level == "PRE_A1"              # practises with A1 content
    seed_curriculum(db_session)

    vocab = [n for n in _lesson_nodes(db_session, "A1") if n.skill == "vocabulary"][:2]
    for node in vocab:
        db_session.add(CurriculumLessonContent(
            curriculum_code=node.code, level="A1", skill="vocabulary", topic=node.topic,
            content={"title": f"Cached {node.topic}", "summary": "s", "exercises": [
                {"type": "flashcard", "order": 0, "content": {"word": "w", "definition": "d", "translation": "t", "example": "e"}},
            ]},
            total_exercises=1, status=STATUS_APPROVED,
        ))
    db_session.commit()

    def no_llm(*args, **kwargs):
        raise AssertionError("practice should not call the AI while cached lessons remain")

    monkeypatch.setattr("app.api.lessons.execute", no_llm)
    # The live-generation fallback is queued as a background job; don't run it here.
    monkeypatch.setattr("app.api.lessons._run_lesson_generation_job", lambda *a, **k: None)
    first = client.post(f"{API}/lessons/generate", headers=headers, json={"skill": "vocabulary", "background": True})
    assert first.status_code == 200 and first.json()["title"].startswith("Cached ")
    second = client.post(f"{API}/lessons/generate", headers=headers, json={"skill": "vocabulary", "background": True})
    assert second.status_code == 200
    assert second.json()["topic"] != first.json()["topic"]      # a topic not studied yet

    # Both cached topics done → falls back to live generation (queued job).
    third = client.post(f"{API}/lessons/generate", headers=headers, json={"skill": "vocabulary", "background": True})
    assert third.status_code == 202
