"""Spaced repetition: FSRS scheduling + the review API end to end."""
from datetime import datetime, timedelta

from app.models.learner_profile import LearnerProfile
from app.models.lesson import Exercise, Lesson
from app.models.review_item import ReviewItem
from app.models.user import User
from app.services.srs import AGAIN, EASY, GOOD, HARD, retrievability, schedule

API = "/api/v1"
NOW = datetime(2026, 10, 26, 8, 0)


# ── FSRS scheduler ───────────────────────────────────────────────────────────
def test_retrievability_is_90_percent_after_stability_days():
    assert abs(retrievability(10, 10) - 0.9) < 1e-9
    assert retrievability(0, 5) == 1.0


def test_first_review_uses_initial_stability_per_grade():
    good = schedule(None, None, None, GOOD, NOW)
    assert round(good.stability, 4) == 3.7145
    assert good.due_at == NOW + timedelta(days=4)
    again = schedule(None, None, None, AGAIN, NOW)
    assert again.state == "relearning"
    assert again.due_at == NOW + timedelta(minutes=10)
    assert schedule(None, None, None, EASY, NOW).due_at > good.due_at


def test_intervals_grow_on_success_and_shrink_on_lapse():
    first = schedule(None, None, None, GOOD, NOW)
    t2 = first.due_at
    second = schedule(first.stability, first.difficulty, NOW, GOOD, t2)
    assert second.stability > first.stability
    assert second.interval_days > first.interval_days

    lapse = schedule(second.stability, second.difficulty, t2, AGAIN, second.due_at)
    assert lapse.stability < second.stability
    assert lapse.difficulty > second.difficulty


def test_hard_grows_less_than_good():
    first = schedule(None, None, None, GOOD, NOW)
    later = first.due_at
    hard = schedule(first.stability, first.difficulty, NOW, HARD, later)
    good = schedule(first.stability, first.difficulty, NOW, GOOD, later)
    assert hard.stability < good.stability


# ── API ──────────────────────────────────────────────────────────────────────
def _auth(client, email):
    client.post(f"{API}/auth/register", json={
        "email": email, "password": "Strong123", "full_name": "Rev",
        "display_name": "Rev", "role": "learner",
    })
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Strong123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _vocab_lesson(db_session, email):
    learner = (
        db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id)
        .filter(User.email == email).one()
    )
    lesson = Lesson(
        learner_id=learner.id, skill="vocabulary", topic="Food", level="A1", title="Food",
        content={"vocabulary": [
            {"word": "bread", "phonetic": "/bred/", "definition": "baked food", "translation": "bánh mì",
             "example": "I eat bread."},
            {"word": "rice", "definition": "a grain", "translation": "cơm"},
        ]},
        total_exercises=2,
    )
    db_session.add(lesson)
    db_session.flush()
    db_session.add_all([
        Exercise(lesson_id=lesson.id, order=0, type="flashcard",
                 content={"word": "Bread", "definition": "baked food", "translation": "bánh mì"}),
        Exercise(lesson_id=lesson.id, order=1, type="multiple_choice", content={
            "question": "Which word means 'cơm'?",
            "options": {"A": "bread", "B": "rice", "C": "milk", "D": "egg"},
            "correct_answer": "B", "explanation": "Rice = cơm.",
        }),
    ])
    db_session.commit()
    return lesson


def test_lesson_feeds_notebook_and_review_session(client, db_session):
    email = "review1@example.com"
    headers = _auth(client, email)
    lesson = _vocab_lesson(db_session, email)
    mc = next(e for e in lesson.exercises if e.type == "multiple_choice")

    r = client.post(f"{API}/lessons/{lesson.id}/submit-exercise", headers=headers,
                    json={"exercise_id": mc.id, "answer": "A"})
    assert r.status_code == 200 and r.json()["is_correct"] is False
    finish = client.post(f"{API}/lessons/{lesson.id}/finish", headers=headers)
    assert finish.status_code == 200 and finish.json()["words_saved"] == 2

    summary = client.get(f"{API}/review/summary", headers=headers).json()
    # Words are deduplicated ("Bread" flashcard == "bread"); only the mistake is due today.
    assert summary["vocab_total"] == 2
    assert summary["mistake_total"] == 1
    assert summary["due_count"] == 1

    mistakes = client.get(f"{API}/review/items?kind=mistake", headers=headers).json()["items"]
    assert mistakes[0]["back"] == "rice"
    assert mistakes[0]["last_wrong_answer"] == "bread"

    session = client.get(f"{API}/review/session", headers=headers).json()
    assert [q["prompt_type"] for q in session["questions"]] == ["mistake"]
    q = session["questions"][0]
    assert sorted(q["options"]) == ["bread", "egg", "milk", "rice"]

    ans = client.post(f"{API}/review/items/{q['item_id']}/answer", headers=headers,
                      json={"prompt_type": "mistake", "answer": "Rice"}).json()
    assert ans["correct"] is True
    assert ans["interval_days"] >= 1
    assert ans["xp_earned"] == 2
    assert client.get(f"{API}/review/summary", headers=headers).json()["due_count"] == 0

    # Practising ahead reaches the not-yet-due words but earns no XP.
    ahead = client.get(f"{API}/review/session?ahead=true", headers=headers).json()["questions"]
    vocab_q = next(x for x in ahead if x["prompt_type"] == "meaning")
    assert len(vocab_q["options"]) == 4
    expected = "bánh mì" if vocab_q["prompt"] == "bread" else "cơm"
    assert expected in vocab_q["options"]
    ans = client.post(f"{API}/review/items/{vocab_q['item_id']}/answer", headers=headers,
                      json={"prompt_type": "meaning", "answer": expected}).json()
    assert ans["correct"] is True and ans["xp_earned"] == 0


def test_wrong_review_comes_back_soon(client, db_session):
    email = "review2@example.com"
    headers = _auth(client, email)
    lesson = _vocab_lesson(db_session, email)
    mc = next(e for e in lesson.exercises if e.type == "multiple_choice")
    client.post(f"{API}/lessons/{lesson.id}/submit-exercise", headers=headers,
                json={"exercise_id": mc.id, "answer": "C"})
    item = db_session.query(ReviewItem).filter(ReviewItem.kind == "mistake").one()

    ans = client.post(f"{API}/review/items/{item.id}/answer", headers=headers,
                      json={"prompt_type": "mistake", "answer": "milk"}).json()
    assert ans["correct"] is False
    assert ans["correct_answer"] == "rice"
    assert ans["interval_days"] < 1
    assert ans["xp_earned"] == 0


def test_review_items_are_private(client, db_session):
    owner = "review3@example.com"
    headers = _auth(client, owner)
    _vocab_lesson(db_session, owner)
    other = _auth(client, "review4@example.com")
    lesson = db_session.query(Lesson).one()
    client.post(f"{API}/lessons/{lesson.id}/finish", headers=headers)
    item = db_session.query(ReviewItem).first()

    assert client.post(f"{API}/review/items/{item.id}/answer", headers=other,
                       json={"prompt_type": "meaning", "answer": "x"}).status_code == 404
    assert client.delete(f"{API}/review/items/{item.id}", headers=other).status_code == 404
    assert client.delete(f"{API}/review/items/{item.id}", headers=headers).status_code == 204
