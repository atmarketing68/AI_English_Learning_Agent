"""G2 · Placement covers 4 skills: 3 listening items (audio only) + 1 read-aloud speaking item."""
import dataclasses

import pytest

from app.agents import orchestrator
from app.agents.assessment_agent import (
    SPEAKING_BANK, SPEAKING_SKIP, build_speaking_question, calculate_final_result, evaluate_answer,
)
from app.api.placement import SKILL_ROTATION, TOTAL_QUESTIONS
from app.models.learner_profile import LearnerProfile
from app.models.placement import PlacementSession
from app.models.user import User

API = "/api/v1"


def _register_login(client, email):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "P", "display_name": "P", "role": "learner", "age": 15,
        },
    )
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def fake_agent(monkeypatch):
    def _swap(agent_name, payload):
        spec = orchestrator.AGENT_SPECS[agent_name]
        patched = dict(orchestrator.AGENT_SPECS)
        patched[agent_name] = dataclasses.replace(spec, handler=lambda **kw: payload)
        monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)
    return _swap


def test_rotation_has_three_listening_and_speaking_last():
    assert len(SKILL_ROTATION) == TOTAL_QUESTIONS == 14
    assert SKILL_ROTATION.count("listening") == 3
    assert SKILL_ROTATION.count("speaking") == 1 and SKILL_ROTATION[-1] == "speaking"


def test_speaking_question_is_deterministic_and_level_bound():
    q1 = build_speaking_question("A2", "session-x")
    q2 = build_speaking_question("A2", "session-x")
    assert q1 == q2
    assert q1["target_text"] in SPEAKING_BANK["A2"]
    assert build_speaking_question("ZZ", "s")["level"] == "A1"   # unknown level falls back


def test_evaluate_speaking_answer_scores_transcript_and_skip():
    q = build_speaking_question("A1", "s")
    good = evaluate_answer(q, q["target_text"].lower())
    assert good["is_correct"] is True and good["score_delta"] == 15 and good["skipped"] is False
    bad = evaluate_answer(q, "banana banana")
    assert bad["is_correct"] is False and bad["score_delta"] < 15
    skipped = evaluate_answer(q, SPEAKING_SKIP)
    assert skipped["skipped"] is True and skipped["score_delta"] == 0


def test_final_result_ignores_skipped_items():
    answers = [
        {"skill": "grammar", "is_correct": True, "score_delta": 10, "max_score_delta": 10},
        {"skill": "grammar", "is_correct": False, "score_delta": 0, "max_score_delta": 10},
        {"skill": "speaking", "is_correct": False, "score_delta": 0, "max_score_delta": 10, "skipped": True},
    ]
    final = calculate_final_result(answers)
    assert final["total_questions"] == 2
    assert "speaking" not in final["skill_scores"]
    assert calculate_final_result([answers[2]])["total_questions"] == 0


def test_listening_question_exposes_audio_text_only(client, fake_agent):
    fake_agent("placement_question", {
        "skill": "listening", "level": "A1", "passage": "",
        "audio_text": "The train to Hue leaves at nine thirty from platform two.",
        "question": "What time does the train leave?",
        "options": {"A": "9:30", "B": "2:30", "C": "9:00", "D": "10:30"},
        "correct_answer": "A", "explanation": "The speaker says nine thirty.", "effective_level": "A1",
    })
    headers = _register_login(client, "pl1@example.com")
    sid = client.post(f"{API}/placement/start", headers=headers).json()["session_id"]
    db_q = None
    # Walk to the first listening slot (index 2) by answering the two text items.
    for idx in range(3):
        q = client.get(f"{API}/placement/question", params={"session_id": sid}, headers=headers).json()
        if idx < 2:
            client.post(f"{API}/placement/answer", json={"session_id": sid, "answer": "A"}, headers=headers)
        else:
            db_q = q
    assert db_q["skill"] == "listening"
    assert db_q["audio_text"].startswith("The train")
    assert db_q["passage"] is None
    assert db_q["question_index"] == 2


def test_speaking_item_end_to_end_updates_speaking_score(client, db_session):
    headers = _register_login(client, "pl2@example.com")
    learner = (
        db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id)
        .filter(User.email == "pl2@example.com").first()
    )
    # Seed the first 13 answers so the next question is the speaking item.
    answers = [
        {"skill": "grammar", "is_correct": i % 2 == 0, "correct_answer": "A", "explanation": "x",
         "score_delta": 15 if i % 2 == 0 else 0, "max_score_delta": 15, "question_index": i}
        for i in range(TOTAL_QUESTIONS - 1)
    ]
    session = PlacementSession(learner_id=learner.id, answers=answers, current_index=TOTAL_QUESTIONS - 1, level="A1")
    db_session.add(session)
    db_session.commit()

    q = client.get(f"{API}/placement/question", params={"session_id": session.id}, headers=headers)
    assert q.status_code == 200, q.text
    assert q.json()["skill"] == "speaking"
    assert q.json()["options"] == {}
    target = q.json()["target_text"]
    assert target in SPEAKING_BANK["A1"]

    ans = client.post(f"{API}/placement/answer", json={"session_id": session.id, "answer": target}, headers=headers)
    assert ans.status_code == 200, ans.text
    assert ans.json()["is_correct"] is True
    assert ans.json()["speaking_score"] >= 95
    assert ans.json()["is_finished"] is True

    fin = client.post(f"{API}/placement/finish", params={"session_id": session.id}, headers=headers)
    assert fin.status_code == 200, fin.text
    assert fin.json()["skill_scores"]["speaking"] >= 95
    assert fin.json()["total_questions"] == TOTAL_QUESTIONS

    db_session.expire_all()
    learner = db_session.query(LearnerProfile).filter(LearnerProfile.id == learner.id).first()
    assert learner.speaking_score >= 95
    assert learner.placement_completed == "done"


def test_skipped_speaking_item_does_not_count(client, db_session):
    headers = _register_login(client, "pl3@example.com")
    learner = (
        db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id)
        .filter(User.email == "pl3@example.com").first()
    )
    answers = [
        {"skill": "vocabulary", "is_correct": True, "correct_answer": "A", "explanation": "x",
         "score_delta": 10, "max_score_delta": 10, "question_index": i}
        for i in range(TOTAL_QUESTIONS - 1)
    ]
    session = PlacementSession(learner_id=learner.id, answers=answers, current_index=TOTAL_QUESTIONS - 1, level="B1")
    db_session.add(session)
    db_session.commit()

    client.get(f"{API}/placement/question", params={"session_id": session.id}, headers=headers)
    ans = client.post(f"{API}/placement/answer", json={"session_id": session.id, "answer": SPEAKING_SKIP}, headers=headers)
    assert ans.status_code == 200
    assert ans.json()["skipped"] is True

    fin = client.post(f"{API}/placement/finish", params={"session_id": session.id}, headers=headers).json()
    assert fin["total_questions"] == TOTAL_QUESTIONS - 1
    assert fin["accuracy_percent"] == 100.0
    assert "speaking" not in fin["skill_scores"]
