from tests.conftest import login
from tests.test_rbac import make_admin
from tests.test_testcases import approved_project


def test_admin_changes_role_and_it_takes_effect(client, analyst, qa, monkeypatch):  # TC-32
    admin = make_admin(client, monkeypatch)
    users = {u["email"]: u for u in client.get("/api/admin/users", headers=admin).json()}
    qa_id = users["qa@example.com"]["id"]
    response = client.patch(f"/api/admin/users/{qa_id}", json={"role": "Analyst"}, headers=admin)
    assert response.status_code == 200 and response.json()["role"] == "Analyst"
    fresh = login(client, "qa@example.com")
    assert client.get("/api/auth/me", headers=fresh).json()["role"] == "Analyst"


def test_edit_approve_export_create_audit_entries(client, analyst, monkeypatch):  # TC-40
    pid, srs = approved_project(client, analyst)
    client.get(f"/api/projects/{pid}/export/srs.docx", headers=analyst)
    admin = make_admin(client, monkeypatch)
    entries = client.get(f"/api/admin/audit?project_id={pid}", headers=admin).json()
    actions = [(e["action"], e["entity"]) for e in entries]
    assert ("approve", "srs") in actions and ("export", "srs") in actions and ("generate", "srs") in actions
    assert all(e["user_name"] == "Ana Analyst" and e["created_at"] for e in entries)
    assert entries[0]["project_name"] == "Library"


def test_audit_log_is_admin_only(client, analyst):
    assert client.get("/api/admin/audit", headers=analyst).status_code == 403
    assert client.patch("/api/admin/users/1", json={"role": "Administrator"}, headers=analyst).status_code == 403


def test_deactivated_user_is_logged_out_and_cannot_log_in(client, analyst, monkeypatch):
    admin = make_admin(client, monkeypatch)
    analyst_id = client.get("/api/auth/me", headers=analyst).json()["id"]
    client.patch(f"/api/admin/users/{analyst_id}", json={"is_active": False}, headers=admin)
    assert client.get("/api/auth/me", headers=analyst).status_code == 401
    response = client.post("/api/auth/login", json={"email": "analyst@example.com", "password": "Str0ngPass!"})
    assert response.status_code == 401


def test_admin_cannot_demote_self(client, monkeypatch):
    admin = make_admin(client, monkeypatch)
    me = client.get("/api/auth/me", headers=admin).json()
    assert client.patch(f"/api/admin/users/{me['id']}", json={"role": "Analyst"}, headers=admin).status_code == 400
    assert client.patch("/api/admin/users/999", json={"role": "Analyst"}, headers=admin).status_code == 404
