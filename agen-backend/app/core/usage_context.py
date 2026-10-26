"""
G10 · Request-scoped "who is using AI right now" for cost tracking.

A pure ASGI middleware (main.py) reads the Bearer token's `sub` and the API
area before the request runs; the orchestrator narrows the feature to the agent
name. llm_client / tts_service read these to attribute each call. Background
jobs (cron, content factory) run without a user, so their rows have user_id=None.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

current_user_id: ContextVar[Optional[str]] = ContextVar("agen_current_user_id", default=None)
current_feature: ContextVar[Optional[str]] = ContextVar("agen_current_feature", default=None)


def feature_from_path(path: str) -> str:
    """'/api/v1/lessons/generate' → 'lessons'."""
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 3 and parts[0] == "api":
        return parts[2][:60]
    return (parts[0] if parts else "root")[:60]


class UsageContextMiddleware:
    """Pure ASGI (no BaseHTTPMiddleware) so contextvars reach the endpoint and its threadpool."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        user_id = None
        for name, value in scope.get("headers") or []:
            if name == b"authorization":
                raw = value.decode("latin-1")
                if raw.lower().startswith("bearer "):
                    from app.core.security import decode_access_token
                    payload = decode_access_token(raw[7:].strip())
                    if payload and payload.get("type") != "refresh":
                        user_id = payload.get("sub")
                break
        t_user = current_user_id.set(user_id)
        t_feat = current_feature.set(feature_from_path(scope.get("path") or ""))
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_id.reset(t_user)
            current_feature.reset(t_feat)
