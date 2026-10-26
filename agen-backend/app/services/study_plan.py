"""
G9 · Kế hoạch ôn thi theo ngày thi và band mục tiêu.

Deterministic (no LLM): from the learner's exam, target score and date it
estimates the current level per skill from the latest mock tests and writing
band, splits the remaining weeks into focus weeks (weakest skill first), sets
weekly targets from the daily study minutes, and says whether this week is
on track by counting LearningEvents since Monday.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.timeutil import LEARNER_TZ, local_today
from app.models.exam_attempt import ExamAttempt
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.speaking_exam import STATUS_FINISHED, SpeakingExamAttempt
from app.models.writing import WritingSubmission

SKILLS = ("listening", "reading", "writing", "speaking")
SKILL_VI = {"listening": "Nghe", "reading": "Đọc", "writing": "Viết", "speaking": "Nói"}
MAX_WEEKS_SHOWN = 12
# Expected gain per focused week (band for IELTS, points for TOEIC) with a normal study load.
GAIN_PER_WEEK = {"ielts": 0.1, "toeic": 10.0}


@dataclass
class WeekPlan:
    index: int
    start: date
    end: date
    focus: list[str]
    lessons: int
    mock_tests: int
    writing_tasks: int
    speaking_sessions: int
    is_current: bool = False


@dataclass
class StudyPlan:
    exam: str
    target_score: float
    exam_date: date
    days_left: int
    weeks_left: int
    current: dict[str, float | None]
    current_overall: float | None
    gap: float | None
    projected: float | None
    status: str                                  # on_track | behind | ahead | no_data | past
    status_vi: str
    weekly_lessons: int
    this_week: dict[str, int] = field(default_factory=dict)
    weeks: list[WeekPlan] = field(default_factory=list)
    advice_vi: list[str] = field(default_factory=list)


def _round_half(x: float) -> float:
    return round(x * 2) / 2


def current_estimates(db: Session, learner: LearnerProfile, exam: str) -> dict[str, float | None]:
    """Best recent estimate per skill from mock tests (reading/listening/speaking) and exam-style writing."""
    out: dict[str, float | None] = {s: None for s in SKILLS}
    rows = db.query(ExamAttempt).filter(ExamAttempt.learner_id == learner.id, ExamAttempt.exam == exam).order_by(ExamAttempt.created_at.desc()).limit(20).all()
    for skill in ("listening", "reading"):
        latest = [r.estimate for r in rows if r.skill == skill][:3]
        if latest:
            out[skill] = max(latest)
    sp = db.query(SpeakingExamAttempt).filter(SpeakingExamAttempt.learner_id == learner.id, SpeakingExamAttempt.exam == exam, SpeakingExamAttempt.status == STATUS_FINISHED).order_by(SpeakingExamAttempt.created_at.desc()).limit(3).all()
    if sp:
        out["speaking"] = max(r.estimate for r in sp if r.estimate is not None) if any(r.estimate is not None for r in sp) else None
    writings = db.query(WritingSubmission).filter(WritingSubmission.learner_id == learner.id).order_by(WritingSubmission.created_at.desc()).limit(10).all()
    bands = []
    for w in writings:
        band = (w.evaluation or {}).get("exam_band") if isinstance(w.evaluation, dict) else None
        if band and band.get("exam") == exam:
            bands.append(float(band["overall"]))
    if bands:
        out["writing"] = max(bands[:3])
    return out


def _overall(exam: str, current: dict[str, float | None]) -> float | None:
    vals = [v for v in current.values() if v is not None]
    if not vals:
        return None
    mean = sum(vals) / len(vals)
    return _round_half(mean) if exam == "ielts" else float(round(mean / 5) * 5)


def _week_events(db: Session, learner_id: str, monday: date) -> dict[str, int]:
    start_utc = datetime.combine(monday, datetime.min.time(), tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)
    rows = db.query(LearningEvent.event_type, LearningEvent.skill).filter(LearningEvent.learner_id == learner_id, LearningEvent.recorded_at >= start_utc).all()
    counts = {"lessons": 0, "mock_tests": 0, "writing_tasks": 0, "speaking_sessions": 0}
    for et, skill in rows:
        if et == "lesson_completed":
            counts["lessons"] += 1
        elif et in ("exam_completed", "speaking_exam_completed"):
            counts["mock_tests"] += 1
        elif et == "writing_submitted":
            counts["writing_tasks"] += 1
        elif skill == "speaking":
            counts["speaking_sessions"] += 1
    return counts


def build_plan(db: Session, learner: LearnerProfile, today: date | None = None) -> StudyPlan | None:
    if not (learner.exam_target and learner.exam_target_score and learner.exam_date):
        return None
    exam = learner.exam_target
    today = today or local_today()
    days_left = (learner.exam_date - today).days
    weeks_left = max(0, (days_left + 6) // 7)
    current = current_estimates(db, learner, exam)
    overall = _overall(exam, current)
    gap = round(learner.exam_target_score - overall, 1) if overall is not None else None

    minutes = learner.daily_study_minutes or 15
    weekly_lessons = 5 if minutes < 20 else 7 if minutes < 40 else 10
    monday = today - timedelta(days=today.weekday())
    this_week = _week_events(db, learner.id, monday)

    # Weakest skills first; unknown skills come first so the learner measures them.
    order = sorted(SKILLS, key=lambda s: (current[s] is not None, current[s] if current[s] is not None else 0))
    weeks: list[WeekPlan] = []
    for i in range(min(weeks_left, MAX_WEEKS_SHOWN)):
        start = monday + timedelta(days=7 * i)
        focus = [order[i % 4], order[(i + 1) % 4]]
        last = i == weeks_left - 1
        weeks.append(WeekPlan(index=i + 1, start=start, end=min(start + timedelta(days=6), learner.exam_date), focus=focus,
                              lessons=weekly_lessons, mock_tests=2 if last else 1, writing_tasks=1, speaking_sessions=2, is_current=i == 0))

    # Projection: current + gain per focused week, capped at the scale.
    projected = None
    if overall is not None:
        cap = 9.0 if exam == "ielts" else 990.0
        projected = min(cap, overall + GAIN_PER_WEEK[exam] * weeks_left)
        projected = _round_half(projected) if exam == "ielts" else float(round(projected / 5) * 5)

    if days_left < 0:
        status, status_vi = "past", "Ngày thi đã qua — cập nhật ngày thi mới hoặc mục tiêu mới nhé."
    elif overall is None:
        status, status_vi = "no_data", "Chưa có dữ liệu. Làm một đề thi thử mỗi kỹ năng để biết điểm hiện tại."
    else:
        weekday_fraction = (today.weekday() + 1) / 7
        expected_lessons = round(weekly_lessons * weekday_fraction)
        if this_week["lessons"] >= weekly_lessons:
            status, status_vi = "ahead", "Tuần này bạn đã vượt chỉ tiêu bài học. Giữ nhịp nhé!"
        elif this_week["lessons"] >= expected_lessons:
            status, status_vi = "on_track", "Đúng tiến độ tuần này."
        else:
            status, status_vi = "behind", f"Chậm tiến độ: cần thêm {expected_lessons - this_week['lessons']} bài để kịp kế hoạch tuần."

    advice: list[str] = []
    if gap is not None and gap > 0 and projected is not None and projected < learner.exam_target_score:
        unit = "band" if exam == "ielts" else "điểm"
        advice.append(f"Với nhịp hiện tại, dự kiến đến ngày thi đạt khoảng {projected:g} ({unit}), còn thiếu {round(learner.exam_target_score - projected, 1):g}. Tăng phút học mỗi ngày hoặc lùi ngày thi.")
    weakest = next((s for s in order if current[s] is not None), None)
    if weakest:
        advice.append(f"Kỹ năng yếu nhất: {SKILL_VI[weakest]} ({current[weakest]:g}). Tuần này ưu tiên {SKILL_VI[weakest]}.")
    missing = [SKILL_VI[s] for s in SKILLS if current[s] is None]
    if missing:
        advice.append("Chưa đo: " + ", ".join(missing) + ". Làm thi thử để có điểm xuất phát.")
    if 0 <= days_left <= 7:
        advice.append("Tuần cuối: làm 2 đề thi thử trọn vẹn, ngủ đủ, không học kiến thức mới.")

    return StudyPlan(exam=exam, target_score=learner.exam_target_score, exam_date=learner.exam_date, days_left=days_left, weeks_left=weeks_left,
                     current=current, current_overall=overall, gap=gap, projected=projected, status=status, status_vi=status_vi,
                     weekly_lessons=weekly_lessons, this_week=this_week, weeks=weeks, advice_vi=advice)
