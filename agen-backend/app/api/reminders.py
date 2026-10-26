"""
AGEN — Reminders API
Daily reminder settings, web push subscriptions, email unsubscribe and the
scheduler hook that sends due reminders.
"""
import hmac
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import limiter
from app.core.security import get_current_user
from app.core.timeutil import LEARNER_TZ
from app.models.learner_profile import LearnerProfile
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.services.reminders import (
    compose_message, push_to_learner, run_due_reminders, send_email, user_id_from_unsubscribe_token,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class ReminderSettingsOut(BaseModel):
    hour: Optional[int]               # local hour 0–23, None = off
    email: bool
    push_devices: int
    push_available: bool              # server has VAPID keys
    push_public_key: Optional[str]
    email_available: bool             # server can send email
    email_address: str


class ReminderSettingsIn(BaseModel):
    hour: Optional[int] = Field(default=None, ge=0, le=23)
    email: bool = False


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=1, max_length=200)
    auth: str = Field(min_length=1, max_length=100)


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(min_length=1, max_length=2000)
    keys: PushKeys


class PushUnsubscribeIn(BaseModel):
    endpoint: str = Field(min_length=1, max_length=2000)


class TestResult(BaseModel):
    push: int
    email: bool


class UnsubscribeIn(BaseModel):
    token: str = Field(min_length=1, max_length=1000)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


def _settings_out(db: Session, learner: LearnerProfile, user: User) -> ReminderSettingsOut:
    devices = db.query(PushSubscription).filter(PushSubscription.learner_id == learner.id).count()
    return ReminderSettingsOut(
        hour=learner.reminder_hour,
        email=bool(learner.reminder_email),
        push_devices=devices,
        push_available=settings.push_enabled,
        push_public_key=settings.VAPID_PUBLIC_KEY or None,
        email_available=settings.email_enabled,
        email_address=user.email,
    )


# ── Learner endpoints ─────────────────────────────────────────────────────────
@router.get("/settings", response_model=ReminderSettingsOut)
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _settings_out(db, _get_learner(db, current_user.id), current_user)


@router.put("/settings", response_model=ReminderSettingsOut)
def update_settings(
    payload: ReminderSettingsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(db, current_user.id)
    learner.reminder_hour = payload.hour
    learner.reminder_email = payload.email
    db.commit()
    return _settings_out(db, learner, current_user)


@router.post("/push-subscriptions", response_model=ReminderSettingsOut)
def add_push_subscription(
    payload: PushSubscriptionIn,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.endpoint.startswith("https://"):
        raise HTTPException(status_code=422, detail="Push endpoint must be https.")
    learner = _get_learner(db, current_user.id)
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if sub is None:
        sub = PushSubscription(endpoint=payload.endpoint, learner_id=learner.id, p256dh="", auth="")
        db.add(sub)
    # A browser re-subscribing (or a shared device) moves the endpoint to this learner.
    sub.learner_id = learner.id
    sub.p256dh = payload.keys.p256dh
    sub.auth = payload.keys.auth
    sub.user_agent = (request.headers.get("user-agent") or "")[:300]
    db.commit()
    return _settings_out(db, learner, current_user)


@router.delete("/push-subscriptions", response_model=ReminderSettingsOut)
def remove_push_subscription(
    payload: PushUnsubscribeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learner = _get_learner(db, current_user.id)
    db.query(PushSubscription).filter(
        PushSubscription.endpoint == payload.endpoint, PushSubscription.learner_id == learner.id,
    ).delete(synchronize_session=False)
    db.commit()
    return _settings_out(db, learner, current_user)


@router.post("/test", response_model=TestResult)
@limiter.limit("3/minute")
def send_test_reminder(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send the reminder the learner would get, right now, to check it arrives."""
    from datetime import datetime, timezone

    learner = _get_learner(db, current_user.id)
    message = compose_message(db, learner, datetime.now(timezone.utc).astimezone(LEARNER_TZ))
    pushed = push_to_learner(db, learner, message)
    emailed = bool(learner.reminder_email and send_email(current_user.email, message, current_user.id))
    db.commit()
    return TestResult(push=pushed, email=emailed)


@router.post("/unsubscribe-email")
def unsubscribe_email(payload: UnsubscribeIn, db: Session = Depends(get_db)):
    """One-click email opt-out from the link in a reminder email (no login)."""
    user_id = user_id_from_unsubscribe_token(payload.token)
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first() if user_id else None
    if not learner:
        raise HTTPException(status_code=400, detail="Liên kết không hợp lệ.")
    learner.reminder_email = False
    db.commit()
    return {"ok": True}


# ── Scheduler hook ────────────────────────────────────────────────────────────
@router.post("/cron/run")
def run_reminders(
    x_cron_secret: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Called hourly by the scheduler (see .github/workflows/reminders.yml)."""
    secret = settings.cron_secret
    if not secret or not hmac.compare_digest(x_cron_secret, secret):
        raise HTTPException(status_code=403, detail="Forbidden")
    return run_due_reminders(db)
