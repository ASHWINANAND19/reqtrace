import json

from app.agents.llm import get_llm
from app.agents.uml_agent import strip_fences
from tests.test_agent_base import ScriptedProvider
from tests.test_srs import generate, project_with_input
from tests.test_testcases import approved_project


def gen(client, headers, pid):
    return client.post(f"/api/projects/{pid}/diagrams/generate", headers=headers)


def test_three_diagram_types_generated(client, analyst):  # TC-27
    pid, _ = approved_project(client, analyst)
    response = gen(client, analyst, pid)
    assert response.status_code == 201, response.text
    diagrams = {d["kind"]: d["source"] for d in response.json()}
    assert diagrams["use_case"].startswith("flowchart LR")
    assert diagrams["class"].startswith("classDiagram")
    assert diagrams["sequence"].startswith("sequenceDiagram")
    assert "actorLibrarian" in diagrams["use_case"]


def test_edit_source_and_regenerate_keeps_one_per_kind(client, analyst):  # TC-28
    pid, _ = approved_project(client, analyst)
    gen(client, analyst, pid)
    new_source = "sequenceDiagram\n  actor A\n  A->>B: Hello"
    updated = client.put(f"/api/projects/{pid}/diagrams/sequence", json={"source": new_source}, headers=analyst)
    assert updated.status_code == 200 and updated.json()["source"] == new_source
    gen(client, analyst, pid)
    assert len(client.get(f"/api/projects/{pid}/diagrams", headers=analyst).json()) == 3


def test_wrong_diagram_header_is_retried(client, analyst):
    pid, _ = approved_project(client, analyst)
    bad = {
        "use_case": "graph LR\n a-->b",
        "class_diagram": "erDiagram\n A ||--o{ B : has",
        "sequence": "sequenceDiagram",
    }
    good = dict(bad, class_diagram="```mermaid\nclassDiagram\n class A\n```")
    provider = ScriptedProvider(json.dumps(bad), json.dumps(good))
    client.app.dependency_overrides[get_llm] = lambda: provider
    diagrams = {d["kind"]: d["source"] for d in gen(client, analyst, pid).json()}
    assert diagrams["class"] == "classDiagram\n class A"
    assert "Class diagram must start with classDiagram" in provider.requests[1].prompt


def test_diagrams_need_approved_srs_and_edit_needs_existing(client, analyst):
    pid = project_with_input(client, analyst)
    generate(client, analyst, pid)
    assert gen(client, analyst, pid).status_code == 409
    response = client.put(f"/api/projects/{pid}/diagrams/class", json={"source": "classDiagram"}, headers=analyst)
    assert response.status_code == 404


def test_qa_cannot_generate_diagrams(client, analyst, qa):
    pid, _ = approved_project(client, analyst)
    client.post(f"/api/projects/{pid}/members", json={"email": "qa@example.com"}, headers=analyst)
    assert gen(client, qa, pid).status_code == 403


def test_strip_fences():
    assert strip_fences("```mermaid\nclassDiagram\n```") == "classDiagram"


def test_single_line_sources_are_split_into_statements():  # bug #49
    from app.agents.uml_agent import clean_source

    gemini_class = 'classDiagram; class Book { +String title; +String isbn; }; Member "1" --> "*" Loan : has;'
    assert clean_source(gemini_class).splitlines() == [
        "classDiagram", "  class Book {", "  +String title", "  +String isbn", "  }", '  Member "1" --> "*" Loan : has'
    ]
    sequence = 'sequenceDiagram; actor Member; Member->>UI: "Search; then borrow"; UI-->>Member: "done"'
    assert clean_source(sequence).splitlines() == [
        "sequenceDiagram", "  actor Member", '  Member->>UI: "Search; then borrow"', '  UI-->>Member: "done"'
    ]
    multi_line = "classDiagram\n  class A"
    assert clean_source(multi_line) == multi_line


def test_generated_single_line_class_diagram_is_stored_multi_line(client, analyst):
    pid, _ = approved_project(client, analyst)
    one_line = {"use_case": 'flowchart LR; a{"Ok?"}-->b', "class_diagram": "classDiagram; class A { +int id; }",
                "sequence": "sequenceDiagram; A->>B: hi"}
    client.app.dependency_overrides[get_llm] = lambda: ScriptedProvider(json.dumps(one_line))
    diagrams = {d["kind"]: d["source"] for d in gen(client, analyst, pid).json()}
    assert diagrams["class"] == "classDiagram\n  class A {\n  +int id\n  }"
    assert diagrams["use_case"] == 'flowchart LR\n  a{"Ok?"}-->b'  # braces untouched outside class diagrams
