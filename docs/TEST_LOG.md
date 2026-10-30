# Test execution log

Execution of the 50 test cases in the Test Plan (`ReqTrace-TP-01`, §8). Build: Sprint 2, 29–30 Oct 2026.

**Environments**
- **Unit/integration:** `pytest` in `backend/tests`, 113 tests, in-memory SQLite, mock LLM (also run by CI on every PR)
- **System:** Kubernetes (kind) deployment with PostgreSQL 15, 2 back-end replicas, nginx with TLS, real Gemini key
  (`gemini-3-flash-preview`), plus Docker Compose
- **Browser:** Chromium (Claude Code browser pane) against the local build

**Status key:** Pass · Partial (only some steps run) · Not run (stretch feature not built, or dropped by the team; see the deviation)

| TC | Req. | Title | Evidence | Result |
|---|---|---|---|---|
| TC-01 | FR-01 | Register with valid details | `test_auth::test_register_creates_account_and_user_can_log_in`; browser | Pass |
| TC-02 | FR-01 | Login with valid credentials | same test; browser lands on dashboard | Pass |
| TC-03 | FR-01 | Login with wrong password | `test_auth::test_wrong_password_is_rejected_without_session` | Pass |
| TC-04 | FR-01 | Session expiry after 60 min idle | `test_auth::test_session_expires_after_60_minutes_of_inactivity` (61 min) and `…keeps_session_alive` (59 min) | Pass |
| TC-05 | FR-02 | Create project | `test_projects::test_create_project_appears_in_list`; browser | Pass |
| TC-06 | FR-02 | Add member to project | `test_projects::test_added_member_can_see_project` | Pass |
| TC-07 | FR-02 | Empty project name | `test_projects::test_blank_project_name_rejected` | Pass |
| TC-08 | FR-03 | Submit typed requirements | `test_inputs::test_typed_text_is_stored`; browser | Pass |
| TC-09 | FR-03 | Upload supported file | `test_inputs::test_docx_upload_parsed`, `…pdf_and_txt_upload_parsed` | Pass |
| TC-10 | FR-03 | Oversize / unsupported file | `test_inputs::test_oversize_and_unsupported_files_rejected` (11 MB → 413, .exe → 415), `…exactly_10_mb…accepted` | Pass |
| TC-11 | FR-04 | Generate SRS draft | `test_srs::test_generate_srs_has_all_ieee830_sections_and_unique_ids`; real Gemini on Kubernetes: 12 sections, 7 requirements in 20 s (< 60 s) | Pass |
| TC-12 | FR-04 | Generate from empty input | `test_srs::test_generate_without_input_is_rejected` | Pass |
| TC-13 | FR-04 | IDs are unique | `test_srs::test_generate_srs_has_all_ieee830_sections_and_unique_ids` | Pass |
| TC-14 | FR-05 | Edit and save SRS | `test_srs::test_edit_creates_new_version_and_old_one_is_kept`; browser (v1 → v2) | Pass |
| TC-15 | FR-05 | View earlier version | same test; browser version picker | Pass |
| TC-16 | FR-05 | Approve SRS | `test_srs::test_analyst_approves_with_user_and_time`; browser | Pass |
| TC-17 | FR-06 | Generate test cases | `test_testcases::test_every_requirement_gets_cases_with_all_fields` | Pass |
| TC-18 | FR-06 | Tests from unapproved SRS | `test_testcases::test_generation_blocked_until_srs_approved` (409) | Pass |
| TC-19 | FR-06 | Test case types present | `test_testcases::test_positive_negative_and_boundary_types` | Pass |
| TC-20 | FR-07 | View traceability matrix | `test_traceability::test_matrix_lists_each_requirement_with_its_tests` | Pass |
| TC-21 | FR-07 | Uncovered requirement flagged | `test_traceability::test_deleting_tests_flags_requirement_and_drops_coverage` | Pass |
| TC-22 | FR-07 | Coverage calculation | same test compares with manual count | Pass |
| TC-23 | FR-08 | Export SRS to DOCX | `test_export::test_srs_docx_matches_screen` (file reopened with python-docx) | Pass |
| TC-24 | FR-08 | Export test cases to CSV | `test_export::test_test_cases_csv_has_all_rows_and_columns` | Pass |
| TC-25 | FR-08 | Export diagram PNG | Browser: valid PNG (signature checked, 67 KB) downloaded for the class diagram | Pass |
| TC-26 | FR-09 | Generate test plan | `test_testplan::test_generated_plan_has_all_sections_and_references_ids` | Pass |
| TC-27 | FR-10 | Generate UML diagrams | `test_diagrams::test_three_diagram_types_generated`; browser renders all three | Pass |
| TC-28 | FR-10 | Edit diagram source and re-render | `test_diagrams::test_edit_source_and_regenerate_keeps_one_per_kind` | Pass |
| TC-29 | FR-11 | Ambiguity flagged | `test_quality::test_fast_and_user_friendly_flagged_with_rewrite` | Pass |
| TC-30 | FR-11 | Missing section detected | `test_quality::test_missing_section_reported` | Pass |
| TC-31 | FR-12 | QA cannot approve SRS | `test_srs::test_qa_cannot_approve` (403); Approve button hidden for QA | Pass |
| TC-32 | FR-12 | Admin manages users | `test_admin::test_admin_changes_role_and_it_takes_effect` | Pass |
| TC-33 | SEC-01 | Password stored hashed | `test_auth::test_password_stored_as_bcrypt_hash`; Kubernetes DB: 6 of 6 `password_hash` values are `$2b$` bcrypt | Pass |
| TC-34 | SEC-02 | Token expiry and logout | `test_auth::test_token_rejected_after_logout`, `…tampered_or_missing_token_rejected`; live check (401) | Pass |
| TC-35 | SEC-03 | Direct API call without permission | live: QA calling approve API → 403; non-admin on admin API → 403 | Pass |
| TC-36 | SEC-04 | Injection in input fields | `test_inputs::test_injection_payloads_stored_as_plain_data`; live check; CSV formula injection neutralised | Pass |
| TC-37 | SEC-05 | No secrets in repository | gitleaks: 0 leaks in full history (local); runs on every PR in CI | Pass |
| TC-38 | SEC-06 | Prompt injection resistance | `test_srs::test_prompt_contains_only_this_projects_input`; live with Gemini: no other project's data returned | Pass |
| TC-39 | SEC-07 | Cross-project access and TLS | live: non-member → 403; connection negotiated TLSv1.3; HTTP redirects to HTTPS (301) | Pass |
| TC-40 | FR-15 | Audit entries created | `test_admin::test_edit_approve_export_create_audit_entries` | Pass |
| TC-41 | FR-13 | Architecture suggestion | FR-13 not implemented (Could, deviation D-3) | Not run |
| TC-42 | FR-14 | GitHub issue creation | FR-14 not implemented (Could, deviation D-3) | Not run |
| TC-43 | NFR-01 | Response time under load | Locust, 20 users, 5 min on Kubernetes: 3,036 requests, 0 failures, p95 61 ms (target ≤ 2,000 ms) | Pass |
| TC-44 | NFR-02 | First-time usability | Peer usability session dropped by the team (deviation D-14); the planned task card is in [USABILITY_TEST.md](USABILITY_TEST.md) | Not run |
| TC-45 | NFR-03 | LLM service unavailable | `test_srs::test_llm_outage_gives_friendly_503_and_keeps_input`, `test_agent_base::test_unavailable_provider…` | Pass |
| TC-46 | NFR-05 | Docker one-command deployment | `docker compose up --build` on the development Mac serves https://localhost in Chromium. Clean-machine run and Firefox/Edge not done (deviation D-14) | Partial |
| TC-47 | NFR-06 | Coverage and lint in CI | ruff and ESLint pass; back-end coverage 98% (≥ 70%); CI workflow runs on every PR | Pass |
| TC-48 | NFR-07 | Data volume | `test_projects::test_fifty_projects_listed`; Kubernetes: 50 projects listed in 17–25 ms (target ≤ 2 s) | Pass |
| TC-49 | NFR-08 | Retry on partial LLM response | `test_agent_base::test_malformed_output_is_retried_with_stricter_prompt`, `test_srs::test_malformed_output_retried_then_saved` | Pass |
| TC-50 | FR-03/04 | End-to-end smoke | Browser flow login → project → input → SRS → export; CD smoke test on Kubernetes | Pass |

