"""
AGEN — Writing Coach Agent
Generates writing prompts and provides detailed AI-powered writing evaluation.
"""
from app.services.llm_client import get_llm_response, parse_and_validate
from app.agents.contracts import WritingPromptOutput, WritingEvaluationOutput
from app.services.llm_cache import ai_cache


# --- Writing topic bank by skill area ---
WRITING_TOPICS = {
    "descriptive": [
        "Describe your hometown", "My favourite meal", "A place I love",
        "Describe a memorable day", "My ideal home",
    ],
    "opinion": [
        "Should students use smartphones in class?",
        "Is social media good or bad?",
        "Is online learning better than traditional school?",
        "Should everyone learn English?",
    ],
    "narrative": [
        "A time I felt proud", "An unexpected journey", "My first day at a new place",
        "A challenge I overcame", "A funny misunderstanding",
    ],
    "email": [
        "Write an email to a friend about your weekend plans",
        "Write an email to a hotel to book a room",
        "Write an email to your boss asking for a day off",
    ],
}

# Approximate word counts and structure guidance per CEFR level
LEVEL_GUIDANCE = {
    "PRE_A1": {"words": "20–30",  "sentences": 3},
    "A1":     {"words": "30–50",  "sentences": 5},
    "A2":     {"words": "50–80",  "sentences": 6},
    "B1":     {"words": "80–120", "sentences": "multiple paragraphs"},
    "B2":     {"words": "120–180","sentences": "structured essay"},
    "C1":     {"words": "180–250","sentences": "formal essay with arguments"},
    "C2":     {"words": "250+",   "sentences": "sophisticated essay"},
}


@ai_cache()
def generate_writing_prompt(level: str, genre: str = "opinion") -> dict:
    """
    Generates a structured writing prompt appropriate for the learner's level.

    Returns:
    {
        "title": str,
        "prompt": str,
        "genre": str,
        "word_target": str,
        "guide_steps": [str],
        "useful_phrases": [str],
        "example_opening": str
    }
    """
    import random
    topics = WRITING_TOPICS.get(genre, WRITING_TOPICS["opinion"])
    topic = random.choice(topics)
    guidance = LEVEL_GUIDANCE.get(level, LEVEL_GUIDANCE["A2"])

    prompt = f"""You are an English writing teacher creating a writing task for a CEFR {level} Vietnamese learner.

Topic: {topic}
Genre: {genre}
Word target: {guidance['words']} words

Create a clear, motivating writing prompt with scaffolding support.

Output ONLY JSON (no markdown):
{{
    "title": "Short title of the task",
    "prompt": "The writing task instruction in simple, clear English (2-3 sentences). Be friendly and encouraging.",
    "genre": "{genre}",
    "word_target": "{guidance['words']} words",
    "guide_steps": [
        "Step 1: Start with...",
        "Step 2: Then mention...",
        "Step 3: End with..."
    ],
    "useful_phrases": [
        "I think that...",
        "In my opinion...",
        "One reason is..."
    ],
    "example_opening": "One example opening sentence appropriate for {level} level."
}}

Rules:
- guide_steps: exactly 3 steps, simple Vietnamese-friendly instructions
- useful_phrases: 4-5 phrases learner can use
- example_opening: short, natural, level-appropriate"""

    raw = get_llm_response(prompt)
    result = parse_and_validate(raw, WritingPromptOutput)
    result["level"] = level
    result["topic"] = topic
    return result


def evaluate_writing(prompt_text: str, user_text: str, level: str) -> dict:
    """
    Evaluates a learner's writing submission in detail.

    Returns:
    {
        "overall_score": float (0-100),
        "grade": str (S/A/B/C/D),
        "word_count": int,
        "scores": {
            "grammar": float,
            "vocabulary": float,
            "coherence": float,
            "task_achievement": float
        },
        "grammar_errors": [{"original": str, "corrected": str, "explanation_vi": str}],
        "vocabulary_feedback": str (Vietnamese),
        "coherence_feedback": str (Vietnamese),
        "strengths": [str],
        "improvements": [str],
        "corrected_version": str,
        "encouragement": str (Vietnamese)
    }
    """
    word_count = len(user_text.split())

    prompt = f"""You are an expert English writing evaluator for Vietnamese learners at CEFR {level} level.

Writing Task: {prompt_text}

Student's Writing:
---
{user_text}
---

Word count: {word_count} words

Evaluate this writing THOROUGHLY and return ONLY JSON:
{{
    "overall_score": 75.5,
    "grade": "B",
    "word_count": {word_count},
    "scores": {{
        "grammar": 70.0,
        "vocabulary": 75.0,
        "coherence": 80.0,
        "task_achievement": 78.0
    }},
    "grammar_errors": [
        {{
            "original": "I go to school yesterday",
            "corrected": "I went to school yesterday",
            "explanation_vi": "Dùng thì Quá khứ đơn vì hành động đã xảy ra trong quá khứ ('yesterday')."
        }}
    ],
    "vocabulary_feedback": "Nhận xét về vốn từ bằng tiếng Việt, cụ thể, chỉ ra từ hay dùng và gợi ý từ mới.",
    "coherence_feedback": "Nhận xét về sự mạch lạc và cấu trúc bài viết bằng tiếng Việt.",
    "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
    "improvements": ["Cần cải thiện 1", "Cần cải thiện 2"],
    "corrected_version": "The fully corrected version of the student's writing, keeping their ideas but fixing all errors.",
    "encouragement": "Lời động viên ấm áp bằng tiếng Việt, phù hợp với điểm số và trình độ."
}}

Grading scale:
- S (90-100): Near-perfect, exceptional for the level
- A (75-89): Very good, minor errors only
- B (60-74): Good effort, some notable errors
- C (45-59): Fair, many errors but message is clear
- D (0-44): Needs significant improvement

Rules:
- grammar_errors: list up to 5 most important errors (not all minor ones)
- corrected_version: full corrected text preserving learner's ideas and voice
- Be encouraging and constructive, appropriate for CEFR {level}
- All Vietnamese feedback should be warm and specific"""

    raw = get_llm_response(prompt)
    result = parse_and_validate(raw, WritingEvaluationOutput)
    result["word_count"] = word_count  # Ensure accuracy
    return result
