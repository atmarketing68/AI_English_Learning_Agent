"""Tests for placement credit: a learner placed above A1 must not be locked out
of their level's curriculum roadmap.

Unit tests exercise grant_placement_credit directly; the integration test drives
POST /placement/finish (with a pre-seeded session, no LLM) and asserts the A2
roadmap unlocks afterwards.
"""
from datetime import datetime, timezone

import pytest

from app.models.curriculum import CurriculumLesson, CurriculumUnit, LearnerCurriculumProgress
from app.models.learner_profile import LearnerProfile
from app.models.placement import PlacementSession
from app.models.user import User
from app.services.curriculum_seed import seed_curriculum
from app.services.placement_credit import grant_placement_credit

API = "/api/v1"


def _make_learner(db_session, email="pc@example.com"):
    user = User(email=email, hashed_password="x", full_name="U")
    db_session.add(user)
    db_session.flush()
    learner = LearnerProfile(user_id=user.id, display_name="L")
    db_session.add(learner)
    db_session.flush()
    return user, learner


def _mastered_codes(db_session, learner_id):
    rows = (
        db_session.query(CurriculumLesson.code)
        .join(LearnerCurriculumProgress,
              LearnerCurriculumProgress.curriculum_lesson_id == CurriculumLesson.id)
        .filter(
            LearnerCurriculumProgress.learner_id == learner_id,
            LearnerCurriculumProgress.mastered.is_(True),
        )
        .all()
    )
    return {r[0] for r in rows}


# ── Unit tests: grant_placement_credit ───────────────────────────────────────
def test_a2_placement_credits_all_a1(db_session):
    seed_curriculum(db_session)
    _, learner = _make_learner(db_session)
    credited = grant_placement_credit(db_session, learner, "A2")
    db_session.flush()

    mastered = _mastered_codes(db_session, learner.id)
    assert credited == 30                       # all 30 A1 lessons
    assert "A1-U06-L05" in mastered             # the A2 gate lesson
    assert all(c.startswith("A1-") for c in mastered)
    assert not any(c.startswith("A2-") for c in mastered)  # A2 not credited


def test_b1_placement_credits_a1_and_a2(db_session):
    seed_curriculum(db_session)
    _, learner = _make_learner(db_session, "pc_b1@example.com")
    credited = grant_placement_credit(db_session, learner, "B1")
    db_session.flush()

    mastered = _mastered_codes(db_session, learner.id)
    assert credited == 60                       # all A1 + A2 lessons
    assert "A1-U06-L05" in mastered
    assert "A2-U06-L05" in mastered


def test_a1_placement_credits_nothing(db_session):
    seed_curriculum(db_session)
    _, learner = _make_learner(db_session, "pc_a1@example.com")
    credited = grant_placement_credit(db_session, learner, "A1")
    assert credited == 0
    assert _mastered_codes(db_session, learner.id) == set()


def test_pre_a1_placement_credits_nothing(db_session):
    seed_curriculum(db_session)
    _, learner = _make_learner(db_session, "pc_pre@example.com")
    credited = grant_placement_credit(db_session, learner, "PRE_A1")
    assert credited == 0


def test_credit_is_idempotent(db_session):
    seed_curriculum(db_session)
    _, learner = _make_learner(db_session, "pc_idem@example.com")
    first = grant_placement_credit(db_session, learner, "A2")
    db_session.flush()
    second = grant_placement_credit(db_session, learner, "A2")
    assert first == 30
    assert second == 0                          # nothing new to credit


# ── Integration: finish placement unlocks the placed level ────────────────────
def _register_login(client, email="pcint@example.com"):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "P", "display_name": "P", "role": "learner", "age": 15,
        },
    )
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_finish_placement_unlocks_a2_roadmap(client, db_session):
    # Curriculum must exist in the same DB the client uses.
    seed_curriculum(db_session)
    db_session.commit()

    headers = _register_login(client)

    # Find the learner created by registration.
    learner = (
        db_session.query(LearnerProfile)
        .join(User, User.id == LearnerProfile.user_id)
        .filter(User.email == "pcint@example.com")
        .first()
    )
    assert learner is not None

    # Seed a COMPLETED-answers placement session that maps to A2 (ratio ~0.5).
    # 5 correct of 10 → ratio 0.5 → A2 per calculate_final_result thresholds.
    answers = []
    for i in range(10):
        correct = i < 5
        answers.append({
            "skill": "grammar",
            "is_correct": correct,
            "correct_answer": "A",
            "explanation": "x",
            "score_delta": 15 if correct else 0,
            "max_score_delta": 15,
            "question_index": i,
        })
    session = PlacementSession(
        learner_id=learner.id,
        answers=answers,
        current_index=10,
        level="A2",
        status="active",
    )
    db_session.add(session)
    db_session.commit()

    # Before finishing: the first A2 lesson is locked.
    before = client.get(f"{API}/curriculum/map", params={"level": "A2"}, headers=headers)
    assert before.json()["units"][0]["lessons"][0]["locked"] is True

    # Finish placement.
    resp = client.post(f"{API}/placement/finish", params={"session_id": session.id}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["overall_level"] == "A2"

    # After finishing: first A2 lesson is unlocked, and /next points into A2.
    after = client.get(f"{API}/curriculum/map", params={"level": "A2"}, headers=headers)
    assert after.json()["units"][0]["lessons"][0]["locked"] is False

    nxt = client.get(f"{API}/curriculum/next", params={"level": "A2"}, headers=headers)
    assert nxt.status_code == 200, nxt.text
    assert nxt.json()["code"] == "A2-U01-L01"
