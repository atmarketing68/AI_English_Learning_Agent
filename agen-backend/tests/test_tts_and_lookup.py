"""G2 · Server TTS (off until configured, cached, budgeted) + tap-a-word notebook/lookup."""
import pytest

from app.core.config import settings
from app.services import tts_service
from app.services.llm_client import LLMError

API = "/api/v1"


def _register_login(client, email):
    client.post(
        f"{API}/auth/register",
        json={
            "email": email, "password": "Strong123",
            "full_name": "T", "display_name": "T", "role": "learner", "age": 20,
        },
    )
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Strong123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def tts_env(monkeypatch, tmp_path):
    """A fake provider so no network is touched; cache in a temp dir; fresh budget."""
    calls = []

    def fake_call(text, voice):
        calls.append((text, voice))
        return b"ID3fake-mp3-" + text.encode(), "audio/mpeg"

    monkeypatch.setattr(settings, "TTS_PROVIDER", "auto")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "TTS_CACHE_DIR", str(tmp_path / "tts"))
    monkeypatch.setattr(settings, "TTS_DAILY_CHAR_LIMIT", 1000)
    monkeypatch.setattr(tts_service, "_CALLERS", {"openai": fake_call, "gemini": fake_call})
    monkeypatch.setitem(tts_service._budget, "day", "")
    monkeypatch.setitem(tts_service._budget, "chars", 0)
    return calls


def test_tts_off_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "auto")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    assert tts_service.providers() == []
    assert tts_service.synthesize("hello") is None


def test_tts_provider_pin_and_off(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "o")
    monkeypatch.setattr(settings, "TTS_PROVIDER", "auto")
    assert tts_service.providers() == ["gemini", "openai"]
    monkeypatch.setattr(settings, "TTS_PROVIDER", "openai")
    assert tts_service.providers() == ["openai"]
    monkeypatch.setattr(settings, "TTS_PROVIDER", "off")
    assert tts_service.providers() == []


def test_tts_caches_and_counts_budget_once(tts_env):
    first = tts_service.synthesize("Hello,   world!", "female")
    assert first and first.cached is False and first.mime == "audio/mpeg"
    second = tts_service.synthesize("hello, world!", "female")   # case/whitespace-insensitive
    assert second and second.cached is True
    assert len(tts_env) == 1
    assert tts_service.budget_used_today() == len("Hello, world!")


def test_tts_budget_exhausted_falls_back(tts_env):
    assert tts_service.synthesize("a" * 600) is not None
    assert tts_service.synthesize("b" * 500) is None       # 1100 > 1000 limit
    assert len(tts_env) == 1


def test_tts_provider_failure_returns_none(monkeypatch, tts_env):
    def boom(text, voice):
        raise RuntimeError("model not found")
    monkeypatch.setattr(tts_service, "_CALLERS", {"openai": boom, "gemini": boom})
    assert tts_service.synthesize("new sentence") is None


def test_pcm_to_wav_header():
    wav = tts_service._pcm_to_wav(b"\x00\x00" * 100, 24000)
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"


