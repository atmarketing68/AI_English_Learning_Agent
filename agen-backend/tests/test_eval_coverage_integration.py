"""Integration tests proving writing/placement/speaking now route through the
orchestrator and persist an AgentTrace with AI-evaluation fields (Master Plan §29).

Agent handlers are swapped in AGENT_SPECS so no real LLM is called — we verify the
wiring: API -> orchestrator.execute() -> evaluate_output() -> AgentTrace row.
"""
import dataclasses

import pytest

from app.agents import orchestrator
from app.models.agent_trace import AgentTrace

API = "/api/v1"


@pytest.fixture()
def fake_agent(monkeypatch):
    """Return a function that swaps an AGENT_SPECS handler with a fixed payload."""

    def _swap(agent_name, payload):
        spec = orchestrator.AGENT_SPECS[agent_name]
        new_spec = dataclasses.replace(spec, handler=lambda **kw: payload)
        patched = dict(orchestrator.AGENT_SPECS)
        patched[agent_name] = new_spec
        monkeypatch.setattr(orchestrator, "AGENT_SPECS", patched)

    return _swap


def _register_learner(client, email):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email,
            "password": "Strong123",
            "full_name": "L",
            "display_name": "L",
            "role": "learner",
            "age": 12,
        },
    )
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _traces(db_session, agent):
    return db_session.query(AgentTrace).filter(AgentTrace.agent == agent).all()


def test_writing_prompt_records_evaluated_trace(client, db_session, fake_agent):
    fake_agent("writing_prompt", {
        "title": "My Weekend",
        "prompt": "Write about your weekend in a few sentences.",
        "genre": "narrative",
        "word_target": "60-80 words",
        "guide_steps": ["Start with when", "Say what you did", "End with a feeling"],
        "useful_phrases": ["I went to", "It was fun", "After that"],
        "example_opening": "Last weekend I visited my grandmother.",
        "level": "A1",
        "topic": "your weekend",
    })
    headers = _register_learner(client, "w1@example.com")
    resp = client.post(f"{API}/writing/prompt", json={"genre": "narrative"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "My Weekend"
    # level/topic survive the orchestrator dump (declared optional on the contract)
    assert "level" in resp.json() and "topic" in resp.json()

    traces = _traces(db_session, "writing_prompt")
    assert len(traces) == 1
    assert traces[0].status == "succeeded"
    assert traces[0].eval_score is not None
    assert traces[0].eval_flagged is False


def test_placement_question_records_evaluated_trace(client, db_session, fake_agent):
    fake_agent("placement_question", {
        "skill": "grammar",
        "level": "A1",
        "passage": "",
        "question": "She ___ happy today.",
        "options": {"A": "is", "B": "are", "C": "am", "D": "be"},
        "correct_answer": "A",
        "explanation": "Third person singular uses 'is'.",
        "effective_level": "A1",
    })
    headers = _register_learner(client, "p1@example.com")
    start = client.post(f"{API}/placement/start", headers=headers)
    sid = start.json()["session_id"]
    q = client.get(f"{API}/placement/question", params={"session_id": sid}, headers=headers)
    assert q.status_code == 200, q.text
    assert q.json()["question"].startswith("She")

    traces = _traces(db_session, "placement_question")
    assert len(traces) == 1
    assert traces[0].status == "succeeded"
    assert traces[0].eval_score is not None


def test_speaking_scenario_records_evaluated_trace(client, db_session, fake_agent):
    fake_agent("roleplay_scenario", {
        "system_prompt": "You are a friendly barista. Keep replies short.",
        "ai_first_message": "Hi there! What would you like to order today?",
    })
    headers = _register_learner(client, "s1@example.com")
    resp = client.post(f"{API}/speaking/start", json={"topic": "cafe"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["ai_first_message"].startswith("Hi there")

    traces = _traces(db_session, "roleplay_scenario")
    assert len(traces) == 1
    assert traces[0].status == "succeeded"
    assert traces[0].eval_score is not None


def test_flagged_output_still_delivers_and_is_recorded(client, db_session, fake_agent):
    # A prompt containing a blocklisted word must still be delivered (fail-open)
    # but the trace must be flagged for review.
    fake_agent("writing_prompt", {
        "title": "A lesson about a gun",
        "prompt": "Describe a gun you have seen. Talk about it in detail today.",
        "genre": "descriptive",
        "word_target": "60-80 words",
        "guide_steps": ["Start", "Middle here", "End it"],
        "useful_phrases": ["I saw", "It was", "After"],
        "example_opening": "Yesterday I saw something interesting.",
        "level": "A1",
        "topic": "a gun",
    })
    headers = _register_learner(client, "flag@example.com")
    resp = client.post(f"{API}/writing/prompt", json={"genre": "descriptive"}, headers=headers)
    assert resp.status_code == 200  # still delivered (fail-open)

    traces = _traces(db_session, "writing_prompt")
    assert len(traces) == 1
    assert traces[0].eval_flagged is True
    assert traces[0].eval_flags  # non-empty
