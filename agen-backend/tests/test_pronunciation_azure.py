"""G2 · 9 — Azure phoneme scoring (mapping + endpoint fallback) and the Voicebox TTS provider."""
import io
import wave
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services import pronunciation_azure as az
from app.services import tts_service

API = "/api/v1"


def _register_login(client, email):
    client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "Strong123", "full_name": "A", "display_name": "A", "role": "learner", "age": 20},
    )
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _wav(seconds: float = 0.5) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * int(16000 * seconds))
    return buf.getvalue()


SAMPLE = {
    "RecognitionStatus": "Success",
    "DisplayText": "I sink the weather is nice.",
    "NBest": [{
        "Confidence": 0.9, "Lexical": "i sink the weather is nice", "Display": "I sink the weather is nice.",
        "PronunciationAssessment": {"AccuracyScore": 72.0, "FluencyScore": 88.0, "CompletenessScore": 83.0, "PronScore": 76.5, "ProsodyScore": 70.0},
        "Words": [
            {"Word": "I", "PronunciationAssessment": {"AccuracyScore": 98.0, "ErrorType": "None"},
             "Phonemes": [{"Phoneme": "aɪ", "PronunciationAssessment": {"AccuracyScore": 98.0}}]},
            {"Word": "think", "PronunciationAssessment": {"AccuracyScore": 35.0, "ErrorType": "Mispronunciation"},
             "Phonemes": [{"Phoneme": "θ", "PronunciationAssessment": {"AccuracyScore": 12.0}},
                          {"Phoneme": "ɪ", "PronunciationAssessment": {"AccuracyScore": 90.0}},
                          {"Phoneme": "ŋ", "PronunciationAssessment": {"AccuracyScore": 80.0}},
                          {"Phoneme": "k", "PronunciationAssessment": {"AccuracyScore": 40.0}}]},
            {"Word": "the", "PronunciationAssessment": {"AccuracyScore": 80.0, "ErrorType": "None"},
             "Phonemes": [{"Phoneme": "ð", "PronunciationAssessment": {"AccuracyScore": 55.0}}, {"Phoneme": "ə", "PronunciationAssessment": {"AccuracyScore": 95.0}}]},
            {"Word": "weather", "PronunciationAssessment": {"AccuracyScore": 85.0, "ErrorType": "None"}, "Phonemes": []},
            {"Word": "is", "PronunciationAssessment": {"AccuracyScore": 0.0, "ErrorType": "Omission"}, "Phonemes": []},
            {"Word": "really", "PronunciationAssessment": {"AccuracyScore": 70.0, "ErrorType": "Insertion"}, "Phonemes": []},
            {"Word": "nice", "PronunciationAssessment": {"AccuracyScore": 91.0, "ErrorType": "None"}, "Phonemes": []},
        ],
    }],
}


# ── Mapping ──────────────────────────────────────────────────────────────────
def test_map_response_words_phonemes_and_tips():
    r = az.map_response(SAMPLE, "I think the weather is nice")
    by = {w["word"]: w for w in r.words}
    assert by["i"]["status"] == "ok"
    assert by["think"]["status"] == "wrong" and by["think"]["score"] == 35.0
    assert [p["phoneme"] for p in by["think"]["phonemes"]] == ["θ", "ɪ", "ŋ", "k"]
    assert by["is"]["status"] == "missed"
    assert "really" in r.extra_words and "really" not in by
    assert r.overall_score == 76.5 and r.prosody == 70.0
    sounds = [t["sound"] for t in r.sound_tips]
    assert any("θ" in s for s in sounds)
    th = next(t for t in r.sound_tips if "θ" in t["sound"])
    assert "think" in th["words"] and "the" in th["words"]      # ð scored low inside an "ok" word


def test_map_response_marks_unreturned_reference_words_missed():
    data = {"RecognitionStatus": "Success", "NBest": [{"Display": "", "PronunciationAssessment": {"AccuracyScore": 0, "FluencyScore": 0, "CompletenessScore": 0, "PronScore": 0}, "Words": []}]}
    r = az.map_response(data, "Good morning")
    assert [w["word"] for w in r.words] == ["good", "morning"]
    assert all(w["status"] == "missed" for w in r.words)


def test_map_response_rejects_failed_recognition():
    with pytest.raises(az.AzureUnavailable):
        az.map_response({"RecognitionStatus": "NoMatch", "NBest": []}, "hello")


def test_assess_is_off_without_key(monkeypatch):
    monkeypatch.setattr(settings, "AZURE_SPEECH_KEY", "")
    assert az.is_enabled() is False
    with pytest.raises(az.AzureUnavailable):
        az.assess(_wav(), "hello")


def test_assessment_header_is_base64_json():
    import base64, json
    params = json.loads(base64.b64decode(az._assessment_header("Hi there")))
    assert params["ReferenceText"] == "Hi there" and params["Granularity"] == "Phoneme"


