from app.agents.llm import get_llm
from app.agents.mock import OfflineProvider
from app.agents.quality_agent import vague_flags
from tests.test_srs import edit_payload, generate, project_with_input


def check(client, headers, pid, vid):
    response = client.post(f"/api/projects/{pid}/srs/versions/{vid}/check", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_fast_and_user_friendly_flagged_with_rewrite(client, analyst):  # TC-29
    pid = project_with_input(client, analyst, "The system should be fast and user-friendly.")
    srs = generate(client, analyst, pid).json()
    report = check(client, analyst, pid, srs["id"])
    vague = {f["text"]: f for f in report["flags"] if f["kind"] == "vague" and f["location"].startswith(("FR", "NFR"))}
    assert set(vague) >= {"fast", "user-friendly"}
    assert "within 2 seconds" in vague["fast"]["suggestion"]
    assert "first-time user" in vague["user-friendly"]["suggestion"]
    assert vague["fast"]["reason"]


def test_missing_section_reported(client, analyst):  # TC-30
    pid = project_with_input(client, analyst)
    v1 = generate(client, analyst, pid).json()
    sections = [s for s in edit_payload(v1)["sections"] if s["number"] != "2.4"]
    v2 = client.post(f"/api/projects/{pid}/srs/versions", json=edit_payload(v1, sections=sections),
                     headers=analyst).json()
    report = check(client, analyst, pid, v2["id"])
    missing = [f["location"] for f in report["flags"] if f["kind"] == "missing"]
    assert missing == ["2.4 Operating Environment"]
    assert report["missing"] == 1


def test_conflicting_requirements_flagged(client, analyst):
    pid = project_with_input(
        client, analyst,
        "The system shall allow members to delete their loan history.\n"
        "The system shall not allow members to delete their loan history.",
    )
    srs = generate(client, analyst, pid).json()
    report = check(client, analyst, pid, srs["id"])
    assert report["conflicts"] == 1 and report["conflict_check"] == "done"
    assert report["flags"][-1]["location"] == "FR-01, FR-02"


def test_clean_srs_has_no_vague_flags(client, analyst):
    pid = project_with_input(client, analyst, "The system shall export the report as a PDF file within 5 seconds.")
    srs = generate(client, analyst, pid).json()
    report = check(client, analyst, pid, srs["id"])
    assert [f for f in report["flags"] if f["kind"] == "vague" and f["location"].startswith(("FR", "NFR"))] == []


def test_rule_checks_still_work_when_llm_is_down(client, analyst):
    pid = project_with_input(client, analyst, "Pages must load fast.\nThe system shall list books.")
    srs = generate(client, analyst, pid).json()
    client.app.dependency_overrides[get_llm] = lambda: OfflineProvider()
    report = check(client, analyst, pid, srs["id"])
    assert report["conflict_check"] == "unavailable" and report["vague"] >= 1


def test_vague_word_inside_other_word_not_flagged():
    assert vague_flags("FR-01", "The system shall send breakfast menus") == []
    assert [f.text for f in vague_flags("FR-01", "Support PDF, DOCX etc.")] == ["etc"]
