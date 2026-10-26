"""
G9 · Zalo Official Account as a reminder channel.

Learners and parents follow the OA and send their link code; the webhook
stores the Zalo user id on the account. Reminders then go out as OA
"customer service" text messages (free within the 7-day interaction window,
which a daily reminder keeps open). Everything is off until the app
credentials exist; tokens rotate and the latest pair lives in app_config.

Docs: https://developers.zalo.me/docs/official-account/
"""
from __future__ import annotations

import hashlib
import json
import logging
import secrets
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.app_config import AppConfig
from app.models.user import User

logger = logging.getLogger("agen.zalo")

OAUTH_URL = "https://oauth.zaloapp.com/v4/oa/access_token"
MESSAGE_URL = "https://openapi.zalo.me/v3.0/oa/message/cs"
KEY_ACCESS = "zalo_access_token"
KEY_ACCESS_EXP = "zalo_access_token_exp"
KEY_REFRESH = "zalo_refresh_token"
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def enabled() -> bool:
    return settings.zalo_enabled


def oa_link() -> str | None:
    return f"https://zalo.me/{settings.ZALO_OA_ID}" if settings.ZALO_OA_ID else None


# ── app_config helpers ───────────────────────────────────────────────────────
def _get(db: Session, key: str) -> str | None:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return row.value if row else None


def _set(db: Session, key: str, value: str | None) -> None:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if row is None:
        row = AppConfig(key=key)
        db.add(row)
    row.value = value
    row.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)


