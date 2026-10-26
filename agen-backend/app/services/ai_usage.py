"""
G10 · AI cost tracking per user and per feature.

Every successful LLM call (llm_client) and every TTS synthesis that missed the
cache (tts_service) writes one AiUsage row with an estimated USD cost
(characters / 4 ≈ tokens × the price in settings). Recording never raises: a
broken usage table must not break a lesson. `check_daily_limit` lets the LLM
client refuse a user that went over the optional per-day budget; callers then
take their normal fallback path.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.timeutil import local_day_start_utc
from app.core.usage_context import current_feature, current_user_id
from app.models.ai_usage import AiUsage

logger = logging.getLogger("agen.ai_usage")

# Tests swap this for their own session factory.
_session_factory = SessionLocal

CHARS_PER_TOKEN = 4


def llm_cost_usd(provider: str, input_chars: int, output_chars: int) -> float:
    if provider == "openai":
        p_in, p_out = settings.AI_PRICE_OPENAI_IN, settings.AI_PRICE_OPENAI_OUT
    else:
        p_in, p_out = settings.AI_PRICE_GEMINI_IN, settings.AI_PRICE_GEMINI_OUT
    tokens_in = input_chars / CHARS_PER_TOKEN
    tokens_out = output_chars / CHARS_PER_TOKEN
    return round((tokens_in * p_in + tokens_out * p_out) / 1_000_000, 8)


def tts_cost_usd(chars: int) -> float:
    return round(chars * settings.TTS_PRICE_PER_MCHAR / 1_000_000, 8)


def record(provider: str, model: Optional[str], input_chars: int, output_chars: int, cost_usd: float,
           feature: Optional[str] = None, user_id: Optional[str] = None) -> None:
    try:
        db = _session_factory()
        try:
            db.add(AiUsage(user_id=user_id or current_user_id.get(), feature=(feature or current_feature.get() or "other")[:60],
                           provider=provider[:20], model=(model or None) and model[:60], input_chars=max(0, int(input_chars)),
                           output_chars=max(0, int(output_chars)), cost_usd=max(0.0, float(cost_usd))))
            db.commit()
        finally:
            db.close()
    except Exception:  # usage stats are best-effort
        logger.warning("Could not record AI usage", exc_info=True)


def record_llm(provider: str, model: str, prompt: str, response: str) -> None:
    record(provider, model, len(prompt or ""), len(response or ""), llm_cost_usd(provider, len(prompt or ""), len(response or "")))


def record_tts(provider: str, model: str, text: str) -> None:
    record(provider, model, len(text or ""), 0, tts_cost_usd(len(text or "")), feature="tts")


def _day_start() -> datetime:
    """Start of today (VN) as naive UTC, matching how the DB stores times."""
    return local_day_start_utc().replace(tzinfo=None)


def spent_today_usd(db, user_id: str) -> float:
    total = db.query(func.coalesce(func.sum(AiUsage.cost_usd), 0.0)).filter(
        AiUsage.user_id == user_id, AiUsage.created_at >= _day_start()).scalar()
    return float(total or 0.0)


def daily_limit_for(db, user_id: str) -> float:
    from app.services.subscription_service import is_premium
    try:
        premium = is_premium(db, user_id)
    except Exception:
        premium = False
    return settings.AI_DAILY_LIMIT_USD_PREMIUM if premium else settings.AI_DAILY_LIMIT_USD_FREE


def over_daily_limit(user_id: Optional[str] = None) -> bool:
    """True when the current user already spent their per-day AI budget. Fails open."""
    user_id = user_id or current_user_id.get()
    if not user_id or (settings.AI_DAILY_LIMIT_USD_FREE <= 0 and settings.AI_DAILY_LIMIT_USD_PREMIUM <= 0):
        return False
    try:
        db = _session_factory()
        try:
            limit = daily_limit_for(db, user_id)
            return limit > 0 and spent_today_usd(db, user_id) >= limit
        finally:
            db.close()
    except Exception:
        logger.warning("AI daily limit check failed (allowing the call)", exc_info=True)
        return False


def summary(db, days: int = 30) -> dict:
    """Admin view: totals, per day, per feature, per provider and the top users."""
    from app.core.timeutil import local_date
    from app.models.user import User
    from app.services.subscription_service import is_premium

    today_start = _day_start()
    since = today_start - timedelta(days=max(1, days) - 1)
    rows = db.query(AiUsage).filter(AiUsage.created_at >= since).all()

    def total(start) -> float:
        return round(sum(r.cost_usd or 0 for r in rows if r.created_at >= start), 6)

    by_day: dict[str, dict] = {}
    by_feature: dict[str, dict] = {}
    by_provider: dict[str, dict] = {}
    by_user: dict[str, dict] = {}
    for r in rows:
        day = local_date(r.created_at).isoformat()
        for bucket, key in ((by_day, day), (by_feature, r.feature or "other"), (by_provider, r.provider or "?")):
            b = bucket.setdefault(key, {"key": key, "calls": 0, "cost_usd": 0.0})
            b["calls"] += 1
            b["cost_usd"] += r.cost_usd or 0
        if r.user_id:
            u = by_user.setdefault(r.user_id, {"user_id": r.user_id, "calls": 0, "cost_usd": 0.0})
            u["calls"] += 1
            u["cost_usd"] += r.cost_usd or 0

    top = sorted(by_user.values(), key=lambda u: u["cost_usd"], reverse=True)[:20]
    users = {u.id: u for u in db.query(User).filter(User.id.in_([t["user_id"] for t in top])).all()} if top else {}
    for t in top:
        user = users.get(t["user_id"])
        t["email"] = getattr(user, "email", None)
        t["role"] = getattr(user, "role", None)
        t["premium"] = bool(user and is_premium(db, user.id))
        t["cost_usd"] = round(t["cost_usd"], 6)
        t["cost_vnd"] = round(t["cost_usd"] * settings.USD_TO_VND)

    def finish(bucket: dict) -> list[dict]:
        out = sorted(bucket.values(), key=lambda b: b["cost_usd"], reverse=True)
        for b in out:
            b["cost_usd"] = round(b["cost_usd"], 6)
        return out

    month = total(since)
    return {
        "days": days,
        "usd_to_vnd": settings.USD_TO_VND,
        "today_usd": total(today_start),
        "week_usd": total(today_start - timedelta(days=6)),
        "period_usd": month,
        "period_vnd": round(month * settings.USD_TO_VND),
        "calls": len(rows),
        "users_with_usage": len(by_user),
        "avg_per_user_usd": round(month / len(by_user), 6) if by_user else 0.0,
        "limits": {"free_usd": settings.AI_DAILY_LIMIT_USD_FREE, "premium_usd": settings.AI_DAILY_LIMIT_USD_PREMIUM},
        "by_day": sorted(finish(by_day), key=lambda b: b["key"]),
        "by_feature": finish(by_feature),
        "by_provider": finish(by_provider),
        "top_users": top,
    }
