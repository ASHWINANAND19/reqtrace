# ReqTrace — Build & Sprint Plan (Part 2)

Working plan for building ReqTrace and meeting the Part 2 deliverables plus the professor's note
(product backlog, sprint backlog for two sprints, execute sprints, demo, and **all DevOps tools: Git,
GitHub, GitHub Actions, Docker, Docker Hub, Kubernetes**).

Source of truth for *what* to build: `ReqTrace_Part1_Deliverables.docx` (SRS, Test Plan, SAD).
Anything we do differently goes into `docs/DEVIATIONS.md` and is explained in the final demo.

---

## 1. Situation and ground rules

- **Now:** Thu 29 Oct 2026, ~19:45 IST. Nothing built yet. Deadline: **Fri 30 Oct 2026**.
- The original calendar (backlog 12 Oct, Sprint 1 19–23 Oct, Sprint 2 26–30 Oct) has passed. We run
  both sprints **compressed into 29–30 Oct**. We do **not** backdate commits, issues or PRs — GitHub
  timestamps stay real, and the compressed schedule is recorded as deviation D-1.
- Scope: all **Must** (FR-01–08, FR-12) and **Should** (FR-09–11, FR-15) requirements, NFR-01–08,
  SEC-01–07. **Could** items FR-13 and FR-14 stay in the product backlog, unscheduled (allowed by
  SRS §2.7).
- LLM: **Google Gemini (free tier)** behind the adapter interface (SAD AD-2). A **mock provider** is
  used in automated tests and CI so they never need a key or hit quota.

## 2. Timeline

| When (IST) | Phase | Outcome |
|---|---|---|
| Thu 29 Oct, 19:45–21:00 | **Phase 0 – Setup** | Repo, Project board, labels, milestones, full backlog as issues with points + assignees, CI, Docker skeleton |
| Thu 29 Oct 21:00 → Fri 30 Oct ~11:00 | **Sprint 1** | Login → project → submit requirements → generate SRS → edit/version/approve, in Docker Compose, CI green. **1-min video** |
| Fri 30 Oct ~11:00–17:00 | **Sprint 2** | Tests, test plan, UML, traceability, ambiguity, export, audit/admin; Docker Hub + Kubernetes; security & load tests |
| Fri 30 Oct ~17:00–19:00 | **Wrap-up** | Docs, test summary, deviations, **2-min video**, tag `v1.0.0` (freeze), demo dry-run |

## 3. Technical decisions (follow the SAD; my calls where the SAD is silent)

| Area | Choice |
|---|---|
| Back end | Python 3.11, FastAPI, SQLAlchemy 2, Pydantic v2 |
| Auth | bcrypt (SEC-01), PyJWT with 60-min expiry + server-side revocation list on logout (SEC-02) |
| DB | PostgreSQL 15 (Compose and Kubernetes); SQLite in unit tests for speed |
| Agents | Custom orchestrator + abstract `Agent.run(input)`; SRS, TestCase, TestPlan, UML agents; JSON output validated against a schema, retried up to 2× (NFR-08) |
| LLM | `LLMProvider` interface → `GeminiProvider` (`google-genai` SDK, model name from env) and `MockProvider` |
| Prompt safety | User text wrapped in delimiters as data only; output schema validation; only the current project's data in a prompt (SEC-06) |
| File parsing | `python-docx` (DOCX), `pypdf` (PDF), plain read (TXT); type + size (10 MB) checks (FR-03, SEC-04) |
| Front end | React + Vite + TypeScript, Mantine component library, React Router |
| Diagrams | Mermaid source from the UML agent, rendered in the browser; PNG export from the rendered SVG |
| Export | `python-docx` for SRS/test plan DOCX, `csv` for test cases and RTM |
| Quality | `ruff` (lint), `pytest` + `pytest-cov` (≥70% on core modules), ESLint for the front end |
| Serving | nginx serves the built SPA and proxies `/api` to the back end |

### Repository layout

