"""G3 · Khoá theo mục tiêu: catalogue, sequential unlocking, generation link and completion."""
import dataclasses

import pytest

from app.agents import orchestrator
from app.models.goal_track import GoalTrackProgress
from app.services import goal_tracks

API = "/api/v1"


def _auth(client, email, goal=None):
    client.post(f"{API}/auth/register", json={"email": email, "password": "Strong123", "full_name": "T", "display_name": "T", "role": "learner", "age": 20})
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    if goal:
        client.patch(f"{API}/learner/me", json={"learning_goal": goal}, headers=headers)
    return headers


@pytest.fixture()
def fake_lesson(monkeypatch):
    def _swap(payload):
        spec = orchestrator.AGENT_SPECS["lesson"]
        patched = dict(orchestrator.AGENT_SPECS)
        patched["lesson"] = dataclasses.replace(spec, handler=lambda **kw: payload)
        monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)
    return _swap


VOCAB_LESSON = {
    "title": "IELTS: education", "summary": "Academic words about education.",
    "skill": "vocabulary", "topic": "IELTS academic vocabulary: education and learning", "level": "B1",
    "vocabulary": [{"word": "curriculum", "translation": "chương trình học", "definition": "the subjects taught", "example": "The curriculum is broad."}],
    "exercises": [
        {"type": "flashcard", "order": 0, "content": {"word": "curriculum", "translation": "chương trình học"}},
        {"type": "multiple_choice", "order": 1, "content": {"question": "curriculum?", "options": {"A": "chương trình học", "B": "x", "C": "y", "D": "z"}, "correct_answer": "A", "explanation": "e"}},
        {"type": "multiple_choice", "order": 2, "content": {"question": "q2", "options": {"A": "a", "B": "b", "C": "c", "D": "d"}, "correct_answer": "B", "explanation": "e"}},
    ],
}


def test_catalogue_is_consistent():
    codes = [c for t in goal_tracks.TRACKS for c in goal_tracks.track_lesson_codes(t)]
    assert len(codes) == len(set(codes)) and len(goal_tracks.TRACKS) == 3
    for track in goal_tracks.TRACKS:
        for module in track["modules"]:
            for lesson in module["lessons"]:
                assert lesson["skill"] in ("vocabulary", "grammar", "reading", "listening")
                assert lesson["level"] in ("A2", "B1", "B2")
                assert goal_tracks.find_lesson(lesson["code"])[0]["id"] == track["id"]
    assert goal_tracks.recommended_track_ids("luyen_thi") == ["ielts", "toeic"]
    assert goal_tracks.recommended_track_ids("cong_viec") == ["toeic", "interview"]


def test_tracks_list_and_detail_with_locking(client):
    headers = _auth(client, "tr1@example.com", goal="cong_viec")
    tracks = client.get(f"{API}/curriculum/tracks", headers=headers).json()
    assert [t["id"] for t in tracks][:2] == ["interview", "toeic"]          # recommended first
    assert all(t["recommended"] for t in tracks[:2]) and tracks[2]["recommended"] is False
    detail = client.get(f"{API}/curriculum/tracks/ielts", headers=headers).json()
    first = detail["modules"][0]["lessons"]
    assert first[0]["locked"] is False and first[1]["locked"] is True
    assert detail["next_lesson_code"] == "IELTS-M1-L1" and detail["progress_pct"] == 0.0
    assert client.get(f"{API}/curriculum/tracks/nope", headers=headers).status_code == 404
    locked = client.post(f"{API}/curriculum/tracks/ielts/start", json={"code": "IELTS-M1-L2"}, headers=headers)
    assert locked.status_code == 400


def test_start_generate_finish_updates_track(client, db_session, fake_lesson):
    fake_lesson(VOCAB_LESSON)
    headers = _auth(client, "tr2@example.com")
    start = client.post(f"{API}/curriculum/tracks/ielts/start", json={"code": "IELTS-M1-L1"}, headers=headers)
    assert start.status_code == 200, start.text
    assert start.json()["skill"] == "vocabulary" and start.json()["level"] == "B1"

    gen = client.post(f"{API}/lessons/generate", json={"skill": "vocabulary", "topic": start.json()["topic"], "track_code": "IELTS-M1-L1"}, headers=headers)
    assert gen.status_code == 200, gen.text
    lesson = gen.json()
    assert lesson["level"] == "B1"                                  # the track's level, not the learner's
    prog = db_session.query(GoalTrackProgress).filter(GoalTrackProgress.lesson_code == "IELTS-M1-L1").one()
    assert prog.generated_lesson_id == lesson["id"] and prog.status == "in_progress"

    for ex in lesson["exercises"]:
        if ex["type"] == "multiple_choice":
            client.post(f"{API}/lessons/{lesson['id']}/submit-exercise", json={"exercise_id": ex["id"], "answer": ex["content"].get("correct_answer", "A") if "correct_answer" in ex["content"] else "A"}, headers=headers)
    fin = client.post(f"{API}/lessons/{lesson['id']}/finish", headers=headers)
    assert fin.status_code == 200, fin.text

    db_session.expire_all()
    prog = db_session.query(GoalTrackProgress).filter(GoalTrackProgress.lesson_code == "IELTS-M1-L1").one()
    assert prog.status == "completed" and prog.attempts == 1 and prog.best_score >= 0
    detail = client.get(f"{API}/curriculum/tracks/ielts", headers=headers).json()
    assert detail["completed_lessons"] == 1
    assert detail["modules"][0]["lessons"][1]["locked"] is False       # next lesson unlocked
    assert detail["next_lesson_code"] == "IELTS-M1-L2"
    summary = next(t for t in client.get(f"{API}/curriculum/tracks", headers=headers).json() if t["id"] == "ielts")
    assert summary["completed_lessons"] == 1 and summary["progress_pct"] > 0
