# Test summary report

**Project:** ReqTrace · **Test Plan:** ReqTrace-TP-01 · **Build:** Sprint 2 (`v1.0.0` candidate) · **Date:** 30 Oct 2026

## Results

| Level | Scope | Result |
|---|---|---|
| Unit / integration | 113 automated back-end tests (pytest, mock LLM) | 113 pass |
| Coverage | `backend/app` line coverage | 98% (target ≥ 70%, NFR-06) |
| Static checks | ruff, ESLint, TypeScript build, gitleaks | Clean |
| System | TC-01 to TC-50 ([TEST_LOG.md](TEST_LOG.md)) | 46 pass, 2 not run, 2 pending |
| Security | TC-33 to TC-39, live on Kubernetes with Gemini | 9/9 live checks pass; bcrypt confirmed in DB |
| Performance | TC-43: 20 users × 5 min (Locust) | p95 61 ms, 0 failures (target ≤ 2 s) |
| Data volume | TC-48: 50 projects | listed in 17–25 ms |
| Deployment | Docker Compose; Kubernetes (kind): postgres, 2 back-end replicas, front end | Running; CD smoke test on every PR |

## Against the pass criteria (TP §4.2)

| Criterion | Status |
|---|---|
| 100% of Must test cases pass | Met. Every case for FR-01–08 and FR-12 passes |
| At least 90% of Should test cases pass | Met. 100% for FR-09, FR-10, FR-11, FR-15 |
| No open Critical or High defects | Met. #28 (High) fixed |
| 100% requirement coverage in the RTM | Met for all built requirements. FR-13 and FR-14 (Could) were not built, so TC-41/42 are out of scope (TP §1.2) |

## Open items before sign-off

- **TC-44 usability:** three peers run the task in [USABILITY_TEST.md](USABILITY_TEST.md).
- **TC-46 portability:** open the app in Firefox and Edge.

## Defects

| Issue | Severity | Found by | Resolution |
|---|---|---|---|
| #28 Default Gemini model unavailable for new API keys | High | TC-11 with a real key | Fallback model list; fixed |

During development the team also found and fixed several issues before merge:
- Mermaid diagrams failed to render when drawn in parallel.
- Text labels drawn as HTML blocked PNG export.
- The kind host port clashed with a local service.
