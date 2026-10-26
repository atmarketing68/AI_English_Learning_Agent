"""G9 · Kế hoạch ôn thi: set the target (exam, score, date) and read the weekly plan + on-track status."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.timeutil import local_today
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import study_plan as svc

router = APIRouter(prefix="/study-plan", tags=["Study plan"])


class WeekOut(BaseModel):
    index: int
    start: date
    end: date
    focus: list[str]
    lessons: int
    mock_tests: int
    writing_tasks: int
    speaking_sessions: int
    is_current: bool


class PlanOut(BaseModel):
    configured: bool
    exam: Optional[str] = None
    target_score: Optional[float] = None
    exam_date: Optional[date] = None
    days_left: Optional[int] = None
    weeks_left: Optional[int] = None
    current: dict[str, Optional[float]] = {}
    current_overall: Optional[float] = None
    gap: Optional[float] = None
    projected: Optional[float] = None
    status: str = "unset"
    status_vi: str = ""
    weekly_lessons: int = 0
    this_week: dict[str, int] = {}
    weeks: list[WeekOut] = []
    advice_vi: list[str] = []
    skill_labels: dict[str, str] = svc.SKILL_VI


class PlanIn(BaseModel):
    exam: str = Field(pattern="^(ielts|toeic)$")
    target_score: float = Field(gt=0)
    exam_date: date

    @field_validator("target_score")
    @classmethod
    def valid_score(cls, v: float, info):
        return v


def _learner(db: Session, user: User) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found")
    return learner


def _out(db: Session, learner: LearnerProfile) -> PlanOut:
    plan = svc.build_plan(db, learner)
    if not plan:
        return PlanOut(configured=False)
    return PlanOut(configured=True, exam=plan.exam, target_score=plan.target_score, exam_date=plan.exam_date, days_left=plan.days_left, weeks_left=plan.weeks_left,
                   current=plan.current, current_overall=plan.current_overall, gap=plan.gap, projected=plan.projected, status=plan.status, status_vi=plan.status_vi,
                   weekly_lessons=plan.weekly_lessons, this_week=plan.this_week, weeks=[WeekOut(**w.__dict__) for w in plan.weeks], advice_vi=plan.advice_vi)


@router.get("", response_model=PlanOut)
def get_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _out(db, _learner(db, current_user))


@router.put("", response_model=PlanOut)
def set_plan(payload: PlanIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    if payload.exam == "ielts" and not (1.0 <= payload.target_score <= 9.0 and (payload.target_score * 2).is_integer()):
        raise HTTPException(status_code=422, detail="Band IELTS từ 1.0 đến 9.0, bước 0.5.")
    if payload.exam == "toeic" and not (10 <= payload.target_score <= 990 and payload.target_score % 5 == 0):
        raise HTTPException(status_code=422, detail="Điểm TOEIC từ 10 đến 990, bước 5.")
    if payload.exam_date <= local_today():
        raise HTTPException(status_code=422, detail="Ngày thi phải ở tương lai.")
    learner.exam_target = payload.exam
    learner.exam_target_score = payload.target_score
    learner.exam_date = payload.exam_date
    if not learner.learning_goal or learner.learning_goal in ("giao_tiep", "khac"):
        learner.learning_goal = "luyen_thi"
    db.commit()
    return _out(db, learner)


@router.delete("", response_model=PlanOut)
def clear_plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learner = _learner(db, current_user)
    learner.exam_target = None
    learner.exam_target_score = None
    learner.exam_date = None
    db.commit()
    return PlanOut(configured=False)
