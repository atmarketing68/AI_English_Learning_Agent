"""
Daily learning reminders (G1 · nhắc học): web push + email.

A scheduler (GitHub Actions, hourly) calls run_due_reminders(). Learners
whose chosen hour has come, who have not studied yet today and were not
reminded today get one message, personalised from their streak, due reviews
and unfinished quests. Each channel is skipped while it is not configured.
"""
import html
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from jose import JWTError, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.timeutil import LEARNER_TZ
from app.models.learner_profile import LearnerProfile
from app.models.push_subscription import PushSubscription
from app.models.review_item import ReviewItem
from app.models.user import User
from app.services.notification_service import create_notification
from app.services.streak_service import streak_state

logger = logging.getLogger("agen.reminders")

# Send within this many hours after the chosen hour, so a late or missed
# scheduler run still delivers the day's reminder.
SEND_WINDOW_HOURS = 3
UNSUBSCRIBE_TOKEN_TYPE = "reminder_unsubscribe"


@dataclass
class ReminderMessage:
    title: str
    body: str
    url: str


def compose_message(db: Session, learner: LearnerProfile, now_local: datetime) -> ReminderMessage:
    """Pick the most motivating reason to study right now."""
    state = streak_state(learner, now_local.date())
    due = (
        db.query(func.count(ReviewItem.id))
        .filter(ReviewItem.learner_id == learner.id, ReviewItem.due_at <= datetime.now(timezone.utc).replace(tzinfo=None))
        .scalar()
        or 0
    )
    name = learner.display_name or "bạn"
    if state.current >= 2:
        return ReminderMessage(
            title=f"🔥 Giữ chuỗi {state.current} ngày nhé, {name}!",
            body="Chỉ cần 1 bài ngắn hôm nay là chuỗi được giữ."
            + (f" Có {due} từ đang chờ bạn ôn." if due else ""),
            url="/dashboard",
        )
    if due:
        return ReminderMessage(
            title=f"🧠 {due} từ đang chờ bạn ôn",
            body="Ôn đúng lúc sắp quên giúp nhớ lâu gấp nhiều lần. Mất khoảng "
            f"{max(1, round(due * 0.25))} phút thôi.",
            url="/review",
        )
    return ReminderMessage(
        title=f"📚 Đến giờ học tiếng Anh rồi, {name}!",
        body=f"{learner.daily_study_minutes or 15} phút mỗi ngày — làm 3 nhiệm vụ hôm nay để nhận XP.",
        url="/dashboard",
    )


# ── Web push ─────────────────────────────────────────────────────────────────
def send_push(db: Session, sub: PushSubscription, message: ReminderMessage, tag: str = "daily-reminder") -> bool:
    """Deliver one push. Expired subscriptions are deleted. Returns success."""
    from pywebpush import WebPushException, webpush  # heavy import, only when sending

    payload = {"title": message.title, "body": message.body, "url": message.url, "tag": tag}
    try:
        webpush(
            subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
            ttl=6 * 3600,
            timeout=10,
        )
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            db.delete(sub)
        else:
            logger.warning("Web push failed (%s): %s", status, exc)
        return False
    except Exception as exc:  # network errors etc. must not stop the batch
        logger.warning("Web push failed: %s", exc)
        return False
    sub.last_sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
    return True


def push_to_learner(db: Session, learner: LearnerProfile, message: ReminderMessage) -> int:
    if not settings.push_enabled:
        return 0
    subs = db.query(PushSubscription).filter(PushSubscription.learner_id == learner.id).all()
    return sum(send_push(db, sub, message) for sub in subs)


def push_to_user(db: Session, user_id: str, message: ReminderMessage, tag: str = "parent-alert") -> int:
    """G7 · Push to a non-learner account's devices (parents)."""
    if not settings.push_enabled:
        return 0
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    return sum(send_push(db, sub, message, tag) for sub in subs)


# ── Email ────────────────────────────────────────────────────────────────────
def unsubscribe_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "type": UNSUBSCRIBE_TOKEN_TYPE}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def user_id_from_unsubscribe_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub") if payload.get("type") == UNSUBSCRIBE_TOKEN_TYPE else None


