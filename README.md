# ReqTrace

Agentic AI assistant for SRS, test case and software development support.

ReqTrace turns raw requirements into an IEEE 830 SRS, then generates test cases, a test plan and UML
diagrams, and keeps a requirement-to-test traceability matrix. Every AI output is editable, versioned
and approved by a human.

- Requirements, test plan and architecture: Part 1 deliverables (SRS `ReqTrace-SRS-01`, Test Plan
  `ReqTrace-TP-01`, SAD `ReqTrace-SAD-01`)
- Build and sprint plan: [docs/PLAN.md](docs/PLAN.md)

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

## Team

| Member | Role |
|---|---|
| Abhinav D | Back end, agent orchestration, database |
| Abhay Natesh | Front end, test design and execution |
| Abhishek M | Documentation, DevOps (Docker, CI), integration |
| Ashwin Anand | Scrum Master and repo owner; UML and test-case agents, security and performance testing |
