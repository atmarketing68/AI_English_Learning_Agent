"""Tests for the Content Factory: pre-generate + cache + materialize curriculum
content, plus the learner flow serving cached content without an LLM call.
"""
import dataclasses

import pytest

from app.agents import orchestrator
from app.models.curriculum_content import (
    STATUS_APPROVED, STATUS_DRAFT, CurriculumLessonContent,
)
from app.models.lesson import Lesson
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import curriculum_content_service as ccs
from app.services.curriculum_seed import seed_curriculum

API = "/api/v1"

# A valid lesson payload the fake agent returns (so no real LLM is called).
FAKE_LESSON = {
    "title": "Past Simple Basics",
    "summary": "Học thì quá khứ đơn.",
    "skill": "grammar",
    "level": "A2",
    "exercises": [
        {"type": "multiple_choice", "order": 0, "content": {
            "question": "She ___ to school yesterday.",
            "options": {"A": "go", "B": "went", "C": "goes", "D": "going"},
            "correct_answer": "B", "explanation": "Past simple of go is went.",
        }},
        {"type": "multiple_choice", "order": 1, "content": {
            "question": "They ___ football last week.",
            "options": {"A": "played", "B": "play", "C": "plays", "D": "playing"},
            "correct_answer": "A", "explanation": "Regular past -ed.",
        }},
        {"type": "multiple_choice", "order": 2, "content": {
            "question": "I ___ a film last night.",
            "options": {"A": "watch", "B": "watches", "C": "watched", "D": "watching"},
            "correct_answer": "C", "explanation": "Regular past -ed.",
        }},
    ],
}


@pytest.fixture()
def fake_lesson_agent(monkeypatch):
    """Swap the 'lesson' agent handler so no real LLM is called."""
    spec = orchestrator.AGENT_SPECS["lesson"]
    new_spec = dataclasses.replace(spec, handler=lambda **kw: dict(FAKE_LESSON))
    patched = dict(orchestrator.AGENT_SPECS)
    patched["lesson"] = new_spec
    monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)


@pytest.fixture()
def seeded(db_session):
    seed_curriculum(db_session)
    db_session.commit()


def _learner(db_session, email="cc@example.com"):
    user = User(email=email, hashed_password="x", full_name="U")
    db_session.add(user)
    db_session.flush()
    learner = LearnerProfile(user_id=user.id, display_name="L", overall_level="A2")
    db_session.add(learner)
    db_session.flush()
    return user, learner


# ── generate_and_cache ────────────────────────────────────────────────────────
def test_generate_and_cache_creates_draft(db_session, seeded, fake_lesson_agent):
    row = ccs.generate_and_cache(db_session, "A2-U01-L01")
    db_session.commit()
    assert row.curriculum_code == "A2-U01-L01"
    assert row.status == STATUS_DRAFT
    assert row.total_exercises == 3
    assert row.eval_score is not None  # quality gate ran


def test_generate_auto_approve(db_session, seeded, fake_lesson_agent):
    row = ccs.generate_and_cache(db_session, "A2-U01-L01", auto_approve=True)
    db_session.commit()
    assert row.status == STATUS_APPROVED
    assert row.approved_at is not None


def test_generate_is_idempotent_without_force(db_session, seeded, fake_lesson_agent):
    r1 = ccs.generate_and_cache(db_session, "A2-U01-L01")
    db_session.commit()
    created_at = r1.created_at
    r2 = ccs.generate_and_cache(db_session, "A2-U01-L01")  # returns existing
    assert r2.created_at == created_at
    assert db_session.query(CurriculumLessonContent).count() == 1


def test_generate_rejects_non_lesson_skill(db_session, seeded, fake_lesson_agent):
    # A2-U01-L04 is a speaking node → not pre-generatable.
    with pytest.raises(ccs.ContentGenerationError):
        ccs.generate_and_cache(db_session, "A2-U01-L04")


# ── materialize ────────────────────────────────────────────────────────────────
def test_materialize_requires_approved(db_session, seeded, fake_lesson_agent):
    ccs.generate_and_cache(db_session, "A2-U01-L01")  # draft
    db_session.commit()
    _, learner = _learner(db_session)
    # Draft content is not served.
    assert ccs.materialize_lesson_for_learner(db_session, learner, "A2-U01-L01") is None


def test_materialize_creates_lesson_from_approved(db_session, seeded, fake_lesson_agent):
    ccs.generate_and_cache(db_session, "A2-U01-L01", auto_approve=True)
    db_session.commit()
    _, learner = _learner(db_session, "cc2@example.com")
    lesson = ccs.materialize_lesson_for_learner(db_session, learner, "A2-U01-L01")
    db_session.commit()
    assert isinstance(lesson, Lesson)
    assert lesson.learner_id == learner.id
    assert lesson.title == FAKE_LESSON["title"]
    assert lesson.total_exercises == 3
    assert len(lesson.exercises) == 3


def test_materialize_no_cache_returns_none(db_session, seeded):
    _, learner = _learner(db_session, "cc3@example.com")
    assert ccs.materialize_lesson_for_learner(db_session, learner, "A2-U01-L01") is None


# ── set_status ──────────────────────────────────────────────────────────────────
def test_approve_then_reject(db_session, seeded, fake_lesson_agent):
    ccs.generate_and_cache(db_session, "A2-U01-L01")
    db_session.commit()
    ccs.set_status(db_session, "A2-U01-L01", STATUS_APPROVED)
    db_session.commit()
    row = ccs.get_cached_content(db_session, "A2-U01-L01")
    assert row.status == STATUS_APPROVED and row.approved_at is not None
    ccs.set_status(db_session, "A2-U01-L01", "rejected")
    db_session.commit()
    row = ccs.get_cached_content(db_session, "A2-U01-L01")
    assert row.status == "rejected" and row.approved_at is None


# ── batch ────────────────────────────────────────────────────────────────────────
def test_batch_generate_level(db_session, seeded, fake_lesson_agent):
    summary = ccs.batch_generate_level(db_session, "A2", auto_approve=True, limit=3)
    assert summary["generated"] == 3
    assert summary["failed"] == 0


# ── Learner flow via API: cached content served without LLM ─────────────────────
def test_generate_endpoint_serves_cache(client, db_session, seeded, fake_lesson_agent, monkeypatch):
    # Pre-generate + approve content for a node.
    ccs.generate_and_cache(db_session, "A2-U01-L01", auto_approve=True)
    db_session.commit()

    # Register a learner at A2.
    client.post(f"{API}/auth/register", json={
        "email": "flow@example.com", "password": "Strong123",
        "full_name": "F", "display_name": "F", "role": "learner", "age": 15,
    })
    token = client.post(f"{API}/auth/login", data={"username": "flow@example.com", "password": "Strong123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure that if the code path tried to call the live agent it would fail loudly,
    # proving the cache path is used (no LLM). Break the lesson handler:
    def _boom(**kw):
        raise AssertionError("LLM should NOT be called when cache exists")
    spec = orchestrator.AGENT_SPECS["lesson"]
    monkeypatch.setattr(orchestrator, "AGENT_SPECS", {**orchestrator.AGENT_SPECS, "lesson": dataclasses.replace(spec, handler=_boom)})

    resp = client.post(f"{API}/lessons/generate", json={
        "skill": "grammar", "topic": "Past Simple Tense",
        "curriculum_code": "A2-U01-L01", "background": False,
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == FAKE_LESSON["title"]
    assert resp.json()["total_exercises"] == 3
