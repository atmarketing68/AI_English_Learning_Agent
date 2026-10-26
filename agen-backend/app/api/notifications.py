"""AGEN — Notifications API. Learner-facing in-app notification inbox."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.notification import Notification
from app.services import fcm

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class NotificationOut(BaseModel):
    id: str
    type: str
    title: str
    body: str | None
    icon: str | None
    is_read: bool
    created_at: datetime


class UnreadCountOut(BaseModel):
    unread: int


class DeviceTokenIn(BaseModel):
    token: str = Field(min_length=20, max_length=400)
    platform: str = Field(default="android", pattern="^(android|ios)$")


class DeviceTokenOut(BaseModel):
    id: str
    platform: str
    native_push_enabled: bool


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the learner's notifications, newest first."""
    learner = _get_learner(db, current_user.id)
    q = db.query(Notification).filter(Notification.learner_id == learner.id)
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    rows = q.order_by(Notification.created_at.desc()).limit(min(limit, 100)).all()
    return [
        NotificationOut(
            id=n.id, type=n.type, title=n.title, body=n.body, icon=n.icon,
            is_read=n.is_read, created_at=n.created_at,
        )
        for n in rows
    ]


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Number of unread notifications (for a badge)."""
    learner = _get_learner(db, current_user.id)
    count = (
        db.query(func.count(Notification.id))
        .filter(Notification.learner_id == learner.id, Notification.is_read.is_(False))
        .scalar()
    ) or 0
    return UnreadCountOut(unread=int(count))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single notification as read."""
    learner = _get_learner(db, current_user.id)
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.learner_id == learner.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông báo.")
    if not n.is_read:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        db.commit()
    db.refresh(n)
    return NotificationOut(
        id=n.id, type=n.type, title=n.title, body=n.body, icon=n.icon,
        is_read=n.is_read, created_at=n.created_at,
    )


@router.post("/read-all", response_model=UnreadCountOut)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all of the learner's notifications as read."""
    learner = _get_learner(db, current_user.id)
    db.query(Notification).filter(
        Notification.learner_id == learner.id,
        Notification.is_read.is_(False),
    ).update({"is_read": True, "read_at": datetime.now(timezone.utc)})
    db.commit()
    return UnreadCountOut(unread=0)


# ── G8 · Native push (Capacitor app) ─────────────────────────────────────────
@router.get("/native-push", response_model=dict)
def native_push_status(current_user: User = Depends(get_current_user)):
    """Whether the server can send native push (FCM configured)."""
    return {"enabled": fcm.enabled()}


@router.post("/device-tokens", response_model=DeviceTokenOut)
def register_device_token(
    payload: DeviceTokenIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register this device's FCM token; learners and parents alike (learner_id is set when there is a profile)."""
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    row = fcm.register(db, current_user.id, learner.id if learner else None, payload.token.strip(), payload.platform)
    db.commit()
    return DeviceTokenOut(id=row.id, platform=row.platform, native_push_enabled=fcm.enabled())


@router.delete("/device-tokens", status_code=204)
def unregister_device_token(
    payload: DeviceTokenIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fcm.unregister(db, current_user.id, payload.token.strip())
    db.commit()