# ── Tokens ───────────────────────────────────────────────────────────────────
def refresh_access_token(db: Session) -> str | None:
    """Exchange the (rotating) refresh token for a new access token; stores both."""
    refresh = _get(db, KEY_REFRESH) or settings.ZALO_OA_REFRESH_TOKEN
    if not refresh:
        return None
    try:
        resp = httpx.post(OAUTH_URL, data={"refresh_token": refresh, "app_id": settings.ZALO_APP_ID, "grant_type": "refresh_token"},
                          headers={"secret_key": settings.ZALO_APP_SECRET, "Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
        body = resp.json()
    except Exception as exc:
        logger.warning("Zalo token refresh failed: %s", exc)
        return None
    token = body.get("access_token")
    if not token:
        logger.warning("Zalo token refresh rejected: %s", str(body)[:200])
        return None
    _set(db, KEY_ACCESS, token)
    _set(db, KEY_ACCESS_EXP, str(int(time.time()) + int(body.get("expires_in", 86400))))
    if body.get("refresh_token"):
        _set(db, KEY_REFRESH, body["refresh_token"])
    db.commit()
    return token


def access_token(db: Session) -> str | None:
    if not enabled():
        return None
    token = _get(db, KEY_ACCESS) or settings.ZALO_OA_ACCESS_TOKEN or None
    exp = _get(db, KEY_ACCESS_EXP)
    if token and (not exp or int(exp) - 300 > time.time()):
        return token
    return refresh_access_token(db) or token


# ── Sending ──────────────────────────────────────────────────────────────────
def send_text(db: Session, zalo_user_id: str, text: str, _retry: bool = True) -> bool:
    token = access_token(db)
    if not token or not zalo_user_id:
        return False
    try:
        resp = httpx.post(MESSAGE_URL, json={"recipient": {"user_id": zalo_user_id}, "message": {"text": text[:2000]}},
                          headers={"access_token": token, "Content-Type": "application/json"}, timeout=10)
        body = resp.json()
    except Exception as exc:
        logger.warning("Zalo send failed: %s", exc)
        return False
    code = int(body.get("error", 0) or 0)
    if code == 0:
        return True
    if code in (-216, -124) and _retry:                 # access token expired / invalid → refresh once
        if refresh_access_token(db):
            return send_text(db, zalo_user_id, text, _retry=False)
    logger.warning("Zalo send error %s: %s", code, body.get("message"))
    return False


def send_to_user(db: Session, user: User, text: str) -> int:
    return int(bool(user.zalo_user_id) and send_text(db, user.zalo_user_id, text))


# ── Linking ──────────────────────────────────────────────────────────────────
def link_code_for(db: Session, user: User) -> str:
    """The code this person sends to the OA (created on first request)."""
    if not user.zalo_link_code:
        for _ in range(20):
            code = "ZL-" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(5))
            if not db.query(User).filter(User.zalo_link_code == code).first():
                user.zalo_link_code = code
                db.commit()
                break
    return user.zalo_link_code


def _normalize_code(text: str) -> str:
    return "".join(ch for ch in (text or "").upper() if ch.isalnum() or ch == "-").strip("-")


def link_by_code(db: Session, code_text: str, zalo_user_id: str) -> User | None:
    """Match a message text to a link code (ZL-XXXXX, or a learner's AGEN-XXXX invite code)."""
    code = _normalize_code(code_text)
    if not code:
        return None
    user = db.query(User).filter(User.zalo_link_code == code).first()
    if not user and code.startswith("AGEN-"):
        from app.models.learner_profile import LearnerProfile
        learner = db.query(LearnerProfile).filter(LearnerProfile.invite_code == code).first()
        user = db.query(User).filter(User.id == learner.user_id).first() if learner else None
    if not user:
        return None
    other = db.query(User).filter(User.zalo_user_id == zalo_user_id, User.id != user.id).first()
    if other:
        other.zalo_user_id = None                        # one Zalo account ↔ one AGEN account
    user.zalo_user_id = zalo_user_id
    db.commit()
    return user


def unlink(db: Session, user: User) -> None:
    user.zalo_user_id = None
    db.commit()


# ── Webhook ──────────────────────────────────────────────────────────────────
def verify_signature(raw_body: bytes, timestamp: str, signature: str) -> bool:
    """Zalo: X-ZEvent-Signature = "mac=" + sha256(appId + body + timestamp + OAsecretKey). Skipped while no secret key is set."""
    if not settings.ZALO_OA_SECRET_KEY:
        return True
    expected = hashlib.sha256((settings.ZALO_APP_ID + raw_body.decode("utf-8") + str(timestamp) + settings.ZALO_OA_SECRET_KEY).encode("utf-8")).hexdigest()
    given = (signature or "").replace("mac=", "").strip()
    return secrets.compare_digest(expected, given)


def handle_event(db: Session, event: dict) -> dict:
    """Process one webhook event. Returns what happened (for logs/tests)."""
    name = event.get("event_name", "")
    sender = (event.get("sender") or {}).get("id") or event.get("user_id_by_app") or ""
    if name == "user_send_text" and sender:
        text = (event.get("message") or {}).get("text", "")
        user = link_by_code(db, text, sender)
        if user:
            send_text(db, sender, "✅ Đã kết nối Zalo với tài khoản AI AGENT ENGLISH. Từ nay lời nhắc học và báo cáo sẽ được gửi vào đây. Nhắn \"TAT\" để tắt.")
            return {"action": "linked", "user_id": user.id}
        if _normalize_code(text) in ("TAT", "STOP", "OFF"):
            u = db.query(User).filter(User.zalo_user_id == sender).first()
            if u:
                unlink(db, u)
                send_text(db, sender, "Đã tắt nhắc qua Zalo. Gửi lại mã kết nối trong ứng dụng khi muốn bật.")
                return {"action": "unlinked", "user_id": u.id}
        send_text(db, sender, "Chào bạn! Để nhận nhắc học qua Zalo, mở AI AGENT ENGLISH → Nhắc học → Kết nối Zalo, rồi gửi mã (dạng ZL-XXXXX) vào đây.")
        return {"action": "help"}
    if name == "follow" and sender:
        send_text(db, sender, "Cảm ơn bạn đã quan tâm AI AGENT ENGLISH! Gửi mã kết nối từ ứng dụng (Nhắc học → Kết nối Zalo) để nhận lời nhắc.")
        return {"action": "welcome"}
    if name == "unfollow" and sender:
        u = db.query(User).filter(User.zalo_user_id == sender).first()
        if u:
            unlink(db, u)
            return {"action": "unlinked", "user_id": u.id}
    return {"action": "ignored", "event": name}


def parse_events(body: bytes) -> list[dict]:
    try:
        data = json.loads(body.decode("utf-8") or "{}")
    except ValueError:
        return []
    return data if isinstance(data, list) else [data]
