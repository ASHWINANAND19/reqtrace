# Sprint 1 review

**Sprint goal:** an analyst can log in, create a project, submit requirements (text or file),
generate an IEEE 830 SRS with Gemini, then edit, version and approve it. Runs with
`docker compose up`; CI runs on every pull request.

**Planned:** 19–23 Oct 2026. **Executed:** 29 Oct 2026 (deviation D-1).

## Completed stories

| Story | Owner | Points | Requirements | Tests |
|---|---|---|---|---|
| PB-1 Repository scaffold, PR template, branch protection | Abhishek | 1 | – | – |
| PB-2 CI pipeline: lint, tests, coverage, build, secret scan | Abhishek | 3 | NFR-06, SEC-05 | TC-37, TC-47 |
| PB-3 Dockerfiles and Docker Compose | Abhishek | 3 | NFR-05 | TC-46 |
| PB-4 Registration, login, logout (bcrypt, JWT) | Abhinav | 5 | FR-01, SEC-01, SEC-02 | TC-01–04, TC-33, TC-34 |
| PB-5 Role-based access control | Abhinav | 3 | FR-12, SEC-03 | TC-35 |
| PB-6 Projects and members | Abhinav | 5 | FR-02, SEC-07 | TC-05–07, TC-39, TC-48 |
| PB-7 Front-end shell | Abhay | 5 | NFR-02 | TC-02, TC-05 |
| PB-8 Requirements input (text, TXT/DOCX/PDF) | Abhay | 3 | FR-03, SEC-04 | TC-08–10, TC-36 |
| PB-9 LLM adapter, retries, prompt-injection guard | Ashwin | 5 | NFR-03, NFR-08, SEC-06 | TC-38, TC-45, TC-49 |
| PB-10 SRS agent (IEEE 830, unique IDs) | Ashwin | 5 | FR-04 | TC-11–13 |
| PB-11 SRS editor, versions, compare, approve | Abhay | 5 | FR-05 | TC-14–16, TC-31 |
| PB-12 Sprint review and video | Abhishek | 1 | – | TC-50 |

**Velocity:** 44 of 44 planned points.

## Quality

- 69 automated back-end tests, 98% line coverage (target 70%, NFR-06)
- Front-end lint and type-checked build pass
- gitleaks: no secrets in history (TC-37)
- End-to-end check in the browser: register → create project → add input → generate SRS → edit
  (v2) → compare v1/v2 → approve
- Real Gemini run: 6-sentence input → 12 IEEE 830 sections, 9 requirements in 12.5 s (TC-11)

## Defects found

| Issue | Severity | Status |
|---|---|---|
| #28 Default Gemini model unavailable for new API keys | High | Fixed (fallback model list) |

## Demo video

`videos/sprint-1.mp4` (one minute).

## Deviations

See [DEVIATIONS.md](DEVIATIONS.md): D-1, D-5 to D-11 apply to this sprint.
