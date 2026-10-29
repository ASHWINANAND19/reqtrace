"""SRS generation, versions and approval (FR-04, FR-05)."""
import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import audit
from app.agents.base import AgentError, looks_like_injection
from app.agents.llm import LLMProvider, get_llm
from app.agents.srs_agent import IEEE830_SECTIONS, SRSAgent, assign_ids
from app.db import get_db
from app.deps import get_project, require_roles
from app.models import Project, Requirement, RequirementInput, SRSVersion, User
from app.permissions import EDIT_SRS

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects/{project_id}/srs", tags=["srs"])

SECTION_TITLES = dict(IEEE830_SECTIONS)
MAX_INPUT_CHARS = 100_000  # roughly 25 pages


class SectionOut(BaseModel):
    number: str
    title: str
    content: str


class RequirementOut(BaseModel):
    req_id: str
    type: str
    title: str
    description: str
    priority: str

    model_config = {"from_attributes": True}


class VersionSummary(BaseModel):
    id: int
    version_no: int
    title: str
    status: str
    source: str
    note: str
    author_name: str | None
    created_at: datetime
    approved_by_name: str | None
    approved_at: datetime | None
    requirement_count: int


class VersionOut(VersionSummary):
    sections: list[SectionOut]
    requirements: list[RequirementOut]


def summary(version: SRSVersion) -> VersionSummary:
    return VersionSummary(
        id=version.id,
        version_no=version.version_no,
        title=version.title,
        status=version.status,
        source=version.source,
        note=version.note,
        author_name=version.author.name if version.author else None,
        created_at=version.created_at,
        approved_by_name=version.approver.name if version.approver else None,
        approved_at=version.approved_at,
        requirement_count=len(version.requirements),
    )


def version_out(version: SRSVersion) -> VersionOut:
    return VersionOut(
        **summary(version).model_dump(),
        sections=[SectionOut(**s) for s in version.sections],
        requirements=[RequirementOut.model_validate(r) for r in version.requirements],
    )


def load_version(db: Session, project: Project, version_id: int) -> SRSVersion:
    version = db.get(SRSVersion, version_id)
    if version is None or version.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SRS version not found.")
    return version


def create_version(
    db: Session,
    project: Project,
    user: User,
    title: str,
    sections: list[dict],
    requirements: list[dict],
    source: str,
    note: str = "",
) -> SRSVersion:
    latest = db.scalar(select(func.max(SRSVersion.version_no)).where(SRSVersion.project_id == project.id)) or 0
    version = SRSVersion(
        project_id=project.id,
        version_no=latest + 1,
        title=title,
        sections=sections,
        source=source,
        note=note,
        created_by=user.id,
    )
    version.requirements = [
        Requirement(
            project_id=project.id,
            req_id=r["req_id"],
            type=r["type"],
            title=r["title"],
            description=r["description"],
            priority=r["priority"],
        )
        for r in requirements
    ]
    db.add(version)
    db.flush()
    return version


@router.post("/generate", response_model=VersionOut, status_code=status.HTTP_201_CREATED)
def generate_srs(
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*EDIT_SRS)),
    llm: LLMProvider = Depends(get_llm),
    db: Session = Depends(get_db),
) -> VersionOut:
    inputs = db.scalars(
        select(RequirementInput).where(RequirementInput.project_id == project.id).order_by(RequirementInput.id)
    ).all()
    text = "\n\n".join(i.content for i in inputs).strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Add requirements on the Input tab before generating an SRS.")
    if len(text) > MAX_INPUT_CHARS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The input is too long for one generation (about 25 pages).")
    if looks_like_injection(text):
        log.warning("project %s: input contains instruction-like text; treated as data only", project.id)

    started = time.monotonic()
    try:
        draft = SRSAgent(llm).run({"text": text})
    except AgentError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    seconds = time.monotonic() - started

    content = {s.number.strip(): s.content.strip() for s in draft.sections}
    sections = [{"number": n, "title": t, "content": content[n]} for n, t in IEEE830_SECTIONS]
    version = create_version(db, project, user, draft.title, sections, assign_ids(draft.requirements), "generated")
    audit.record(db, user, "generate", "srs", version.version_no, project.id, f"{seconds:.1f}s via {llm.name}")
    db.commit()
    return version_out(version)


@router.get("/versions", response_model=list[VersionSummary])
def list_versions(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> list[VersionSummary]:
    query = select(SRSVersion).where(SRSVersion.project_id == project.id).order_by(SRSVersion.version_no.desc())
    return [summary(v) for v in db.scalars(query)]


@router.get("/versions/{version_id}", response_model=VersionOut)
def get_version(version_id: int, project: Project = Depends(get_project), db: Session = Depends(get_db)) -> VersionOut:
    return version_out(load_version(db, project, version_id))
