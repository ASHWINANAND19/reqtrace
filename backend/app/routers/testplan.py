"""Test plan generation and editing (FR-09)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.agents.base import AgentError
from app.agents.llm import LLMProvider, get_llm
from app.agents.testplan_agent import PLAN_SECTIONS, TestPlanAgent
from app.db import get_db, utcnow
from app.deps import get_project, require_roles
from app.models import Project, SRSVersion, TestPlan, User
from app.permissions import EDIT_TESTS, GENERATE_TESTS
from app.routers.srs import require_approved

router = APIRouter(prefix="/api/projects/{project_id}/test-plan", tags=["test plan"])


class PlanSectionIO(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(max_length=20_000)


class TestPlanOut(BaseModel):
    __test__ = False

    id: int
    srs_version_no: int
    sections: list[PlanSectionIO]
    requirement_ids: list[str]
    created_at: datetime
    updated_at: datetime


class TestPlanIn(BaseModel):
    __test__ = False

    sections: list[PlanSectionIO]


def plan_out(db: Session, plan: TestPlan) -> TestPlanOut:
    return TestPlanOut(
        id=plan.id,
        srs_version_no=db.get(SRSVersion, plan.srs_version_id).version_no,
        sections=[PlanSectionIO(**s) for s in plan.sections],
        requirement_ids=plan.requirement_ids,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def latest_plan(db: Session, project: Project) -> TestPlan | None:
    query = select(TestPlan).where(TestPlan.project_id == project.id).order_by(TestPlan.id.desc())
    return db.scalars(query).first()


@router.get("", response_model=TestPlanOut | None)
def get_plan(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> TestPlanOut | None:
    plan = latest_plan(db, project)
    return plan_out(db, plan) if plan else None


@router.post("/generate", response_model=TestPlanOut, status_code=status.HTTP_201_CREATED)
def generate_plan(
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*GENERATE_TESTS)),
    llm: LLMProvider = Depends(get_llm),
    db: Session = Depends(get_db),
) -> TestPlanOut:
    version = require_approved(db, project)
    requirements = [
        {"req_id": r.req_id, "type": r.type, "priority": r.priority, "description": r.description}
        for r in version.requirements
    ]
    try:
        draft = TestPlanAgent(llm).run({"title": version.title, "requirements": requirements})
    except AgentError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    content = {s.title.strip().lower(): s.content.strip() for s in draft.sections}
    known = {r["req_id"] for r in requirements}
    plan = TestPlan(
        project_id=project.id,
        srs_version_id=version.id,
        sections=[{"title": t, "content": content[t.lower()]} for t in PLAN_SECTIONS],
        requirement_ids=[r for r in dict.fromkeys(draft.requirements_in_scope) if r in known],
        created_by=user.id,
    )
    db.add(plan)
    db.flush()
    audit.record(db, user, "generate", "test_plan", plan.id, project.id, f"SRS v{version.version_no}")
    db.commit()
    return plan_out(db, plan)


@router.put("/{plan_id}", response_model=TestPlanOut)
def update_plan(
    plan_id: int,
    body: TestPlanIn,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*EDIT_TESTS)),
    db: Session = Depends(get_db),
) -> TestPlanOut:
    plan = db.get(TestPlan, plan_id)
    if plan is None or plan.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test plan not found.")
    plan.sections = [s.model_dump() for s in body.sections]
    plan.updated_at = utcnow()
    audit.record(db, user, "edit", "test_plan", plan.id, project.id)
    db.commit()
    return plan_out(db, plan)
