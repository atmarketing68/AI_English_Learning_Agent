"""The six interactive exercise types: building them from lesson content and grading."""
import json

from app.api.lessons import GenerateLessonRequest, _persist_generated_lesson
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services.exercise_builder import SKIP_ANSWER, check_answer, extra_exercises

API = "/api/v1"

VOCAB = [
    {"word": w, "translation": t, "example": e}
    for w, t, e in [
        ("breakfast", "bữa sáng", "I eat breakfast at seven."),
        ("kitchen", "nhà bếp", "Mum is cooking in the kitchen."),
        ("spicy", "cay", "Thai food is very spicy."),
        ("bake", "nướng", "We bake bread on Sundays."),
        ("hungry", "đói", "I am hungry now."),
        ("recipe", "công thức", "Follow the recipe carefully."),
    ]
]


def _by_type(items):
    return {e["type"]: e["content"] for e in items}


def test_vocabulary_lesson_gets_four_new_types():
    built = _by_type(extra_exercises("vocabulary", {"vocabulary": VOCAB}))
    assert set(built) == {"match_pairs", "listen_choose", "speak_repeat", "dictation"}
    assert len(built["match_pairs"]["pairs"]) == 5
    lc = built["listen_choose"]
    assert lc["audio_text"] == "recipe"
    assert lc["options"][lc["correct_answer"]] == "công thức" and len(lc["options"]) == 4
    assert built["speak_repeat"] == {"text": "I eat breakfast at seven.", "hint": "breakfast = bữa sáng"}
    assert built["dictation"]["text"] == "Mum is cooking in the kitchen."
    # Deterministic: the same lesson always builds the same exercises.
    assert extra_exercises("vocabulary", {"vocabulary": VOCAB}) == extra_exercises("vocabulary", {"vocabulary": VOCAB})


def test_grammar_and_listening_builders():
    grammar = extra_exercises("grammar", {"explanation": {"examples": [
        {"en": "She walked to school.", "vi": "Cô ấy đã đi bộ đến trường."},
        {"en": "They played football.", "vi": "Họ đã chơi bóng đá."},
    ]}})
    assert [e["type"] for e in grammar] == ["word_bank", "word_bank"]
    bank = grammar[0]["content"]
    assert bank["tokens"][:4] == ["She", "walked", "to", "school."] and len(bank["tokens"]) == 6

    listening = _by_type(extra_exercises("listening", {"passage": {"script_lines": [
        {"speaker": "A", "text": "Hello, can I help you?"},
        {"speaker": "B", "text": "Yes, I would like a coffee please."},
        {"speaker": "A", "text": "Sure, that is two dollars."},
    ]}}))
    assert len(listening["dialogue_order"]["lines"]) == 3
    assert listening["dictation"]["text"] == "Hello, can I help you?"

    assert extra_exercises("reading", {"text": "x"}) == []
    assert extra_exercises("vocabulary", {"vocabulary": "garbage"}) == []


def test_grading_rules():
    assert check_answer("word_bank", {"answer": "She walked to school.", "prompt_vi": "x"}, "she walked to school")[0]
    assert not check_answer("word_bank", {"answer": "She walked to school."}, "she school to walked")[0]

    pairs = {"pairs": [{"left": "a", "right": "1"}, {"left": "b", "right": "2"}]}
    assert check_answer("match_pairs", pairs, json.dumps([["a", "1"], ["b", "2"]]))[0]
    ok, _, note = check_answer("match_pairs", pairs, json.dumps([["a", "2"], ["a", "1"], ["b", "2"]]))
    assert not ok and "1 lần" in note
    assert not check_answer("match_pairs", pairs, "not json")[0]

    text = {"text": "Mum is cooking in the kitchen."}
    assert check_answer("dictation", text, "mum is cooking in the kitchen")[0]
    assert check_answer("dictation", text, "mum is cooking in the kichen")[0]          # small typo
    assert not check_answer("dictation", text, "mum cooks")[0]

    speak = {"text": "I eat breakfast at seven."}
    assert check_answer("speak_repeat", speak, "I eat breakfast at seven")[0]
    assert not check_answer("speak_repeat", speak, "I eat")[0]
    assert check_answer("speak_repeat", speak, SKIP_ANSWER) == (True, "", "Đã bỏ qua phần nói.")

    lines = {"lines": [{"text": "a"}, {"text": "b"}, {"text": "c"}]}
    assert check_answer("dialogue_order", lines, "[0, 1, 2]")[0]
    assert not check_answer("dialogue_order", lines, "[1, 0, 2]")[0]

    lc = {"audio_text": "cat", "options": {"A": "chó", "B": "mèo"}, "correct_answer": "B"}
    assert check_answer("listen_choose", lc, "b")[0] and not check_answer("listen_choose", lc, "A")[0]


def test_lesson_flow_with_new_types(client, db_session):
    email = "types@example.com"
    client.post(f"{API}/auth/register", json={"email": email, "password": "Strong123", "full_name": "T",
                                             "display_name": "T", "role": "learner"})
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    learner = db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id).filter(User.email == email).one()

    lesson = _persist_generated_lesson(
        db_session, learner, GenerateLessonRequest(skill="vocabulary"),
        {"title": "Food", "summary": "s", "vocabulary": VOCAB, "exercises": [
            {"type": "flashcard", "order": 0, "content": {"word": "breakfast"}},
        ]},
    )
    db_session.commit()
    assert lesson.total_exercises == 5
    detail = client.get(f"{API}/lessons/{lesson.id}", headers=headers).json()
    types = [e["type"] for e in detail["exercises"]]
    assert types == ["flashcard", "match_pairs", "listen_choose", "speak_repeat", "dictation"]
    ex = {e["type"]: e for e in detail["exercises"]}

    def submit(kind, answer):
        return client.post(f"{API}/lessons/{lesson.id}/submit-exercise", headers=headers,
                           json={"exercise_id": ex[kind]["id"], "answer": answer}).json()

    submit("flashcard", "viewed")
    pairs = [[p["left"], p["right"]] for p in ex["match_pairs"]["content"]["pairs"]]
    assert submit("match_pairs", json.dumps(pairs))["is_correct"] is True
    wrong = submit("listen_choose", "Z")
    assert wrong["is_correct"] is False and wrong["correct_answer"] == ex["listen_choose"]["content"]["correct_answer"]
    assert submit("speak_repeat", SKIP_ANSWER)["is_correct"] is True
    assert submit("dictation", "Mum is cooking in the kitchen")["is_correct"] is True

    finish = client.post(f"{API}/lessons/{lesson.id}/finish", headers=headers).json()
    # Flashcards and the skipped speaking task are not graded: 2 of 3 graded answers correct.
    assert (finish["correct"], finish["total"]) == (2, 3)
