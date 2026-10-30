from tests.conftest import login, register


def create(client, headers, name="Library System"):
    response = client.post("/api/projects", json={"name": name, "description": "demo"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_project_appears_in_list(client, analyst):  # TC-05
    project = create(client, analyst)
    listed = client.get("/api/projects", headers=analyst).json()
    assert [p["id"] for p in listed] == [project["id"]]
    assert project["members"][0]["email"] == "analyst@example.com"


def test_blank_project_name_rejected(client, analyst):  # TC-07
    response = client.post("/api/projects", json={"name": "   "}, headers=analyst)
    assert response.status_code == 422
    assert client.get("/api/projects", headers=analyst).json() == []


def test_added_member_can_see_project(client, analyst, qa):  # TC-06
    project = create(client, analyst)
    response = client.post(f"/api/projects/{project['id']}/members", json={"email": "qa@example.com"},
                           headers=analyst)
    assert response.status_code == 201
    assert client.get(f"/api/projects/{project['id']}", headers=qa).status_code == 200
    assert len(client.get("/api/projects", headers=qa).json()) == 1


def test_non_member_cannot_open_project(client, analyst):  # TC-39, SEC-07
    project = create(client, analyst)
    register(client, "outsider@example.com", "Developer")
    outsider = login(client, "outsider@example.com")
    assert client.get(f"/api/projects/{project['id']}", headers=outsider).status_code == 403
    assert client.get("/api/projects", headers=outsider).json() == []


def test_rename_archive_and_delete(client, analyst):
    project = create(client, analyst)
    pid = project["id"]
    renamed = client.patch(f"/api/projects/{pid}", json={"name": "Renamed"}, headers=analyst).json()
    assert renamed["name"] == "Renamed"
    client.patch(f"/api/projects/{pid}", json={"archived": True}, headers=analyst)
    assert client.get("/api/projects", headers=analyst).json() == []
    assert len(client.get("/api/projects?include_archived=true", headers=analyst).json()) == 1
    assert client.delete(f"/api/projects/{pid}", headers=analyst).status_code == 204
    assert client.get("/api/projects?include_archived=true", headers=analyst).json() == []


def test_only_owner_can_delete(client, analyst, qa):
    project = create(client, analyst)
    client.post(f"/api/projects/{project['id']}/members", json={"email": "qa@example.com"}, headers=analyst)
    assert client.delete(f"/api/projects/{project['id']}", headers=qa).status_code == 403


def test_add_unknown_or_duplicate_member(client, analyst):
    project = create(client, analyst)
    url = f"/api/projects/{project['id']}/members"
    assert client.post(url, json={"email": "nobody@example.com"}, headers=analyst).status_code == 404
    assert client.post(url, json={"email": "analyst@example.com"}, headers=analyst).status_code == 409


def test_remove_member(client, analyst, qa):
    project = create(client, analyst)
    pid = project["id"]
    qa_id = client.post(f"/api/projects/{pid}/members", json={"email": "qa@example.com"},
                        headers=analyst).json()["members"][1]["id"]
    assert client.delete(f"/api/projects/{pid}/members/{qa_id}", headers=analyst).status_code == 200
    assert client.get(f"/api/projects/{pid}", headers=qa).status_code == 403
    owner_id = project["owner_id"]
    assert client.delete(f"/api/projects/{pid}/members/{owner_id}", headers=analyst).status_code == 400


def test_fifty_projects_listed(client, analyst):  # TC-48 data volume
    for i in range(50):
        create(client, analyst, f"Project {i}")
    assert len(client.get("/api/projects", headers=analyst).json()) == 50
