"""Shared rate limiter, keyed by the real client IP."""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def client_ip(request: Request) -> str:
    """
    The caller's IP. Behind Render's proxy every request arrives from the proxy,
    so without this all users would share one rate-limit bucket. The proxy
    appends the address it saw as the LAST X-Forwarded-For entry; earlier
    entries are client-supplied and must not be trusted.
    """
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip, default_limits=["200/minute"])