def test_tts_endpoint_404_when_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "off")
    headers = _register_login(client, "tts1@example.com")
    assert client.get(f"{API}/audio/tts/status", headers=headers).json()["enabled"] is False
    resp = client.get(f"{API}/audio/tts", params={"text": "hello"}, headers=headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "tts_disabled"


def test_tts_endpoint_streams_audio(client, tts_env):
    headers = _register_login(client, "tts2@example.com")
    resp = client.get(f"{API}/audio/tts", params={"text": "Good morning", "voice": "male"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("audio/mpeg")
    assert resp.headers["x-tts-cache"] == "miss"
    assert resp.content.startswith(b"ID3")
    again = client.get(f"{API}/audio/tts", params={"text": "Good morning", "voice": "male"}, headers=headers)
    assert again.headers["x-tts-cache"] == "hit"
    assert tts_env[0][1] == "male"


def test_tts_requires_auth(client):
    assert client.get(f"{API}/audio/tts", params={"text": "hello"}).status_code == 401


# ── Notebook: add a tapped word + lookup ─────────────────────────────────────
def test_add_word_to_notebook_is_idempotent(client):
    headers = _register_login(client, "nb1@example.com")
    resp = client.post(
        f"{API}/review/items",
        json={"word": "Platform", "meaning": "sân ga", "phonetic": "/ˈplætfɔːm/", "example": "Platform two."},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["created"] is True
    assert resp.json()["item"]["front"] == "Platform"
    again = client.post(f"{API}/review/items", json={"word": "platform", "meaning": "khác"}, headers=headers)
    assert again.status_code == 201
    assert again.json()["created"] is False
    page = client.get(f"{API}/review/items", params={"kind": "vocab"}, headers=headers).json()
    assert page["total"] == 1


def test_lookup_uses_dictionary_service(client, monkeypatch):
    from app.api import review as review_api  # noqa: F401  (module import keeps patch target explicit)
    import app.services.dictionary_service as dictionary_service

    def fake_lookup(word, context="", level="A2"):
        return {"word": word, "phonetic": "/wɜːd/", "part_of_speech": "noun",
                "meaning_vi": "từ", "definition_en": "a unit of language", "example": f"A {word}."}
    monkeypatch.setattr(dictionary_service, "lookup_word", fake_lookup)

    headers = _register_login(client, "nb2@example.com")
    resp = client.get(f"{API}/review/lookup", params={"word": "Word,", "context": "A word."}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["word"] == "word"
    assert resp.json()["meaning_vi"] == "từ"
    assert client.get(f"{API}/review/lookup", params={"word": "..."}, headers=headers).status_code == 422


def test_lookup_llm_failure_is_502_or_429(client, monkeypatch):
    import app.services.dictionary_service as dictionary_service

    def boom(word, context="", level="A2"):
        raise LLMError("AI bận", is_quota=True)
    monkeypatch.setattr(dictionary_service, "lookup_word", boom)
    headers = _register_login(client, "nb3@example.com")
    assert client.get(f"{API}/review/lookup", params={"word": "hello"}, headers=headers).status_code == 429


def test_edge_provider_comes_before_llm_providers(monkeypatch):
    monkeypatch.setattr(settings, "EDGE_TTS_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "o")
    monkeypatch.setattr(settings, "TTS_PROVIDER", "auto")
    assert tts_service.providers() == ["edge", "gemini", "openai"]
    monkeypatch.setattr(settings, "TTS_PROVIDER", "edge")
    assert tts_service.providers() == ["edge"]
    monkeypatch.setattr(settings, "TTS_PROVIDER", "auto")
    monkeypatch.setattr(settings, "EDGE_TTS_ENABLED", False)
    assert tts_service.providers() == ["gemini", "openai"]


def test_edge_failure_falls_through_to_next_provider(monkeypatch, tmp_path):
    """Edge down (blocked IP, network) → Gemini; both down → None so the browser voice takes over."""
    used = []

    def edge_down(text, voice, lang="en"):
        used.append("edge")
        raise RuntimeError("blocked")

    def gemini_ok(text, voice, lang="en"):
        used.append("gemini")
        return b"RIFFfakeWAVE", "audio/wav"

    monkeypatch.setattr(settings, "EDGE_TTS_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "TTS_PROVIDER", "auto")
    monkeypatch.setattr(settings, "TTS_CACHE_DIR", str(tmp_path / "tts"))
    monkeypatch.setattr(settings, "TTS_DAILY_CHAR_LIMIT", 1000)
    monkeypatch.setitem(tts_service._budget, "day", "")
    monkeypatch.setitem(tts_service._budget, "chars", 0)
    monkeypatch.setattr(tts_service, "_CALLERS", {"edge": edge_down, "gemini": gemini_ok})
    res = tts_service.synthesize("The bus is late.", "female")
    assert res and res.provider == "gemini" and used == ["edge", "gemini"]

    monkeypatch.setattr(tts_service, "_CALLERS", {"edge": edge_down, "gemini": edge_down})
    assert tts_service.synthesize("A different sentence.", "female") is None


def test_edge_voice_names_cover_both_languages():
    for lang in ("en", "vi"):
        assert set(tts_service.EDGE_VOICES[lang]) == {"female", "male"}
