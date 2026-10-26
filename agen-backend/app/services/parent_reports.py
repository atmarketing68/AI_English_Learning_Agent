"""
Weekly child report for parents (Master Plan §21): deterministic, no LLM.
Shared by the parent API and the G3 weekly e-mail digest.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.services.streak_service import effective_streak

SKILL_LABELS_VI = {
    "vocabulary": "Từ vựng", "grammar": "Ngữ pháp", "reading": "Đọc",
    "listening": "Nghe", "speaking": "Nói", "writing": "Viết",
}


def build_child_report(db: Session, learner: LearnerProfile, now: datetime | None = None) -> dict:
    """Answers "What improved? / What needs help? / What should parents do?" for the last 7 days."""
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(days=7)).replace(tzinfo=None)
    events = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.learner_id == learner.id,
            LearningEvent.recorded_at >= since,
            LearningEvent.event_type == "lesson_completed",
        )
        .all()
    )

    sessions = len(events)
    xp_week = sum(e.xp_earned or 0 for e in events)
    study_minutes = sessions * 6          # rough: ~6 minutes per completed lesson
    scored = [e.score for e in events if e.score is not None]
    accuracy = round(sum(scored) / len(scored), 1) if scored else 0.0

    skill_scores = {
        "listening": learner.listening_score or 0.0,
        "speaking": learner.speaking_score or 0.0,
        "reading": learner.reading_score or 0.0,
        "writing": learner.writing_score or 0.0,
        "vocabulary": learner.vocabulary_score or 0.0,
        "grammar": learner.grammar_score or 0.0,
    }
    skills = [
        {"skill": s, "label": SKILL_LABELS_VI.get(s, s), "score": round(v, 1)}
        for s, v in skill_scores.items()
    ]
    best_skill = max(skill_scores, key=skill_scores.get)
    focus_skill = min(skill_scores, key=skill_scores.get)
    best_label = SKILL_LABELS_VI[best_skill]
    focus_label = SKILL_LABELS_VI[focus_skill]

    name = learner.display_name
    streak = effective_streak(learner)
    if sessions == 0:
        what_improved = f"Tuần này {name} chưa có buổi học nào."
        what_needs_help = "Cần tạo thói quen học đều đặn."
        what_to_do = f"Hãy cùng {name} đặt mục tiêu học 3 buổi ngắn (10-15 phút) trong tuần tới."
    else:
        what_improved = (
            f"{name} hoàn thành {sessions} buổi học, kiếm được {xp_week} XP tuần này. "
            f"Kỹ năng mạnh nhất hiện tại là {best_label} ({skill_scores[best_skill]:.0f}%)."
        )
        if accuracy >= 80:
            what_improved += f" Độ chính xác rất tốt ({accuracy:.0f}%)!"
        what_needs_help = (
            f"{focus_label} đang là kỹ năng yếu nhất ({skill_scores[focus_skill]:.0f}%) — cần luyện thêm."
        )
        if streak >= 3:
            what_to_do = (
                f"{name} đang có chuỗi {streak} ngày liên tiếp — hãy động viên con giữ vững! "
                f"Tuần tới ưu tiên 2-3 buổi {focus_label}."
            )
        else:
            what_to_do = (
                f"Hãy khuyến khích {name} học đều mỗi ngày để xây chuỗi streak, "
                f"và tập trung vào {focus_label}."
            )

    return {
        "learner_id": learner.id,
        "display_name": learner.display_name,
        "overall_level": learner.overall_level or "PRE_A1",
        "sessions_this_week": sessions,
        "xp_this_week": xp_week,
        "study_minutes_estimate": study_minutes,
        "current_streak": streak,
        "accuracy_pct": accuracy,
        "skills": skills,
        "best_skill": best_label,
        "focus_skill": focus_label,
        "what_improved": what_improved,
        "what_needs_help": what_needs_help,
        "what_to_do": what_to_do,
    }
