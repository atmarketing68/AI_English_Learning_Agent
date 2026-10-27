"""
AGEN - LLM Client
Resilient provider gateway with retry, quota detection and user-friendly errors.
Supports Gemini (priority) and OpenAI (fallback).
"""
import json
import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger("agen.llm")

# Retry config
MAX_ATTEMPTS = 3           # per provider
RETRY_DELAYS = [1.5, 4.0]  # seconds between retries
REQUEST_TIMEOUT_S = 45     # per provider call, so a hung request cannot hold a worker indefinitely

# Phrases that indicate quota/rate-limit errors (case-insensitive)
_QUOTA_PHRASES = (
    "quota", "resource_exhausted", "rate_limit",
    "429", "too many requests", "limit exceeded",
)

ModelT = TypeVar("ModelT", bound=BaseModel)

def normal_model(provider: str) -> str:
    return settings.GEMINI_MODEL if provider == "gemini" else settings.OPENAI_MODEL


def economy_model(provider: str) -> str:
    """G12 · cheaper model while economy mode is on (empty setting → normal model)."""
    eco = settings.AI_ECONOMY_GEMINI_MODEL if provider == "gemini" else settings.AI_ECONOMY_OPENAI_MODEL
    return eco or normal_model(provider)


# Back-compat name used by older code/tests.
MODELS = {"gemini": settings.GEMINI_MODEL, "openai": settings.OPENAI_MODEL}


class LLMError(RuntimeError):
    """Raised when every configured LLM provider fails."""

    def __init__(self, message: str, is_quota: bool = False) -> None:
        super().__init__(message)
        self.is_quota_error = is_quota


def _is_quota_error(exc: Exception) -> bool:
    return any(p in str(exc).lower() for p in _QUOTA_PHRASES)


def _configured_providers() -> list[str]:
    providers: list[str] = []
    if settings.GEMINI_API_KEY:
        providers.append("gemini")
    if settings.OPENAI_API_KEY:
        providers.append("openai")
    return providers


def get_llm_response(prompt: str) -> str:
    """
    Call the configured LLM provider and return a text response.
    Priority: Gemini → OpenAI.
    Each provider is retried up to MAX_ATTEMPTS times with back-off.
    Raises LLMError (with is_quota_error flag) on total failure.
    """
    providers = _configured_providers()
    if not providers:
        raise LLMError(
            "Dịch vụ AI chưa được cấu hình bởi người vận hành. Vui lòng liên hệ quản trị viên pilot.",
            is_quota=False,
        )

    from app.services import ai_usage
    if ai_usage.over_daily_limit():
        # G10 · per-user daily AI budget: callers treat this like any quota error and fall back.
        raise LLMError(
            "Bạn đã dùng hết lượt AI hôm nay. Hãy quay lại vào ngày mai nhé!",
            is_quota=True,
        )

    failures: list[str] = []
    quota_hit = False
    economy = ai_usage.economy_active()

    for provider in providers:
        model = economy_model(provider) if economy else normal_model(provider)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                caller = _call_gemini if provider == "gemini" else _call_openai
                # keep the one-argument call for the normal model (tests and wrappers rely on it)
                text = caller(prompt) if model == normal_model(provider) else caller(prompt, model=model)
                ai_usage.record_llm(provider, model, prompt, text or "")
                return text
            except Exception as exc:
                is_quota = _is_quota_error(exc)
                if is_quota:
                    quota_hit = True
                failures.append(f"{provider} attempt {attempt}: {exc}")
                logger.warning(
                    "LLM %s failed (attempt %d/%d, quota=%s): %s",
                    provider, attempt, MAX_ATTEMPTS, is_quota, exc,
                )
                if model != normal_model(provider):
                    # G12 · the economy model failed (renamed, unavailable…): fall back to the normal one at once.
                    logger.warning("Economy model %s failed; retrying with %s", model, normal_model(provider))
                    model = normal_model(provider)
                    continue
                if is_quota:
                    # Retrying an exhausted quota only adds waiting; try the next provider.
                    break
                if attempt < MAX_ATTEMPTS:
                    delay = RETRY_DELAYS[attempt - 1] if attempt - 1 < len(RETRY_DELAYS) else 4.0
                    time.sleep(delay)

    user_msg = (
        "Hệ thống AI đang bận hoặc đã hết giới hạn sử dụng hôm nay. "
        "Vui lòng thử lại sau vài phút."
        if quota_hit else
        "Dịch vụ AI tạm thời không phản hồi. Vui lòng thử lại sau."
    )
    logger.error("All LLM providers failed (quota=%s): %s", quota_hit, " | ".join(failures))
    raise LLMError(user_msg, is_quota=quota_hit)


def _call_gemini(prompt: str, model: str | None = None) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_S * 1000),
    )
    # Use Chat (Interactions API) — avoids AFC warning
    chat = client.chats.create(model=model or settings.GEMINI_MODEL)
    response = chat.send_message(prompt)
    return response.text


def _call_openai(prompt: str, model: str | None = None) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=REQUEST_TIMEOUT_S, max_retries=0)
    response = client.chat.completions.create(
        model=model or settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── JSON utilities ─────────────────────────────────────────────────────────────
def parse_json_response(raw: str) -> Any:
    """Parse JSON from LLM response, tolerating markdown code fences."""
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean
        clean = clean.rsplit("```", 1)[0].strip()

    decoder = json.JSONDecoder()
    for index, char in enumerate(clean):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(clean[index:])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("LLM response did not contain valid JSON")


def parse_and_validate(raw: str, model: type[ModelT]) -> dict[str, Any]:
    """
    Parse an LLM response and validate it against a Pydantic contract.
    Returns a plain dict (exclude_none) ready for downstream use.
    """
    payload = parse_json_response(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object for {model.__name__}")
    return model.model_validate(payload).model_dump(exclude_none=True)
