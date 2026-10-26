"""Privacy, consent, data export and account deletion endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, verify_password
from app.models import AgentJob, AgentTrace, AuthSession, ConsentRecord, LearnerProfile, User
from app.models.learning_event import LearningEvent
from app.models.lesson import Lesson
from app.models.achievement import LearnerAchievement, DailyChallenge
from app.models.placement import PlacementSession
from app.models.roleplay import RoleplaySession
from app.models.writing import WritingSubmission
from app.models.review_item import ReviewItem

router = APIRouter(prefix="/privacy", tags=["Privacy"])
PRIVACY_POLICY_VERSION = "2026-09-07"


class ConsentRequest(BaseModel):
    consent_type: str = Field(min_length=1, max_length=80)
    granted: bool


class ConsentResponse(BaseModel):
    consent_type: str
    policy_version: str
    granted: bool
    recorded_at: datetime


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1)


@router.post("/consents", response_model=ConsentResponse)
def record_consent(
    payload: ConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = ConsentRecord(
        user_id=current_user.id,
        consent_type=payload.consent_type,
        policy_version=PRIVACY_POLICY_VERSION,
        granted=payload.granted,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/consents", response_model=list[ConsentResponse])
def list_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(ConsentRecord).filter(ConsentRecord.user_id == current_user.id).order_by(ConsentRecord.recorded_at.desc()).all()


@router.get("/export")
def export_personal_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    events = db.query(LearningEvent).filter(LearningEvent.learner_id == profile.id).all() if profile else []
    lessons = db.query(Lesson).filter(Lesson.learner_id == profile.id).all() if profile else []
    review_items = db.query(ReviewItem).filter(ReviewItem.learner_id == profile.id).all() if profile else []
    consents = db.query(ConsentRecord).filter(ConsentRecord.user_id == current_user.id).all()
    return {
        "user": {"id": current_user.id, "email": current_user.email, "full_name": current_user.full_name},
        "learner_profile": {
            "id": profile.id,
            "display_name": profile.display_name,
            "age": profile.age,
            "grade": profile.grade,
            "overall_level": profile.overall_level,
            "scores": {"listening": profile.listening_score, "speaking": profile.speaking_score, "reading": profile.reading_score, "writing": profile.writing_score},
        } if profile else None,
        "learning_events": [{"id": event.id, "event_type": event.event_type, "skill": event.skill, "score": event.score, "recorded_at": event.recorded_at} for event in events],
        "lessons": [{"id": lesson.id, "skill": lesson.skill, "topic": lesson.topic, "status": lesson.status, "score": lesson.score, "created_at": lesson.created_at} for lesson in lessons],
        "review_items": [{"id": item.id, "kind": item.kind, "front": item.front, "back": item.back, "reps": item.reps, "due_at": item.due_at} for item in review_items],
        "consents": [{"consent_type": consent.consent_type, "policy_version": consent.policy_version, "granted": consent.granted, "recorded_at": consent.recorded_at} for consent in consents],
    }


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if profile:
        db.query(LearnerAchievement).filter(LearnerAchievement.learner_id == profile.id).delete(synchronize_session=False)
        db.query(DailyChallenge).filter(DailyChallenge.learner_id == profile.id).delete(synchronize_session=False)
        db.query(LearningEvent).filter(LearningEvent.learner_id == profile.id).delete(synchronize_session=False)
        db.query(AgentJob).filter(AgentJob.learner_id == profile.id).delete(synchronize_session=False)
        db.query(AgentTrace).filter(AgentTrace.learner_id == profile.id).delete(synchronize_session=False)
        db.query(PlacementSession).filter(PlacementSession.learner_id == profile.id).delete(synchronize_session=False)
        db.query(RoleplaySession).filter(RoleplaySession.learner_id == profile.id).delete(synchronize_session=False)
        db.query(WritingSubmission).filter(WritingSubmission.learner_id == profile.id).delete(synchronize_session=False)
        db.query(ReviewItem).filter(ReviewItem.learner_id == profile.id).delete(synchronize_session=False)
        lesson_ids = [lesson.id for lesson in db.query(Lesson).filter(Lesson.learner_id == profile.id).all()]
        if lesson_ids:
            from app.models.lesson import Exercise
            db.query(Exercise).filter(Exercise.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
        db.query(Lesson).filter(Lesson.learner_id == profile.id).delete(synchronize_session=False)
        db.delete(profile)
    db.query(ConsentRecord).filter(ConsentRecord.user_id == current_user.id).delete(synchronize_session=False)
    db.query(AuthSession).filter(AuthSession.user_id == current_user.id).delete(synchronize_session=False)
    db.delete(current_user)
    db.commit()