```
reqtrace/
├── backend/            FastAPI app: auth, projects, inputs, srs, agents, trace, export, audit
│   ├── app/
│   └── tests/
├── frontend/           React SPA
├── docker-compose.yml  one-command start at the repo root
├── deploy/
│   └── k8s/            namespace, postgres, backend, frontend, configmap, secret template
├── loadtest/           locustfile.py (NFR-01)
├── docs/               PLAN, DEVIATIONS, USER_GUIDE, TEST_LOG, TEST_SUMMARY, sprint reviews
├── videos/             sprint-1.mp4, sprint-2.mp4
└── .github/
    ├── workflows/      ci.yml, cd.yml
    └── pull_request_template.md
```

## 4. How each DevOps tool is used

| Tool | Use |
|---|---|
| **Git** | One branch per story (`feat/<issue#>-<slug>`), conventional commits, `Closes #N` in commit/PR |
| **GitHub** | Repo, Issues = backlog, **Projects** board (Backlog → Sprint → In Progress → In Review → Done) with *Story Points* and *Sprint* fields, milestones *Sprint 1* / *Sprint 2*, PRs with review, branch protection on `main` (PR + 1 approval + green CI) |
| **GitHub Actions** | `ci.yml` on every PR and push: ruff, pytest with coverage report, front-end lint + build, gitleaks secret scan (SEC-05, TC-37). `cd.yml` on merge to `main`: build images → push to Docker Hub → spin up a **kind** Kubernetes cluster in the runner → apply manifests → smoke-test `/api/health` |
| **Docker** | Multi-stage Dockerfiles for back end and front end (nginx); `docker compose up` runs everything with one command (NFR-05, TC-46) |
| **Docker Hub** | `<dockerhub-user>/reqtrace-backend` and `reqtrace-frontend`, tagged with the git SHA and `latest` |
| **Kubernetes** | Manifests in `deploy/k8s/`; demo cluster is **kind** on your Mac pulling images from Docker Hub; back end runs 2 replicas to show independent scaling (NFR-07) |

## 5. Product backlog

Story points use Fibonacci (1, 2, 3, 5, 8). Owners follow SRS Appendix B roles. Ashwin is the Scrum Master.

