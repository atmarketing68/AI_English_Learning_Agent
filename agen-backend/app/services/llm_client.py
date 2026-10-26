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

# Phrases that indicate quota/rate-limit errors (case-insensitive)
_QUOTA_PHRASES = (
    "quota", "resource_exhausted", "rate_limit",
    "429", "too many requests", "limit exceeded",
)

ModelT = TypeVar("ModelT", bound=BaseModel)


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

    failures: list[str] = []
    quota_hit = False

    for provider in providers:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                if provider == "gemini":
                    return _call_gemini(prompt)
                return _call_openai(prompt)
            except Exception as exc:
                is_quota = _is_quota_error(exc)
                if is_quota:
                    quota_hit = True
                failures.append(f"{provider} attempt {attempt}: {exc}")
                logger.warning(
                    "LLM %s failed (attempt %d/%d, quota=%s): %s",
                    provider, attempt, MAX_ATTEMPTS, is_quota, exc,
                )
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


def _call_gemini(prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    # Use Chat (Interactions API) — avoids AFC warning
    chat = client.chats.create(model="gemini-3.6-flash")
    response = chat.send_message(prompt)
    return response.text


def _call_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0, max_retries=0)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
