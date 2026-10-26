"""Errors must reach the browser: CORS headers on 500s, readable validation messages."""
from main import app
from app.core.config import Settings

ORIGIN = "http://localhost:3000"


def _boom():
    raise RuntimeError("boom")


def test_unhandled_error_keeps_cors_headers(client):
    app.add_api_route("/__test_boom", _boom)
    res = client.get("/__test_boom", headers={"Origin": ORIGIN})
    assert res.status_code == 500
    assert res.headers.get("access-control-allow-origin") == ORIGIN
    assert "lỗi nội bộ" in res.json()["detail"]


def test_app_url_is_an_allowed_origin():
    s = Settings(ALLOWED_ORIGINS="https://agen-web.vercel.app", APP_URL="https://hoc.example.vn/")
    assert s.cors_origins == ["https://agen-web.vercel.app", "https://hoc.example.vn"]
    assert Settings(ALLOWED_ORIGINS="https://a.vn/", APP_URL="https://a.vn").cors_origins == ["https://a.vn"]


def test_weak_password_message_is_vietnamese(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "weak@example.com", "password": "abcdefghij",
        "full_name": "A", "display_name": "A", "role": "learner",
    })
    assert res.status_code == 422
    assert "chữ số" in res.json()["detail"][0]["msg"]


def test_duplicate_email_message_is_vietnamese(client):
    payload = {"email": "dup@example.com", "password": "abcdefgh12",
               "full_name": "A", "display_name": "A", "role": "learner"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 400
    assert "đã được đăng ký" in res.json()["detail"]
