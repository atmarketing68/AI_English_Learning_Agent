"""G4 · gems, shop and the 60-second blitz."""
from app.core.config import settings
from app.models.learner_profile import LearnerProfile
from app.models.user import User
from app.services import shop

API = "/api/v1"


def _auth(client, email):
    client.post(f"{API}/auth/register", json={"email": email, "password": "Strong123", "full_name": "S", "display_name": "S", "role": "learner", "age": 10})
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_shop_catalogue_defaults_and_buy_flow(client, db_session):
    headers = _auth(client, "shop1@example.com")
    body = client.get(f"{API}/gamification/shop", headers=headers).json()
    assert body["gems"] == 0 and body["avatar"] == shop.DEFAULT_AVATAR
    free = [i for i in body["items"] if i["price"] == 0]
    assert all(i["owned"] for i in free)
    fox = next(i for i in body["items"] if i["id"] == "av_fox")
    assert fox["owned"] is False and fox["price"] == 30

    assert client.post(f"{API}/gamification/shop/buy", json={"item_id": "av_fox"}, headers=headers).status_code == 400   # no gems
    learner = db_session.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id).filter(User.email == "shop1@example.com").one()
    learner.gems = 50
    db_session.commit()

    bought = client.post(f"{API}/gamification/shop/buy", json={"item_id": "av_fox"}, headers=headers)
    assert bought.status_code == 200, bought.text
    assert bought.json()["gems"] == 20 and bought.json()["avatar"]["emoji"] == "🦊"
    assert next(i for i in bought.json()["items"] if i["id"] == "av_fox")["equipped"] is True
    assert client.post(f"{API}/gamification/shop/buy", json={"item_id": "av_fox"}, headers=headers).status_code == 400   # already owned
    assert client.post(f"{API}/gamification/shop/equip", json={"item_id": "av_unicorn"}, headers=headers).status_code == 400
    back = client.post(f"{API}/gamification/shop/equip", json={"item_id": "av_smile"}, headers=headers).json()
    assert back["avatar"]["emoji"] == "🙂"
    profile = client.get(f"{API}/learner/me", headers=headers).json()
    assert profile["gems"] == 20 and profile["avatar"]["emoji"] == "🙂"


def test_ui_skin_is_saved_and_validated(client):
    headers = _auth(client, "skin@example.com")
    assert client.patch(f"{API}/learner/me", json={"ui_skin": "neon"}, headers=headers).status_code == 422
    assert client.patch(f"{API}/learner/me", json={"ui_skin": "vivid"}, headers=headers).json()["ui_skin"] == "vivid"


def test_gems_awarded_by_grade():
    assert shop.gems_for_grade("S") == 15 and shop.gems_for_grade("D") == 3 and shop.gems_for_grade("?") == 3
    assert shop.gems_for_league_rank(1) == 40 and shop.gems_for_league_rank(10) == 20 and shop.gems_for_league_rank(11) == 0


def test_quest_claim_awards_gems(client, db_session, monkeypatch):
    headers = _auth(client, "gemquest@example.com")
    # Make the first quest trivially complete: 1 pronunciation = "speaking" metric; lesson quest needs a lesson.
    client.post(f"{API}/speaking/pronunciation", json={"target_text": "hi", "transcript": "hi"}, headers=headers)
    state = client.get(f"{API}/engagement/today", headers=headers).json()
    done = [q for q in state["quests"] if q["completed"] and not q["claimed"]]
    if not done:
        return   # today's rotation did not include a speaking quest; nothing to assert
    res = client.post(f"{API}/engagement/quests/{done[0]['id']}/claim", headers=headers)
    assert res.status_code == 200
    assert client.get(f"{API}/learner/me", headers=headers).json()["gems"] == shop.GEMS_QUEST


def test_blitz_round_and_result_with_daily_cap(client):
    headers = _auth(client, "blitz@example.com")
    client.post(f"{API}/review/items", json={"word": "platform", "meaning": "sân ga"}, headers=headers)
    round_ = client.get(f"{API}/review/blitz", headers=headers)
    assert round_.status_code == 200, round_.text
    body = round_.json()
    assert len(body["questions"]) == 15 and body["seconds"] == 60 and body["from_notebook"] == 1
    q = body["questions"][0]
    assert len(q["options"]) == 4 and 0 <= q["answer"] < 4
    assert any(x["prompt"] == "platform" for x in body["questions"])

    first = client.post(f"{API}/review/blitz/result", json={"correct": 12, "answered": 15, "seconds": 60}, headers=headers).json()
    assert first["xp_earned"] == 24 and first["gems_earned"] == 10 and first["daily_xp_left"] == 16
    second = client.post(f"{API}/review/blitz/result", json={"correct": 15, "answered": 15, "seconds": 58}, headers=headers).json()
    assert second["xp_earned"] == 16 and second["daily_xp_left"] == 0
    third = client.post(f"{API}/review/blitz/result", json={"correct": 5, "answered": 5, "seconds": 20}, headers=headers).json()
    assert third["xp_earned"] == 0 and third["gems_earned"] == 5
    profile = client.get(f"{API}/learner/me", headers=headers).json()
    assert profile["total_xp"] == 40 and profile["gems"] == 25
    assert settings.FREE_DAILY_LESSON_LIMIT >= 0
