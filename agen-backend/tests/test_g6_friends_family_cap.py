"""G6 · Thử thách bạn bè, giới hạn 4 con cho gói gia đình, giọng Bo tiếng Việt."""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.core.timeutil import LEARNER_TZ, local_today
from app.models.learner_profile import LearnerProfile
from app.models.learning_event import LearningEvent
from app.models.user import User
from app.services import friends, tts_service

API = "/api/v1"


def _auth(client, email, role="learner", age=12):
    body = {"email": email, "password": "Strong123", "full_name": "U", "display_name": email.split("@")[0], "role": role}
    if role == "learner":
        body["age"] = age
    client.post(f"{API}/auth/register", json=body)
    token = client.post(f"{API}/auth/login", data={"username": email, "password": "Strong123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _learner(db, email):
    return db.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id).filter(User.email == email).one()


def _xp(db, learner_id, xp):
    when = datetime.combine(local_today(), datetime.min.time().replace(hour=12), tzinfo=LEARNER_TZ).astimezone(timezone.utc).replace(tzinfo=None)
    db.add(LearningEvent(learner_id=learner_id, event_type="lesson_completed", skill="vocabulary", xp_earned=xp, recorded_at=when))
    db.commit()


# ── Bạn học ──────────────────────────────────────────────────────────────────
def test_add_friend_by_code_and_duo_quest_claim(client, db_session):
    an = _auth(client, "an@example.com")
    binh = _auth(client, "binh@example.com")
    me = client.get(f"{API}/learner/me", headers=an).json()
    assert client.post(f"{API}/friends", json={"code": me["invite_code"]}, headers=an).status_code == 400     # own code
    assert client.post(f"{API}/friends", json={"code": "AGEN-NOPE"}, headers=binh).status_code == 400
    res = client.post(f"{API}/friends", json={"code": me["invite_code"]}, headers=binh)
    assert res.status_code == 200, res.text
    assert res.json()["friends"][0]["display_name"] == "an" and res.json()["goal"] == 200
    assert client.post(f"{API}/friends", json={"code": me["invite_code"]}, headers=binh).status_code == 400     # twice

    # Both sides see each other; the quest is open.
    mine = client.get(f"{API}/friends", headers=an).json()
    assert mine["my_code"] == me["invite_code"] and mine["friends"][0]["display_name"] == "binh"
    q = mine["friends"][0]["quest"]
    assert q["done"] is False and q["claimable"] is False and q["my_xp"] == 0

    # 160 + 40: total reached but Binh is under the per-person minimum.
    a, b = _learner(db_session, "an@example.com"), _learner(db_session, "binh@example.com")
    _xp(db_session, a.id, 160)
    _xp(db_session, b.id, 40)
    q = client.get(f"{API}/friends", headers=an).json()["friends"][0]["quest"]
    assert q["my_xp"] == 160 and q["friend_xp"] == 40 and q["done"] is False
    assert client.post(f"{API}/friends/{b.id}/claim", headers=an).status_code == 400

    _xp(db_session, b.id, 20)
    q = client.get(f"{API}/friends", headers=an).json()["friends"][0]["quest"]
    assert q["done"] is True and q["claimable"] is True
    claimed = client.post(f"{API}/friends/{b.id}/claim", headers=an)
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["xp"] == 30 and claimed.json()["gems"] == 10
    assert client.post(f"{API}/friends/{b.id}/claim", headers=an).status_code == 400          # once per week
    # Binh claims independently.
    assert client.post(f"{API}/friends/{a.id}/claim", headers=binh).status_code == 200
    profile = client.get(f"{API}/learner/me", headers=binh).json()
    assert profile["gems"] == 10 and profile["total_xp"] == 30      # events were seeded directly; only the reward touched total_xp

    # Removing the friend hides the quest.
    assert client.delete(f"{API}/friends/{b.id}", headers=an).json()["friends"] == []
    assert client.delete(f"{API}/friends/{b.id}", headers=an).status_code == 404


def test_friend_limit(db_session):
    from app.models.learner_profile import LearnerProfile as LP
    from app.models.user import User as U
    def mk(i):
        u = U(email=f"f{i}@example.com", hashed_password="x", full_name="F")
        db_session.add(u); db_session.flush()
        lp = LP(user_id=u.id, display_name=f"F{i}", invite_code=f"AGEN-F{i:03d}")
        db_session.add(lp); db_session.flush()
        return lp
    me = mk(0)
    for i in range(1, friends.MAX_FRIENDS + 1):
        friends.add_friend(db_session, me, mk(i).invite_code)
    with pytest.raises(friends.FriendError):
        friends.add_friend(db_session, me, mk(99).invite_code)


# ── Gói gia đình: tối đa 4 con ───────────────────────────────────────────────
def test_family_plan_caps_links_at_four(client, monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_UPGRADE", True)
    mom = _auth(client, "mom6@example.com", role="parent")
    kids = [_auth(client, f"c{i}@example.com") for i in range(5)]
    codes = [client.get(f"{API}/learner/me", headers=k).json()["invite_code"] for k in kids]
    # Without a family plan a parent may link any number of children.
    for code in codes[:5]:
        assert client.post(f"{API}/parent/link-child", json={"invite_code": code}, headers=mom).status_code == 200
    assert client.post(f"{API}/billing/upgrade", json={"months": 1, "plan": "family"}, headers=mom).status_code == 200
    children = client.get(f"{API}/parent/children", headers=mom).json()
    # Only the first four links are covered.
    covered = [c["display_name"] for c in children if c["premium_source"] == "family"]
    assert covered == ["c0", "c1", "c2", "c3"]
    assert client.get(f"{API}/billing/subscription", headers=kids[4]).json()["is_premium"] is False
    # With the plan active a 6th link is refused; unlinking one child makes room again.
    sixth = _auth(client, "c5@example.com")
    code6 = client.get(f"{API}/learner/me", headers=sixth).json()["invite_code"]
    res = client.post(f"{API}/parent/link-child", json={"invite_code": code6}, headers=mom)
    assert res.status_code == 400 and "tối đa 4" in res.json()["detail"]
    fifth_id = next(c["learner_id"] for c in children if c["display_name"] == "c4")
    client.delete(f"{API}/parent/children/{fifth_id}", headers=mom)
    client.delete(f"{API}/parent/children/{next(c['learner_id'] for c in children if c['display_name'] == 'c0')}", headers=mom)
    assert client.post(f"{API}/parent/link-child", json={"invite_code": code6}, headers=mom).status_code == 200
    assert client.get(f"{API}/billing/subscription", headers=sixth).json()["premium_source"] == "family"


# ── Bo nói tiếng Việt ────────────────────────────────────────────────────────
def test_tts_lang_is_part_of_cache_key_and_provider_call(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "TTS_CACHE_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(tts_service, "providers", lambda: ["openai"])
    monkeypatch.setattr(tts_service, "_cache_dir", lambda: tmp_path)
    calls = []
    monkeypatch.setitem(tts_service._CALLERS, "openai", lambda text, voice, lang="en": (calls.append(lang) or (b"RIFF0000WAVE", "audio/wav")))
    assert tts_service._cache_key("openai", "m", "female", "Chào bạn", "vi") != tts_service._cache_key("openai", "m", "female", "Chào bạn", "en")
    en = tts_service.synthesize("Hello", "female", "en")
    vi = tts_service.synthesize("Hello", "female", "vi")
    assert en and vi and calls == ["en", "vi"]
    assert tts_service.synthesize("Hello", "female", "vi").cached is True


def test_tts_endpoint_validates_lang(client, monkeypatch):
    monkeypatch.setattr(tts_service, "is_enabled", lambda: True)
    monkeypatch.setattr(tts_service, "synthesize", lambda text, voice, lang="en": tts_service.TTSResult(b"x", "audio/wav", "openai", False) if lang == "vi" else None)
    headers = _auth(client, "tts@example.com")
    assert client.get(f"{API}/audio/tts", params={"text": "Chào", "lang": "vi"}, headers=headers).status_code == 200
    assert client.get(f"{API}/audio/tts", params={"text": "Chào", "lang": "fr"}, headers=headers).status_code == 422
