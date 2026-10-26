"""Shared pytest fixtures for the AGEN backend test suite.

Provides an isolated in-memory SQLite database and a FastAPI TestClient with the
`get_db` dependency overridden so integration tests never touch the dev database.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importing the models package registers every table on Base.metadata so that
# create_all() below builds a complete schema.
import app.models  # noqa: F401
from app.core.database import Base, get_db


@pytest.fixture()
def db_engine():
    """A fresh in-memory SQLite engine with the full schema created.

    StaticPool + a single shared connection keeps the in-memory DB alive across
    sessions within one test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """A SQLAlchemy session bound to the in-memory engine."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_engine):
    """A FastAPI TestClient wired to the in-memory database.

    The app's get_db dependency is overridden to hand out sessions bound to the
    test engine, so requests operate on the isolated schema.
    """
    from fastapi.testclient import TestClient

    from main import app

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Disable slowapi rate limiting during tests so repeated register/login
    # calls in the suite are not throttled.
    if getattr(app.state, "limiter", None) is not None:
        app.state.limiter.enabled = False
    try:
        from app.api.auth import limiter as auth_limiter

        auth_limiter.enabled = False
    except Exception:
        pass

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
