"""G7 · Nhóm học: lớp (giáo viên) và doanh nghiệp (HR) — API cho chủ nhóm và học viên."""
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import groups as svc
from app.services.payments import TEAM_PRICES_VND
from app.services.subscription_service import get_or_create_subscription, premium_source

router = APIRouter(prefix="/groups", tags=["Groups"])


# ── Schemas ──────────────────────────────────────────────────────────────────
class GroupOut(BaseModel):
    id: str
    name: str
    kind: str
    code: str
    member_count: int
    created_at: datetime


class OwnerHome(BaseModel):
    groups: list[GroupOut]
    plan: str                      # free | team
    seats: int
    is_premium: bool
    members_total: int
    team_prices: list[dict]        # [{months, amount_vnd}] per seat


class MemberOut(BaseModel):
    learner_id: str
    display_name: str
    level: str
    avatar: dict
    streak: int
    weekly_xp: int
    total_xp: int
    lessons: int
    active_today: bool
    assignments_done: int
    premium_source: Optional[str]
    joined_at: datetime


class AssignmentOut(BaseModel):
    id: str
    title: str
    skill: str
    topic: str
    note: Optional[str]
    due_on: Optional[date]
    created_at: datetime
    done_count: int
    member_count: int
    started: bool
    done: bool
    score: Optional[int]
    overdue: bool


class GroupDetail(BaseModel):
    group: GroupOut
    members: list[MemberOut]
    assignments: list[AssignmentOut]
    covered_seats: int


class CreateGroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: str = Field(default="class", pattern="^(class|company)$")


class CreateAssignmentIn(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    skill: str = Field(pattern="^(vocabulary|grammar|reading|listening)$")
    topic: str = Field(min_length=1, max_length=100)
    note: Optional[str] = Field(default=None, max_length=500)
    due_on: Optional[date] = None


class JoinIn(BaseModel):
    code: str = Field(min_length=3, max_length=20)


class LearnerGroupOut(BaseModel):
    group: GroupOut
    owner_name: str
    assignments: list[AssignmentOut]


class LearnerHome(BaseModel):
    groups: list[LearnerGroupOut]


class StartOut(BaseModel):
    assignment_id: str
    skill: str
    topic: str
    title: str


def _group_out(db: Session, g) -> GroupOut:
    return GroupOut(id=g.id, name=g.name, kind=g.kind, code=g.code,
                    member_count=db.query(svc.GroupMember).filter(svc.GroupMember.group_id == g.id).count(), created_at=g.created_at)


def _assignment_out(v: svc.AssignmentView) -> AssignmentOut:
    return AssignmentOut(**v.__dict__)


def _owner(user: User) -> User:
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Chỉ tài khoản giáo viên / doanh nghiệp mới dùng được mục này.")
    return user


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


# ── Owner (teacher / company) ────────────────────────────────────────────────
@router.get("/mine", response_model=OwnerHome)
def owner_home(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owner(current_user)
    groups = svc.owned_groups(db, current_user)
    sub = get_or_create_subscription(db, current_user.id)
    source = premium_source(db, current_user.id)
    return OwnerHome(
        groups=[_group_out(db, g) for g in groups],
        plan=sub.plan if source else "free", seats=sub.seats or 0, is_premium=source is not None,
        members_total=sum(db.query(svc.GroupMember).filter(svc.GroupMember.group_id == g.id).count() for g in groups),
        team_prices=[{"months": m, "amount_vnd": a} for m, a in TEAM_PRICES_VND.items()],
    )


@router.post("", response_model=GroupOut)
def create_group(payload: CreateGroupIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owner(current_user)
    try:
        g = svc.create_group(db, current_user, payload.name, payload.kind)
    except svc.GroupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return _group_out(db, g)


@router.get("/{group_id}", response_model=GroupDetail)
def group_detail(group_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owner(current_user)
    try:
        g = svc.get_owned(db, current_user, group_id)
    except svc.GroupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    from app.services.subscription_service import team_covered_learners
    return GroupDetail(
        group=_group_out(db, g),
        members=[MemberOut(**m.__dict__) for m in svc.member_views(db, g)],
        assignments=[_assignment_out(a) for a in svc.group_assignments(db, g.id)],
        covered_seats=len(team_covered_learners(db, current_user.id)),
    )


@router.get("/{group_id}/report.csv")
def group_report_csv(group_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """G8 · Progress of every member as CSV (UTF-8 with BOM so Excel opens it with Vietnamese intact)."""
    _owner(current_user)
    try:
        g = svc.get_owned(db, current_user, group_id)
    except svc.GroupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    csv_text = svc.report_csv(db, g)
    safe = "".join(c if c.isascii() and c.isalnum() else "-" for c in g.name).strip("-")[:40] or "nhom"
    return Response(content="\ufeff" + csv_text, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="bao-cao-{safe}.csv"'})


@router.delete("/{group_id}/members/{learner_id}", status_code=204)
def remove_member(group_id: str, learner_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owner(current_user)
    try:
        g = svc.get_owned(db, current_user, group_id)
    except svc.GroupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not svc.leave_group(db, learner_id, g.id):
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên.")
    db.commit()


@router.post("/{group_id}/assignments", response_model=AssignmentOut)
def create_assignment(group_id: str, payload: CreateAssignmentIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owner(current_user)
    try:
        g = svc.get_owned(db, current_user, group_id)
        a = svc.create_assignment(db, g, payload.title, payload.skill, payload.topic, payload.due_on, payload.note)
    except svc.GroupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return next(_assignment_out(v) for v in svc.group_assignments(db, g.id) if v.id == a.id)


@router.delete("/{group_id}/assignments/{assignment_id}", status_code=204)
def delete_assignment(group_id: str, assignment_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owner(current_user)
    try:
        g = svc.get_owned(db, current_user, group_id)
    except svc.GroupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not svc.delete_assignment(db, g, assignment_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy bài tập.")
    db.commit()


# ── Learner ──────────────────────────────────────────────────────────────────
@router.get("/learner/mine", response_model=LearnerHome)
def learner_home(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    out = []
    for g in svc.learner_groups(db, learner.id):
        owner = db.query(User).filter(User.id == g.owner_user_id).first()
        out.append(LearnerGroupOut(
            group=_group_out(db, g), owner_name=(owner.full_name if owner else None) or "Giáo viên",
            assignments=[_assignment_out(a) for a in svc.group_assignments(db, g.id, learner.id)],
        ))
    return LearnerHome(groups=out)


@router.post("/join", response_model=LearnerHome)
def join(payload: JoinIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    try:
        svc.join_group(db, learner, payload.code)
    except svc.GroupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return learner_home(current_user, db)


@router.post("/{group_id}/leave", response_model=LearnerHome)
def leave(group_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    if not svc.leave_group(db, learner.id, group_id):
        raise HTTPException(status_code=404, detail="Bạn không ở trong nhóm này.")
    db.commit()
    return learner_home(current_user, db)


@router.post("/assignments/{assignment_id}/start", response_model=StartOut)
def start_assignment(assignment_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    try:
        a = svc.start_assignment(db, learner, assignment_id)
    except svc.GroupError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return StartOut(assignment_id=a.id, skill=a.skill, topic=a.topic, title=a.title)
