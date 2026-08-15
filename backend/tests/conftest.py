import os
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_for_unit_tests_only_attendance_sys_123"
os.environ["ENVIRONMENT"] = "test"

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.db.init_db import init_db
from app.core.rate_limit import reset_rate_limit_store

# In-memory SQLite engine for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh database schema for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    init_db(session)
    reset_rate_limit_store()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    """Obtain JWT token for default seeded admin (Rajavel)."""
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "Rajavel",
        "password": "Admin@123456"
    })
    return res.json()["data"]["access_token"]


@pytest.fixture
def manager_token(client):
    """Obtain JWT token for default seeded manager."""
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "manager",
        "password": "Manager@123456"
    })
    return res.json()["data"]["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def manager_headers(manager_token):
    return {"Authorization": f"Bearer {manager_token}"}
