"""Test Case Agent: positive, negative and boundary tests for each requirement (FR-06)."""
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agents.base import Agent, wrap_untrusted
from app.agents.mock import register_mock


class TestCaseDraft(BaseModel):
    __test__ = False

    requirement_id: str
    title: str = Field(min_length=1, max_length=200)
    type: Literal["positive", "negative", "boundary"]
    preconditions: str = ""
    steps: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1)


class TestSuiteDraft(BaseModel):
    __test__ = False

    test_cases: list[TestCaseDraft] = Field(min_length=1)


def requirement_lines(requirements: list[dict[str, Any]]) -> str:
    return "\n".join(f"{r['req_id']} ({r['type']}): {r['description']}" for r in requirements)


class TestCaseAgent(Agent[TestSuiteDraft]):
    __test__ = False

    task = "testcases"
    output_model = TestSuiteDraft
    system_prompt = (
        "You are the Test Case Agent of ReqTrace. You design precise, executable black-box test cases using "
        "equivalence partitioning and boundary value analysis."
    )

    def build_prompt(self, data: dict[str, Any]) -> str:
        return (
            "Write test cases for EVERY requirement in the data below.\n"
            "For each requirement give one positive test, one negative test, and a boundary test when the "
            "requirement has a limit, size, time or count (2 to 4 cases per requirement).\n"
            "Return JSON with test_cases: each has requirement_id (exactly as given, e.g. FR-01), title, type "
            "(positive, negative or boundary), preconditions, steps (list of short imperative steps) and "
            "expected_result (observable and checkable). Do not number the test cases.\n\n"
            f"Requirements:\n{wrap_untrusted(requirement_lines(data['requirements']))}"
        )

    def check(self, output: TestSuiteDraft, data: dict[str, Any]) -> None:
        covered = {tc.requirement_id.strip() for tc in output.test_cases}
        missing = [r["req_id"] for r in data["requirements"] if r["req_id"] not in covered]
        if missing:
            raise ValueError(f"no test cases for: {', '.join(missing)}")


# ---- Offline mock -----------------------------------------------------------------------------------

_NUMBER = re.compile(r"\b\d+(\.\d+)?\s*(seconds?|s|ms|minutes?|mb|kb|gb|%|users?|days?|characters?)?\b", re.I)


@register_mock("testcases")
def mock_testcases(payload: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for r in payload["requirements"]:
        subject = r["title"] or r["req_id"]
        cases.append({
            "requirement_id": r["req_id"], "title": f"{subject}: valid use", "type": "positive",
            "preconditions": "User is logged in with a permitted role.",
            "steps": ["Open the relevant page", f"Perform the action described in {r['req_id']} with valid data",
                      "Observe the result"],
            "expected_result": f"Behaviour matches {r['req_id']}: {r['description']}",
        })
        cases.append({
            "requirement_id": r["req_id"], "title": f"{subject}: invalid input rejected", "type": "negative",
            "preconditions": "User is logged in.",
            "steps": ["Open the relevant page", "Repeat the action with missing or invalid data", "Submit"],
            "expected_result": "The action is rejected with a clear error message and no data is changed.",
        })
        match = _NUMBER.search(r["description"])
        if match:
            limit = match.group(0).strip()
            cases.append({
                "requirement_id": r["req_id"], "title": f"{subject}: limit {limit}", "type": "boundary",
                "preconditions": "Test data prepared at, just below and just above the limit.",
                "steps": [f"Exercise the requirement exactly at {limit}", "Repeat just above the limit"],
                "expected_result": "At the limit the requirement is met; above it the system responds as specified.",
            })
    return {"test_cases": cases}
