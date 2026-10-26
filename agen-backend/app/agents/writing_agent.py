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

# G5 · Exam-style genres: the prompt follows the real task format and the
# evaluation adds a band (IELTS 0–9 by 4 criteria) or a TOEIC Writing score.
EXAM_GENRES: dict[str, dict] = {
    "ielts_task2": {
        "exam": "ielts", "label": "IELTS Writing Task 2", "words": "250+",
        "format": "IELTS Academic/General Writing Task 2: a 250-word essay answering a question on the topic. "
                  "Use one of the real question types: agree/disagree, discuss both views, advantages/disadvantages, problem/solution, two-part question.",
        "topics": [
            "Some people think that universities should only teach job-related subjects. To what extent do you agree or disagree?",
            "Many people now shop online instead of in shops. Discuss the advantages and disadvantages.",
            "Traffic congestion is increasing in big cities. What problems does this cause and what solutions can you suggest?",
            "Some believe children should start learning a foreign language at primary school. Discuss both views and give your opinion.",
            "In many countries people are living longer. What are the causes and is this a positive or negative development?",
        ],
    },
    "ielts_task1": {
        "exam": "ielts", "label": "IELTS Writing Task 1 (General – letter)", "words": "150+",
        "format": "IELTS General Training Writing Task 1: a 150-word letter (formal, semi-formal or informal) covering three bullet points given in the task.",
        "topics": [
            "You recently stayed at a hotel and had a problem with your room. Write a letter to the manager.",
            "A friend has invited you to visit, but you cannot go. Write a letter explaining why and suggesting another time.",
            "You want to take a short English course abroad. Write a letter to the school asking for information.",
            "You have lost an item on public transport. Write a letter to the transport company.",
        ],
    },
    "toeic_email": {
        "exam": "toeic", "label": "TOEIC Writing – Respond to an email (Q6–7)", "words": "80–120",
        "format": "TOEIC Speaking & Writing, Questions 6–7: read a short business e-mail and write a reply that does the two or three things the instructions ask for (e.g. ask two questions and make one suggestion).",
        "topics": [
            "A customer e-mails asking about delivery options for an order. Reply: give two options and ask one question.",
            "Your manager asks you to organise a team lunch. Reply: suggest two places and ask one question.",
            "A supplier e-mails about a delayed shipment. Reply: ask two questions and make one request.",
            "A colleague asks for help preparing a presentation. Reply: make two suggestions and ask one question.",
        ],
    },
    "toeic_essay": {
        "exam": "toeic", "label": "TOEIC Writing – Opinion essay (Q8)", "words": "300",
        "format": "TOEIC Writing Question 8: an opinion essay of at least 300 words that states an opinion, gives reasons and examples.",
        "topics": [
            "Do you agree or disagree: Employees should be allowed to work from home at least two days a week?",
            "Some companies reward employees with money, others with extra holiday. Which is better and why?",
            "Is it better to work for a large company or a small one? Give reasons and examples.",
            "Do you agree or disagree: It is more important to have a good salary than to enjoy your job?",
        ],
    },
}

IELTS_CRITERIA = {"task_response": "Task Response", "coherence_cohesion": "Coherence & Cohesion", "lexical_resource": "Lexical Resource", "grammatical_range": "Grammatical Range & Accuracy"}
TOEIC_CRITERIA = {"task_completion": "Hoàn thành yêu cầu", "organisation": "Tổ chức ý", "vocabulary": "Từ vựng", "grammar": "Ngữ pháp"}

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
    exam = EXAM_GENRES.get(genre)
    topics = exam["topics"] if exam else WRITING_TOPICS.get(genre, WRITING_TOPICS["opinion"])
    topic = random.choice(topics)
    guidance = LEVEL_GUIDANCE.get(level, LEVEL_GUIDANCE["A2"])
    if exam:
        guidance = {"words": exam["words"], "sentences": "exam format"}
    exam_note = f"\nExam format (follow it exactly): {exam['format']}\n" if exam else ""

    prompt = f"""You are an English writing teacher creating a writing task for a CEFR {level} Vietnamese learner.

Topic: {topic}
Genre: {genre}
Word target: {guidance['words']} words
{exam_note}
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


def _exam_rubric(genre: str) -> str:
    exam = EXAM_GENRES.get(genre)
    if not exam:
        return ""
    if exam["exam"] == "ielts":
        return """
EXAM BAND (this is an IELTS task): also return
    "exam_band": {
        "exam": "ielts",
        "overall": 6.0,
        "criteria": {"task_response": 6.0, "coherence_cohesion": 6.0, "lexical_resource": 5.5, "grammatical_range": 6.0},
        "next_band_tips": ["2-3 concrete, Vietnamese tips to reach the next half band"]
    }
Use the official public IELTS band descriptors (0–9 in 0.5 steps) for each criterion; overall = mean of the four, rounded to the nearest 0.5 (round .25 up). A text well under the word limit is penalised in task_response."""
    return """
EXAM SCORE (this is a TOEIC Writing task): also return
    "exam_band": {
        "exam": "toeic",
        "overall": 140,
        "criteria": {"task_completion": 4, "organisation": 3, "vocabulary": 4, "grammar": 3},
        "next_band_tips": ["2-3 concrete, Vietnamese tips to raise the score"]
    }
Rate each criterion 0–5 as an ETS rater would (e-mail tasks 0–4, essay 0–5; use the 0–5 scale here), then map the average to the TOEIC Writing scaled score 0–200 (5 → 200, 4 → 170, 3 → 140, 2 → 100, 1 → 60, 0 → 0, interpolate)."""


def evaluate_writing(prompt_text: str, user_text: str, level: str, genre: str = "opinion") -> dict:
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
- All Vietnamese feedback should be warm and specific
{_exam_rubric(genre)}"""

    raw = get_llm_response(prompt)
    result = parse_and_validate(raw, WritingEvaluationOutput)
    result["word_count"] = word_count  # Ensure accuracy
    if genre not in EXAM_GENRES:
        result["exam_band"] = None
    return result