def _email_html(message: ReminderMessage, unsubscribe_url: str) -> str:
    link = settings.app_url + message.url
    return f"""<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:0 auto;padding:24px;color:#1d1d1f">
  <p style="font-size:13px;color:#86868b;margin:0 0 16px">AI AGENT ENGLISH</p>
  <h1 style="font-size:22px;margin:0 0 12px">{html.escape(message.title)}</h1>
  <p style="font-size:15px;line-height:1.5;margin:0 0 24px">{html.escape(message.body)}</p>
  <a href="{html.escape(link)}" style="display:inline-block;background:#0071e3;color:#fff;text-decoration:none;padding:12px 22px;border-radius:999px;font-weight:600">Học ngay</a>
  <p style="font-size:12px;color:#86868b;margin:32px 0 0">Bạn nhận email này vì đã bật nhắc học hằng ngày.
  <a href="{html.escape(unsubscribe_url)}" style="color:#86868b">Tắt email nhắc học</a></p>
</div>"""


def deliver_email(to: str, subject: str, html_body: str, text: str, unsubscribe_url: str | None = None) -> bool:
    """Send one e-mail through Resend. False (and a log line) on any failure."""
    if not settings.email_enabled:
        return False
    payload = {"from": settings.EMAIL_FROM, "to": [to], "subject": subject, "html": html_body, "text": text}
    if unsubscribe_url:
        payload["headers"] = {"List-Unsubscribe": f"<{unsubscribe_url}>"}
    try:
        res = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json=payload,
            timeout=10,
        )
    except httpx.HTTPError as exc:
        logger.warning("Email failed: %s", exc)
        return False
    if res.status_code >= 300:
        logger.warning("Email rejected (%s): %s", res.status_code, res.text[:200])
        return False
    return True


def send_email(to: str, message: ReminderMessage, user_id: str) -> bool:
    if not settings.email_enabled:
        return False
    unsubscribe_url = f"{settings.app_url}/unsubscribe?token={unsubscribe_token(user_id)}"
    return deliver_email(
        to, message.title, _email_html(message, unsubscribe_url),
        f"{message.title}\n\n{message.body}\n\n{settings.app_url}{message.url}\n\nTắt email nhắc học: {unsubscribe_url}",
        unsubscribe_url=unsubscribe_url,
    )


# ── Scheduler entry point ────────────────────────────────────────────────────
def remind(db: Session, learner: LearnerProfile, user: User, now_local: datetime) -> dict:
    """Send one learner's reminder on every enabled channel."""
    message = compose_message(db, learner, now_local)
    pushed = push_to_learner(db, learner, message)
    emailed = bool(learner.reminder_email and user.email and send_email(user.email, message, user.id))
    create_notification(db, learner.id, type="reminder", title=message.title, body=message.body, icon="⏰")
    return {"push": pushed, "email": int(emailed)}


def run_due_reminders(db: Session, now: datetime | None = None) -> dict:
    now_local = (now or datetime.now(timezone.utc)).astimezone(LEARNER_TZ)
    today = now_local.date()
    hour = now_local.hour
    candidates = (
        db.query(LearnerProfile, User)
        .join(User, User.id == LearnerProfile.user_id)
        .filter(
            LearnerProfile.reminder_hour.isnot(None),
            LearnerProfile.reminder_hour <= hour,
            LearnerProfile.reminder_hour > hour - SEND_WINDOW_HOURS,
            (LearnerProfile.last_reminder_on.is_(None)) | (LearnerProfile.last_reminder_on != today.isoformat()),
            User.is_active.isnot(False),
        )
        .all()
    )
    stats = {"checked": len(candidates), "reminded": 0, "skipped_studied": 0, "push": 0, "email": 0}
    for learner, user in candidates:
        if streak_state(learner, today).studied_today:
            stats["skipped_studied"] += 1
            continue
        sent = remind(db, learner, user, now_local)
        learner.last_reminder_on = today.isoformat()
        stats["reminded"] += 1
        stats["push"] += sent["push"]
        stats["email"] += sent["email"]
        db.commit()
    return stats
