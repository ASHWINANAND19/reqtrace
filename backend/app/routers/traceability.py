"""Requirements traceability matrix with coverage (FR-07)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_project
from app.models import Project, Requirement, SRSVersion, TestCase, TraceLink
from app.routers.srs import VersionSummary, latest_approved, summary

router = APIRouter(prefix="/api/projects/{project_id}/traceability", tags=["traceability"])


class TraceRow(BaseModel):
    req_id: str
    type: str
    title: str
    priority: str
    test_cases: list[str]
    covered: bool


class TraceMatrix(BaseModel):
    srs_version: VersionSummary | None
    rows: list[TraceRow]
    total: int
    covered: int
    coverage_percent: float
    uncovered: list[str]


def build_matrix(db: Session, version: SRSVersion) -> list[TraceRow]:
    links = db.execute(
        select(Requirement.id, TestCase.tc_id)
        .join(TraceLink, TraceLink.requirement_id == Requirement.id)
        .join(TestCase, TestCase.id == TraceLink.test_case_id)
        .where(Requirement.srs_version_id == version.id)
        .order_by(TestCase.tc_id)
    ).all()
    tests_by_req: dict[int, list[str]] = {}
    for req_pk, tc_id in links:
        tests_by_req.setdefault(req_pk, []).append(tc_id)
    return [
        TraceRow(
            req_id=r.req_id,
            type=r.type,
            title=r.title,
            priority=r.priority,
            test_cases=tests_by_req.get(r.id, []),
            covered=bool(tests_by_req.get(r.id)),
        )
        for r in version.requirements
    ]


@router.get("", response_model=TraceMatrix)
def get_matrix(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> TraceMatrix:
    version = latest_approved(db, project)
    if version is None:
        return TraceMatrix(srs_version=None, rows=[], total=0, covered=0, coverage_percent=0.0, uncovered=[])
    rows = build_matrix(db, version)
    covered = sum(r.covered for r in rows)
    return TraceMatrix(
        srs_version=summary(version),
        rows=rows,
        total=len(rows),
        covered=covered,
        coverage_percent=round(100 * covered / len(rows), 1) if rows else 0.0,
        uncovered=[r.req_id for r in rows if not r.covered],
    )
