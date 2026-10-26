"""
G2 · 9 — Chấm phát âm đến từng âm (phoneme) bằng Azure AI Speech
Pronunciation Assessment, qua REST (không cần SDK).

Bật khi có AZURE_SPEECH_KEY (+ AZURE_SPEECH_REGION). Không có khoá → is_enabled()
False và API trả về chấm theo transcript như cũ, nên giao diện không đổi.

Audio: WAV 16 kHz mono 16-bit (web app tự chuyển từ MediaRecorder), tối đa ~60 s.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field

import httpx

from app.core.config import settings
from app.services.pronunciation_service import _SOUND_RULES, _normalize, sound_tips

logger = logging.getLogger("agen.pronunciation.azure")

MAX_AUDIO_BYTES = 2_500_000          # ≈ 75 s of 16 kHz 16-bit mono
WORD_PASS_SCORE = 60.0
PHONEME_PASS_SCORE = 60.0

# IPA phoneme → id of the Vietnamese-speaker tip in pronunciation_service._SOUND_RULES
_PHONEME_RULE = {
    "θ": "th", "ð": "th",
    "r": "r", "ɹ": "r",
    "ʃ": "sh_ch_j", "tʃ": "sh_ch_j", "dʒ": "sh_ch_j", "ʒ": "sh_ch_j",
    "w": "w_v", "v": "w_v",
    "l": "l_n",
    "iː": "long_vowel", "uː": "long_vowel", "i:": "long_vowel", "u:": "long_vowel",
}


class AzureUnavailable(RuntimeError):
    """Azure is off, the request failed or the audio could not be assessed."""


@dataclass
class AzureAssessment:
    overall_score: float
    accuracy: float
    fluency: float
    completeness: float
    prosody: float | None
    recognized_text: str
    words: list[dict] = field(default_factory=list)     # {word, status, score, phonemes:[{phoneme, score}]}
    extra_words: list[str] = field(default_factory=list)
    sound_tips: list[dict] = field(default_factory=list)


def is_enabled() -> bool:
    return bool(settings.AZURE_SPEECH_KEY and settings.AZURE_SPEECH_REGION)


def _endpoint() -> str:
    return (
        f"https://{settings.AZURE_SPEECH_REGION}.stt.speech.microsoft.com"
        "/speech/recognition/conversation/cognitiveservices/v1?language=en-US&format=detailed"
    )


def _assessment_header(reference_text: str) -> str:
    params = {
        "ReferenceText": reference_text,
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",
        "Dimension": "Comprehensive",
        "EnableMiscue": True,
        "EnableProsodyAssessment": True,
        "PhonemeAlphabet": "IPA",
    }
    return base64.b64encode(json.dumps(params).encode("utf-8")).decode("ascii")


def call_azure(wav_bytes: bytes, reference_text: str) -> dict:
    """Raw Azure response (JSON). Separated so tests can stub it."""
    response = httpx.post(
        _endpoint(),
        headers={
            "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
            "Pronunciation-Assessment": _assessment_header(reference_text),
        },
        content=wav_bytes,
        timeout=30,
    )
    if response.status_code >= 300:
        raise AzureUnavailable(f"Azure speech {response.status_code}: {response.text[:200]}")
    return response.json()


def _pa(node: dict) -> dict:
    """Pronunciation fields live under 'PronunciationAssessment' (or inline on older shapes)."""
    inner = node.get("PronunciationAssessment")
    return inner if isinstance(inner, dict) else node


def _score(node: dict, key: str = "AccuracyScore") -> float | None:
    value = _pa(node).get(key)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def map_response(data: dict, reference_text: str) -> AzureAssessment:
    """Turn Azure's NBest[0] into the app's per-word / per-phoneme verdict."""
    if data.get("RecognitionStatus") not in (None, "Success"):
        raise AzureUnavailable(f"Azure recognition status {data.get('RecognitionStatus')}")
    nbest = data.get("NBest") or []
    if not nbest:
        raise AzureUnavailable("Azure returned no hypothesis")
    best = nbest[0]
    summary = _pa(best)

    words: list[dict] = []
    extra: list[str] = []
    for w in best.get("Words") or []:
        text = _normalize(str(w.get("Word", "")))
        word = text[0] if text else ""
        if not word:
            continue
        pa = _pa(w)
        error = str(pa.get("ErrorType") or "None")
        score = _score(w)
        phonemes = [
            {"phoneme": str(p.get("Phoneme", "")), "score": _score(p)}
            for p in (w.get("Phonemes") or [])
            if p.get("Phoneme")
        ]
        if error == "Insertion":
            extra.append(word)
            continue
        if error == "Omission":
            status = "missed"
        elif error == "Mispronunciation" or (score is not None and score < WORD_PASS_SCORE):
            status = "wrong"
        else:
            status = "ok"
        words.append({"word": word, "status": status, "score": score, "phonemes": phonemes})

    # Azure sometimes omits reference words entirely when nothing was said: keep the
    # target order and mark anything missing as "missed".
    present = {w["word"] for w in words}
    for target_word in _normalize(reference_text):
        if target_word not in present:
            words.append({"word": target_word, "status": "missed", "score": None, "phonemes": []})
            present.add(target_word)

    accuracy = float(summary.get("AccuracyScore") or 0.0)
    fluency = float(summary.get("FluencyScore") or 0.0)
    completeness = float(summary.get("CompletenessScore") or 0.0)
    prosody_raw = summary.get("ProsodyScore")
    prosody = float(prosody_raw) if prosody_raw is not None else None
    overall = float(summary.get("PronScore") or (accuracy * 0.6 + fluency * 0.2 + completeness * 0.2))

    tips = _merge_tips(sound_tips(words), words)
    return AzureAssessment(
        overall_score=overall,
        accuracy=accuracy,
        fluency=fluency,
        completeness=completeness,
        prosody=prosody,
        recognized_text=str(best.get("Display") or best.get("Lexical") or data.get("DisplayText") or ""),
        words=words,
        extra_words=extra,
        sound_tips=tips,
    )


def _merge_tips(base: list[dict], words: list[dict], limit: int = 3) -> list[dict]:
    """Add tips for phonemes that scored low even inside words that passed."""
    by_sound = {t["sound"]: t for t in base}
    rule_by_id = {rule_id: (sound, tip) for rule_id, sound, tip, _ in _SOUND_RULES}
    for w in words:
        for p in w.get("phonemes") or []:
            score = p.get("score")
            if score is None or score >= PHONEME_PASS_SCORE:
                continue
            rule_id = _PHONEME_RULE.get(p["phoneme"])
            if not rule_id:
                continue
            sound, tip = rule_by_id[rule_id]
            entry = by_sound.setdefault(sound, {"sound": sound, "tip_vi": tip, "words": []})
            if w["word"] not in entry["words"] and len(entry["words"]) < 4:
                entry["words"].append(w["word"])
    return list(by_sound.values())[:limit]


def assess(wav_bytes: bytes, reference_text: str) -> AzureAssessment:
    if not is_enabled():
        raise AzureUnavailable("Azure Speech is not configured")
    if not wav_bytes or len(wav_bytes) > MAX_AUDIO_BYTES:
        raise AzureUnavailable("Audio is empty or too long")
    try:
        data = call_azure(wav_bytes, reference_text)
    except httpx.HTTPError as exc:
        raise AzureUnavailable(f"Azure speech request failed: {exc}") from exc
    return map_response(data, reference_text)
