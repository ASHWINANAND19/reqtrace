from app.agents.llm import get_llm
from app.agents.mock import OfflineProvider
from tests.test_projects import create
from tests.test_srs import generate, project_with_input


def approved_project(client, headers, text=None):
    pid = project_with_input(client, headers) if text is None else project_with_input(client, headers, text)
    srs = generate(client, headers, pid).json()
    client.post(f"/api/projects/{pid}/srs/versions/{srs['id']}/approve", headers=headers)
    return pid, srs


def gen_tests(client, headers, pid):
    return client.post(f"/api/projects/{pid}/tests/generate", headers=headers)


def test_every_requirement_gets_cases_with_all_fields(client, analyst):  # TC-17
    pid, srs = approved_project(client, analyst)
    response = gen_tests(client, analyst, pid)
    assert response.status_code == 201, response.text
    cases = response.json()["test_cases"]
    covered = {r for tc in cases for r in tc["requirement_ids"]}
    assert covered == {r["req_id"] for r in srs["requirements"]}
    for tc in cases:
        assert tc["tc_id"].startswith("TC-") and tc["title"] and tc["steps"] and tc["expected_result"]
    assert len({tc["tc_id"] for tc in cases}) == len(cases)


def test_positive_negative_and_boundary_types(client, analyst):  # TC-19
    pid, _ = approved_project(client, analyst)
    cases = gen_tests(client, analyst, pid).json()["test_cases"]
    nfr = [tc for tc in cases if "NFR-01" in tc["requirement_ids"]]
    assert {tc["type"] for tc in nfr} == {"positive", "negative", "boundary"}


def test_generation_blocked_until_srs_approved(client, analyst):  # TC-18
    pid = project_with_input(client, analyst)
    generate(client, analyst, pid)
    response = gen_tests(client, analyst, pid)
    assert response.status_code == 409
    assert "Approve an SRS version first" in response.json()["detail"]


def test_regenerating_replaces_suite(client, analyst):
    pid, _ = approved_project(client, analyst)
    first = len(gen_tests(client, analyst, pid).json()["test_cases"])
    second = gen_tests(client, analyst, pid).json()["test_cases"]
    assert len(second) == first and second[0]["tc_id"] == "TC-001"


def test_edit_create_and_delete_test_case(client, analyst):
    pid, _ = approved_project(client, analyst)
    cases = gen_tests(client, analyst, pid).json()["test_cases"]
    body = {"title": "Edited", "type": "negative", "preconditions": "", "steps": ["Do it"],
            "expected_result": "Rejected", "requirement_ids": ["FR-01", "FR-02"]}
    edited = client.put(f"/api/projects/{pid}/tests/{cases[0]['id']}", json=body, headers=analyst).json()
    assert edited["title"] == "Edited" and edited["requirement_ids"] == ["FR-01", "FR-02"]
    created = client.post(f"/api/projects/{pid}/tests", json=body, headers=analyst)
    assert created.status_code == 201 and created.json()["tc_id"] == f"TC-{len(cases) + 1:03d}"
    assert client.delete(f"/api/projects/{pid}/tests/{cases[0]['id']}", headers=analyst).status_code == 204
    assert len(client.get(f"/api/projects/{pid}/tests", headers=analyst).json()["test_cases"]) == len(cases)


def test_unknown_requirement_link_rejected(client, analyst):
    pid, _ = approved_project(client, analyst)
    body = {"title": "X", "type": "positive", "steps": ["a"], "expected_result": "b", "requirement_ids": ["FR-77"]}
    assert client.post(f"/api/projects/{pid}/tests", json=body, headers=analyst).status_code == 422


def test_developer_cannot_generate_tests(client, analyst):
    from tests.conftest import login, register

    pid, _ = approved_project(client, analyst)
    register(client, "dev@example.com", "Developer")
    client.post(f"/api/projects/{pid}/members", json={"email": "dev@example.com"}, headers=analyst)
    assert gen_tests(client, login(client, "dev@example.com"), pid).status_code == 403


def test_qa_can_generate_tests(client, analyst, qa):
    pid, _ = approved_project(client, analyst)
    client.post(f"/api/projects/{pid}/members", json={"email": "qa@example.com"}, headers=analyst)
    assert gen_tests(client, qa, pid).status_code == 201


def test_llm_outage_keeps_existing_tests(client, analyst):
    pid, _ = approved_project(client, analyst)
    before = gen_tests(client, analyst, pid).json()["test_cases"]
    client.app.dependency_overrides[get_llm] = lambda: OfflineProvider()
    assert gen_tests(client, analyst, pid).status_code == 503
    assert len(client.get(f"/api/projects/{pid}/tests", headers=analyst).json()["test_cases"]) == len(before)


def test_large_srs_is_generated_in_batches(client, analyst):
    text = "\n".join(f"The system shall support feature number {i} for members." for i in range(30))
    pid, srs = approved_project(client, analyst, text)
    cases = gen_tests(client, analyst, pid).json()["test_cases"]
    assert {r for tc in cases for r in tc["requirement_ids"]} == {r["req_id"] for r in srs["requirements"]}


def test_no_approved_srs_lists_empty(client, analyst):
    pid = create(client, analyst)["id"]
    assert client.get(f"/api/projects/{pid}/tests", headers=analyst).json() == {"srs_version": None, "test_cases": []}
