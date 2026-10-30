from tests.test_projects import create
from tests.test_testcases import approved_project, gen_tests


def matrix(client, headers, pid):
    return client.get(f"/api/projects/{pid}/traceability", headers=headers).json()


def test_matrix_lists_each_requirement_with_its_tests(client, analyst):  # TC-20
    pid, srs = approved_project(client, analyst)
    cases = gen_tests(client, analyst, pid).json()["test_cases"]
    m = matrix(client, analyst, pid)
    assert [r["req_id"] for r in m["rows"]] == [r["req_id"] for r in srs["requirements"]]
    fr01 = next(r for r in m["rows"] if r["req_id"] == "FR-01")
    assert fr01["test_cases"] == sorted(tc["tc_id"] for tc in cases if "FR-01" in tc["requirement_ids"])
    assert m["coverage_percent"] == 100.0 and m["uncovered"] == []


def test_deleting_tests_flags_requirement_and_drops_coverage(client, analyst):  # TC-21, TC-22
    pid, srs = approved_project(client, analyst)
    cases = gen_tests(client, analyst, pid).json()["test_cases"]
    for tc in cases:
        if tc["requirement_ids"] == ["FR-02"]:
            client.delete(f"/api/projects/{pid}/tests/{tc['id']}", headers=analyst)
    m = matrix(client, analyst, pid)
    total = len(srs["requirements"])
    assert m["uncovered"] == ["FR-02"]
    assert m["covered"] == total - 1
    assert m["coverage_percent"] == round(100 * (total - 1) / total, 1)
    assert next(r for r in m["rows"] if r["req_id"] == "FR-02")["covered"] is False


def test_no_tests_means_zero_coverage(client, analyst):
    pid, srs = approved_project(client, analyst)
    m = matrix(client, analyst, pid)
    assert m["coverage_percent"] == 0.0 and len(m["uncovered"]) == len(srs["requirements"])


def test_no_approved_srs(client, analyst):
    pid = create(client, analyst)["id"]
    assert matrix(client, analyst, pid)["srs_version"] is None
