"""
AGEN — AI Lesson Agent
Generates personalized lesson content using LLM based on skill, level and topic.
Returns structured JSON that maps directly to the Lesson + Exercise models.
"""
from app.services.llm_client import get_llm_response, parse_and_validate
from app.agents.contracts import LessonOutput
from app.services.llm_cache import ai_cache

# ── Topic banks per skill (AI will pick one if not specified) ─────────────────
TOPIC_BANK = {
    "vocabulary": [
        "Daily Routines", "Food & Cooking", "Travel & Transport", "Shopping",
        "Work & Career", "Health & Body", "Nature & Environment", "Technology",
        "Emotions & Feelings", "Family & Relationships", "Sports & Hobbies", "Education",
    ],
    "grammar": [
        "Simple Present Tense", "Simple Past Tense", "Present Continuous",
        "Future with Will/Going to", "Modal Verbs (can, must, should)",
        "Prepositions of Time", "Prepositions of Place", "Articles (a/an/the)",
        "Comparative & Superlative", "Present Perfect", "Passive Voice",
        "Conditionals (Type 1 & 2)",
    ],
    "reading": [
        "A Day in the Life", "Environmental Issues", "Technology & Society",
        "Health & Wellness", "Travel Adventures", "Cultural Differences",
        "Science Discoveries", "Famous People", "Social Media & Communication",
    ],
    "listening": [
        "At the Airport", "Ordering Food in a Restaurant", "Weather Forecast",
        "Job Interview", "Booking a Hotel", "Asking for Directions",
        "A Phone Conversation", "Shopping for Clothes", "University Lecture",
    ],
}

XP_PER_LESSON = {
    "PRE_A1": 20, "A1": 25, "A2": 30,
    "B1": 40,    "B2": 50, "C1": 60, "C2": 80,
}


# ── Vocabulary Lesson ─────────────────────────────────────────────────────────
@ai_cache()
def generate_vocabulary_lesson(level: str, topic: str, learner_age: int | None = None) -> dict:
    age_ctx = f"The learner is {learner_age} years old." if learner_age else ""
    prompt = f"""You are an expert English vocabulary teacher. Create a vocabulary lesson.

Settings:
- CEFR Level: {level}
- Topic: {topic}
- {age_ctx}

Generate exactly 8 vocabulary items and then 5 flashcard exercises.

Output ONLY this JSON (no markdown, no extra text):
{{
  "title": "Lesson title here",
  "summary": "One sentence intro about this lesson in Vietnamese",
  "vocabulary": [
    {{
      "word": "example",
      "phonetic": "/ɪɡˈzɑːmpl/",
      "part_of_speech": "noun",
      "definition": "English definition",
      "translation": "Vietnamese translation",
      "example": "Example sentence using the word.",
      "image_hint": "simple emoji representing the word"
    }}
  ],
  "exercises": [
    {{
      "type": "flashcard",
      "order": 0,
      "content": {{
        "word": "example",
        "phonetic": "/ɪɡˈzɑːmpl/",
        "definition": "English definition",
        "translation": "Vietnamese translation",
        "example": "Example sentence.",
        "image_hint": "📝"
      }}
    }},
    {{
      "type": "multiple_choice",
      "order": 5,
      "content": {{
        "question": "Which word means '...'?",
        "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "correct_answer": "A",
        "explanation": "Brief explanation"
      }}
    }}
  ]
}}

Rules:
- vocabulary array: exactly 8 items
- exercises array: first 5 items are flashcards (type: flashcard), then 3 multiple_choice questions testing the vocabulary
- Keep it appropriate for {level} level learners
- Make definitions clear and examples natural"""

    raw = get_llm_response(prompt)
    data = parse_and_validate(raw, LessonOutput)
    data["skill"] = "vocabulary"
    data["topic"] = topic
    data["level"] = level
    data["xp_value"] = XP_PER_LESSON.get(level, 30)
    return data


# ── Grammar Lesson ────────────────────────────────────────────────────────────
@ai_cache()
def generate_grammar_lesson(level: str, topic: str, learner_age: int | None = None) -> dict:
    age_ctx = f"The learner is {learner_age} years old." if learner_age else ""
    prompt = f"""You are an expert English grammar teacher. Create a grammar lesson for Vietnamese learners.

Settings:
- CEFR Level: {level}
- Grammar Topic: {topic}
- {age_ctx}

Output ONLY this JSON (no markdown):
{{
  "title": "Lesson title",
  "summary": "One sentence intro in Vietnamese",
  "explanation": {{
    "rule": "Clear grammar rule in English (1-2 sentences)",
    "rule_vi": "Giải thích ngữ pháp bằng tiếng Việt",
    "structure": "Formula e.g. Subject + V-ed + Object",
    "examples": [
      {{"en": "She walked to school.", "vi": "Cô ấy đi bộ đến trường."}},
      {{"en": "They played football.", "vi": "Họ chơi bóng đá."}}
    ],
    "common_mistakes": ["Common mistake 1", "Common mistake 2"]
  }},
  "exercises": [
    {{
      "type": "fill_blank",
      "order": 0,
      "content": {{
        "sentence": "She ___ to school yesterday.",
        "blank_word": "walked",
        "hint": "past tense of 'walk'",
        "options": ["walk", "walked", "walking", "walks"]
      }}
    }}
  ]
}}

Rules:
- exercises: exactly 6 fill_blank exercises
- Make fill_blank options plausible (common mistakes) not obviously wrong
- Explanation must be in BOTH English and Vietnamese"""

    raw = get_llm_response(prompt)
    data = parse_and_validate(raw, LessonOutput)
    data["skill"] = "grammar"
    data["topic"] = topic
    data["level"] = level
    data["xp_value"] = XP_PER_LESSON.get(level, 30)
    return data


