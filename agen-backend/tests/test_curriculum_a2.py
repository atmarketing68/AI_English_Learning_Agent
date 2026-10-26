"""Integration tests for the curriculum map, focused on A2 and the A1->A2 bridge.

Uses the in-memory DB + TestClient fixtures. The curriculum is seeded per-test
into the isolated schema so we assert on the real seed data + API behaviour.
"""
import pytest

from app.services.curriculum_seed import seed_curriculum

API = "/api/v1"


@pytest.fixture()
def seeded(db_session):
    """Seed the full curriculum (A1 + A2) into the test DB."""
    seed_curriculum(db_session)
    db_session.commit()


def _learner_headers(client, email="cur@example.com"):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email,
            "password": "Strong123",
            "full_name": "C",
            "display_name": "C",
            "role": "learner",
            "age": 13,
        },
    )
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_a2_map_has_six_units_thirty_lessons(client, seeded):
    headers = _learner_headers(client)
    resp = client.get(f"{API}/curriculum/map", params={"level": "A2"}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["level"] == "A2"
    assert len(body["units"]) == 6
    assert body["total_lessons"] == 30
    # Every unit has 5 lessons
    assert all(len(u["lessons"]) == 5 for u in body["units"])


def test_a1_still_present(client, seeded):
    headers = _learner_headers(client, "cur2@example.com")
    resp = client.get(f"{API}/curriculum/map", params={"level": "A1"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total_lessons"] == 30


def test_first_a2_lesson_is_locked_until_a1_done(client, seeded):
    headers = _learner_headers(client, "cur3@example.com")
    resp = client.get(f"{API}/curriculum/map", params={"level": "A2"}, headers=headers)
    first_unit = resp.json()["units"][0]
    first_lesson = first_unit["lessons"][0]
    assert first_lesson["code"] == "A2-U01-L01"
    # Prerequisite is the last A1 lesson, which the new learner has not mastered.
    assert first_lesson["locked"] is True


def test_next_lesson_starts_at_a1_for_new_learner(client, seeded):
    headers = _learner_headers(client, "cur4@example.com")
    resp = client.get(f"{API}/curriculum/next", params={"level": "A1"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["code"] == "A1-U01-L01"


def test_cannot_start_locked_a2_lesson(client, seeded):
    headers = _learner_headers(client, "cur5@example.com")
    resp = client.post(
        f"{API}/curriculum/start",
        json={"code": "A2-U01-L01"},
        headers=headers,
    )
    # Prerequisite A1-U06-L05 not mastered → blocked
    assert resp.status_code == 400
    assert "A1-U06-L05" in resp.json()["detail"]


def test_can_start_first_a1_lesson(client, seeded):
    headers = _learner_headers(client, "cur6@example.com")
    resp = client.post(
        f"{API}/curriculum/start",
        json={"code": "A1-U01-L01"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_b1_map_present_and_gated_behind_a2(client, seeded):
    headers = _learner_headers(client, "curb1@example.com")
    resp = client.get(f"{API}/curriculum/map", params={"level": "B1"}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["level"] == "B1"
    assert body["total_lessons"] == 30
    assert len(body["units"]) == 6
    # First B1 lesson is locked until the last A2 lesson is mastered.
    first = body["units"][0]["lessons"][0]
    assert first["code"] == "B1-U01-L01"
    assert first["locked"] is True


def test_a2_units_have_all_four_productive_skills(client, seeded):
    """Each A2 unit should cover a mix of skills, and A2 overall must include
    speaking + writing (productive skills), which A1 only introduced late."""
    headers = _learner_headers(client, "cur7@example.com")
    resp = client.get(f"{API}/curriculum/map", params={"level": "A2"}, headers=headers)
    skills = {
        lesson["skill"]
        for unit in resp.json()["units"]
        for lesson in unit["lessons"]
    }
    assert {"vocabulary", "grammar", "reading", "listening", "speaking", "writing"} <= skills
