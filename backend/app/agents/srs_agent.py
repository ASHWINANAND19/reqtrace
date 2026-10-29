"""SRS Agent: drafts an IEEE 830 SRS from raw requirements and assigns unique IDs (FR-04)."""
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agents.base import Agent, wrap_untrusted
from app.agents.mock import register_mock

# IEEE 830 sections the agent writes. 3.2 and 3.3 are built from the requirement list itself.
IEEE830_SECTIONS: list[tuple[str, str]] = [
    ("1.1", "Purpose"),
    ("1.2", "Scope"),
    ("1.3", "Definitions, Acronyms and Abbreviations"),
    ("1.4", "References"),
    ("1.5", "Overview"),
    ("2.1", "Product Perspective"),
    ("2.2", "Product Functions"),
    ("2.3", "User Classes and Characteristics"),
    ("2.4", "Operating Environment"),
    ("2.5", "Design and Implementation Constraints"),
    ("2.6", "Assumptions and Dependencies"),
    ("3.1", "External Interface Requirements"),
]
CHAPTERS = {"1": "Introduction", "2": "Overall Description", "3": "Specific Requirements"}


class RequirementDraft(BaseModel):
    type: Literal["functional", "non-functional"]
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    priority: Literal["Must", "Should", "Could"] = "Should"


class SectionDraft(BaseModel):
    number: str
    content: str


class SRSDraft(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    sections: list[SectionDraft]
    requirements: list[RequirementDraft] = Field(min_length=1)


def assign_ids(requirements: list[RequirementDraft]) -> list[dict[str, Any]]:
    """Number requirements FR-01.. and NFR-01.. so IDs are unique regardless of what the model returned."""
    counters = {"functional": 0, "non-functional": 0}
    numbered = []
    for req in requirements:
        counters[req.type] += 1
        prefix = "FR" if req.type == "functional" else "NFR"
        numbered.append({"req_id": f"{prefix}-{counters[req.type]:02d}", **req.model_dump()})
    return numbered


class SRSAgent(Agent[SRSDraft]):
    task = "srs"
    output_model = SRSDraft
    system_prompt = (
        "You are the SRS Agent of ReqTrace, a requirements engineering assistant. You write clear, testable "
        "Software Requirements Specifications that follow IEEE Std 830-1998."
    )

    def build_prompt(self, data: dict[str, Any]) -> str:
        section_list = "\n".join(f"- {num} {title}" for num, title in IEEE830_SECTIONS)
        return (
            "Write an IEEE 830 Software Requirements Specification for the system described in the data below.\n\n"
            "Return JSON with:\n"
            "- title: the system name followed by 'Software Requirements Specification'.\n"
            "- sections: one entry for EACH of these section numbers, with 'number' and 'content' (plain text, "
            "short paragraphs or '- ' bullet lists, no headings):\n"
            f"{section_list}\n"
            "- requirements: every individual requirement as its own item, with type ('functional' or "
            "'non-functional'), a short title, a description written as one testable 'The system shall ...' "
            "statement, and priority (Must, Should or Could). Split compound statements. Make non-functional "
            "requirements measurable. Do not number the requirements; the system assigns IDs.\n\n"
            f"Raw requirements:\n{wrap_untrusted(data['text'])}"
        )

    def check(self, output: SRSDraft, data: dict[str, Any]) -> None:
        written = {s.number.strip() for s in output.sections if s.content.strip()}
        missing = [num for num, _ in IEEE830_SECTIONS if num not in written]
        if missing:
            raise ValueError(f"missing or empty sections: {', '.join(missing)}")
        if not any(r.type == "functional" for r in output.requirements):
            raise ValueError("no functional requirements were produced")


# ---- Offline mock: a rule-based draft so the app works without an API key -------------------------

_NFR_HINTS = re.compile(
    r"\b(second|seconds|ms|performance|fast|secure|security|encrypt|password|availab|uptime|reliab|"
    r"usab|user-friendly|scal|concurrent|backup|response time|%)",
    re.IGNORECASE,
)


def _statements(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    cleaned = [re.sub(r"^\s*([-*•]|\d+[.)])\s*", "", p).strip() for p in parts]
    return [c.rstrip(".") for c in cleaned if len(c.split()) >= 3][:40]


_ABILITY = re.compile(
    r"^(?P<who>[\w ]{1,40}?) (?:can|may|(?:must|should|shall) be able to|are able to|is able to) (?P<what>.+)$",
    re.IGNORECASE,
)
_LEAD = re.compile(r"(?i)^(the (system|application)s? )?(shall|must|should|will) (be able to )?")


def _as_shall(statement: str) -> str:
    ability = _ABILITY.match(statement)
    if ability and not ability["who"].lower().startswith("the system"):
        return f"The system shall allow {ability['who'].lower()} to {ability['what']}."
    if re.search(r"\b(shall|must|should|will)\b", statement, re.IGNORECASE):
        return statement[0].upper() + statement[1:] + "."
    return f"The system shall {statement[0].lower() + statement[1:]}."


def _title(statement: str) -> str:
    ability = _ABILITY.match(statement)
    text = ability["what"] if ability else _LEAD.sub("", statement)
    words = re.sub(r"[^\w\s-]", "", text).split()[:5]
    return " ".join(words).capitalize() or "Requirement"


@register_mock("srs")
def mock_srs(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload["text"]
    statements = _statements(text) or ["The system shall provide the functions described by the user"]
    requirements = []
    for s in statements:
        kind = "non-functional" if _NFR_HINTS.search(s) else "functional"
        priority = "Must" if re.search(r"\b(shall|must)\b", s, re.IGNORECASE) else "Should"
        requirements.append({"type": kind, "title": _title(s), "description": _as_shall(s), "priority": priority})
    if not any(r["type"] == "functional" for r in requirements):
        requirements[0]["type"] = "functional"
    summary = "; ".join(r["title"].lower() for r in requirements[:5])
    content = {
        "1.1": "This document specifies the software requirements for the system described by the stakeholders.",
        "1.2": f"The system covers: {summary}.",
        "1.3": "- SRS: Software Requirements Specification\n- FR / NFR: Functional / Non-Functional Requirement",
        "1.4": "- IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications",
        "1.5": "Section 2 describes the product context; Section 3 lists the specific requirements.",
        "2.1": "The system is a self-contained application used through a web browser.",
        "2.2": "\n".join(f"- {r['title']}" for r in requirements if r["type"] == "functional"),
        "2.3": "- End users who perform the main tasks\n- Administrators who manage the system",
        "2.4": "Current desktop web browsers; server hosted in containers.",
        "2.5": "To be confirmed with stakeholders.",
        "2.6": "Users have network access and valid accounts.",
        "3.1": "User interface: web pages. Software interfaces: none identified in the input.",
    }
    return {
        "title": "System Software Requirements Specification",
        "sections": [{"number": n, "content": c} for n, c in content.items()],
        "requirements": requirements,
    }
