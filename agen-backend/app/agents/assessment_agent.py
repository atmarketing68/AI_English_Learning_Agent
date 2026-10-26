"""
AGEN - Assessment Agent
Dùng LLM để:
1. Sinh câu hỏi trắc nghiệm/điền từ phù hợp với trình độ
2. Chấm điểm câu trả lời
3. Điều chỉnh độ khó theo kết quả (Adaptive Testing cơ bản)
4. Tổng hợp kết quả cuối bài test thành trình độ CEFR
"""
from typing import Optional
from app.services.llm_client import get_llm_response, parse_and_validate
from app.agents.contracts import PlacementQuestionOutput


CEFR_LEVELS = ["PRE_A1", "A1", "A2", "B1", "B2", "C1", "C2"]


def generate_placement_question(
    skill: str,
    current_level: str,
    question_index: int,
    previous_correct: Optional[bool] = None,
    learner_age: Optional[int] = None,
    learner_grade: Optional[str] = None,
) -> dict:
    """
    Sinh 1 câu hỏi placement test.
    Tự động tăng/giảm độ khó dựa trên câu trước (adaptive).
    """
    # Adaptive level adjustment
    level_idx = CEFR_LEVELS.index(current_level) if current_level in CEFR_LEVELS else 1
    if previous_correct is True and level_idx < len(CEFR_LEVELS) - 1:
        level_idx += 1
    elif previous_correct is False and level_idx > 0:
        level_idx -= 1
    effective_level = CEFR_LEVELS[level_idx]

    age_context = f"The learner is {learner_age} years old." if learner_age else ""
    grade_context = f"The learner is in {learner_grade.replace('_', ' ')}." if learner_grade else ""

    skill_map = {
        "vocabulary": "vocabulary knowledge (word meaning, usage, synonyms)",
        "grammar": "grammar (sentence structure, tense, prepositions, articles)",
        "reading": "reading comprehension (short passage with a question)",
        "listening": "listening comprehension (describe a short scenario in text, then ask about it)",
    }
    skill_desc = skill_map.get(skill, "English knowledge")

    prompt = f"""You are an expert English language assessment AI. Generate exactly ONE placement test question.

Context:
- Target CEFR Level: {effective_level}
- Skill to test: {skill_desc}
- Question number: {question_index + 1} in a 10-question test
- {age_context} {grade_context}

Requirements:
- MUST output valid JSON only, no markdown, no extra text
- For reading skill: include a short passage (2-4 sentences) in the "passage" field
- Create a multiple-choice question with exactly 4 options (A, B, C, D)
- Make the question natural, engaging, and age-appropriate
- The correct answer must be clearly correct; distractors must be plausible

Output this exact JSON structure:
{{
  "skill": "{skill}",
  "level": "{effective_level}",
  "passage": "...(for reading only, else empty string)...",
  "question": "...",
  "options": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  }},
  "correct_answer": "A",
  "explanation": "Brief explanation of why the answer is correct"
}}"""

    raw = get_llm_response(prompt)
    question_data = parse_and_validate(raw, PlacementQuestionOutput)

    question_data["effective_level"] = effective_level
    return question_data


def evaluate_answer(question: dict, user_answer: str) -> dict:
    """
    Chấm điểm câu trả lời người dùng.
    Returns: {is_correct, correct_answer, explanation, score_delta}
    """
    is_correct = user_answer.upper().strip() == question["correct_answer"].upper().strip()
    skill = question.get("skill", "vocabulary")

    # Score delta based on level difficulty
    level = question.get("effective_level", "A1")
    level_idx = CEFR_LEVELS.index(level) if level in CEFR_LEVELS else 1
    base_score = 10 + level_idx * 5  # A1=10pts, A2=15pts, ... C2=40pts

    return {
        "is_correct": is_correct,
        "correct_answer": question["correct_answer"],
        "explanation": question.get("explanation", ""),
        "score_delta": base_score if is_correct else 0,
        "skill": skill,
    }


def calculate_final_result(session_answers: list[dict]) -> dict:
    """
    Tổng hợp kết quả cuối bài test.
    Returns: overall_level, skill_scores, recommendations
    """
    if not session_answers:
        return {"overall_level": "A1", "skill_scores": {}, "recommendations": []}

    # Aggregate by skill
    skill_totals: dict[str, dict] = {}
    for ans in session_answers:
        skill = ans.get("skill", "vocabulary")
        if skill not in skill_totals:
            skill_totals[skill] = {"correct": 0, "total": 0, "score": 0, "max_score": 0}
        skill_totals[skill]["total"] += 1
        skill_totals[skill]["max_score"] += ans.get("max_score_delta", 25)
        if ans.get("is_correct"):
            skill_totals[skill]["correct"] += 1
            skill_totals[skill]["score"] += ans.get("score_delta", 0)

    # Convert to percentages
    skill_scores = {}
    for skill, data in skill_totals.items():
        pct = (data["score"] / data["max_score"] * 100) if data["max_score"] > 0 else 0
        skill_scores[skill] = round(pct, 1)

    # Determine overall CEFR level from correct-answer ratio
    total_correct = sum(d["correct"] for d in skill_totals.values())
    total_questions = sum(d["total"] for d in skill_totals.values())
    ratio = total_correct / total_questions if total_questions > 0 else 0

    # Simple threshold mapping
    if ratio >= 0.90:
        overall_level = "C1"
    elif ratio >= 0.75:
        overall_level = "B2"
    elif ratio >= 0.60:
        overall_level = "B1"
    elif ratio >= 0.45:
        overall_level = "A2"
    elif ratio >= 0.25:
        overall_level = "A1"
    else:
        overall_level = "PRE_A1"

    # Recommendations based on weak skills
    recommendations = []
    for skill, score in skill_scores.items():
        if score < 50:
            recommendations.append(f"Cần tập trung cải thiện kỹ năng {skill.capitalize()}")

    return {
        "overall_level": overall_level,
        "skill_scores": skill_scores,
        "total_correct": total_correct,
        "total_questions": total_questions,
        "accuracy_percent": round(ratio * 100, 1),
        "recommendations": recommendations,
    }
