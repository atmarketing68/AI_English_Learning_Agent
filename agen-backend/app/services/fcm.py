"""
G8 · Native push through Firebase Cloud Messaging (HTTP v1) for the Capacitor app.

Off until FIREBASE_SERVICE_ACCOUNT_JSON holds a Firebase service-account key.
The OAuth2 access token is minted from that key with a signed JWT (RS256, via
python-jose) and cached until shortly before it expires — no Firebase SDK
needed. Unregistered tokens are deleted so the table cleans itself.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

import httpx
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.device_token import DeviceToken

logger = logging.getLogger("agen.fcm")

TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_cache: dict = {"token": None, "exp": 0.0}


def enabled() -> bool:
    return settings.fcm_enabled


def _service_account() -> dict | None:
    try:
        data = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
    except ValueError:
        logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON; native push disabled")
        return None
    if not all(data.get(k) for k in ("client_email", "private_key", "project_id")):
        logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON is missing client_email/private_key/project_id")
        return None
    return data


def access_token() -> str | None:
    """OAuth2 bearer token for the FCM API (cached ~55 minutes)."""
    if _cache["token"] and _cache["exp"] - 120 > time.time():
        return _cache["token"]
    sa = _service_account()
    if not sa:
        return None
    now = int(time.time())
    assertion = jwt.encode(
        {"iss": sa["client_email"], "scope": SCOPE, "aud": TOKEN_URL, "iat": now, "exp": now + 3600},
        sa["private_key"], algorithm="RS256",
    )
    try:
        resp = httpx.post(TOKEN_URL, data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}, timeout=10)
        resp.raise_for_status()
        body = resp.json()
    except Exception as exc:
        logger.warning("FCM token exchange failed: %s", exc)
        return None
    _cache["token"] = body.get("access_token")
    _cache["exp"] = time.time() + int(body.get("expires_in", 3600))
    return _cache["token"]


def send(db: Session, row: DeviceToken, title: str, body: str, url: str = "/dashboard", tag: str = "reminder") -> bool:
    """Send one notification. Returns success; drops tokens FCM reports as gone."""
    sa = _service_account()
    token = access_token() if sa else None
    if not token:
        return False
    payload = {
        "message": {
            "token": row.token,
            "notification": {"title": title, "body": body},
            "data": {"url": url, "tag": tag},
            "android": {"priority": "high", "notification": {"tag": tag, "click_action": "FLUTTER_NOTIFICATION_CLICK"}},
            "apns": {"payload": {"aps": {"sound": "default", "thread-id": tag}}},
        }
    }
    try:
        resp = httpx.post(
            f"https://fcm.googleapis.com/v1/projects/{sa['project_id']}/messages:send",
            json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=10,
        )
    except Exception as exc:
        logger.warning("FCM send failed: %s", exc)
        return False
    if resp.status_code == 200:
        row.last_sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return True
    text = resp.text or ""
    if resp.status_code == 404 or "UNREGISTERED" in text or "INVALID_ARGUMENT" in text:
        db.delete(row)                      # token no longer valid on this device
    else:
        logger.warning("FCM send failed (%s): %s", resp.status_code, text[:200])
    return False


def send_to_learner(db: Session, learner_id: str, title: str, body: str, url: str = "/dashboard", tag: str = "reminder") -> int:
    if not enabled():
        return 0
    rows = db.query(DeviceToken).filter(DeviceToken.learner_id == learner_id).all()
    return sum(send(db, r, title, body, url, tag) for r in rows)


def send_to_user(db: Session, user_id: str, title: str, body: str, url: str = "/dashboard", tag: str = "reminder") -> int:
    if not enabled():
        return 0
    rows = db.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()
    return sum(send(db, r, title, body, url, tag) for r in rows)


def register(db: Session, user_id: str, learner_id: str | None, token: str, platform: str) -> DeviceToken:
    """Upsert a device token (a token moves with the account that last registered it)."""
    platform = platform if platform in ("android", "ios") else "android"
    row = db.query(DeviceToken).filter(DeviceToken.token == token).first()
    if row:
        row.user_id, row.learner_id, row.platform = user_id, learner_id, platform
        return row
    row = DeviceToken(user_id=user_id, learner_id=learner_id, token=token, platform=platform)
    db.add(row)
    db.flush()
    return row


def unregister(db: Session, user_id: str, token: str) -> bool:
    row = db.query(DeviceToken).filter(DeviceToken.token == token, DeviceToken.user_id == user_id).first()
    if not row:
        return False
    db.delete(row)
    return True
