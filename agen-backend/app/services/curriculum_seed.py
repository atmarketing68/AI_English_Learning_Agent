"""
AGEN — Curriculum Map Seed Data
Human-designed curriculum map (Master Plan Phần B).

Structure: LEVEL (A1, A2, ...) → 6 UNITS → each unit has 4 skill lessons + 1 review.
This is the fixed skeleton; AI fills in the actual exercise content on demand.

Levels are seeded in order (A1 then A2), and the prerequisite chain spans across
levels: the first A2 lesson requires the last A1 lesson, so a learner must finish
A1 before A2 unlocks. Idempotent: safe to run on every startup.
"""
from sqlalchemy.orm import Session

from app.models.curriculum import CurriculumUnit, CurriculumLesson
from app.services.curriculum_a2 import A2_CURRICULUM
from app.services.curriculum_b1 import B1_CURRICULUM

# ── A1 CURRICULUM MAP ──────────────────────────────────────────────────────────
# Each unit: (code, order, title, theme, icon, [lessons])
# Each lesson: (order, code, title, skill, difficulty, topic, objective,
#               vocabulary_focus, grammar_focus, is_review, is_assessment)
A1_CURRICULUM: list[dict] = [
    {
        "code": "A1-U01", "order": 1, "title": "Me & My World",
        "theme": "Introductions & Identity", "icon": "👋",
        "description": "Chào hỏi, giới thiệu bản thân, gia đình và trường học.",
        "lessons": [
            {"order": 1, "code": "A1-U01-L01", "title": "Hello!", "skill": "vocabulary", "difficulty": 1,
             "topic": "Greetings", "objective": "Chào hỏi và giới thiệu tên.",
             "vocabulary_focus": ["hello", "hi", "goodbye", "name", "nice to meet you"],
             "grammar_focus": "Verb 'to be' (I am / You are)"},
            {"order": 2, "code": "A1-U01-L02", "title": "My Family", "skill": "vocabulary", "difficulty": 1,
             "topic": "Family & Relationships", "objective": "Gọi tên các thành viên gia đình.",
             "vocabulary_focus": ["mother", "father", "sister", "brother", "family"],
             "grammar_focus": "Possessive adjectives (my, your)"},
            {"order": 3, "code": "A1-U01-L03", "title": "This is my school", "skill": "grammar", "difficulty": 2,
             "topic": "Simple Present Tense", "objective": "Dùng This/That để chỉ đồ vật.",
             "vocabulary_focus": ["school", "classroom", "teacher", "student", "book"],
             "grammar_focus": "Demonstratives (this / that)"},
            {"order": 4, "code": "A1-U01-L04", "title": "A day at school", "skill": "reading", "difficulty": 2,
             "topic": "A Day in the Life", "objective": "Đọc hiểu đoạn văn ngắn về trường học.",
             "vocabulary_focus": ["morning", "lesson", "friend", "play", "learn"],
             "grammar_focus": "Simple Present Tense"},
            {"order": 5, "code": "A1-U01-L05", "title": "Unit 1 Review", "skill": "vocabulary", "difficulty": 2,
             "topic": "Me & My World", "objective": "Ôn tập Unit 1.",
             "vocabulary_focus": [], "grammar_focus": None, "is_review": True},
        ],
    },
    {
        "code": "A1-U02", "order": 2, "title": "Daily Life",
        "theme": "Routines & Time", "icon": "🕐",
        "description": "Thói quen hằng ngày, thời gian và hoạt động.",
        "lessons": [
            {"order": 1, "code": "A1-U02-L01", "title": "Daily Routines", "skill": "vocabulary", "difficulty": 2,
             "topic": "Daily Routines", "objective": "Nói về hoạt động hằng ngày.",
             "vocabulary_focus": ["wake up", "eat", "study", "sleep", "play"],
             "grammar_focus": "Simple Present (I wake up...)"},
            {"order": 2, "code": "A1-U02-L02", "title": "What time is it?", "skill": "grammar", "difficulty": 2,
             "topic": "Prepositions of Time", "objective": "Hỏi và trả lời về thời gian.",
             "vocabulary_focus": ["o'clock", "morning", "afternoon", "evening", "night"],
             "grammar_focus": "Prepositions of time (at, in, on)"},
            {"order": 3, "code": "A1-U02-L03", "title": "Listen: My morning", "skill": "listening", "difficulty": 2,
             "topic": "A Phone Conversation", "objective": "Nghe hiểu mô tả buổi sáng.",
             "vocabulary_focus": ["breakfast", "brush", "school bus", "early"],
             "grammar_focus": "Simple Present Tense"},
            {"order": 4, "code": "A1-U02-L04", "title": "My weekend", "skill": "reading", "difficulty": 2,
             "topic": "A Day in the Life", "objective": "Đọc hiểu về hoạt động cuối tuần.",
             "vocabulary_focus": ["weekend", "visit", "watch", "relax"],
             "grammar_focus": "Simple Present Tense"},
            {"order": 5, "code": "A1-U02-L05", "title": "Unit 2 Review", "skill": "grammar", "difficulty": 3,
             "topic": "Daily Life", "objective": "Ôn tập Unit 2.",
             "vocabulary_focus": [], "grammar_focus": None, "is_review": True},
        ],
    },
    {
        "code": "A1-U03", "order": 3, "title": "Food & Drink",
        "theme": "Food, Meals & Preferences", "icon": "🍎",
        "description": "Đồ ăn, thức uống, bữa ăn và sở thích.",
        "lessons": [
            {"order": 1, "code": "A1-U03-L01", "title": "Yummy Food", "skill": "vocabulary", "difficulty": 2,
             "topic": "Food & Cooking", "objective": "Gọi tên các món ăn quen thuộc.",
             "vocabulary_focus": ["rice", "bread", "milk", "apple", "chicken"],
             "grammar_focus": "Countable / uncountable nouns"},
            {"order": 2, "code": "A1-U03-L02", "title": "I like / I don't like", "skill": "grammar", "difficulty": 2,
             "topic": "Simple Present Tense", "objective": "Diễn đạt sở thích ăn uống.",
             "vocabulary_focus": ["like", "love", "hate", "favourite"],
             "grammar_focus": "Present Simple: like + noun"},
            {"order": 3, "code": "A1-U03-L03", "title": "At the restaurant", "skill": "listening", "difficulty": 3,
             "topic": "Ordering Food in a Restaurant", "objective": "Nghe hiểu hội thoại gọi món.",
             "vocabulary_focus": ["order", "menu", "waiter", "bill"],
             "grammar_focus": "Would like / Can I have"},
            {"order": 4, "code": "A1-U03-L04", "title": "My favourite meal", "skill": "reading", "difficulty": 3,
             "topic": "Food & Cooking", "objective": "Đọc hiểu đoạn văn về bữa ăn.",
             "vocabulary_focus": ["delicious", "dinner", "cook", "healthy"],
             "grammar_focus": "Simple Present Tense"},
            {"order": 5, "code": "A1-U03-L05", "title": "Unit 3 Assessment", "skill": "vocabulary", "difficulty": 3,
             "topic": "Food & Drink", "objective": "Đánh giá năng lực Unit 1-3.",
             "vocabulary_focus": [], "grammar_focus": None, "is_review": True, "is_assessment": True},
        ],
    },
    {
        "code": "A1-U04", "order": 4, "title": "Hobbies & Free Time",
        "theme": "Activities & Interests", "icon": "⚽",
        "description": "Sở thích, hoạt động giải trí và thể thao.",
        "lessons": [
            {"order": 1, "code": "A1-U04-L01", "title": "What do you like doing?", "skill": "vocabulary", "difficulty": 2,
             "topic": "Sports & Hobbies", "objective": "Nói về sở thích cá nhân.",
             "vocabulary_focus": ["swim", "read", "dance", "sing", "draw"],
             "grammar_focus": "Verb + -ing (like swimming)"},
            {"order": 2, "code": "A1-U04-L02", "title": "Can you play?", "skill": "grammar", "difficulty": 3,
             "topic": "Modal Verbs (can, must, should)", "objective": "Diễn đạt khả năng với 'can'.",
             "vocabulary_focus": ["play", "football", "piano", "guitar"],
             "grammar_focus": "Modal verb 'can' for ability"},
            {"order": 3, "code": "A1-U04-L03", "title": "Talk about your hobby", "skill": "speaking", "difficulty": 3,
             "topic": "Sports & Hobbies", "objective": "Luyện nói về sở thích (roleplay).",
             "vocabulary_focus": ["hobby", "free time", "fun", "together"],
             "grammar_focus": "Present Simple questions"},
            {"order": 4, "code": "A1-U04-L04", "title": "Write about your weekend", "skill": "writing", "difficulty": 3,
             "topic": "My favourite hobby", "objective": "Viết đoạn văn ngắn về sở thích.",
             "vocabulary_focus": ["because", "enjoy", "usually", "often"],
             "grammar_focus": "Linking word 'because'"},
            {"order": 5, "code": "A1-U04-L05", "title": "Unit 4 Review", "skill": "grammar", "difficulty": 3,
             "topic": "Hobbies & Free Time", "objective": "Ôn tập Unit 4.",
             "vocabulary_focus": [], "grammar_focus": None, "is_review": True},
        ],
    },
    {
        "code": "A1-U05", "order": 5, "title": "My Home & Places",
        "theme": "Home, Rooms & Directions", "icon": "🏠",
        "description": "Nhà cửa, các phòng và chỉ đường.",
        "lessons": [
            {"order": 1, "code": "A1-U05-L01", "title": "Rooms in my house", "skill": "vocabulary", "difficulty": 2,
             "topic": "My ideal home", "objective": "Gọi tên các phòng trong nhà.",
             "vocabulary_focus": ["bedroom", "kitchen", "bathroom", "living room"],
             "grammar_focus": "There is / There are"},
            {"order": 2, "code": "A1-U05-L02", "title": "Where is it?", "skill": "grammar", "difficulty": 3,
             "topic": "Prepositions of Place", "objective": "Mô tả vị trí đồ vật.",
             "vocabulary_focus": ["in", "on", "under", "next to", "behind"],
             "grammar_focus": "Prepositions of place"},
            {"order": 3, "code": "A1-U05-L03", "title": "Asking for directions", "skill": "listening", "difficulty": 3,
             "topic": "Asking for Directions", "objective": "Nghe hiểu chỉ đường cơ bản.",
             "vocabulary_focus": ["left", "right", "straight", "turn", "corner"],
             "grammar_focus": "Imperatives (turn, go)"},
            {"order": 4, "code": "A1-U05-L04", "title": "Describe your home", "skill": "writing", "difficulty": 3,
             "topic": "My ideal home", "objective": "Viết mô tả ngôi nhà.",
             "vocabulary_focus": ["big", "small", "comfortable", "beautiful"],
             "grammar_focus": "There is / There are + adjectives"},
            {"order": 5, "code": "A1-U05-L05", "title": "Unit 5 Review", "skill": "reading", "difficulty": 3,
             "topic": "My Home & Places", "objective": "Ôn tập Unit 5.",
             "vocabulary_focus": [], "grammar_focus": None, "is_review": True},
        ],
    },
    {
        "code": "A1-U06", "order": 6, "title": "Nature & Weather",
        "theme": "Weather, Animals & Seasons", "icon": "🌤️",
        "description": "Thời tiết, động vật và các mùa trong năm.",
        "lessons": [
            {"order": 1, "code": "A1-U06-L01", "title": "How's the weather?", "skill": "vocabulary", "difficulty": 2,
             "topic": "Nature & Environment", "objective": "Mô tả thời tiết.",
             "vocabulary_focus": ["sunny", "rainy", "cloudy", "windy", "hot", "cold"],
             "grammar_focus": "It is + weather adjective"},
            {"order": 2, "code": "A1-U06-L02", "title": "Animals around us", "skill": "vocabulary", "difficulty": 2,
             "topic": "Nature & Environment", "objective": "Gọi tên động vật.",
             "vocabulary_focus": ["dog", "cat", "bird", "fish", "elephant"],
             "grammar_focus": "Plural nouns (-s)"},
            {"order": 3, "code": "A1-U06-L03", "title": "The weather forecast", "skill": "listening", "difficulty": 3,
             "topic": "Weather Forecast", "objective": "Nghe hiểu dự báo thời tiết.",
             "vocabulary_focus": ["forecast", "temperature", "tomorrow", "degree"],
             "grammar_focus": "Future with 'will'"},
            {"order": 4, "code": "A1-U06-L04", "title": "My favourite season", "skill": "writing", "difficulty": 3,
             "topic": "Describe a memorable day", "objective": "Viết về mùa yêu thích.",
             "vocabulary_focus": ["spring", "summer", "autumn", "winter", "season"],
             "grammar_focus": "Because + reason"},
            {"order": 5, "code": "A1-U06-L05", "title": "A1 Final Assessment", "skill": "reading", "difficulty": 4,
             "topic": "Nature & Weather", "objective": "Đánh giá tổng kết cấp độ A1.",
             "vocabulary_focus": [], "grammar_focus": None, "is_review": True, "is_assessment": True},
        ],
    },
]

