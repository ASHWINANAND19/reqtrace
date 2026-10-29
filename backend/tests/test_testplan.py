import json

from app.agents.llm import LLMRequest, get_llm
from app.agents.mock import MockProvider
from app.agents.testplan_agent import PLAN_SECTIONS
from tests.test_agent_base import ScriptedProvider
from tests.test_srs import generate, project_with_input
from tests.test_testcases import approved_project


def test_generated_plan_has_all_sections_and_references_ids(client, analyst):  # TC-26
    pid, srs = approved_project(client, analyst)
    response = client.post(f"/api/projects/{pid}/test-plan/generate", headers=analyst)
    assert response.status_code == 201, response.text
    plan = response.json()
    assert [s["title"] for s in plan["sections"]] == PLAN_SECTIONS
    assert all(s["content"] for s in plan["sections"])
    assert "FR-01" in plan["sections"][0]["content"]
    assert set(plan["requirement_ids"]) == {r["req_id"] for r in srs["requirements"]}
    assert client.get(f"/api/projects/{pid}/test-plan", headers=analyst).json()["id"] == plan["id"]


def test_plan_requires_approved_srs(client, analyst):
    pid = project_with_input(client, analyst)
    generate(client, analyst, pid)
    assert client.post(f"/api/projects/{pid}/test-plan/generate", headers=analyst).status_code == 409
    assert client.get(f"/api/projects/{pid}/test-plan", headers=analyst).json() is None


def test_plan_without_requirement_ids_is_retried(client, analyst):
    pid, srs = approved_project(client, analyst)
    payload = {"title": "x", "requirements": [{"req_id": r["req_id"], "type": r["type"], "priority": r["priority"],
                                               "description": r["description"]} for r in srs["requirements"]]}
    good = json.loads(MockProvider().generate(LLMRequest(task="testplan", system="", prompt="", payload=payload)))
    no_ids = {"sections": [{"title": t, "content": "Generic text."} for t in PLAN_SECTIONS],
              "requirements_in_scope": ["FR-01"]}
    provider = ScriptedProvider(json.dumps(no_ids), json.dumps(good))
    client.app.dependency_overrides[get_llm] = lambda: provider
    assert client.post(f"/api/projects/{pid}/test-plan/generate", headers=analyst).status_code == 201
    assert "does not reference any requirement IDs" in provider.requests[1].prompt


def test_edit_plan_section(client, analyst):
    pid, _ = approved_project(client, analyst)
    plan = client.post(f"/api/projects/{pid}/test-plan/generate", headers=analyst).json()
    sections = plan["sections"]
    sections[3]["content"] = "Sprint 2: 26-30 Oct."
    updated = client.put(f"/api/projects/{pid}/test-plan/{plan['id']}", json={"sections": sections}, headers=analyst)
    assert updated.status_code == 200 and updated.json()["sections"][3]["content"] == "Sprint 2: 26-30 Oct."
    missing = client.put(f"/api/projects/{pid}/test-plan/999", json={"sections": sections}, headers=analyst)
    assert missing.status_code == 404