| PB | Story | Requirements | Test cases | Pts | Owner | Sprint |
|---|---|---|---|---|---|---|
| 1 | Repo scaffold, PR template, branch protection | – | – | 1 | Abhishek | 1 |
| 2 | CI pipeline: lint, tests + coverage, front-end build, secret scan | NFR-06, SEC-05 | TC-37, TC-47 | 3 | Abhishek | 1 |
| 3 | Dockerfiles + Docker Compose, one-command start | NFR-05 | TC-46 | 3 | Abhishek | 1 |
| 4 | Register / login / logout with bcrypt + JWT, 60-min expiry | FR-01, SEC-01, SEC-02 | TC-01–04, 33, 34 | 5 | Abhinav | 1 |
| 5 | Role-based access control, server-side 403 | FR-12, SEC-03 | TC-31, 35 | 3 | Abhinav | 1 |
| 6 | Projects: create, rename, archive, delete, members; member-only access | FR-02, SEC-07 | TC-05–07, 39 | 5 | Abhinav | 1 |
| 7 | Front-end shell: login, register, dashboard, project page | NFR-02 | TC-02, 05 | 5 | Abhay | 1 |
| 8 | Requirements input: text + TXT/DOCX/PDF ≤ 10 MB, validation | FR-03, SEC-04 | TC-08–10, 36 | 3 | Abhay | 1 |
| 9 | LLM adapter (Gemini + mock), 2× retry, friendly failure, prompt-injection guard | NFR-03, NFR-08, SEC-06 | TC-38, 45, 49 | 5 | Ashwin | 1 |
| 10 | SRS agent: IEEE 830 draft with unique FR/NFR IDs | FR-04 | TC-11–13, 50 | 5 | Ashwin | 1 |
| 11 | SRS editor, version history, compare, approve | FR-05 | TC-14–16 | 5 | Abhay | 1 |
| 12 | Sprint 1 review: 1-min video + sprint notes | – | TC-50 | 1 | Abhishek | 1 |
| 13 | Test case agent: positive / negative / boundary per requirement, approval gate | FR-06 | TC-17–19 | 5 | Ashwin | 2 |
| 14 | Traceability matrix, coverage %, uncovered highlighted | FR-07 | TC-20–22 | 3 | Abhinav | 2 |
| 15 | Ambiguity and completeness check with suggested rewrites | FR-11 | TC-29, 30 | 3 | Abhinav | 2 |
| 16 | Test plan agent | FR-09 | TC-26 | 3 | Abhinav | 2 |
| 17 | UML agent: use-case, class, sequence (Mermaid), edit + re-render | FR-10 | TC-27, 28 | 5 | Ashwin | 2 |
| 18 | Export: SRS/test plan DOCX, test cases + RTM CSV, diagram PNG | FR-08 | TC-23–25 | 3 | Abhay | 2 |
| 19 | Audit log + admin page (user roles, audit view) | FR-15, FR-12 | TC-32, 40 | 3 | Abhay | 2 |
| 20 | Docker Hub publishing from GitHub Actions | NFR-05 | – | 2 | Abhishek | 2 |
| 21 | Kubernetes manifests, kind deploy, CD smoke test | NFR-05, NFR-07 | TC-48 | 5 | Abhishek | 2 |
| 22 | Security + load testing (Locust, 20 users) | NFR-01, NFR-04 | TC-33–39, 43 | 3 | Ashwin | 2 |
| 23 | Usability walkthrough + system test execution log | NFR-02 | TC-44, all | 2 | Abhay | 2 |
| 24 | Docs: README, user guide, deviations, test summary report | §3.5 | – | 3 | Abhishek | 2 |
| 25 | Sprint 2 review: 2-min video, `v1.0.0` tag (freeze) | – | TC-50 | 1 | Abhishek | 2 |
| 26 | Architecture suggestions (stretch) | FR-13 | TC-41 | 5 | Ashwin | – |
| 27 | GitHub issue creation from requirements (stretch) | FR-14 | TC-42 | 5 | Abhinav | – |

**Load:** Sprint 1 = 44 pts (Abhinav 13, Ashwin 10, Abhay 13, Abhishek 8).
Sprint 2 = 41 pts (Ashwin 13, Abhinav 9, Abhay 8, Abhishek 11).

## 6. Sprint backlogs

### Sprint 1 — PB-1 to PB-12
**Goal:** An analyst can log in, create a project, submit requirements (text or file), generate an
IEEE 830 SRS with Gemini, then edit, version and approve it. Runs with `docker compose up`; CI runs on
every PR.

### Sprint 2 — PB-13 to PB-25
**Goal:** From an approved SRS, generate test cases, a test plan and UML diagrams; see the traceability
matrix and ambiguity flags; export everything; admins manage roles and read the audit log. Images
publish to Docker Hub and the app runs on Kubernetes. Testing, docs and the release are complete.

### Definition of Done (every story)
Code on a feature branch → unit tests for new logic → CI green → PR raised by the story owner →
reviewed and merged by the repo owner → issue auto-closed → card in *Done*.

## 7. Step-by-step execution

Legend: **[C]** I (Claude) do it · **[A]** Ashwin does it · **[T]** teammates do it

### Phase 0 — Setup
1. **[A]** Create a Gemini API key (aistudio.google.com) and a Docker Hub account + access token.
2. **[C]** `git init`, scaffold the repo layout, `.gitignore`, `.env.example` (no secrets), PR template.
3. **[C]** Create the GitHub repo `reqtrace` on your account and push `main`.
4. **[A]** Add teammates as collaborators; they accept the invites.
5. **[A]** Put secrets in GitHub: `gh secret set DOCKERHUB_USERNAME` and `gh secret set DOCKERHUB_TOKEN`
   (you type the values; I never see them). Put the Gemini key in your local `.env`.
