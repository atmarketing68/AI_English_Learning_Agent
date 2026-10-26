"""
AGEN — Achievement Definitions & Auto-award Logic
All achievement catalog is defined here and seeded on startup.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.achievement import Achievement, LearnerAchievement, DailyChallenge
from app.models.learner_profile import LearnerProfile

# ── Achievement Catalog ────────────────────────────────────────────────────────
ACHIEVEMENT_CATALOG = [
    # --- Lessons ---
    {
        "id": "first_lesson",
        "name": "First Step",
        "description": "Hoàn thành bài học đầu tiên",
        "icon": "🎓",
        "category": "lesson",
        "xp_reward": 50,
        "condition_type": "lessons_completed",
        "condition_value": 1,
    },
    {
        "id": "lesson_10",
        "name": "Dedicated Learner",
        "description": "Hoàn thành 10 bài học",
        "icon": "📚",
        "category": "lesson",
        "xp_reward": 100,
        "condition_type": "lessons_completed",
        "condition_value": 10,
    },
    {
        "id": "lesson_50",
        "name": "Knowledge Seeker",
        "description": "Hoàn thành 50 bài học",
        "icon": "🏛️",
        "category": "lesson",
        "xp_reward": 300,
        "condition_type": "lessons_completed",
        "condition_value": 50,
    },
    # --- Streaks ---
    {
        "id": "streak_3",
        "name": "On a Roll",
        "description": "Học 3 ngày liên tiếp",
        "icon": "🔥",
        "category": "streak",
        "xp_reward": 30,
        "condition_type": "streak_days",
        "condition_value": 3,
    },
    {
        "id": "streak_7",
        "name": "Week Warrior",
        "description": "Học 7 ngày liên tiếp",
        "icon": "⚡",
        "category": "streak",
        "xp_reward": 100,
        "condition_type": "streak_days",
        "condition_value": 7,
    },
    {
        "id": "streak_30",
        "name": "Iron Learner",
        "description": "Học 30 ngày liên tiếp",
        "icon": "🦾",
        "category": "streak",
        "xp_reward": 500,
        "condition_type": "streak_days",
        "condition_value": 30,
    },
    # --- XP ---
    {
        "id": "xp_100",
        "name": "Getting Started",
        "description": "Kiếm được 100 XP",
        "icon": "⭐",
        "category": "xp",
        "xp_reward": 0,
        "condition_type": "xp_total",
        "condition_value": 100,
    },
    {
        "id": "xp_500",
        "name": "Rising Star",
        "description": "Kiếm được 500 XP",
        "icon": "🌟",
        "category": "xp",
        "xp_reward": 50,
        "condition_type": "xp_total",
        "condition_value": 500,
    },
    {
        "id": "xp_2000",
        "name": "English Champion",
        "description": "Kiếm được 2000 XP",
        "icon": "🏆",
        "category": "xp",
        "xp_reward": 200,
        "condition_type": "xp_total",
        "condition_value": 2000,
    },
    # --- Skills ---
    {
        "id": "speaking_master",
        "name": "Speaker",
        "description": "Đạt Speaking score ≥ 70%",
        "icon": "🗣️",
        "category": "skill",
        "xp_reward": 80,
        "condition_type": "speaking_score",
        "condition_value": 70,
    },
    {
        "id": "writing_master",
        "name": "Writer",
        "description": "Đạt Writing score ≥ 70%",
        "icon": "✍️",
        "category": "skill",
        "xp_reward": 80,
        "condition_type": "writing_score",
        "condition_value": 70,
    },
    {
        "id": "reading_master",
        "name": "Reader",
        "description": "Đạt Reading score ≥ 70%",
        "icon": "📖",
        "category": "skill",
        "xp_reward": 80,
        "condition_type": "reading_score",
        "condition_value": 70,
    },
    {
        "id": "listening_master",
        "name": "Listener",
        "description": "Đạt Listening score ≥ 70%",
        "icon": "🎧",
        "category": "skill",
        "xp_reward": 80,
        "condition_type": "listening_score",
        "condition_value": 70,
    },
    # --- Special ---
    {
        "id": "placement_done",
        "name": "Know Thyself",
        "description": "Hoàn thành bài kiểm tra đầu vào",
        "icon": "🎯",
        "category": "special",
        "xp_reward": 40,
        "condition_type": "placement_completed",
        "condition_value": 1,
    },
    {
        "id": "polyglot",
        "name": "Polyglot",
        "description": "Luyện tập cả 4 kỹ năng (Listening, Speaking, Reading, Writing)",
        "icon": "🌐",
        "category": "special",
        "xp_reward": 150,
        "condition_type": "all_skills_practiced",
        "condition_value": 1,
    },
]


def seed_achievements(db: Session) -> None:
    """Seed the achievement catalog into the DB (idempotent)."""
    existing_ids = {a.id for a in db.query(Achievement.id).all()}
    for ach_data in ACHIEVEMENT_CATALOG:
        if ach_data["id"] not in existing_ids:
            db.add(Achievement(**ach_data))
    db.commit()


def check_and_award_achievements(learner: LearnerProfile, db: Session) -> list[dict]:
    """
    Check all achievements for a learner and award any newly earned ones.
    Returns list of newly earned achievement dicts (for real-time notification).
    """
    # Get already earned achievement IDs
    earned_ids = {
        la.achievement_id
        for la in db.query(LearnerAchievement).filter(LearnerAchievement.learner_id == learner.id).all()
    }

    all_achievements = db.query(Achievement).all()
    newly_earned = []

    for ach in all_achievements:
        if ach.id in earned_ids:
            continue

        # Evaluate condition
        unlocked = False
        ct = ach.condition_type
        cv = ach.condition_value

        if ct == "lessons_completed":
            unlocked = (learner.total_lessons_completed or 0) >= cv
        elif ct == "streak_days":
            unlocked = (learner.current_streak or 0) >= cv
        elif ct == "xp_total":
            unlocked = (learner.total_xp or 0) >= cv
        elif ct == "speaking_score":
            unlocked = (learner.speaking_score or 0) >= cv
        elif ct == "writing_score":
            unlocked = (learner.writing_score or 0) >= cv
        elif ct == "reading_score":
            unlocked = (learner.reading_score or 0) >= cv
        elif ct == "listening_score":
            unlocked = (learner.listening_score or 0) >= cv
        elif ct == "placement_completed":
            unlocked = learner.placement_completed == "done"
        elif ct == "all_skills_practiced":
            unlocked = all([
                (learner.speaking_score or 0) > 0,
                (learner.writing_score or 0) > 0,
                (learner.reading_score or 0) > 0,
                (learner.listening_score or 0) > 0,
            ])

        if unlocked:
            # Award it
            la = LearnerAchievement(
                learner_id=learner.id,
                achievement_id=ach.id,
            )
            db.add(la)
            learner.total_xp = (learner.total_xp or 0) + ach.xp_reward
            newly_earned.append({
                "id": ach.id,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "xp_reward": ach.xp_reward,
            })

    if newly_earned:
        # Emit in-app notifications for each newly-earned achievement.
        from app.services.notification_service import notify_achievements
        notify_achievements(db, learner.id, newly_earned)
        db.commit()

    return newly_earned


def get_or_create_daily_challenge(learner: LearnerProfile, db: Session) -> DailyChallenge:
    """
    Returns today's daily challenge for the learner.
    Creates one if it doesn't exist yet.
    """
    import random
    from app.core.timeutil import local_today
    today = local_today().isoformat()

    existing = db.query(DailyChallenge).filter(
        DailyChallenge.learner_id == learner.id,
        DailyChallenge.date == today,
    ).first()

    if existing:
        return existing

    # Generate a challenge based on weakest skill
    scores = {
        "vocabulary": learner.vocabulary_score or 0,
        "grammar":    learner.grammar_score or 0,
        "reading":    learner.reading_score or 0,
        "listening":  learner.listening_score or 0,
        "speaking":   learner.speaking_score or 0,
        "writing":    learner.writing_score or 0,
    }
    weakest_skill = min(scores, key=scores.get)

    CHALLENGE_TEMPLATES = {
        "vocabulary": {
            "title": "📚 Vocabulary Builder",
            "description": "Hoàn thành 1 bài học Vocabulary hôm nay",
            "target_type": "complete_lesson",
            "target_value": 1,
            "xp_reward": 25,
        },
        "grammar": {
            "title": "📝 Grammar Master",
            "description": "Hoàn thành 1 bài tập Grammar hôm nay",
            "target_type": "complete_lesson",
            "target_value": 1,
            "xp_reward": 25,
        },
        "reading": {
            "title": "📖 Reading Focus",
            "description": "Hoàn thành 1 bài đọc hiểu hôm nay",
            "target_type": "complete_lesson",
            "target_value": 1,
            "xp_reward": 30,
        },
        "listening": {
            "title": "🎧 Listening Challenge",
            "description": "Hoàn thành 1 bài nghe hiểu hôm nay",
            "target_type": "complete_lesson",
            "target_value": 1,
            "xp_reward": 30,
        },
        "speaking": {
            "title": "🗣️ Speaking Practice",
            "description": "Hoàn thành 1 buổi luyện nói Roleplay hôm nay",
            "target_type": "complete_lesson",
            "target_value": 1,
            "xp_reward": 35,
        },
        "writing": {
            "title": "✍️ Writing Challenge",
            "description": "Nộp 1 bài viết và nhận nhận xét AI hôm nay",
            "target_type": "complete_lesson",
            "target_value": 1,
            "xp_reward": 35,
        },
    }

    template = CHALLENGE_TEMPLATES[weakest_skill]
    challenge = DailyChallenge(
        learner_id=learner.id,
        date=today,
        skill=weakest_skill,
        **template,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge
