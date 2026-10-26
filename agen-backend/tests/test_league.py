"""G3/G4 · Giải đấu tuần: groups of 30 per tier, promotion/relegation, last week's reward."""
from datetime import date, datetime, time, timedelta, timezone

from app.core.timeutil import LEARNER_TZ, local_today
from app.models.league_membership import LeagueMembership
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.user import User
from app.services import league
from app.services.engagement import week_key

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


def test_board_groups_members_and_ranks_this_week_only(db_session):
    today = local_today()
    monday, _ = league.week_bounds(today)
    a, b, c = (_learner(db_session, f"{n}@example.com", n) for n in ("An", "Binh", "Chi"))
    for lp in (a, b, c):
        league.ensure_membership(db_session, lp, today)
    _xp(db_session, a.id, 50, _at(monday))
    _xp(db_session, b.id, 120, _at(today))
    _xp(db_session, b.id, 30, _at(monday - timedelta(days=1)))      # last week: ignored
    _xp(db_session, c.id, 80, _at(today))
    db_session.flush()

    board = league.board(db_session, a, today)
    assert board.tier == 0 and board.tier_name == "Đồng" and board.group_no == 1
    assert [e["display_name"] for e in board.entries] == ["Binh", "Chi", "An"]
    assert board.entries[0]["zone"] == "promote" and board.entries[0]["xp"] == 120
    assert board.me.rank == 3 and board.me.xp == 50 and board.me.participants == 3
    assert board.entries[2]["is_me"] is True and "emoji" in board.entries[2]["avatar"]


def test_groups_fill_to_thirty_then_open_a_new_one(db_session):
    today = local_today()
    learners = [_learner(db_session, f"g{i}@example.com", f"L{i}") for i in range(31)]
    memberships = [league.ensure_membership(db_session, lp, today) for lp in learners]
    assert {m.group_no for m in memberships[:30]} == {1}
    assert memberships[30].group_no == 2
    assert league.ensure_membership(db_session, learners[0], today).id == memberships[0].id    # idempotent


def test_promotion_relegation_and_inactivity_between_weeks(db_session):
    today = local_today()
    last_monday, _ = league.week_bounds(today - timedelta(days=7))
    last_week = week_key(last_monday)
    learners = [_learner(db_session, f"p{i}@example.com", f"P{i}") for i in range(12)]
    for lp in learners:
        db_session.add(LeagueMembership(learner_id=lp.id, week=last_week, tier=1, group_no=1))
    db_session.flush()
    # Ranks 1–7 promote, ranks 8–12 (bottom 5 of 12) relegate; P11 sat the week out.
    for i, lp in enumerate(learners[:11]):
        _xp(db_session, lp.id, 500 - i * 20, _at(last_monday + timedelta(days=1)))
    db_session.flush()

    assert league.ensure_membership(db_session, learners[0], today).tier == 2       # rank 1 → promoted
    assert league.ensure_membership(db_session, learners[6], today).tier == 2       # rank 7 → promoted
    assert league.ensure_membership(db_session, learners[7], today).tier == 0       # rank 8 → relegated
    assert league.ensure_membership(db_session, learners[10], today).tier == 0      # rank 11 → relegated
    assert league.ensure_membership(db_session, learners[11], today).tier == 0      # sat out → drops
    assert league.last_week(db_session, learners[7], today).movement == "relegated"
    lw = league.last_week(db_session, learners[0], today)
    assert lw.rank == 1 and lw.reward_xp == 100 and lw.reward_gems == 40 and lw.movement == "promoted" and lw.claimable
    assert league.last_week(db_session, learners[11], today).movement == "inactive"
    assert league.last_week(db_session, learners[11], today).rank is None

    before_xp, before_gems = learners[0].total_xp or 0, learners[0].gems or 0
    got = league.claim_last_week(db_session, learners[0], today)
    assert got == {"xp": 100, "gems": 40}
    assert learners[0].total_xp == before_xp + 100 and learners[0].gems == before_gems + 40
    try:
        league.claim_last_week(db_session, learners[0], today)
        assert False, "second claim must fail"
    except league.LeagueClaimError:
        pass


def test_new_learner_without_xp_has_no_reward(db_session):
    lp = _learner(db_session, "zero@example.com", "Zero")
    b = league.board(db_session, lp)
    assert b.me.rank == 1 and b.me.xp == 0 and b.tier == 0          # alone in a fresh group
    assert league.last_week(db_session, lp).claimable is False
    assert league.reward_for(11) == 0 and league.reward_for(10) == 40


def test_league_endpoints(client):
    client.post(f"{API}/auth/register", json={"email": "lg@example.com", "password": "Strong123", "full_name": "L", "display_name": "Lan", "role": "learner"})
    token = client.post(f"{API}/auth/login", data={"username": "lg@example.com", "password": "Strong123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post(f"{API}/speaking/pronunciation", json={"target_text": "hello world", "transcript": "hello world"}, headers=headers)
    resp = client.get(f"{API}/engagement/league", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tier_name"] == "Đồng" and body["tiers"][-1] == "Kim cương" and body["group_size"] == 30
    assert body["me"]["rank"] == 1 and body["me"]["xp"] > 0
    assert body["entries"][0]["display_name"] == "Lan" and body["entries"][0]["is_me"] is True
    assert body["last_week"]["claimable"] is False and body["last_week"]["movement"] == "new"
    assert client.post(f"{API}/engagement/league/claim", headers=headers).status_code == 400
