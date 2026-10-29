"""Test case generation and maintenance (FR-06)."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import audit
from app.agents.base import AgentError
from app.agents.llm import LLMProvider, get_llm
from app.agents.testcase_agent import TestCaseAgent
from app.db import get_db
from app.deps import get_project, require_roles
from app.models import Project, Requirement, SRSVersion, TestCase, TraceLink, User
from app.permissions import EDIT_TESTS, GENERATE_TESTS
from app.routers.srs import VersionSummary, latest_approved, require_approved, summary

router = APIRouter(prefix="/api/projects/{project_id}/tests", tags=["tests"])

BATCH_SIZE = 12  # requirements per LLM call, keeps each response well inside the output limit


class TestCaseOut(BaseModel):
    __test__ = False

    id: int
    tc_id: str
    title: str
    type: str
    preconditions: str
    steps: list[str]
    expected_result: str
    requirement_ids: list[str]
    created_at: datetime


class TestSuiteOut(BaseModel):
    __test__ = False

    srs_version: VersionSummary | None
    test_cases: list[TestCaseOut]


class TestCaseIn(BaseModel):
    __test__ = False

    title: str = Field(min_length=1, max_length=200)
    type: Literal["positive", "negative", "boundary"]
    preconditions: str = Field("", max_length=2000)
    steps: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1, max_length=2000)
    requirement_ids: list[str] = Field(min_length=1)


def case_out(tc: TestCase) -> TestCaseOut:
    return TestCaseOut(
        id=tc.id,
        tc_id=tc.tc_id,
        title=tc.title,
        type=tc.type,
        preconditions=tc.preconditions,
        steps=tc.steps,
        expected_result=tc.expected_result,
        requirement_ids=sorted(link.requirement.req_id for link in tc.links),
        created_at=tc.created_at,
    )


def cases_for(db: Session, version: SRSVersion) -> list[TestCase]:
    return list(db.scalars(select(TestCase).where(TestCase.srs_version_id == version.id).order_by(TestCase.id)))


def _requirements_by_id(version: SRSVersion) -> dict[str, Requirement]:
    return {r.req_id: r for r in version.requirements}


def _next_tc_number(db: Session, version: SRSVersion) -> int:
    numbers = [int(tc.tc_id.split("-")[1]) for tc in cases_for(db, version) if tc.tc_id.split("-")[-1].isdigit()]
    return max(numbers, default=0) + 1


def _link(tc: TestCase, version: SRSVersion, req_ids: list[str]) -> None:
    by_id = _requirements_by_id(version)
    unknown = [r for r in req_ids if r not in by_id]
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unknown requirement IDs: {', '.join(unknown)}")
    tc.links = [TraceLink(requirement=by_id[r]) for r in dict.fromkeys(req_ids)]


@router.get("", response_model=TestSuiteOut)
def list_tests(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> TestSuiteOut:
    version = latest_approved(db, project)
    if version is None:
        return TestSuiteOut(srs_version=None, test_cases=[])
    return TestSuiteOut(srs_version=summary(version), test_cases=[case_out(tc) for tc in cases_for(db, version)])


@router.post("/generate", response_model=TestSuiteOut, status_code=status.HTTP_201_CREATED)
def generate_tests(
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*GENERATE_TESTS)),
    llm: LLMProvider = Depends(get_llm),
    db: Session = Depends(get_db),
) -> TestSuiteOut:
    version = require_approved(db, project)
    requirements = [
        {"req_id": r.req_id, "type": r.type, "title": r.title, "description": r.description}
        for r in version.requirements
    ]
    if not requirements:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The approved SRS has no requirements to test.")

    drafts = []
    agent = TestCaseAgent(llm)
    try:
        for start in range(0, len(requirements), BATCH_SIZE):
            batch = requirements[start : start + BATCH_SIZE]
            drafts.extend(agent.run({"requirements": batch}).test_cases)
    except AgentError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    # Regenerating replaces the previous AI-generated suite for this SRS version
    db.execute(delete(TestCase).where(TestCase.srs_version_id == version.id))
    by_id = _requirements_by_id(version)
    number = 0
    for draft in drafts:
        requirement = by_id.get(draft.requirement_id.strip())
        if requirement is None:
            continue  # the model referenced an ID that does not exist; drop it
        number += 1
        db.add(
            TestCase(
                project_id=project.id,
                srs_version_id=version.id,
                tc_id=f"TC-{number:03d}",
                title=draft.title,
                type=draft.type,
                preconditions=draft.preconditions,
                steps=draft.steps,
                expected_result=draft.expected_result,
                created_by=user.id,
                links=[TraceLink(requirement=requirement)],
            )
        )
    audit.record(db, user, "generate", "test_cases", version.version_no, project.id, f"{number} cases")
    db.commit()
    return TestSuiteOut(srs_version=summary(version), test_cases=[case_out(tc) for tc in cases_for(db, version)])


@router.post("", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
def create_test(
    body: TestCaseIn,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*EDIT_TESTS)),
    db: Session = Depends(get_db),
) -> TestCaseOut:
    version = require_approved(db, project)
    tc = TestCase(
        project_id=project.id,
        srs_version_id=version.id,
        tc_id=f"TC-{_next_tc_number(db, version):03d}",
        title=body.title,
        type=body.type,
        preconditions=body.preconditions,
        steps=body.steps,
        expected_result=body.expected_result,
        created_by=user.id,
    )
    _link(tc, version, body.requirement_ids)
    db.add(tc)
    db.flush()
    audit.record(db, user, "create", "test_case", tc.tc_id, project.id)
    db.commit()
    return case_out(tc)


def _load(db: Session, project: Project, test_id: int) -> TestCase:
    tc = db.get(TestCase, test_id)
    if tc is None or tc.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test case not found.")
    return tc


@router.put("/{test_id}", response_model=TestCaseOut)
def update_test(
    test_id: int,
    body: TestCaseIn,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*EDIT_TESTS)),
    db: Session = Depends(get_db),
) -> TestCaseOut:
    tc = _load(db, project, test_id)
    for field in ("title", "type", "preconditions", "steps", "expected_result"):
        setattr(tc, field, getattr(body, field))
    _link(tc, db.get(SRSVersion, tc.srs_version_id), body.requirement_ids)
    audit.record(db, user, "edit", "test_case", tc.tc_id, project.id)
    db.commit()
    return case_out(tc)


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(
    test_id: int,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*EDIT_TESTS)),
    db: Session = Depends(get_db),
) -> Response:
    tc = _load(db, project, test_id)
    audit.record(db, user, "delete", "test_case", tc.tc_id, project.id)
    db.delete(tc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
