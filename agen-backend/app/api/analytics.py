"""
AGEN — Analytics & Adaptive Coach API
Endpoints for progress overview, event history, AI coach advice and weekly reports.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.services.streak_service import effective_streak
from app.agents.adaptive_coach import analyze_learner, generate_weekly_report

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class SkillScores(BaseModel):
    vocabulary: float
    grammar: float
    reading: float
    speaking: float
    listening: float
    writing: float


class OverviewResponse(BaseModel):
    overall_level: str
    total_xp: int
    current_streak: int
    total_lessons_completed: int
    skill_scores: SkillScores
    xp_to_next_level: int
    progress_pct: float


class ActivityDay(BaseModel):
    date: str      # ISO date string "YYYY-MM-DD"
    xp: int
    sessions: int


class ActivityResponse(BaseModel):
    days: list[ActivityDay]
    total_xp_30d: int
    total_sessions_30d: int


class LeaderboardEntry(BaseModel):
    learner_id: str
    display_name: str
    avatar: str
    level: str
    xp: int
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]


class AssessmentOutcome(BaseModel):
    id: str
    topic: str
    reason: str


class RecommendedTopic(BaseModel):
    skill: str
    topic: str
    reason: str


class CoachAdviceResponse(BaseModel):
    weak_skills: list[str]
    strong_skills: list[str]
    focus_area: str
    recommended_topics: list[RecommendedTopic]
    study_plan_today: str
    motivational_message: str


class WeeklyReportResponse(BaseModel):
    sessions_count: int
    xp_earned_this_week: int
    best_skill: str
    most_practiced_skill: str
    highlight: str
    areas_to_improve: list[str]
    next_week_goal: str
    encouragement: str


class AssessmentSnapshot(BaseModel):
    assessment_type: str
    completed_at: datetime
    overall_level: str
    accuracy_percent: float
    skill_scores: dict[str, float]


class AssessmentOutcomeResponse(BaseModel):
    baseline: Optional[AssessmentSnapshot]
    latest_followup: Optional[AssessmentSnapshot]
    accuracy_delta: Optional[float]
    skill_deltas: dict[str, float]


# ── XP level thresholds ───────────────────────────────────────────────────────
LEVEL_THRESHOLDS = {
    "PRE_A1": 0,    "A1": 100,  "A2": 300,
    "B1": 600,      "B2": 1000, "C1": 1500, "C2": 2500,
}
LEVEL_ORDER = ["PRE_A1", "A1", "A2", "B1", "B2", "C1", "C2"]


def _xp_progress(level: str, total_xp: int) -> tuple[int, float]:
    """Returns (xp_to_next_level, pct_progress)"""
    idx = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 0
    current_threshold = LEVEL_THRESHOLDS.get(level, 0)
    if idx + 1 < len(LEVEL_ORDER):
        next_threshold = LEVEL_THRESHOLDS.get(LEVEL_ORDER[idx + 1], current_threshold + 200)
        xp_in_level = total_xp - current_threshold
        span = next_threshold - current_threshold
        # Clamp to [0, 100] — prevent negative pct when xp < threshold
        pct = round(max(min((xp_in_level / span) * 100, 100.0), 0.0), 1)
        remaining = max(next_threshold - total_xp, 0)
        return remaining, pct
    return 0, 100.0


def _get_learner(db: Session, user_id: str) -> LearnerProfile:
    learner = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner profile not found.")
    return learner


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns overall learner stats for the dashboard/progress page."""
    learner = _get_learner(db, current_user.id)
    xp_to_next, progress_pct = _xp_progress(learner.overall_level, learner.total_xp)

    return OverviewResponse(
        overall_level=learner.overall_level,
        total_xp=learner.total_xp,
        current_streak=effective_streak(learner),
        total_lessons_completed=learner.total_lessons_completed,
        skill_scores=SkillScores(
            vocabulary=learner.vocabulary_score or 0.0,
            grammar=learner.grammar_score or 0.0,
            reading=learner.reading_score or 0.0,
            speaking=learner.speaking_score or 0.0,
            listening=learner.listening_score or 0.0,
            writing=learner.writing_score or 0.0,
        ),
        xp_to_next_level=xp_to_next,
        progress_pct=progress_pct,
    )


