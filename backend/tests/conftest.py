import os

# Tests run against an in-memory database and the mock LLM, before the app is imported.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests-only-32b"
os.environ["STORAGE_DIR"] = "/tmp/reqtrace-test-storage"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402

PASSWORD = "Str0ngPass!"


@pytest.fixture(autouse=True)
def fresh_db():
    from app import models  # noqa: F401

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def register(client, email, role="Analyst", name="Test User"):
    response = client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": PASSWORD, "role": role}
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client, email, password=PASSWORD):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def analyst(client):
    register(client, "analyst@example.com", "Analyst", "Ana Analyst")
    return login(client, "analyst@example.com")


@pytest.fixture
def qa(client):
    register(client, "qa@example.com", "QA Engineer", "Quinn QA")
    return login(client, "qa@example.com")