6. **[C]** Create labels (`must`/`should`/`could`, `backend`/`frontend`/`agent`/`devops`/`test`/`docs`, `bug`),
   milestones *Sprint 1* and *Sprint 2*, and the GitHub Project with *Story Points* and *Sprint* fields
   linked to the repo.
7. **[C]** Script-create all 27 backlog issues with acceptance criteria, TC links, points, labels,
   milestone and assignee, and add them to the board.
8. **[C]** Add `ci.yml`; turn on branch protection for `main`.

### Sprint 1 — per story, in this order
PB-3 → PB-4 → PB-5 → PB-6 → PB-9 → PB-10 → PB-7 → PB-8 → PB-11

For each story:
1. **[C]** Move the card to *In Progress*, create `feat/<issue#>-<slug>`, implement with tests, commit, push.
2. **[T/A]** The owner opens the PR (GitHub shows a "Compare & pull request" button, about one minute).
3. **[C]** Check that CI is green and fix it if not.
4. **[A]** Ashwin (Scrum Master, repo owner) reviews and merges (merge commit, so stacked story
   branches stay clean); the issue closes and the card moves to *Done*. GitHub does not let anyone
   approve their own PR, so Ashwin merges his own stories with the admin bypass.

Then:
5. **[C]** End-to-end smoke test (TC-50) in Docker Compose with the real Gemini key; write `docs/sprint-1-review.md`.
6. **[A]** Record the **1-minute Sprint 1 video** (Cmd+Shift+5 on Mac) from my demo script.
7. **[C]** Commit it to `videos/` through a PR (PB-12).

### Sprint 2
1. Same per-story loop for PB-13 → PB-16 → PB-14 → PB-15 → PB-17 → PB-18 → PB-19.
2. **[C]** PB-20: add `cd.yml` (build + push to Docker Hub on merge to `main`). Verify the images on Docker Hub.
3. **[C]** PB-21: add the k8s manifests, `brew install kind`, create the cluster, create the k8s Secret
   from your `.env` locally, `kubectl apply`, and open the app through a port-forward.
4. **[C]** PB-22: run the security cases TC-33–39 and Locust TC-43, and record the results.
5. **[T]** PB-23: three people do the first-time SRS task (TC-44).
6. **[C]** Fill the test execution log for TC-01–50.
7. **[C]** PB-24: README (Compose + Kubernetes), user guide, `DEVIATIONS.md`, test summary report.
8. **[A]** Record the **2-minute Sprint 2 video** covering:
   - the full flow
   - the board
   - a PR with green CI
   - the Docker Hub images
   - `kubectl get pods`
9. **[C]** Commit the video and tag `v1.0.0` (freeze). The board shows both sprints done.

### Final demo (suggested 5–7 min)
1. Backlog and board.
2. A PR with green CI.
3. Live end-to-end run on Kubernetes.
4. Traceability with 100% coverage.
5. Exports.
6. Deviations.

## 8. Anticipated deviations (`docs/DEVIATIONS.md`)

| ID | Deviation | Reason |
|---|---|---|
| D-1 | Backlog and both sprints executed 29–30 Oct instead of 12–30 Oct | Team started late; scope kept, schedule compressed |
| D-2 | Kubernetes deployment added (SAD §7 has Docker Compose only) | Course requirement to use Kubernetes; Compose kept for local dev |
| D-3 | FR-13 and FR-14 not implemented | *Could* priority; capacity |
| D-4 | Diagram PNG rendered in the browser (Mermaid), not server-side Graphviz | Avoids a headless-browser dependency in the back end |
| D-5 | Generation runs synchronously with a progress indicator, no background queue | Gemini Flash returns within the 60 s limit; simpler |
| D-6 | Unit tests use SQLite; Compose and Kubernetes use PostgreSQL | Fast, dependency-free CI |
| D-7 | TLS via a self-signed certificate at nginx in the demo environment | No public domain for the course demo |
