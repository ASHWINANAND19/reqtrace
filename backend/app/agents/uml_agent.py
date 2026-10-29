"""UML Agent: use-case, class and sequence diagrams as Mermaid source (FR-10)."""
import re
from typing import Any

from pydantic import BaseModel

from app.agents.base import Agent, wrap_untrusted
from app.agents.mock import register_mock

# kind -> (title, Mermaid header the source must start with)
DIAGRAM_KINDS = {
    "use_case": ("Use-case diagram", ("flowchart", "graph")),
    "class": ("Class diagram", ("classDiagram",)),
    "sequence": ("Sequence diagram", ("sequenceDiagram",)),
}


class UMLDraft(BaseModel):
    use_case: str
    class_diagram: str
    sequence: str

    def by_kind(self) -> dict[str, str]:
        return {"use_case": self.use_case, "class": self.class_diagram, "sequence": self.sequence}


def strip_fences(source: str) -> str:
    source = source.strip()
    source = re.sub(r"^```(?:mermaid)?\s*", "", source)
    return re.sub(r"\s*```$", "", source).strip()


class UMLAgent(Agent[UMLDraft]):
    task = "uml"
    output_model = UMLDraft
    system_prompt = "You are the UML Agent of ReqTrace. You produce correct, minimal Mermaid 11 diagrams."

    def build_prompt(self, data: dict[str, Any]) -> str:
        lines = "\n".join(f"{r['req_id']}: {r['description']}" for r in data["requirements"])
        return (
            f"Create three UML diagrams for the system '{data['title']}' from the requirements in the data below.\n"
            "Return JSON with three Mermaid sources (no code fences, no styling, no comments):\n"
            "- use_case: a 'flowchart LR' use-case diagram. Actors are nodes like actorAnalyst((Analyst)); use cases "
            "are nodes like uc1([\"Generate SRS\"]) inside one subgraph named after the system; edges actor --> "
            "use case. Cover every functional requirement.\n"
            "- class_diagram: a 'classDiagram' of the main domain classes with key attributes, methods and "
            "relationships with multiplicities.\n"
            "- sequence: a 'sequenceDiagram' of the most important user flow, with actor, UI, API and database "
            "participants.\n"
            "Always wrap labels that contain spaces or punctuation in double quotes.\n\n"
            f"Requirements:\n{wrap_untrusted(lines)}"
        )

    def check(self, output: UMLDraft, data: dict[str, Any]) -> None:
        for kind, source in output.by_kind().items():
            title, headers = DIAGRAM_KINDS[kind]
            if not strip_fences(source).startswith(headers):
                raise ValueError(f"{title} must start with {' or '.join(headers)}")


# ---- Offline mock -----------------------------------------------------------------------------------

def _label(text: str) -> str:
    return re.sub(r"[^\w\s-]", "", text).strip()[:40] or "Use case"


def _actors(requirements: list[dict[str, Any]]) -> list[str]:
    found = []
    for r in requirements:
        match = re.search(r"allow (\w+)", r["description"], re.IGNORECASE)
        if match:
            found.append(match.group(1).rstrip("s").capitalize())
    return list(dict.fromkeys(found)) or ["User"]


@register_mock("uml")
def mock_uml(payload: dict[str, Any]) -> dict[str, Any]:
    reqs = [r for r in payload["requirements"] if r["req_id"].startswith("FR")] or payload["requirements"]
    actors = _actors(reqs)
    system = _label(payload["title"].replace("Software Requirements Specification", "")) or "System"
    use_case = ["flowchart LR"]
    use_case += [f"  actor{a}(({a}))" for a in actors]
    use_case.append(f'  subgraph sys["{system}"]')
    use_case += [f'    uc{i}(["{_label(r["title"])}"])' for i, r in enumerate(reqs, 1)]
    use_case.append("  end")
    for i, r in enumerate(reqs, 1):
        match = re.search(r"allow (\w+)", r["description"], re.IGNORECASE)
        actor = match.group(1).rstrip("s").capitalize() if match else actors[0]
        use_case.append(f"  actor{actor} --> uc{i}")

    operations = [re.sub(r"\W", "", _label(r["title"]).title()) for r in reqs[:6]]
    class_diagram = ["classDiagram"]
    for a in actors:
        class_diagram += [f"  class {a} {{", "    +int id", "    +string name", "  }"]
    class_diagram += ["  class System {"] + [f"    +{op[0].lower() + op[1:]}()" for op in operations if op] + ["  }"]
    class_diagram += [f'  {a} "1" --> "*" System : uses' for a in actors]

    first = _label(reqs[0]["title"]) if reqs else "Request"
    sequence = [
        "sequenceDiagram",
        f"  actor U as {actors[0]}",
        "  participant UI as Web UI",
        "  participant API as Back end",
        "  participant DB as Database",
        f"  U->>UI: {first}",
        "  UI->>API: HTTPS request",
        "  API->>DB: Read or write data",
        "  DB-->>API: Result",
        "  API-->>UI: JSON response",
        "  UI-->>U: Show result",
    ]
    return {"use_case": "\n".join(use_case), "class_diagram": "\n".join(class_diagram), "sequence": "\n".join(sequence)}