# Levels are seeded in this order; the prerequisite chain flows continuously
# through the whole sequence (last A1 lesson → first A2 lesson).
_LEVELS: list[tuple[str, list[dict]]] = [
    ("A1", A1_CURRICULUM),
    ("A2", A2_CURRICULUM),
    ("B1", B1_CURRICULUM),
]


def _prerequisite_of(units: list[dict], prev_code: str | None) -> list[tuple[dict, str | None]]:
    """Return (lesson, prerequisite_code) pairs without mutating the source dicts.

    `prev_code` seeds the chain (e.g. the last lesson code of the previous level).
    """
    pairs: list[tuple[dict, str | None]] = []
    for unit in units:
        for lesson in unit.get("lessons", []):
            pairs.append((lesson, prev_code))
            prev_code = lesson["code"]
    return pairs


def _seed_level(db: Session, level: str, units: list[dict], prev_code: str | None,
                existing_unit_codes: set[str], existing_lesson_codes: set[str]) -> tuple[int, str | None]:
    """Seed one level. Returns (new_lesson_count, last_lesson_code)."""
    prereq_pairs = dict(
        (lesson["code"], prereq) for lesson, prereq in _prerequisite_of(units, prev_code)
    )
    new_lessons = 0
    last_code = prev_code

    for unit_data in units:
        if unit_data["code"] not in existing_unit_codes:
            unit = CurriculumUnit(
                level=level,
                order=unit_data["order"],
                code=unit_data["code"],
                title=unit_data["title"],
                description=unit_data.get("description"),
                theme=unit_data.get("theme"),
                icon=unit_data.get("icon"),
            )
            db.add(unit)
            db.flush()
            existing_unit_codes.add(unit_data["code"])
        else:
            unit = db.query(CurriculumUnit).filter(CurriculumUnit.code == unit_data["code"]).first()

        for ld in unit_data.get("lessons", []):
            last_code = ld["code"]
            if ld["code"] in existing_lesson_codes:
                continue
            db.add(CurriculumLesson(
                unit_id=unit.id,
                order=ld["order"],
                code=ld["code"],
                title=ld["title"],
                skill=ld["skill"],
                difficulty=ld.get("difficulty", 1),
                topic=ld["topic"],
                objective=ld.get("objective"),
                vocabulary_focus=ld.get("vocabulary_focus", []),
                grammar_focus=ld.get("grammar_focus"),
                cefr_reference=level,
                prerequisite_code=prereq_pairs.get(ld["code"]),
                is_review=ld.get("is_review", False),
                is_assessment=ld.get("is_assessment", False),
            ))
            existing_lesson_codes.add(ld["code"])
            new_lessons += 1

    return new_lessons, last_code


def seed_curriculum(db: Session) -> int:
    """
    Seed all curriculum levels (A1, A2, ...) into the DB (idempotent).
    Returns the number of newly created lessons.
    """
    existing_unit_codes = {u.code for u in db.query(CurriculumUnit.code).all()}
    existing_lesson_codes = {l.code for l in db.query(CurriculumLesson.code).all()}

    new_lessons = 0
    prev_code: str | None = None
    for level, units in _LEVELS:
        added, prev_code = _seed_level(
            db, level, units, prev_code, existing_unit_codes, existing_lesson_codes
        )
        new_lessons += added

    db.commit()
    return new_lessons
