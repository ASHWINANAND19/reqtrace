"""Ambiguity and completeness check (FR-11): rule-based vague-word and missing-section checks, plus an
LLM agent that looks for conflicting requirements."""
import re
from typing import Any

from pydantic import BaseModel, Field

from app.agents.base import Agent, wrap_untrusted
from app.agents.mock import register_mock

# vague term -> (why it is a problem, measurable replacement used in the suggested rewrite)
VAGUE_TERMS: dict[str, tuple[str, str]] = {
    "fast": ("'fast' is not measurable", "within 2 seconds for 95% of requests"),
    "quickly": ("'quickly' is not measurable", "within 2 seconds"),
    "quick": ("'quick' is not measurable", "completed within 2 seconds"),
    "user-friendly": (
        "'user-friendly' cannot be tested",
        "usable by a first-time user without training within 10 minutes",
    ),
    "easy": ("'easy' is subjective", "possible in at most 3 steps"),
    "easily": ("'easily' is subjective", "in at most 3 steps"),
    "simple": ("'simple' is subjective", "possible in at most 3 steps"),
    "intuitive": ("'intuitive' cannot be tested", "usable without training by 9 of 10 first-time users"),
    "efficient": ("'efficient' has no threshold", "using at most <N> MB of memory and <N>% CPU"),
    "flexible": ("'flexible' has no acceptance criterion", "configurable through <named settings>"),
    "robust": ("'robust' has no acceptance criterion", "recovering from <named failure> without data loss"),
    "seamless": ("'seamless' cannot be tested", "without the user re-entering data"),
    "adequate": ("'adequate' is undefined", "at least <specified value>"),
    "sufficient": ("'sufficient' is undefined", "at least <specified value>"),
    "several": ("'several' is an unspecified quantity", "<exact number>"),
    "many": ("'many' is an unspecified quantity", "at least <exact number>"),
    "approximately": ("'approximately' gives no tolerance", "within ±<tolerance> of"),
    "as appropriate": ("'as appropriate' leaves the behaviour undefined", "<state the exact condition>"),
    "if possible": ("'if possible' makes the requirement optional", ""),
    "etc": ("'etc.' leaves the list open", "<complete list>"),
    "and/or": ("'and/or' is ambiguous", "<choose 'and' or 'or'>"),
    "tbd": ("'TBD' marks an unfinished requirement", "<decided value>"),
}
_VAGUE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(t) for t in VAGUE_TERMS) + r")(?![\w-])", re.IGNORECASE)


class Flag(BaseModel):
    kind: str  # vague | missing | conflict
    location: str
    text: str
    reason: str
    suggestion: str


def vague_flags(location: str, text: str) -> list[Flag]:
    flags = []
    for term in dict.fromkeys(m.group(1).lower() for m in _VAGUE.finditer(text)):
        reason, replacement = VAGUE_TERMS[term]
        pattern = re.compile(r"(?<![\w-])" + re.escape(term) + r"\.?(?![\w-])", re.IGNORECASE)
        rewrite = re.sub(r"\s{2,}", " ", pattern.sub(replacement, text, count=1)).strip()
        flags.append(Flag(kind="vague", location=location, text=term, reason=reason, suggestion=rewrite))
    return flags


def missing_flags(sections: list[dict[str, Any]], requirements: list[dict[str, Any]]) -> list[Flag]:
    flags = [
        Flag(
            kind="missing",
            location=f"{s['number']} {s['title']}",
            text="",
            reason="Mandatory IEEE 830 section is empty or missing",
            suggestion=f"Write the {s['title']} section.",
        )
        for s in sections
        if not s["content"].strip()
    ]
    chapters = (("functional", "3.2 Functional Requirements"), ("non-functional", "3.3 Non-Functional Requirements"))
    for kind, label in chapters:
        if not any(r["type"] == kind for r in requirements):
            flags.append(Flag(kind="missing", location=label, text="", reason="No requirements in this section",
                              suggestion=f"Add at least one {kind} requirement."))
    return flags


class Conflict(BaseModel):
    requirement_ids: list[str] = Field(min_length=2)
    reason: str
    suggestion: str


class ConflictReport(BaseModel):
    conflicts: list[Conflict]


class ConflictAgent(Agent[ConflictReport]):
    task = "conflicts"
    output_model = ConflictReport
    system_prompt = "You are the quality reviewer of ReqTrace. You find requirements that contradict each other."

    def build_prompt(self, data: dict[str, Any]) -> str:
        lines = "\n".join(f"{r['req_id']}: {r['description']}" for r in data["requirements"])
        return (
            "List pairs or groups of requirements in the data below that contradict each other (they cannot all be "
            "satisfied at once). For each give requirement_ids, the reason, and a suggestion to resolve it. "
            "Return an empty list if there are none. Do not report vague wording or missing details.\n\n"
            f"Requirements:\n{wrap_untrusted(lines)}"
        )

    def check(self, output: ConflictReport, data: dict[str, Any]) -> None:
        known = {r["req_id"] for r in data["requirements"]}
        for conflict in output.conflicts:
            unknown = [i for i in conflict.requirement_ids if i not in known]
            if unknown:
                raise ValueError(f"unknown requirement IDs in conflicts: {', '.join(unknown)}")


# ---- Offline mock: same subject with 'shall' and 'shall not' ------------------------------------------

_STOP = {"the", "system", "shall", "not", "a", "an", "to", "of", "and", "or", "be", "by", "in", "for", "with", "allow"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP and len(w) > 2}


@register_mock("conflicts")
def mock_conflicts(payload: dict[str, Any]) -> dict[str, Any]:
    reqs = payload["requirements"]
    conflicts = []
    for i, a in enumerate(reqs):
        for b in reqs[i + 1 :]:
            negated = ("not" in a["description"].lower().split()) != ("not" in b["description"].lower().split())
            if negated and len(_words(a["description"]) & _words(b["description"])) >= 2:
                conflicts.append({
                    "requirement_ids": [a["req_id"], b["req_id"]],
                    "reason": "One requirement allows what the other forbids for the same subject.",
                    "suggestion": "Decide which behaviour is intended and state the condition that separates them.",
                })
    return {"conflicts": conflicts}
