"""G2 · Luyện nói 3 bước: curated scenarios, persona roleplay, per-word pronunciation."""
import dataclasses

import pytest

from app.agents import orchestrator
from app.services import speaking_scenarios
from app.services.pronunciation_service import align_words, score_pronunciation, sound_tips

API = "/api/v1"


def _register_login(client, email):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "S", "display_name": "S", "role": "learner", "age": 14,
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


# ── Scenario catalogue ───────────────────────────────────────────────────────
def test_catalogue_has_20_plus_scenarios_with_complete_data():
    assert len(speaking_scenarios.SCENARIOS) >= 20
    ids = [s["id"] for s in speaking_scenarios.SCENARIOS]
    assert len(ids) == len(set(ids)), "scenario ids must be unique"
    for s in speaking_scenarios.SCENARIOS:
        assert s["category"] in speaking_scenarios.CATEGORIES
        assert s["level"] in speaking_scenarios.LEVEL_ORDER
        assert len(s["phrases"]) >= 5
        assert all(p["en"] and p["vi"] for p in s["phrases"])
        assert s["persona"]["voice"] in ("female", "male")
        assert s["first_message"].strip()


def test_recommended_flag_follows_learner_level():
    items = {s["id"]: s for s in speaking_scenarios.list_scenarios("A1")}
    assert items["cafe_order"]["recommended"] is True          # A1
    assert items["hotel_checkin"]["recommended"] is True       # A2 = one step up
    assert items["job_interview"]["recommended"] is False      # B1
    assert "phrases" not in items["cafe_order"]


def test_system_prompt_mentions_persona_and_level():
    s = speaking_scenarios.get_scenario("cafe_order")
    prompt = speaking_scenarios.build_system_prompt(s, "A2")
    assert "Linh" in prompt and "A2" in prompt and "Stay in character" in prompt


# ── API: scenarios + persona roleplay ────────────────────────────────────────
def test_scenarios_endpoint_and_detail(client):
    headers = _register_login(client, "sc1@example.com")
    resp = client.get(f"{API}/speaking/scenarios", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["learner_level"] in speaking_scenarios.LEVEL_ORDER
    assert len(body["scenarios"]) >= 20
    assert "daily" in body["categories"]

    detail = client.get(f"{API}/speaking/scenarios/cafe_order", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["persona"]["name"] == "Linh"
    assert len(detail.json()["phrases"]) >= 5

    assert client.get(f"{API}/speaking/scenarios/nope", headers=headers).status_code == 404


def test_start_with_scenario_needs_no_llm(client):
    headers = _register_login(client, "sc2@example.com")
    resp = client.post(f"{API}/speaking/start", json={"scenario_id": "cafe_order"}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["scenario_id"] == "cafe_order"
    assert body["persona"]["name"] == "Linh"
    assert body["ai_first_message"].startswith("Hi there")
    assert "Linh" in body["system_prompt"]


def test_start_without_topic_or_scenario_is_422(client):
    headers = _register_login(client, "sc3@example.com")
    assert client.post(f"{API}/speaking/start", json={}, headers=headers).status_code == 422


def test_reply_returns_coach_fields_and_finish_summarises(client, fake_agent):
    fake_agent("speaking_turn", {
        "ai_reply": "Sure! Iced milk coffee coming up. Anything else?",
        "feedback": "Rất tốt!",
        "is_correct": True,
        "score": 90,
        "corrected": "",
        "hint_en": "No, that's all. How much is it?",
    })
    headers = _register_login(client, "sc4@example.com")
    sid = client.post(f"{API}/speaking/start", json={"scenario_id": "cafe_order"}, headers=headers).json()["session_id"]
    reply = client.post(
        f"{API}/speaking/reply",
        json={"session_id": sid, "user_message": "can i have an iced milk coffee please"},
        headers=headers,
    )
    assert reply.status_code == 200, reply.text
    assert reply.json()["hint_en"].startswith("No, that")
    assert reply.json()["corrected"] == ""

    fin = client.post(
        f"{API}/speaking/finish",
        json={"session_id": sid, "topic": "x", "total_turns": 99, "average_score": 1},
        headers=headers,
    )
    assert fin.status_code == 200
    assert fin.json()["total_turns"] == 1
    assert fin.json()["average_score"] == 90.0
    assert fin.json()["xp_earned"] == 20 + 18


# ── Per-word pronunciation verdicts + sound tips ─────────────────────────────
def test_align_words_marks_ok_wrong_and_missed():
    words = align_words(["i", "think", "three", "books"], ["i", "sink", "tree"])
    by_word = {w["word"]: w for w in words}
    assert by_word["i"]["status"] == "ok"
    assert by_word["think"]["status"] == "wrong" and by_word["think"]["heard"] == "sink"
    assert by_word["three"]["status"] == "wrong" and by_word["three"]["heard"] == "tree"
    assert by_word["books"]["status"] == "missed"


def test_sound_tips_explain_vietnamese_problem_sounds():
    words = align_words(["i", "think", "three", "books"], ["i", "sink", "tree"])
    tips = sound_tips(words)
    sounds = [t["sound"] for t in tips]
    assert any("θ" in s for s in sounds), sounds
    th_tip = next(t for t in tips if "θ" in t["sound"])
    assert set(th_tip["words"]) == {"think", "three"}
    assert len(tips) <= 3


def test_perfect_attempt_has_no_tips_and_all_ok():
    r = score_pronunciation("The cat is on the mat", "the cat is on the mat")
    assert all(w["status"] == "ok" for w in r.words)
    assert r.sound_tips == []
    assert "words" in r.to_dict() and "sound_tips" in r.to_dict()


def test_pronunciation_endpoint_returns_words(client):
    headers = _register_login(client, "sc5@example.com")
    resp = client.post(
        f"{API}/speaking/pronunciation",
        json={"target_text": "I think this is right", "transcript": "I sink this is", "source": "scenario_step2"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [w["word"] for w in body["words"]] == ["i", "think", "this", "is", "right"]
    assert body["words"][1]["status"] == "wrong"
    assert body["words"][-1]["status"] == "missed"
    assert body["sound_tips"]
