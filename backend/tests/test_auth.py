from datetime import timedelta

from sqlalchemy import select

from app.models import AuthSession, User
from tests.conftest import PASSWORD, login, register


def test_register_creates_account_and_user_can_log_in(client):  # TC-01, TC-02
    register(client, "new@example.com")
    headers = login(client, "new@example.com")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "new@example.com"


def test_duplicate_email_is_rejected(client):
    register(client, "dup@example.com")
    response = client.post(
        "/api/auth/register", json={"name": "X", "email": "DUP@example.com", "password": PASSWORD}
    )
    assert response.status_code == 409


def test_wrong_password_is_rejected_without_session(client, db):  # TC-03
    register(client, "user@example.com")
    response = client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrong-pass"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
    assert db.scalars(select(AuthSession)).all() == []


def test_session_expires_after_60_minutes_of_inactivity(client, db):  # TC-04
    register(client, "idle@example.com")
    headers = login(client, "idle@example.com")
    session = db.scalars(select(AuthSession)).one()
    session.last_seen -= timedelta(minutes=61)
    db.commit()
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert "inactivity" in response.json()["detail"]


def test_activity_within_60_minutes_keeps_session_alive(client, db):  # TC-04 boundary
    register(client, "active@example.com")
    headers = login(client, "active@example.com")
    session = db.scalars(select(AuthSession)).one()
    session.last_seen -= timedelta(minutes=59)
    db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 200


def test_password_stored_as_bcrypt_hash(client, db):  # TC-33, SEC-01
    register(client, "hash@example.com")
    user = db.scalars(select(User).where(User.email == "hash@example.com")).one()
    assert user.password_hash.startswith("$2b$")
    assert PASSWORD not in user.password_hash


def test_token_rejected_after_logout(client):  # TC-34, SEC-02
    register(client, "out@example.com")
    headers = login(client, "out@example.com")
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_tampered_or_missing_token_rejected(client):  # TC-34
    assert client.get("/api/auth/me").status_code == 401
    bad = {"Authorization": "Bearer not.a.valid.token"}
    assert client.get("/api/auth/me", headers=bad).status_code == 401


def test_short_password_rejected(client):
    response = client.post(
        "/api/auth/register", json={"name": "X", "email": "short@example.com", "password": "abc"}
    )
    assert response.status_code == 422
