"""AI "Vì sao sai?" explanations and grammar-rule persistence."""
import app.api.lessons as lessons_api
from app.api.lessons import GenerateLessonRequest, _persist_generated_lesson
from app.models.learner_profile import LearnerProfile
from app.models.lesson import Exercise, Lesson
from app.models.user import User
from app.services.llm_client import LLMError

API = "/api/v1"


def _auth(client, email):
    client.post(f"{API}/auth/register", json={
        "email": email, "password": "Strong123", "full_name": "Exp",
        "display_name": "Exp", "role": "learner",
    })
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Strong123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _learner(db_session, email):
    return (
        db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id)
        .filter(User.email == email).one()
    )


def _lesson(db_session, email):
    lesson = Lesson(learner_id=_learner(db_session, email).id, skill="grammar", topic="Past",
                    level="A2", title="Past simple", total_exercises=1)
    db_session.add(lesson)
    db_session.flush()
    ex = Exercise(lesson_id=lesson.id, order=0, type="multiple_choice", content={
        "question": "She ___ to school yesterday.",
        "options": {"A": "go", "B": "went", "C": "goes", "D": "going"},
        "correct_answer": "B", "explanation": "Yesterday → past simple.",
    })
    db_session.add(ex)
    db_session.commit()
    return lesson, ex


def test_explain_wrong_answer_calls_ai_once_and_caches(client, db_session, monkeypatch):
    email = "explain1@example.com"
    headers = _auth(client, email)
    lesson, ex = _lesson(db_session, email)
    prompts = []

    def fake_llm(prompt):
        prompts.append(prompt)
        return "**Sai rồi**: 'yesterday' báo hiệu quá khứ nên dùng 'went'."

    monkeypatch.setattr(lessons_api, "get_llm_response", fake_llm)
    client.post(f"{API}/lessons/{lesson.id}/submit-exercise", headers=headers,
                json={"exercise_id": ex.id, "answer": "A"})

    url = f"{API}/lessons/{lesson.id}/exercises/{ex.id}/explain"
    first = client.post(url, headers=headers).json()
    assert first["source"] == "ai"
    assert first["explanation"] == "Sai rồi: 'yesterday' báo hiệu quá khứ nên dùng 'went'."
    assert "Learner's answer: A. go" in prompts[0]
    assert "Correct answer: B. went" in prompts[0]

    second = client.post(url, headers=headers).json()
    assert second["source"] == "cached"
    assert len(prompts) == 1


def test_explain_requires_a_wrong_answer_by_the_owner(client, db_session, monkeypatch):
    email = "explain2@example.com"
    headers = _auth(client, email)
    lesson, ex = _lesson(db_session, email)
    monkeypatch.setattr(lessons_api, "get_llm_response", lambda prompt: "x")
    url = f"{API}/lessons/{lesson.id}/exercises/{ex.id}/explain"

    assert client.post(url, headers=headers).status_code == 400          # not answered yet
    client.post(f"{API}/lessons/{lesson.id}/submit-exercise", headers=headers,
                json={"exercise_id": ex.id, "answer": "B"})
    assert client.post(url, headers=headers).status_code == 400          # answered correctly

    other = _auth(client, "explain3@example.com")
    assert client.post(url, headers=other).status_code == 404


def test_explain_falls_back_to_static_explanation(client, db_session, monkeypatch):
    email = "explain4@example.com"
    headers = _auth(client, email)
    lesson, ex = _lesson(db_session, email)

    def broken(prompt):
        raise LLMError("busy", is_quota=True)

    monkeypatch.setattr(lessons_api, "get_llm_response", broken)
    client.post(f"{API}/lessons/{lesson.id}/submit-exercise", headers=headers,
                json={"exercise_id": ex.id, "answer": "C"})
    body = client.post(f"{API}/lessons/{lesson.id}/exercises/{ex.id}/explain", headers=headers).json()
    assert body == {"exercise_id": ex.id, "explanation": "Yesterday → past simple.", "source": "fallback"}


def test_grammar_lesson_keeps_its_rule_explanation(client, db_session):
    email = "explain5@example.com"
    _auth(client, email)
    learner = _learner(db_session, email)
    rule = {"rule": "Use past simple for finished actions.", "rule_vi": "Dùng quá khứ đơn...",
            "structure": "S + V-ed", "examples": [{"en": "I walked.", "vi": "Tôi đã đi bộ."}]}
    lesson = _persist_generated_lesson(
        db_session, learner, GenerateLessonRequest(skill="grammar", topic="Past"),
        {"title": "Past", "summary": "s", "explanation": rule,
         "exercises": [{"type": "fill_blank", "order": 0, "content": {"sentence": "I ___.", "blank_word": "walked"}}]},
    )
    assert lesson.content == {"explanation": rule}


def test_fill_blank_fallback_is_vietnamese(client, db_session, monkeypatch):
    email = "explain6@example.com"
    headers = _auth(client, email)
    lesson = Lesson(learner_id=_learner(db_session, email).id, skill="grammar", topic="Past",
                    level="A2", title="Past", total_exercises=1)
    db_session.add(lesson)
    db_session.flush()
    ex = Exercise(lesson_id=lesson.id, order=0, type="fill_blank", content={
        "sentence": "She ___ home.", "blank_word": "walked", "hint": "past of 'walk'",
        "options": ["walk", "walked"],
    })
    db_session.add(ex)
    db_session.commit()

    def broken(prompt):
        raise LLMError("busy")

    monkeypatch.setattr(lessons_api, "get_llm_response", broken)
    client.post(f"{API}/lessons/{lesson.id}/submit-exercise", headers=headers,
                json={"exercise_id": ex.id, "answer": "walk"})
    body = client.post(f"{API}/lessons/{lesson.id}/exercises/{ex.id}/explain", headers=headers).json()
    assert body["source"] == "fallback"
    assert body["explanation"] == "Đáp án đúng là “walked”. Gợi ý: past of 'walk'."
