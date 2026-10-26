"""G6 · Bạn học & thử thách đôi tuần."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import friends as svc

router = APIRouter(prefix="/friends", tags=["Friends"])


class DuoQuestOut(BaseModel):
    week: str
    my_xp: int
    friend_xp: int
    goal: int
    min_each: int
    done: bool
    claimed: bool
    claimable: bool
    reward_xp: int
    reward_gems: int


class FriendOut(BaseModel):
    learner_id: str
    display_name: str
    level: str
    avatar: dict
    streak: int
    studied_today: bool
    quest: DuoQuestOut


class FriendsOut(BaseModel):
    my_code: str | None
    goal: int
    min_each: int
    reward_xp: int
    reward_gems: int
    max_friends: int
    friends: list[FriendOut]


class AddFriendIn(BaseModel):
    code: str = Field(min_length=3, max_length=20)


class ClaimOut(BaseModel):
    xp: int
    gems: int
    total_xp: int
    gems_total: int


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


def _out(db: Session, learner: LearnerProfile) -> FriendsOut:
    views = svc.list_friends(db, learner)
    return FriendsOut(
        my_code=learner.invite_code, goal=svc.DUO_GOAL_XP, min_each=svc.DUO_MIN_EACH,
        reward_xp=svc.DUO_REWARD_XP, reward_gems=svc.DUO_REWARD_GEMS, max_friends=svc.MAX_FRIENDS,
        friends=[FriendOut(**{**v.__dict__, "quest": DuoQuestOut(**v.quest.__dict__)}) for v in views],
    )


@router.get("", response_model=FriendsOut)
def list_friends(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _out(db, _learner(db, current_user))


@router.post("", response_model=FriendsOut)
def add_friend(payload: AddFriendIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    try:
        svc.add_friend(db, learner, payload.code)
    except svc.FriendError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return _out(db, learner)


@router.delete("/{friend_id}", response_model=FriendsOut)
def remove_friend(friend_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    if not svc.remove_friend(db, learner, friend_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy bạn học này.")
    db.commit()
    return _out(db, learner)


@router.post("/{friend_id}/claim", response_model=ClaimOut)
def claim_duo(friend_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    try:
        result = svc.claim(db, learner, friend_id)
    except svc.FriendError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    return ClaimOut(**result)