## TC-43 load test (NFR-01)

Run: `locust -f loadtest/locustfile.py --headless -u 20 -r 5 -t 5m --host https://localhost:8443` against the
Kubernetes deployment (2 back-end replicas). LLM generation is excluded, as NFR-01 states. Full report:
[`loadtest/results/tc43.html`](../loadtest/results/tc43.html).

| Request | Count | Failures | Median (ms) | p95 (ms) | p99 (ms) | Max (ms) |
|---|---|---|---|---|---|---|
| GET `/api/projects` (dashboard) | 849 | 0 | 16 | 48 | 310 | 687 |
| GET `/api/projects/[id]` | 603 | 0 | 16 | 65 | 420 | 756 |
| GET `/api/projects/[id]/inputs` | 599 | 0 | 15 | 41 | 210 | 803 |
| GET `/api/projects/[id]/srs/versions` | 316 | 0 | 17 | 47 | 260 | 456 |
| GET `/api/projects/[id]/traceability` | 315 | 0 | 16 | 46 | 290 | 518 |
| GET `/` (single-page app) | 274 | 0 | 3 | 10 | 55 | 218 |
| POST `/api/auth/login` (bcrypt) | 20 | 0 | 330 | 430 | 430 | 428 |
| **All requests** | **3,036** | **0** | **15** | **61** | **380** | **803** |

Result: **Pass**. p95 is 61 ms, well under the 2 s limit, at about 10 requests per second.

## Defects

| Issue | Found by | Severity | Status |
|---|---|---|---|
| #28 Default Gemini model unavailable for new API keys | TC-11 with a real key | High | Fixed |
