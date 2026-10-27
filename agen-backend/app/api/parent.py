"""
AGEN — Parent API (P5 persona)
Parents link to their children via an invite code, then view easy-to-read
weekly progress reports with actionable guidance.

Master Plan §21: report answers "What improved? / What needs help? / What should
parents do?" — NOT a raw scoreboard.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.subscription import PLAN_FAMILY
from app.services.payments import FAMILY_MAX_CHILDREN
from app.services.subscription_service import get_or_create_subscription, premium_source
from app.models.learner_profile import LearnerProfile
from app.models.parent import ParentProfile, ParentChildLink
from app.services.streak_service import effective_streak

router = APIRouter(prefix="/parent", tags=["Parent"])

SKILL_LABELS_VI = {
    "vocabulary": "Từ vựng", "grammar": "Ngữ pháp", "reading": "Đọc",
    "listening": "Nghe", "speaking": "Nói", "writing": "Viết",
}


# ── Schemas ───────────────────────────────────────────────────────────────────
class LinkChildRequest(BaseModel):
    invite_code: str = Field(min_length=4, max_length=20)
    relationship_label: str | None = None


class ChildSummary(BaseModel):
    learner_id: str
    display_name: str
    overall_level: str
    total_xp: int
    current_streak: int
    total_lessons_completed: int
    relationship_label: str | None
    premium_source: str | None = None     # G5 · "own" | "family" | None


class SkillImprovement(BaseModel):
    skill: str
    label: str
    score: float


class ChildReport(BaseModel):
    learner_id: str
    display_name: str
    overall_level: str
    # This week (last 7 days)
    sessions_this_week: int
    xp_this_week: int
    study_minutes_estimate: int
    current_streak: int
    accuracy_pct: float
    skills: list[SkillImprovement]
    best_skill: str
    focus_skill: str
    # Human-readable guidance (Master Plan §21)
    what_improved: str
    what_needs_help: str
    what_to_do: str
    # G14 · bài kiểm tra ở lớp của con (giáo viên giao), có kết quả của con
    class_tests: list[dict] = []


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_parent(db: Session, user: User) -> ParentProfile:
    if user.role != "parent":
        raise HTTPException(status_code=403, detail="Tài khoản này không phải phụ huynh.")
    parent = db.query(ParentProfile).filter(ParentProfile.user_id == user.id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ phụ huynh.")
    return parent


def _assert_linked(db: Session, parent_id: str, learner_id: str) -> ParentChildLink:
    link = db.query(ParentChildLink).filter(
        ParentChildLink.parent_id == parent_id,
        ParentChildLink.learner_id == learner_id,
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Bạn chưa liên kết với học viên này.")
    return link


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/link-child", response_model=ChildSummary)
def link_child(
    payload: LinkChildRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Link the current parent to a learner using the learner's invite code."""
    parent = _get_parent(db, current_user)
    code = payload.invite_code.strip().upper()

    learner = db.query(LearnerProfile).filter(LearnerProfile.invite_code == code).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Mã liên kết không đúng.")

    existing = db.query(ParentChildLink).filter(
        ParentChildLink.parent_id == parent.id,
        ParentChildLink.learner_id == learner.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bạn đã liên kết với học viên này rồi.")

    # G6 · a family plan covers at most FAMILY_MAX_CHILDREN children: refuse the next link
    # while the plan is active, instead of silently leaving a child uncovered.
    linked = db.query(ParentChildLink).filter(ParentChildLink.parent_id == parent.id).count()
    sub = get_or_create_subscription(db, current_user.id)
    if sub.plan == PLAN_FAMILY and premium_source(db, current_user.id) == "own" and linked >= FAMILY_MAX_CHILDREN:
        raise HTTPException(status_code=400, detail=f"Gói gia đình bao gồm tối đa {FAMILY_MAX_CHILDREN} con. Hãy huỷ liên kết một con trước khi thêm con mới.")

    link = ParentChildLink(
        parent_id=parent.id,
        learner_id=learner.id,
        relationship_label=payload.relationship_label,
    )
    db.add(link)
    db.commit()

    return ChildSummary(
        learner_id=learner.id,
        display_name=learner.display_name,
        overall_level=learner.overall_level or "PRE_A1",
        total_xp=learner.total_xp or 0,
        current_streak=effective_streak(learner),
        total_lessons_completed=learner.total_lessons_completed or 0,
        relationship_label=payload.relationship_label,
    )


@router.get("/children", response_model=list[ChildSummary])
def list_children(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all children linked to the current parent."""
    parent = _get_parent(db, current_user)
    links = db.query(ParentChildLink).filter(ParentChildLink.parent_id == parent.id).all()

    out: list[ChildSummary] = []
    for link in links:
        learner = db.query(LearnerProfile).filter(LearnerProfile.id == link.learner_id).first()
        if not learner:
            continue
        out.append(ChildSummary(
            learner_id=learner.id,
            display_name=learner.display_name,
            overall_level=learner.overall_level or "PRE_A1",
            total_xp=learner.total_xp or 0,
            current_streak=effective_streak(learner),
            total_lessons_completed=learner.total_lessons_completed or 0,
            relationship_label=link.relationship_label,
            premium_source=premium_source(db, learner.user_id),
        ))
    return out


@router.delete("/children/{learner_id}", status_code=204)
def unlink_child(
    learner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unlink a child from the current parent."""
    parent = _get_parent(db, current_user)
    link = _assert_linked(db, parent.id, learner_id)
    db.delete(link)
    db.commit()


@router.get("/child/{learner_id}/report", response_model=ChildReport)
def child_report(
    learner_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Weekly progress report for a linked child.
    Deterministic (no LLM) — reliable, quota-free, easy to read.
    """
    parent = _get_parent(db, current_user)
    _assert_linked(db, parent.id, learner_id)

    learner = db.query(LearnerProfile).filter(LearnerProfile.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Không tìm thấy học viên.")

    from app.services.parent_reports import build_child_report
    report = build_child_report(db, learner)
    report["skills"] = [SkillImprovement(**sk) for sk in report["skills"]]
    from app.services.groups import learner_class_tests
    report["class_tests"] = learner_class_tests(db, learner.id, limit=10)
    return ChildReport(**report)


# ── G3 · Proactive e-mails ────────────────────────────────────────────────────
class ParentSettingsOut(BaseModel):
    weekly_report_email: bool
    email_available: bool
    email_address: str
    last_weekly_report_week: str | None
    # G7 · web push to the parent's devices
    push_alerts: bool = True
    push_available: bool = False
    push_public_key: str | None = None
    push_devices: int = 0
    # G13 · native app (Capacitor + FCM) on the parent's phone
    native_push_available: bool = False
    native_devices: int = 0
    # G9 · Zalo OA
    zalo_available: bool = False
    zalo_oa_link: str | None = None
    zalo_linked: bool = False
    zalo_link_code: str | None = None


class ParentSettingsIn(BaseModel):
    weekly_report_email: bool | None = None
    push_alerts: bool | None = None


class PushKeysIn(BaseModel):
    p256dh: str
    auth: str


class ParentPushIn(BaseModel):
    endpoint: str
    keys: PushKeysIn


class ParentPushOutIn(BaseModel):
    endpoint: str


def _parent_settings_out(db: Session, parent: ParentProfile, user: User) -> ParentSettingsOut:
    from app.core.config import settings
    from app.services import zalo
    from app.models.device_token import DeviceToken
    from app.models.push_subscription import PushSubscription
    from app.services import fcm
    return ParentSettingsOut(
        weekly_report_email=bool(parent.weekly_report_email),
        email_available=settings.email_enabled,
        email_address=user.email,
        last_weekly_report_week=parent.last_weekly_report_week,
        push_alerts=bool(parent.push_alerts),
        push_available=settings.push_enabled,
        push_public_key=settings.VAPID_PUBLIC_KEY or None,
        push_devices=db.query(PushSubscription).filter(PushSubscription.user_id == user.id).count(),
        native_push_available=fcm.enabled(),
        native_devices=db.query(DeviceToken).filter(DeviceToken.user_id == user.id).count(),
        zalo_available=zalo.enabled(),
        zalo_oa_link=zalo.oa_link(),
        zalo_linked=bool(user.zalo_user_id),
        zalo_link_code=zalo.link_code_for(db, user) if zalo.enabled() else None,
    )


@router.get("/settings", response_model=ParentSettingsOut)
def get_parent_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _parent_settings_out(db, _get_parent(db, current_user), current_user)


@router.put("/settings", response_model=ParentSettingsOut)
def update_parent_settings(
    payload: ParentSettingsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parent = _get_parent(db, current_user)
    if payload.weekly_report_email is not None:
        parent.weekly_report_email = payload.weekly_report_email
    if payload.push_alerts is not None:
        parent.push_alerts = payload.push_alerts
    db.commit()
    return _parent_settings_out(db, parent, current_user)


# ── G7 · web push to the parent's own devices ────────────────────────────────
@router.post("/push-subscriptions", response_model=ParentSettingsOut)
def add_parent_push(payload: ParentPushIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.push_subscription import PushSubscription
    parent = _get_parent(db, current_user)
    if not payload.endpoint.startswith("https://"):
        raise HTTPException(status_code=422, detail="Push endpoint must be https.")
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if sub is None:
        sub = PushSubscription(endpoint=payload.endpoint, p256dh="", auth="")
        db.add(sub)
    sub.user_id = current_user.id
    sub.learner_id = None
    sub.p256dh = payload.keys.p256dh
    sub.auth = payload.keys.auth
    parent.push_alerts = True
    db.commit()
    return _parent_settings_out(db, parent, current_user)


@router.delete("/push-subscriptions", response_model=ParentSettingsOut)
def remove_parent_push(payload: ParentPushOutIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.push_subscription import PushSubscription
    parent = _get_parent(db, current_user)
    db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint, PushSubscription.user_id == current_user.id).delete(synchronize_session=False)
    db.commit()
    return _parent_settings_out(db, parent, current_user)
