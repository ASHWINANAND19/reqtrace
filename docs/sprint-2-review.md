# Sprint 2 review

**Sprint goal:** from an approved SRS, generate test cases, a test plan and UML diagrams; show the
traceability matrix and ambiguity flags; export everything; let admins manage roles and read the audit
log. Publish images to Docker Hub and run the app on Kubernetes. Complete testing, documentation and
the release.

**Planned:** 26–30 Oct 2026. **Executed:** 29–30 Oct 2026 (deviation D-1).

## Completed stories

| Story | Owner | Points | Requirements | Tests |
|---|---|---|---|---|
| PB-13 Test case agent | Ashwin | 5 | FR-06 | TC-17–19 |
| PB-14 Traceability matrix | Abhinav | 3 | FR-07 | TC-20–22 |
| PB-15 Ambiguity and completeness check | Abhinav | 3 | FR-11 | TC-29, TC-30 |
| PB-16 Test plan agent | Abhinav | 3 | FR-09 | TC-26 |
| PB-17 UML agent | Ashwin | 5 | FR-10 | TC-27, TC-28 |
| PB-18 Export DOCX / CSV / PNG | Abhay | 3 | FR-08 | TC-23–25 |
| PB-19 Audit log and admin page | Abhay | 3 | FR-15, FR-12 | TC-32, TC-40 |
| PB-20 Docker Hub publishing | Abhishek | 2 | NFR-05 | – |
| PB-21 Kubernetes deployment and CD smoke test | Abhishek | 5 | NFR-05, NFR-07 | TC-48 |
| PB-22 Security and load testing | Ashwin | 3 | NFR-01, NFR-04 | TC-33–39, TC-43 |
| PB-23 Test execution log and usability checklist | Abhay | 2 | NFR-02 | TC-01–50 |
| PB-24 Documentation | Abhishek | 3 | SRS 3.5 | – |
| PB-25 Sprint review, video, v1.0.0 | Abhishek | 1 | – | TC-50 |
| #28 Gemini model fallback (bug) | Ashwin | – | NFR-03 | TC-11, TC-45 |

**Velocity:** 41 of 41 planned points. Total across both sprints: 85 points. PB-26 and PB-27 (Could)
remain in the product backlog.

## Demo highlights

- Full flow on Kubernetes with the real Gemini key: input → SRS (20 s) → quality check → approve →
  test cases → 100% traceability → test plan → UML diagrams → DOCX/CSV/PNG exports
- Admin page: role change and audit log entries for every generate, edit, approve and export
- DevOps pipeline:
  - Every PR runs CI (lint, 113 tests, 98% coverage, build, secret scan) and PR automation.
  - Every PR is also deployed to a throwaway Kubernetes cluster and smoke-tested.
  - Merges to `main` publish images to Docker Hub and deploy them.

## Quality

See [TEST_SUMMARY.md](TEST_SUMMARY.md):
- 46 of 50 test cases pass. TC-41 and TC-42 are stretch features not built.
- TC-44 (usability) was not run and TC-46 (portability) was run only in part (deviation D-14).
- p95 is 61 ms under 20 users.
- 9 of 9 live security checks pass.

## Demo video

`videos/sprint-2.mp4` (two minutes).

## Deviations

See [DEVIATIONS.md](DEVIATIONS.md), D-1 to D-14.
