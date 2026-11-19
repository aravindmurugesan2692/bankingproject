"""Pytest fixtures using an isolated SQLite database."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure settings load before app import
os.environ["MOCK_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["OPENAI_API_KEY"] = ""

from app.database import Base, get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.seed import seed_support_teams  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed teams into the isolated test DB (lifespan seeds a different engine)
    seed_db = TestingSessionLocal()
    try:
        seed_support_teams(seed_db)
    finally:
        seed_db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