# ── Endpoint ─────────────────────────────────────────────────────────────────
def test_status_and_audio_endpoint_404_when_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "AZURE_SPEECH_KEY", "")
    headers = _register_login(client, "az1@example.com")
    assert client.get(f"{API}/speaking/pronunciation/status", headers=headers).json()["phoneme_enabled"] is False
    resp = client.post(
        f"{API}/speaking/pronunciation-audio",
        files={"audio": ("take.wav", _wav(), "audio/wav")},
        data={"target_text": "hello world", "transcript": "hello world"},
        headers=headers,
    )
    assert resp.status_code == 404 and resp.json()["detail"] == "phoneme_disabled"


def test_audio_endpoint_returns_phoneme_mode(client, monkeypatch):
    monkeypatch.setattr(settings, "AZURE_SPEECH_KEY", "k")
    monkeypatch.setattr(settings, "AZURE_SPEECH_REGION", "southeastasia")
    calls = []

    def fake_call(wav_bytes, reference_text):
        calls.append((len(wav_bytes), reference_text))
        return SAMPLE
    monkeypatch.setattr(az, "call_azure", fake_call)

    headers = _register_login(client, "az2@example.com")
    assert client.get(f"{API}/speaking/pronunciation/status", headers=headers).json() == {"phoneme_enabled": True, "provider": "azure"}
    resp = client.post(
        f"{API}/speaking/pronunciation-audio",
        files={"audio": ("take.wav", _wav(), "audio/wav")},
        data={"target_text": "I think the weather is nice", "transcript": "I sink the weather nice", "source": "scenario_repeat"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == "phoneme"
    assert body["overall_score"] == 76.5 and body["prosody"] == 70.0 and body["completeness"] == 83.0
    assert body["words"][1]["word"] == "think" and body["words"][1]["phonemes"][0]["phoneme"] == "θ"
    assert body["missed_words"] == ["is"] and body["extra_words"] == ["really"]
    assert body["xp_earned"] == 5 + int(0.765 * 15)
    assert calls[0][1] == "I think the weather is nice"


def test_audio_endpoint_falls_back_to_transcript_when_azure_fails(client, monkeypatch):
    monkeypatch.setattr(settings, "AZURE_SPEECH_KEY", "k")

    def boom(wav_bytes, reference_text):
        raise az.AzureUnavailable("503")
    monkeypatch.setattr(az, "call_azure", boom)
    headers = _register_login(client, "az3@example.com")
    resp = client.post(
        f"{API}/speaking/pronunciation-audio",
        files={"audio": ("take.wav", _wav(), "audio/wav")},
        data={"target_text": "hello world", "transcript": "hello world"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["mode"] == "transcript"
    assert resp.json()["overall_score"] >= 95


# ── Voicebox TTS provider ────────────────────────────────────────────────────
def test_voicebox_is_first_provider_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "TTS_PROVIDER", "auto")
    monkeypatch.setattr(settings, "VOICEBOX_URL", "http://voicebox.local:17493")
    monkeypatch.setattr(settings, "VOICEBOX_PROFILE_ID", "prof-f")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    assert tts_service.providers() == ["voicebox", "gemini"]
    monkeypatch.setattr(settings, "VOICEBOX_PROFILE_ID", "")
    assert tts_service.providers() == ["gemini"]


def test_voicebox_call_generates_then_fetches_audio(monkeypatch):
    monkeypatch.setattr(settings, "VOICEBOX_URL", "http://voicebox.local:17493/")
    monkeypatch.setattr(settings, "VOICEBOX_PROFILE_ID", "prof-f")
    monkeypatch.setattr(settings, "VOICEBOX_PROFILE_ID_MALE", "prof-m")
    monkeypatch.setattr(settings, "VOICEBOX_API_KEY", "")
    requests = []

    class FakeResponse:
        def __init__(self, json_data=None, content=b"", headers=None):
            self._json, self.content, self.headers = json_data, content, headers or {}
        def raise_for_status(self):
            return None
        def json(self):
            return self._json

    class FakeClient:
        def __init__(self, *a, **kw):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def post(self, url, json=None):
            requests.append(("POST", url, json))
            return FakeResponse(json_data={"id": "gen-1", "audio_path": "/tmp/gen-1.wav"})
        def get(self, url):
            requests.append(("GET", url, None))
            return FakeResponse(content=b"RIFF....WAVE", headers={"content-type": "audio/wav"})

    import httpx
    monkeypatch.setattr(httpx, "Client", FakeClient)
    data, mime = tts_service._call_voicebox("Hello there", "male")
    assert data.startswith(b"RIFF") and mime == "audio/wav"
    assert requests[0] == ("POST", "http://voicebox.local:17493/generate", {"profile_id": "prof-m", "text": "Hello there", "language": "en"})
    assert requests[1] == ("GET", "http://voicebox.local:17493/audio/gen-1", None)
