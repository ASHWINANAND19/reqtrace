# ReqTrace

Agentic AI assistant for SRS, test case and software development support.

ReqTrace turns raw requirements into an IEEE 830 SRS, then generates test cases, a test plan and UML
diagrams, and keeps a requirement-to-test traceability matrix. Every AI output is editable, versioned
and approved by a human.

## Features

| Area | What it does | Requirements |
|---|---|---|
| Accounts | Register, log in, 60-minute idle timeout, four roles | FR-01, FR-12 |
| Projects | Projects with members; only members can open them | FR-02 |
| Input | Paste text or upload TXT / DOCX / PDF (≤ 10 MB) | FR-03 |
| SRS | IEEE 830 draft with unique IDs; edit, version, compare, approve | FR-04, FR-05 |
| Quality check | Vague words with measurable rewrites, missing sections, conflicts | FR-11 |
| Test cases | Positive, negative and boundary tests per requirement | FR-06 |
| Traceability | Requirement-to-test matrix with coverage | FR-07 |
| Test plan | IEEE 829-style plan from the approved SRS | FR-09 |
| UML | Use-case, class and sequence diagrams (Mermaid), editable | FR-10 |
| Export | SRS and test plan DOCX, test cases and matrix CSV, diagram PNG | FR-08 |
| Admin | User roles and the audit log | FR-12, FR-15 |

Architecture follows the SAD: React SPA → nginx (TLS) → FastAPI modular monolith (auth, projects,
agents behind an LLM adapter) → PostgreSQL. The LLM provider is Google Gemini; an offline mock is used
in tests and when no key is set.

## Documentation

| Document | Contents |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | How to use ReqTrace |
| [docs/PLAN.md](docs/PLAN.md) | Product backlog, sprint backlogs, DevOps plan |
| [docs/sprint-1-review.md](docs/sprint-1-review.md), [docs/sprint-2-review.md](docs/sprint-2-review.md) | Sprint reviews |
| [docs/TEST_LOG.md](docs/TEST_LOG.md), [docs/TEST_SUMMARY.md](docs/TEST_SUMMARY.md) | Test execution and summary |
| [docs/DEVIATIONS.md](docs/DEVIATIONS.md) | Differences from the SRS, SAD and Test Plan |
| [deploy/README.md](deploy/README.md) | Docker Compose and Kubernetes details |

Requirements, test plan and architecture come from the Part 1 deliverables (SRS `ReqTrace-SRS-01`,
Test Plan `ReqTrace-TP-01`, SAD `ReqTrace-SAD-01`).

## Develop locally

```bash
cd backend && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pytest --cov            # tests use SQLite and the mock LLM
.venv/bin/uvicorn app.main:app --reload --port 8000
cd ../frontend && npm ci && npm run dev    # http://localhost:5173, proxies /api to :8000
```

## Run with Docker Compose

Requires Docker. From the repository root:

```bash
cp .env.example .env   # optional: add GEMINI_API_KEY and set LLM_PROVIDER=gemini
docker compose up --build
```

Open https://localhost (the certificate is self-signed, so the browser asks you to accept it once).
Without a `.env` file the app starts with the offline mock LLM.

| Service | Image | Purpose |
|---|---|---|
| `frontend` | nginx + built React app | Serves the UI, terminates TLS, proxies `/api` |
| `backend` | Python 3.11 + FastAPI | REST API and AI agents |
| `db` | PostgreSQL 15 | Persistent storage |

If ports 80/443 are taken, set `HTTP_PORT` and `HTTPS_PORT` in `.env`.

## Run on Kubernetes

```bash
DOCKERHUB_USER=hadesash ./deploy/k8s/deploy.sh   # or: ./deploy/k8s/deploy.sh --build
```

Creates a local [kind](https://kind.sigs.k8s.io) cluster, a secret from `.env`, PostgreSQL, two back-end replicas and
the nginx front end, then serves the app at https://localhost:8443. See [deploy/README.md](deploy/README.md).


## CI/CD

| Workflow | Trigger | What it does |
|---|---|---|
| `CI` | every PR and push to `main` | ruff + pytest with coverage (≥70%), ESLint + type-checked build, gitleaks secret scan |
| `PR automation` | every PR | requires a linked backlog issue (`Closes #N`), labels by changed paths, assigns the author |
| `CD` | push to `main`, `v*` tags | builds both images and publishes them to Docker Hub as [`hadesash/reqtrace-backend`](https://hub.docker.com/r/hadesash/reqtrace-backend) and [`hadesash/reqtrace-frontend`](https://hub.docker.com/r/hadesash/reqtrace-frontend) (tags: `latest`, `sha-<commit>`, version), then deploys them to a kind Kubernetes cluster and smoke-tests the app |
| `CD` (PR) | every PR | builds the images from the PR, deploys them to a throwaway kind cluster and runs the smoke test |

Docker Hub credentials are repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (an access token, never a password).

To run the published images instead of building locally:

```bash
DOCKERHUB_USER=hadesash docker compose pull && DOCKERHUB_USER=hadesash docker compose up
```

## Team

| Member | Role |
|---|---|
| Abhinav D | Back end, agent orchestration, database |
| Abhay Natesh | Front end, test design and execution |
| Abhishek M | Documentation, DevOps (Docker, CI), integration |
| Ashwin Anand | Scrum Master and repo owner; UML and test-case agents, security and performance testing |
