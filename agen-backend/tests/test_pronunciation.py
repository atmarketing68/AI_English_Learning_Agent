"""Tests for transcript-based pronunciation scoring."""
import pytest

from app.services.pronunciation_service import score_pronunciation

API = "/api/v1"


# ── Unit: scoring logic ───────────────────────────────────────────────────────
def test_perfect_match_scores_high():
    r = score_pronunciation("The cat is on the mat", "the cat is on the mat")
    assert r.overall_score >= 95
    assert r.accuracy == 100.0
    assert r.coverage == 100.0
    assert r.missed_words == []


def test_case_and_punctuation_insensitive():
    r = score_pronunciation("Hello, world!", "hello world")
    assert r.accuracy == 100.0
    assert r.coverage == 100.0


def test_missing_words_lower_coverage():
    r = score_pronunciation("I would like a cup of coffee", "I like coffee")
    assert r.coverage < 100
    assert "would" in r.missed_words
    assert "cup" in r.missed_words


def test_completely_wrong_scores_low():
    r = score_pronunciation("Good morning teacher", "banana banana banana")
    assert r.overall_score < 40


def test_empty_transcript():
    r = score_pronunciation("Hello world", "")
    assert r.said_word_count == 0
    assert r.coverage == 0.0


def test_empty_target_is_zero():
    r = score_pronunciation("", "anything")
    assert r.overall_score == 0.0


def test_fluency_no_duration_is_full():
    r = score_pronunciation("one two three four", "one two three four")
    assert r.fluency == 100.0


def test_fluency_penalizes_too_slow():
    # 4 words in 20s = 12 wpm → very slow → floor 50
    r = score_pronunciation("one two three four", "one two three four", duration_seconds=20)
    assert r.fluency == 50.0


def test_extra_words_tracked():
    r = score_pronunciation("I like tea", "I really like tea a lot")
    assert "really" in r.extra_words
    assert "lot" in r.extra_words


def test_to_dict_shape():
    r = score_pronunciation("hello world", "hello world")
    d = r.to_dict()
    assert set(d) >= {"overall_score", "accuracy", "coverage", "fluency", "feedback_vi"}


# ── API ───────────────────────────────────────────────────────────────────────
def _register_login(client, email="pron@example.com"):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "P", "display_name": "P", "role": "learner", "age": 12,
        },
    )
    token = client.post(
        f"{API}/auth/login",
        data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_pronunciation_endpoint(client):
    headers = _register_login(client, "pron1@example.com")
    resp = client.post(
        f"{API}/speaking/pronunciation",
        json={"target_text": "The sun is bright today", "transcript": "the sun is bright today"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["overall_score"] >= 95
    assert body["xp_earned"] > 0
    assert "feedback_vi" in body


def test_pronunciation_endpoint_partial(client):
    headers = _register_login(client, "pron2@example.com")
    resp = client.post(
        f"{API}/speaking/pronunciation",
        json={"target_text": "I have been studying English for two years", "transcript": "I study English"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["overall_score"] < 100
    assert len(resp.json()["missed_words"]) > 0