# ── Reading Lesson ────────────────────────────────────────────────────────────
@ai_cache()
def generate_reading_lesson(level: str, topic: str, learner_age: int | None = None) -> dict:
    age_ctx = f"The learner is {learner_age} years old." if learner_age else ""
    # Word count by level
    word_count = {"PRE_A1": 60, "A1": 80, "A2": 120, "B1": 180, "B2": 250, "C1": 320, "C2": 400}.get(level, 120)

    prompt = f"""You are an expert English reading teacher. Create a reading comprehension lesson.

Settings:
- CEFR Level: {level}
- Topic: {topic}
- Passage length: approximately {word_count} words
- {age_ctx}

Output ONLY this JSON (no markdown):
{{
  "title": "Lesson title",
  "summary": "One sentence intro in Vietnamese about the topic",
  "passage": {{
    "text": "The full reading passage here. About {word_count} words.",
    "vocabulary_highlights": [
      {{"word": "word", "definition": "meaning"}}
    ]
  }},
  "exercises": [
    {{
      "type": "multiple_choice",
      "order": 0,
      "content": {{
        "question": "What is the main idea of the passage?",
        "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "correct_answer": "A",
        "explanation": "The passage states that..."
      }}
    }}
  ]
}}

Rules:
- passage.text: appropriate for {level} level, engaging and informative
- exercises: exactly 5 multiple_choice questions based on the passage
- vocabulary_highlights: 3-5 key words from the passage with definitions
- Questions should test: main idea, detail, inference, vocabulary, tone"""

    raw = get_llm_response(prompt)
    data = parse_and_validate(raw, LessonOutput)
    data["skill"] = "reading"
    data["topic"] = topic
    data["level"] = level
    data["xp_value"] = XP_PER_LESSON.get(level, 30)
    return data


# ── Listening Lesson ──────────────────────────────────────────────────────────
@ai_cache()
def generate_listening_lesson(level: str, topic: str, learner_age: int | None = None) -> dict:
    age_ctx = f"The learner is {learner_age} years old." if learner_age else ""
    word_count = {"PRE_A1": 50, "A1": 80, "A2": 120, "B1": 150, "B2": 200, "C1": 250, "C2": 300}.get(level, 120)

    prompt = f"""You are an expert English listening teacher. Create a listening comprehension lesson.

Settings:
- CEFR Level: {level}
- Topic: {topic}
- Transcript length: approximately {word_count} words
- Format: Conversation or monologue
- {age_ctx}

Output ONLY this JSON (no markdown):
{{
  "title": "Lesson title",
  "summary": "One sentence intro in Vietnamese about the topic",
  "passage": {{
    "text": "The full transcript here. About {word_count} words.",
    "script_lines": [
      {{"speaker": "John", "text": "Hello, how can I help you?"}},
      {{"speaker": "Mary", "text": "I would like to order a pizza."}}
    ],
    "vocabulary_highlights": [
      {{"word": "order", "definition": "to request food or goods"}}
    ]
  }},
  "exercises": [
    {{
      "type": "multiple_choice",
      "order": 0,
      "content": {{
        "question": "What does Mary want to do?",
        "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "correct_answer": "A",
        "explanation": "Mary says she wants to order a pizza."
      }}
    }}
  ]
}}

Rules:
- passage.script_lines: Must break down the transcript into lines spoken by specific characters (or 'Narrator' if monologue).
- exercises: exactly 5 multiple_choice questions based on the listening script.
- vocabulary_highlights: 3-5 key words with definitions.
- Keep the language level strictly {level}."""

    raw = get_llm_response(prompt)
    data = parse_and_validate(raw, LessonOutput)
    data["skill"] = "listening"
    data["topic"] = topic
    data["level"] = level
    data["xp_value"] = XP_PER_LESSON.get(level, 30)
    return data


# ── Main Dispatcher ───────────────────────────────────────────────────────────
def generate_lesson(skill: str, level: str, topic: str | None = None, learner_age: int | None = None) -> dict:
    """
    Main entry point. Dispatch to the correct lesson generator by skill.
    If topic not specified, pick a recommended one based on level.
    """
    import random
    if not topic:
        topics = TOPIC_BANK.get(skill, ["General English"])
        topic = random.choice(topics)

    generators = {
        "vocabulary": generate_vocabulary_lesson,
        "grammar":    generate_grammar_lesson,
        "reading":    generate_reading_lesson,
        "listening":  generate_listening_lesson,
    }
    generator = generators.get(skill)
    if not generator:
        raise ValueError(f"Skill '{skill}' not yet supported in Lesson Agent. Supported: {list(generators.keys())}")

    return generator(level=level, topic=topic, learner_age=learner_age)


def compute_lesson_score(exercises_results: list[dict]) -> dict:
    """
    Compute final lesson score from submitted exercise results.
    Returns: { score, correct, total, xp_earned, grade }
    """
    total = len(exercises_results)
    correct = sum(1 for e in exercises_results if e.get("is_correct"))
    score = round((correct / total) * 100, 1) if total > 0 else 0

    if score >= 90:
        grade = "S"  # Xuất sắc
    elif score >= 75:
        grade = "A"  # Tốt
    elif score >= 60:
        grade = "B"  # Khá
    elif score >= 45:
        grade = "C"  # Trung bình
    else:
        grade = "D"  # Cần ôn tập

    # XP: full if ≥ 75%, half if ≥ 45%, minimal if < 45%
    base_xp = 30
    if score >= 75:
        xp = base_xp
    elif score >= 45:
        xp = base_xp // 2
    else:
        xp = 5

    return {"score": score, "correct": correct, "total": total, "xp_earned": xp, "grade": grade}
