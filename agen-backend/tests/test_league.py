"""G3 · Giải đấu tuần: ranking from weekly XP, my standing, last week's reward."""
from datetime import date, datetime, time, timedelta, timezone

from app.core.timeutil import LEARNER_TZ, local_today
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.user import User
from app.services import league

API = "/api/v1"


def _at(d: date, hour: int = 12) -> datetime:
    return datetime.combine(d, time(hour), tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)


def _learner(db, email, name):
    user = User(email=email, hashed_password="x", full_name=name)
    db.add(user)
    db.flush()
    lp = LearnerProfile(user_id=user.id, display_name=name, overall_level="A2")
    db.add(lp)
    db.flush()
    return lp


def _xp(db, learner_id, xp, when):
    db.add(LearningEvent(learner_id=learner_id, event_type="lesson_completed", skill="vocabulary", xp_earned=xp, recorded_at=when))


def test_board_ranks_this_week_only(db_session):
    today = local_today()
    monday, _ = league.week_bounds(today)
    a, b, c = (_learner(db_session, f"{n}@example.com", n) for n in ("An", "Binh", "Chi"))
    _xp(db_session, a.id, 50, _at(monday))
    _xp(db_session, b.id, 120, _at(today))
    _xp(db_session, b.id, 30, _at(monday - timedelta(days=1)))      # last week: ignored
    _xp(db_session, c.id, 80, _at(today))
    db_session.flush()

    board = league.board(db_session, a, today)
    assert [e["display_name"] for e in board.entries] == ["Binh", "Chi", "An"]
    assert board.entries[0]["xp"] == 120 and board.entries[0]["tier"] == "Vàng"
    assert board.me.rank == 3 and board.me.xp == 50 and board.me.participants == 3
    assert board.entries[2]["is_me"] is True


def test_last_week_reward_and_claim_once(db_session):
    today = local_today()
    last_monday, _ = league.week_bounds(today - timedelta(days=7))
    winner = _learner(db_session, "w@example.com", "Win")
    other = _learner(db_session, "o@example.com", "Oth")
    _xp(db_session, winner.id, 200, _at(last_monday + timedelta(days=2)))
    _xp(db_session, other.id, 90, _at(last_monday + timedelta(days=3)))
    db_session.flush()

    lw = league.last_week(db_session, winner, today)
    assert lw.rank == 1 and lw.reward_xp == 100 and lw.claimable is True and lw.tier == "Vàng"
    assert league.last_week(db_session, other, today).reward_xp == 70

    before = winner.total_xp or 0
    assert league.claim_last_week(db_session, winner, today) == 100
    assert winner.total_xp == before + 100
    assert league.last_week(db_session, winner, today).claimed is True
    try:
        league.claim_last_week(db_session, winner, today)
        assert False, "second claim must fail"
    except league.LeagueClaimError:
        pass


def test_no_xp_means_no_rank_and_no_reward(db_session):
    lp = _learner(db_session, "zero@example.com", "Zero")
    assert league.board(db_session, lp).me.rank is None
    assert league.last_week(db_session, lp).claimable is False
    assert league.reward_for(11) == 0 and league.reward_for(10) == 40


def test_league_endpoints(client):
    client.post(f"{API}/auth/register", json={"email": "lg@example.com", "password": "Strong123", "full_name": "L", "display_name": "Lan", "role": "learner"})
    token = client.post(f"{API}/auth/login", data={"username": "lg@example.com", "password": "Strong123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Earn XP this week via pronunciation practice.
    client.post(f"{API}/speaking/pronunciation", json={"target_text": "hello world", "transcript": "hello world"}, headers=headers)
    resp = client.get(f"{API}/engagement/league", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["me"]["rank"] == 1 and body["me"]["xp"] > 0
    assert body["entries"][0]["display_name"] == "Lan" and body["entries"][0]["is_me"] is True
    assert body["board_size"] == 30 and body["rewards"][0] == {"up_to_rank": 1, "xp": 100}
    assert body["last_week"]["claimable"] is False
    assert client.post(f"{API}/engagement/league/claim", headers=headers).status_code == 400
