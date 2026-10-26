"""G3 · Học thử không cần đăng ký: guest accounts and claiming them."""
API = "/api/v1"


def _guest(client):
    resp = client.post(f"{API}/auth/guest")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body


def test_guest_can_learn_without_signup(client):
    headers, body = _guest(client)
    assert body["refresh_token"]
    me = client.get(f"{API}/auth/me", headers=headers).json()
    assert me["is_guest"] is True and me["role"] == "learner"
    assert me["email"].endswith("@guest.agen.local")
    profile = client.get(f"{API}/learner/me", headers=headers)
    assert profile.status_code == 200 and profile.json()["display_name"] == "Bạn học thử"
    # Learning features work: scenarios, pronunciation XP.
    assert client.get(f"{API}/speaking/scenarios", headers=headers).status_code == 200
    pron = client.post(f"{API}/speaking/pronunciation", json={"target_text": "hello", "transcript": "hello"}, headers=headers)
    assert pron.status_code == 200 and pron.json()["xp_earned"] > 0


def test_claim_keeps_progress_and_logs_in_with_new_credentials(client):
    headers, _ = _guest(client)
    client.post(f"{API}/speaking/pronunciation", json={"target_text": "hello", "transcript": "hello"}, headers=headers)
    xp_before = client.get(f"{API}/learner/me", headers=headers).json()["total_xp"]
    assert xp_before > 0

    resp = client.post(
        f"{API}/auth/claim",
        json={"email": "Lan@Example.com", "password": "Strong123", "full_name": "Lan Nguyen", "display_name": "Lan", "age": 14, "grade": "grade_8"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_guest"] is False and resp.json()["email"] == "lan@example.com"

    login = client.post(f"{API}/auth/login", data={"username": "lan@example.com", "password": "Strong123"})
    assert login.status_code == 200
    new_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    profile = client.get(f"{API}/learner/me", headers=new_headers).json()
    assert profile["total_xp"] == xp_before and profile["display_name"] == "Lan" and profile["age"] == 14

    # Claiming twice (now a normal account) is refused.
    again = client.post(
        f"{API}/auth/claim",
        json={"email": "other@example.com", "password": "Strong123", "full_name": "X", "display_name": "X"},
        headers=new_headers,
    )
    assert again.status_code == 400


def test_claim_rejects_taken_email_and_weak_password(client):
    client.post(f"{API}/auth/register", json={"email": "taken@example.com", "password": "Strong123", "full_name": "T", "display_name": "T", "role": "learner"})
    headers, _ = _guest(client)
    taken = client.post(f"{API}/auth/claim", json={"email": "taken@example.com", "password": "Strong123", "full_name": "A", "display_name": "A"}, headers=headers)
    assert taken.status_code == 400
    weak = client.post(f"{API}/auth/claim", json={"email": "new@example.com", "password": "short", "full_name": "A", "display_name": "A"}, headers=headers)
    assert weak.status_code == 422


def test_register_user_is_not_guest(client):
    client.post(f"{API}/auth/register", json={"email": "real@example.com", "password": "Strong123", "full_name": "R", "display_name": "R", "role": "learner"})
    token = client.post(f"{API}/auth/login", data={"username": "real@example.com", "password": "Strong123"}).json()["access_token"]
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["is_guest"] is False
