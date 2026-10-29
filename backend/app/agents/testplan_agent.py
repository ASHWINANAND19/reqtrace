"""Test Plan Agent: IEEE 829-style plan from the approved SRS (FR-09)."""
import re
from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import Agent, wrap_untrusted
from app.agents.mock import register_mock

PLAN_SECTIONS = [
    "Scope",
    "Test Approach",
    "Test Environment",
    "Schedule",
    "Risks and Contingencies",
    "Entry Criteria",
    "Exit Criteria",
]
REQ_ID = re.compile(r"\b(?:FR|NFR|SEC)-\d{1,3}\b")


class PlanSection(BaseModel):
    title: str
    content: str


class TestPlanDraft(BaseModel):
    __test__ = False

    sections: list[PlanSection]
    requirements_in_scope: list[str] = Field(min_length=1)


class TestPlanAgent(Agent[TestPlanDraft]):
    __test__ = False

    task = "testplan"
    output_model = TestPlanDraft
    system_prompt = "You are the Test Plan Agent of ReqTrace. You write concise test plans following IEEE Std 829."

    def build_prompt(self, data: dict[str, Any]) -> str:
        lines = "\n".join(
            f"{r['req_id']} ({r['type']}, {r['priority']}): {r['description']}" for r in data["requirements"]
        )
        return (
            f"Write a test plan for the system '{data['title']}' whose approved requirements are in the data below.\n"
            "Return JSON with sections: one entry for EACH of these titles, in this order, with plain-text content "
            f"(short paragraphs or '- ' bullets): {', '.join(PLAN_SECTIONS)}.\n"
            "Reference requirement IDs (e.g. FR-01) where relevant, especially in Scope and Test Approach. "
            "requirements_in_scope lists every requirement ID covered by the plan.\n\n"
            f"Requirements:\n{wrap_untrusted(lines)}"
        )

    def check(self, output: TestPlanDraft, data: dict[str, Any]) -> None:
        written = {s.title.strip().lower() for s in output.sections if s.content.strip()}
        missing = [t for t in PLAN_SECTIONS if t.lower() not in written]
        if missing:
            raise ValueError(f"missing plan sections: {', '.join(missing)}")
        text = " ".join(s.content for s in output.sections)
        if not REQ_ID.search(text):
            raise ValueError("the plan does not reference any requirement IDs")


@register_mock("testplan")
def mock_testplan(payload: dict[str, Any]) -> dict[str, Any]:
    reqs = payload["requirements"]
    ids = [r["req_id"] for r in reqs]
    must = [r["req_id"] for r in reqs if r["priority"] == "Must"] or ids
    nfr = [r["req_id"] for r in reqs if r["type"] == "non-functional"]
    content = {
        "Scope": f"In scope: {', '.join(ids)}. Out of scope: third-party services beyond their interfaces.",
        "Test Approach": (
            f"- Functional black-box tests for {', '.join(r for r in ids if r.startswith('FR'))}\n"
            f"- Non-functional tests for {', '.join(nfr) or 'none identified'}\n"
            "- Equivalence partitioning and boundary value analysis\n"
            f"- Must requirements first: {', '.join(must)}"
        ),
        "Test Environment": "Docker Compose deployment; current Chrome, Firefox and Edge; seeded test accounts.",
        "Schedule": "- Week 1: test design and unit tests\n- Week 2: system, regression and acceptance testing",
        "Risks and Contingencies": "- Late requirement changes: use the traceability matrix to find affected tests",
        "Entry Criteria": "- SRS approved\n- Build deployed to the test environment\n- Smoke test passes",
        "Exit Criteria": "- All Must test cases pass\n- No open Critical or High defects\n- 100% requirement coverage",
    }
    return {"sections": [{"title": t, "content": content[t]} for t in PLAN_SECTIONS], "requirements_in_scope": ids}
