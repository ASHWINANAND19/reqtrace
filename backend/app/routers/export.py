"""Export endpoints for DOCX, CSV and diagram PNG audit (FR-08)."""
import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import audit, exporter
from app.db import get_db
from app.deps import get_current_user, get_project
from app.models import Project, SRSVersion, User
from app.routers.srs import latest_approved, load_version
from app.routers.testcases import cases_for
from app.routers.testplan import latest_plan
from app.routers.traceability import build_matrix

router = APIRouter(prefix="/api/projects/{project_id}/export", tags=["export"])

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _file(content: bytes, media_type: str, name: str) -> Response:
    return Response(content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{name}"'})


def _slug(project: Project) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", project.name).strip("-")[:40] or "project"


def _approved(db: Session, project: Project) -> SRSVersion:
    version = latest_approved(db, project)
    if version is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "There is no approved SRS to export from yet.")
    return version


@router.get("/srs.docx")
def export_srs(
    version_id: int | None = None,
    project: Project = Depends(get_project),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if version_id is not None:
        version = load_version(db, project, version_id)
    else:
        version = _approved(db, project)
    audit.record(db, user, "export", "srs", version.version_no, project.id, "DOCX")
    db.commit()
    return _file(exporter.srs_docx(version), DOCX, f"{_slug(project)}-SRS-v{version.version_no}.docx")


@router.get("/test-plan.docx")
def export_test_plan(
    project: Project = Depends(get_project), user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    plan = latest_plan(db, project)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Generate a test plan first.")
    audit.record(db, user, "export", "test_plan", plan.id, project.id, "DOCX")
    db.commit()
    content = exporter.test_plan_docx(plan, db.get(SRSVersion, plan.srs_version_id))
    return _file(content, DOCX, f"{_slug(project)}-Test-Plan.docx")


@router.get("/test-cases.csv")
def export_test_cases(
    project: Project = Depends(get_project), user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    version = _approved(db, project)
    audit.record(db, user, "export", "test_cases", version.version_no, project.id, "CSV")
    db.commit()
    return _file(exporter.test_cases_csv(cases_for(db, version)), "text/csv", f"{_slug(project)}-test-cases.csv")


@router.get("/traceability.csv")
def export_traceability(
    project: Project = Depends(get_project), user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    version = _approved(db, project)
    audit.record(db, user, "export", "traceability", version.version_no, project.id, "CSV")
    db.commit()
    return _file(exporter.traceability_csv(build_matrix(db, version)), "text/csv", f"{_slug(project)}-traceability.csv")


@router.post("/diagram-png", status_code=status.HTTP_204_NO_CONTENT)
def log_diagram_export(
    kind: Literal["use_case", "class", "sequence"],
    project: Project = Depends(get_project),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """PNGs are rendered in the browser (deviation D-4); this records the export in the audit log."""
    audit.record(db, user, "export", "diagram", kind, project.id, "PNG")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
