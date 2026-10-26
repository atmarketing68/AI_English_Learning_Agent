"""
G2 · Giọng đọc neural tạo ở server + cache.

Provider chain follows the LLM order (Gemini → OpenAI) unless TTS_PROVIDER pins
one. Everything is optional: with no key, or TTS_PROVIDER=off, `synthesize()`
returns None and the web app falls back to the browser's own voice.

Costs are bounded two ways:
  - a disk cache keyed by (provider, model, voice, text) — a lesson sentence is
    generated once for every learner;
  - a daily character budget (TTS_DAILY_CHAR_LIMIT) counted only on cache misses.
"""
from __future__ import annotations

import base64
import hashlib
import io
import logging
import os
import re
import threading
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("agen.tts")

MAX_TEXT_CHARS = 600
VOICES = {
    "gemini": {"female": "Kore", "male": "Puck"},
    "openai": {"female": "nova", "male": "onyx"},
}
_MIME_EXT = {"audio/mpeg": "mp3", "audio/wav": "wav"}
_lock = threading.Lock()
_budget = {"day": "", "chars": 0}


@dataclass
class TTSResult:
    data: bytes
    mime: str
    provider: str
    cached: bool


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text[:MAX_TEXT_CHARS]


def normalize_voice(voice: Optional[str]) -> str:
    return "male" if (voice or "").lower() == "male" else "female"


def providers() -> list[str]:
    """Providers to try, in order. Empty = server TTS off."""
    mode = (settings.TTS_PROVIDER or "auto").lower()
    if mode == "off":
        return []
    available = []
    if settings.GEMINI_API_KEY:
        available.append("gemini")
    if settings.OPENAI_API_KEY:
        available.append("openai")
    if mode == "auto":
        return available
    return [mode] if mode in available else []


def is_enabled() -> bool:
    return bool(providers())


# ── Cache ────────────────────────────────────────────────────────────────────
def _cache_dir() -> Path:
    path = Path(settings.TTS_CACHE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_key(provider: str, model: str, voice: str, text: str) -> str:
    return hashlib.sha1(f"{provider}|{model}|{voice}|{text.lower()}".encode("utf-8")).hexdigest()


def _cache_get(key: str) -> Optional[tuple[bytes, str]]:
    for mime, ext in _MIME_EXT.items():
        file = _cache_dir() / f"{key}.{ext}"
        if file.exists():
            try:
                return file.read_bytes(), mime
            except OSError:
                return None
    return None


def _cache_put(key: str, data: bytes, mime: str) -> None:
    ext = _MIME_EXT.get(mime, "bin")
    try:
        (_cache_dir() / f"{key}.{ext}").write_bytes(data)
        _evict_if_needed()
    except OSError:
        logger.warning("TTS cache write failed", exc_info=True)


def _evict_if_needed() -> None:
    files = [p for p in _cache_dir().iterdir() if p.is_file()]
    limit = settings.TTS_CACHE_MAX_FILES
    if len(files) <= limit:
        return
    files.sort(key=lambda p: p.stat().st_mtime)
    for p in files[: max(1, len(files) - int(limit * 0.9))]:
        try:
            p.unlink()
        except OSError:
            pass


# ── Daily budget ─────────────────────────────────────────────────────────────
def _budget_allows(chars: int) -> bool:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    with _lock:
        if _budget["day"] != today:
            _budget["day"], _budget["chars"] = today, 0
        if _budget["chars"] + chars > settings.TTS_DAILY_CHAR_LIMIT:
            return False
        _budget["chars"] += chars
        return True


def budget_used_today() -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return _budget["chars"] if _budget["day"] == today else 0


# ── Providers ────────────────────────────────────────────────────────────────
def _model_for(provider: str) -> str:
    return settings.GEMINI_TTS_MODEL if provider == "gemini" else settings.OPENAI_TTS_MODEL


def _pcm_to_wav(pcm: bytes, rate: int = 24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def _call_gemini(text: str, voice: str) -> tuple[bytes, str]:
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=30_000),
    )
    response = client.models.generate_content(
        model=settings.GEMINI_TTS_MODEL,
        contents=f"Read this aloud clearly, at a natural pace, as an English teacher: {text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICES["gemini"][voice])
                )
            ),
        ),
    )
    part = response.candidates[0].content.parts[0]
    inline = part.inline_data
    data = inline.data
    if isinstance(data, str):
        data = base64.b64decode(data)
    mime = (inline.mime_type or "").lower()
    if mime.startswith("audio/l16") or mime in ("", "audio/pcm"):
        rate = 24000
        m = re.search(r"rate=(\d+)", mime)
        if m:
            rate = int(m.group(1))
        return _pcm_to_wav(data, rate), "audio/wav"
    if "mpeg" in mime or "mp3" in mime:
        return data, "audio/mpeg"
    return _pcm_to_wav(data), "audio/wav"


def _call_openai(text: str, voice: str) -> tuple[bytes, str]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30, max_retries=0)
    response = client.audio.speech.create(
        model=settings.OPENAI_TTS_MODEL,
        voice=VOICES["openai"][voice],
        input=text,
        response_format="mp3",
    )
    return response.content, "audio/mpeg"


_CALLERS = {"gemini": _call_gemini, "openai": _call_openai}


def synthesize(text: str, voice: str = "female") -> Optional[TTSResult]:
    """Audio for `text`, from cache or a provider. None → let the client fall back."""
    text = normalize_text(text)
    voice = normalize_voice(voice)
    chain = providers()
    if not text or not chain:
        return None

    # Any provider's cached file is fine — the voice is consistent per provider.
    for provider in chain:
        hit = _cache_get(_cache_key(provider, _model_for(provider), voice, text))
        if hit:
            return TTSResult(hit[0], hit[1], provider, cached=True)

    if not _budget_allows(len(text)):
        logger.warning("TTS daily character budget exhausted; falling back to browser voice")
        return None

    for provider in chain:
        try:
            data, mime = _CALLERS[provider](text, voice)
            if not data:
                raise RuntimeError("empty audio")
            _cache_put(_cache_key(provider, _model_for(provider), voice, text), data, mime)
            return TTSResult(data, mime, provider, cached=False)
        except Exception as exc:  # provider down / model renamed / quota — try the next one
            logger.warning("TTS provider %s failed: %s", provider, exc)
    return None
