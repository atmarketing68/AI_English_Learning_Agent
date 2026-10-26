"""Sanity checks that the shared fixtures wire up correctly."""
from sqlalchemy import inspect

from app.models.user import User


def test_db_session_has_full_schema(db_session, db_engine):
    tables = set(inspect(db_engine).get_table_names())
    # A representative sample from across the model modules.
    assert {"users", "learner_profiles", "agent_traces", "parent_profiles"} <= tables


def test_db_session_can_write_and_read(db_session):
    user = User(
        email="sanity@example.com",
        hashed_password="x",
        full_name="Sanity",
    )
    db_session.add(user)
    db_session.commit()
    fetched = db_session.query(User).filter_by(email="sanity@example.com").one()
    assert fetched.id is not None


def test_client_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
