"""
AGEN — Adaptive Coach Agent
Analyzes learner data and generates personalized study plans and reports.
"""
from app.services.llm_client import get_llm_response, parse_and_validate
from app.agents.contracts import CoachAdviceOutput, WeeklyReportOutput


def analyze_learner(learner_data: dict, recent_events: list[dict]) -> dict:
    """
    Analyzes learner profile and recent activity to create a personalized coaching plan.

    learner_data: {overall_level, vocabulary_score, grammar_score, reading_score,
                   speaking_score, listening_score, total_xp, current_streak, total_lessons_completed}
    recent_events: last 20 LearningEvents as dicts [{skill, score, event_type, topic}]

    Returns: {
        weak_skills, strong_skills, recommended_topics,
        study_plan_today, motivational_message, focus_area
    }
    """
    events_summary = ""
    if recent_events:
        for ev in recent_events[-10:]:
            events_summary += f"- {ev.get('skill','?')} | {ev.get('topic','?')} | score:{ev.get('score', 0):.0f}%\n"
    else:
        events_summary = "- Chưa có hoạt động học nào gần đây.\n"

    skill_scores = {
        "Vocabulary": learner_data.get("vocabulary_score", 0),
        "Grammar":    learner_data.get("grammar_score", 0),
        "Reading":    learner_data.get("reading_score", 0),
        "Speaking":   learner_data.get("speaking_score", 0),
        "Listening":  learner_data.get("listening_score", 0),
    }
    skill_str = "\n".join(f"  - {k}: {v:.0f}%" for k, v in skill_scores.items())

    prompt = f"""You are AGEN — a personalized English learning AI coach for Vietnamese learners.

Learner Profile:
- Level: {learner_data.get("overall_level", "A1")}
- Total XP: {learner_data.get("total_xp", 0)}
- Streak: {learner_data.get("current_streak", 0)} days
- Lessons completed: {learner_data.get("total_lessons_completed", 0)}

Skill Scores (0-100):
{skill_str}

Recent Activity (last 10 events):
{events_summary}

Based on this data, provide a personalized coaching analysis and study plan.

Output ONLY JSON (no markdown):
{{
    "weak_skills": ["Grammar", "Speaking"],
    "strong_skills": ["Reading"],
    "focus_area": "Grammar",
    "recommended_topics": [
        {{"skill": "grammar", "topic": "Modal Verbs", "reason": "Điểm Grammar thấp nhất"}},
        {{"skill": "speaking", "topic": "At the Coffee Shop", "reason": "Cần luyện Speaking thêm"}}
    ],
    "study_plan_today": "📝 15 phút Grammar (Modal Verbs) → 🗣️ 10 phút Speaking Practice → 📚 5 phút Vocabulary",
    "motivational_message": "Cá nhân hóa tin nhắn động viên bằng tiếng Việt, đề cập đến streak và điểm mạnh của người học."
}}

Rules:
- weak_skills: skills with score < 50, or lowest scores
- strong_skills: skills with score >= 70
- recommended_topics: exactly 2 topics
- study_plan_today: realistic 30-minute plan using emoji
- motivational_message: warm, encouraging, personal (Vietnamese), mention their streak if > 0"""

    raw = get_llm_response(prompt)
    return parse_and_validate(raw, CoachAdviceOutput)


def generate_weekly_report(learner_data: dict, weekly_events: list[dict]) -> dict:
    """
    Generates a weekly progress summary.

    Returns: {
        sessions_count, xp_earned_this_week, best_skill, most_practiced_skill,
        highlight, areas_to_improve, next_week_goal, encouragement
    }
    """
    if not weekly_events:
        return {
            "sessions_count": 0,
            "xp_earned_this_week": 0,
            "best_skill": "N/A",
            "most_practiced_skill": "N/A",
            "highlight": "Tuần này bạn chưa học buổi nào.",
            "areas_to_improve": ["Tất cả các kỹ năng"],
            "next_week_goal": "Học ít nhất 3 buổi trong tuần tới!",
            "encouragement": "Mỗi hành trình vĩ đại đều bắt đầu từ một bước nhỏ. Hãy bắt đầu ngay hôm nay! 💪"
        }

    # Compute quick stats
    xp_total = sum(e.get("xp_earned", 0) for e in weekly_events)
    skill_counts: dict[str, int] = {}
    skill_scores: dict[str, list] = {}
    for ev in weekly_events:
        sk = ev.get("skill", "unknown")
        skill_counts[sk] = skill_counts.get(sk, 0) + 1
        skill_scores.setdefault(sk, []).append(ev.get("score", 0))

    most_practiced = max(skill_counts, key=skill_counts.get) if skill_counts else "N/A"
    avg_scores = {sk: sum(v) / len(v) for sk, v in skill_scores.items()}
    best_skill = max(avg_scores, key=avg_scores.get) if avg_scores else "N/A"

    events_summary = "\n".join(
        f"- {e.get('skill')} | {e.get('topic','?')} | score:{e.get('score',0):.0f}% | +{e.get('xp_earned',0)}XP"
        for e in weekly_events
    )

    prompt = f"""You are AGEN — an AI English coach. Generate a warm, encouraging weekly report for a Vietnamese learner.

This week's activity ({len(weekly_events)} sessions, {xp_total} XP earned):
{events_summary}

Learner level: {learner_data.get("overall_level", "A1")}
Most practiced skill: {most_practiced}
Best performing skill: {best_skill}

Output ONLY JSON (no markdown):
{{
    "sessions_count": {len(weekly_events)},
    "xp_earned_this_week": {xp_total},
    "best_skill": "{best_skill}",
    "most_practiced_skill": "{most_practiced}",
    "highlight": "Điểm nổi bật của tuần, bằng tiếng Việt, cụ thể và tích cực.",
    "areas_to_improve": ["Skill cần cải thiện 1", "Skill cần cải thiện 2"],
    "next_week_goal": "Mục tiêu cụ thể cho tuần tới bằng tiếng Việt.",
    "encouragement": "Lời động viên ấm áp và cá nhân hóa bằng tiếng Việt."
}}"""

    raw = get_llm_response(prompt)
    result = parse_and_validate(raw, WeeklyReportOutput)
    # Ensure computed fields are correct
    result["sessions_count"] = len(weekly_events)
    result["xp_earned_this_week"] = xp_total
    return result
