"""UML diagram generation and editing (FR-10)."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import audit
from app.agents.base import AgentError
from app.agents.llm import LLMProvider, get_llm
from app.agents.uml_agent import DIAGRAM_KINDS, UMLAgent, clean_source
from app.db import get_db, utcnow
from app.deps import get_project, require_roles
from app.models import Diagram, Project, SRSVersion, User
from app.permissions import GENERATE_DIAGRAMS
from app.routers.srs import require_approved

router = APIRouter(prefix="/api/projects/{project_id}/diagrams", tags=["diagrams"])

Kind = Literal["use_case", "class", "sequence"]


class DiagramOut(BaseModel):
    kind: str
    title: str
    source: str
    srs_version_no: int
    updated_at: datetime


class DiagramIn(BaseModel):
    source: str = Field(min_length=1, max_length=50_000)


def diagram_out(db: Session, d: Diagram) -> DiagramOut:
    return DiagramOut(
        kind=d.kind,
        title=DIAGRAM_KINDS[d.kind][0],
        source=d.source,
        srs_version_no=db.get(SRSVersion, d.srs_version_id).version_no,
        updated_at=d.updated_at,
    )


def list_for(db: Session, project: Project) -> list[Diagram]:
    order = {kind: i for i, kind in enumerate(DIAGRAM_KINDS)}
    return sorted(db.scalars(select(Diagram).where(Diagram.project_id == project.id)), key=lambda d: order[d.kind])


@router.get("", response_model=list[DiagramOut])
def list_diagrams(project: Project = Depends(get_project), db: Session = Depends(get_db)) -> list[DiagramOut]:
    return [diagram_out(db, d) for d in list_for(db, project)]


@router.post("/generate", response_model=list[DiagramOut], status_code=status.HTTP_201_CREATED)
def generate_diagrams(
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*GENERATE_DIAGRAMS)),
    llm: LLMProvider = Depends(get_llm),
    db: Session = Depends(get_db),
) -> list[DiagramOut]:
    version = require_approved(db, project)
    requirements = [{"req_id": r.req_id, "title": r.title, "description": r.description} for r in version.requirements]
    try:
        draft = UMLAgent(llm).run({"title": version.title, "requirements": requirements})
    except AgentError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    existing = {d.kind: d for d in list_for(db, project)}
    for kind, source in draft.by_kind().items():
        diagram = existing.get(kind) or Diagram(project_id=project.id, kind=kind)
        diagram.srs_version_id = version.id
        diagram.source = clean_source(source)
        diagram.updated_at = utcnow()
        db.add(diagram)
    audit.record(db, user, "generate", "diagrams", version.version_no, project.id)
    db.commit()
    return [diagram_out(db, d) for d in list_for(db, project)]


@router.put("/{kind}", response_model=DiagramOut)
def update_diagram(
    kind: Kind,
    body: DiagramIn,
    project: Project = Depends(get_project),
    user: User = Depends(require_roles(*GENERATE_DIAGRAMS)),
    db: Session = Depends(get_db),
) -> DiagramOut:
    diagram = db.scalar(select(Diagram).where(Diagram.project_id == project.id, Diagram.kind == kind))
    if diagram is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Generate the diagrams first.")
    diagram.source = body.source.strip()
    diagram.updated_at = utcnow()
    audit.record(db, user, "edit", "diagram", kind, project.id)
    db.commit()
    return diagram_out(db, diagram)
