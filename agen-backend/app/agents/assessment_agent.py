"""
AGEN - Assessment Agent
Dùng LLM để:
1. Sinh câu hỏi trắc nghiệm/điền từ phù hợp với trình độ
2. Chấm điểm câu trả lời
3. Điều chỉnh độ khó theo kết quả (Adaptive Testing cơ bản)
4. Tổng hợp kết quả cuối bài test thành trình độ CEFR
"""
import logging
import zlib
from typing import Optional
from app.services.llm_client import get_llm_response, parse_and_validate
from app.agents.contracts import PlacementQuestionOutput
from app.services.placement_bank import bank_question

logger = logging.getLogger(__name__)


CEFR_LEVELS = ["PRE_A1", "A1", "A2", "B1", "B2", "C1", "C2"]

# G2 · The speaking question is a read-aloud sentence per level (no LLM): the
# client transcribes it with the Web Speech API and the transcript is scored.
SPEAKING_SKIP = "__skip__"
SPEAKING_PASS_SCORE = 65.0
SPEAKING_BANK: dict[str, list[str]] = {
    "PRE_A1": ["I am happy today.", "This is my book.", "I like apples and bananas."],
    "A1": [
        "My name is Lan and I live in Hanoi.",
        "I usually have breakfast at seven o'clock.",
        "There are three people in my family.",
    ],
    "A2": [
        "Last weekend I went to the beach with my friends.",
        "I would like to order a cup of coffee, please.",
        "The bus is late, so I will take a taxi to work.",
    ],
    "B1": [
        "If I had more time, I would learn to play the guitar.",
        "I have been studying English for about two years.",
        "Could you tell me how to get to the train station?",
    ],
    "B2": [
        "Although the weather was terrible, we decided to go hiking anyway.",
        "The company is planning to expand into several new markets next year.",
        "I think it is important to protect the environment for future generations.",
    ],
    "C1": [
        "Despite the overwhelming evidence, the committee remained unconvinced by the proposal.",
        "Technological innovation has fundamentally reshaped the way we communicate.",
        "She negotiated the contract with remarkable diplomacy and attention to detail.",
    ],
}
SPEAKING_BANK["C2"] = SPEAKING_BANK["C1"]


def build_speaking_question(current_level: str, seed: str = "") -> dict:
    """Read-aloud placement item at the session's current level (deterministic per seed)."""
    level = current_level if current_level in SPEAKING_BANK else "A1"
    bank = SPEAKING_BANK[level]
    target = bank[zlib.crc32(seed.encode("utf-8")) % len(bank)]
    return {
        "skill": "speaking",
        "level": level,
        "effective_level": level,
        "passage": "",
        "audio_text": "",
        "target_text": target,
        "question": "Hãy đọc to câu sau đây",
        "instruction_vi": "Nhấn micro, đọc rõ cả câu, rồi nhấn Kiểm tra. Nếu không có micro, bạn có thể bỏ qua câu này.",
        "options": {},
        "correct_answer": "",
        "explanation": "",
    }


def evaluate_speaking_answer(question: dict, transcript: str) -> dict:
    """Score the transcript of a read-aloud answer; a skip is recorded but not counted."""
    from app.services.pronunciation_service import score_pronunciation

    target = question.get("target_text", "")
    level = question.get("effective_level", "A1")
    level_idx = CEFR_LEVELS.index(level) if level in CEFR_LEVELS else 1
    base_score = 10 + level_idx * 5
    if transcript.strip() == SPEAKING_SKIP or not transcript.strip():
        return {
            "is_correct": False,
            "correct_answer": target,
            "explanation": "Đã bỏ qua phần nói — không tính vào kết quả.",
            "score_delta": 0,
            "skill": "speaking",
            "skipped": True,
            "speaking_score": None,
        }
    result = score_pronunciation(target, transcript)
    pct = result.overall_score
    return {
        "is_correct": pct >= SPEAKING_PASS_SCORE,
        "correct_answer": target,
        "explanation": f"{result.feedback_vi} Máy nghe được: “{transcript.strip()}”",
        "score_delta": int(round(base_score * pct / 100)),
        "skill": "speaking",
        "skipped": False,
        "speaking_score": round(pct, 1),
        "transcript": transcript.strip()[:300],
    }


def generate_placement_question(
    skill: str,
    current_level: str,
    question_index: int,
    previous_correct: Optional[bool] = None,
    learner_age: Optional[int] = None,
    learner_grade: Optional[str] = None,
    skill_occurrence: int = 0,
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
        "listening": (
            "listening comprehension: the learner will only HEAR a short spoken text (1-3 natural "
            "sentences, e.g. a dialogue line, announcement or short message) that you write in "
            "\"audio_text\"; the question asks what was said or meant. Leave \"passage\" empty."
        ),
    }
    skill_desc = skill_map.get(skill, "English knowledge")

    prompt = f"""You are an expert English language assessment AI. Generate exactly ONE placement test question.

Context:
- Target CEFR Level: {effective_level}
- Skill to test: {skill_desc}
- Question number: {question_index + 1} in a short adaptive placement test
- {age_context} {grade_context}

Requirements:
- MUST output valid JSON only, no markdown, no extra text
- For reading skill: include a short passage (2-4 sentences) in the "passage" field
- For listening skill: put the spoken text in "audio_text" (natural spoken English, 1-3 sentences). Do NOT repeat it in the question or options.
- Create a multiple-choice question with exactly 4 options (A, B, C, D)
- Make the question natural, engaging, and age-appropriate
- The correct answer must be clearly correct; distractors must be plausible

Output this exact JSON structure:
{{
  "skill": "{skill}",
  "level": "{effective_level}",
  "passage": "...(for reading only, else empty string)...",
  "audio_text": "...(for listening only, else empty string)...",
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

    try:
        raw = get_llm_response(prompt)
        question_data = parse_and_validate(raw, PlacementQuestionOutput)
    except Exception as exc:  # AI busy, out of quota or bad JSON: the test must never be blocked
        logger.warning("Placement question from the bank (LLM unavailable): %s", exc)
        return bank_question(skill, effective_level, skill_occurrence)

    question_data["effective_level"] = effective_level
    return question_data


def evaluate_answer(question: dict, user_answer: str) -> dict:
    """
    Chấm điểm câu trả lời người dùng.
    Returns: {is_correct, correct_answer, explanation, score_delta}
    """
    skill = question.get("skill", "vocabulary")
    if skill == "speaking":
        return evaluate_speaking_answer(question, user_answer)
    is_correct = user_answer.upper().strip() == question["correct_answer"].upper().strip()

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
    if not any(not a.get("skipped") for a in session_answers):
        return {
            "overall_level": "A1", "skill_scores": {}, "total_correct": 0,
            "total_questions": 0, "accuracy_percent": 0.0, "recommendations": [],
        }

    # Aggregate by skill (a skipped speaking item carries no information)
    skill_totals: dict[str, dict] = {}
    for ans in session_answers:
        if ans.get("skipped"):
            continue
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
    skill_vi = {
        "vocabulary": "Từ vựng", "grammar": "Ngữ pháp", "reading": "Đọc hiểu",
        "listening": "Nghe hiểu", "speaking": "Nói",
    }
    recommendations = []
    for skill, score in skill_scores.items():
        if score < 50:
            recommendations.append(f"Cần tập trung cải thiện kỹ năng {skill_vi.get(skill, skill.capitalize())}")

    return {
        "overall_level": overall_level,
        "skill_scores": skill_scores,
        "total_correct": total_correct,
        "total_questions": total_questions,
        "accuracy_percent": round(ratio * 100, 1),
        "recommendations": recommendations,
    }
