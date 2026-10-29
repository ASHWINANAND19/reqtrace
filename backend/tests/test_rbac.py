from app.config import get_settings
from app.db import SessionLocal
from app.seed import seed_admin
from tests.conftest import login


def make_admin(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_email", "admin@example.com")
    monkeypatch.setattr(settings, "admin_password", "Adm1nPass!")
    with SessionLocal() as db:
        seed_admin(db)
    return login(client, "admin@example.com", "Adm1nPass!")


def test_admin_can_list_users(client, analyst, monkeypatch):
    admin = make_admin(client, monkeypatch)
    response = client.get("/api/admin/users", headers=admin)
    assert response.status_code == 200
    roles = {u["email"]: u["role"] for u in response.json()}
    assert roles["admin@example.com"] == "Administrator"
    assert roles["analyst@example.com"] == "Analyst"


def test_non_admin_gets_403_on_admin_endpoint(client, qa):  # SEC-03
    response = client.get("/api/admin/users", headers=qa)
    assert response.status_code == 403


def test_cannot_self_register_as_administrator(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Eve", "email": "eve@example.com", "password": "Str0ngPass!", "role": "Administrator"},
    )
    assert response.status_code == 403


def test_seed_admin_is_idempotent(client, monkeypatch):
    make_admin(client, monkeypatch)
    with SessionLocal() as db:
        seed_admin(db)
    assert client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "Adm1nPass!"}
    ).status_code == 200