@router.get("/events", response_model=ActivityResponse)
def get_activity(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns daily activity summary for the last N days (for activity calendar)."""
    learner = _get_learner(db, current_user.id)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.learner_id == learner.id,
            LearningEvent.recorded_at >= since,
        )
        .order_by(LearningEvent.recorded_at.asc())
        .all()
    )

    # Aggregate by date
    day_map: dict[str, dict] = {}
    total_xp = 0
    for ev in events:
        date_str = ev.recorded_at.strftime("%Y-%m-%d")
        if date_str not in day_map:
            day_map[date_str] = {"xp": 0, "sessions": 0}
        day_map[date_str]["xp"] += ev.xp_earned or 0
        day_map[date_str]["sessions"] += 1
        total_xp += ev.xp_earned or 0

    # Fill in all days (even empty ones) for the calendar
    activity_days = []
    for i in range(days):
        day = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        info = day_map.get(day, {"xp": 0, "sessions": 0})
        activity_days.append(ActivityDay(date=day, xp=info["xp"], sessions=info["sessions"]))

    return ActivityResponse(
        days=activity_days,
        total_xp_30d=total_xp,
        total_sessions_30d=len(events),
    )


@router.get("/assessment-outcomes", response_model=AssessmentOutcomeResponse)
def get_assessment_outcomes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return baseline vs latest follow-up assessment results for the learner."""
    learner = _get_learner(db, current_user.id)
    events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.learner_id == learner.id,
            LearningEvent.event_type.in_([
                "baseline_assessment_completed",
                "followup_assessment_completed",
            ]),
        )
        .order_by(LearningEvent.recorded_at.asc())
        .all()
    )

    def snapshot(event: LearningEvent) -> AssessmentSnapshot:
        data = event.extra_data or {}
        return AssessmentSnapshot(
            assessment_type=data.get("assessment_type", "baseline"),
            completed_at=event.recorded_at,
            overall_level=data.get("overall_level", "PRE_A1"),
            accuracy_percent=float(event.score or 0.0),
            skill_scores={k: float(v) for k, v in (data.get("skill_scores") or {}).items()},
        )

    baseline_event = next(
        (event for event in events if event.event_type == "baseline_assessment_completed"),
        None,
    )
    followup_events = [event for event in events if event.event_type == "followup_assessment_completed"]
    baseline = snapshot(baseline_event) if baseline_event else None
    latest_followup = snapshot(followup_events[-1]) if followup_events else None

    if not baseline or not latest_followup:
        return AssessmentOutcomeResponse(
            baseline=baseline,
            latest_followup=latest_followup,
            accuracy_delta=None,
            skill_deltas={},
        )

    skill_keys = set(baseline.skill_scores) | set(latest_followup.skill_scores)
    deltas = {
        key: round(latest_followup.skill_scores.get(key, 0.0) - baseline.skill_scores.get(key, 0.0), 1)
        for key in skill_keys
    }
    return AssessmentOutcomeResponse(
        baseline=baseline,
        latest_followup=latest_followup,
        accuracy_delta=round(latest_followup.accuracy_percent - baseline.accuracy_percent, 1),
        skill_deltas=deltas,
    )


@router.get("/coach-advice", response_model=CoachAdviceResponse)
def get_coach_advice(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI Coach analyzes learner data and generates today's personalized plan."""
    learner = _get_learner(db, current_user.id)

    # Fetch last 20 events
    recent_events = (
        db.query(LearningEvent)
        .filter(LearningEvent.learner_id == learner.id)
        .order_by(LearningEvent.recorded_at.desc())
        .limit(20)
        .all()
    )
    events_data = [
        {
            "skill": e.skill,
            "topic": e.topic,
            "score": e.score or 0,
            "xp_earned": e.xp_earned or 0,
            "event_type": e.event_type,
        }
        for e in recent_events
    ]

    learner_data = {
        "overall_level": learner.overall_level,
        "vocabulary_score": learner.vocabulary_score or 0,
        "grammar_score": learner.grammar_score or 0,
        "reading_score": learner.reading_score or 0,
        "speaking_score": learner.speaking_score or 0,
        "listening_score": learner.listening_score or 0,
        "total_xp": learner.total_xp,
        "current_streak": effective_streak(learner),
        "total_lessons_completed": learner.total_lessons_completed,
    }

    try:
        advice = analyze_learner(learner_data, events_data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coach AI error: {str(e)}")

    return CoachAdviceResponse(
        weak_skills=advice.get("weak_skills", []),
        strong_skills=advice.get("strong_skills", []),
        focus_area=advice.get("focus_area", ""),
        recommended_topics=[
            RecommendedTopic(**t) for t in advice.get("recommended_topics", [])
        ],
        study_plan_today=advice.get("study_plan_today", ""),
        motivational_message=advice.get("motivational_message", "Cố lên bạn nhé!"),
    )


@router.get("/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI-generated weekly progress report based on last 7 days of activity."""
    learner = _get_learner(db, current_user.id)
    since = datetime.now(timezone.utc) - timedelta(days=7)

    weekly_events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.learner_id == learner.id,
            LearningEvent.recorded_at >= since,
        )
        .order_by(LearningEvent.recorded_at.asc())
        .all()
    )
    events_data = [
        {
            "skill": e.skill,
            "topic": e.topic,
            "score": e.score or 0,
            "xp_earned": e.xp_earned or 0,
        }
        for e in weekly_events
    ]

    learner_data = {
        "overall_level": learner.overall_level,
        "total_xp": learner.total_xp,
        "current_streak": effective_streak(learner),
    }

    try:
        report = generate_weekly_report(learner_data, events_data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Report AI error: {str(e)}")

    return WeeklyReportResponse(**report)


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Global XP Leaderboard."""
    learner = _get_learner(db, current_user.id)
    
    # Get top 10 learners by total XP
    top_learners = (
        db.query(LearnerProfile)
        .order_by(LearnerProfile.total_xp.desc())
        .limit(10)
        .all()
    )
    
    entries = []
    for l in top_learners:
        entries.append(LeaderboardEntry(
            learner_id=l.id,
            display_name=l.display_name,
            avatar="🎓", # Default avatar
            level=l.overall_level or "PRE_A1",
            xp=l.total_xp or 0,
            is_current_user=(l.id == learner.id)
        ))
        
    return LeaderboardResponse(entries=entries)
