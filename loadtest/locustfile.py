"""NFR-01 / TC-43: 20 virtual users for 5 minutes on common pages; p95 must stay at or under 2 s.

LLM generation is excluded by the requirement, so only page and API calls are exercised.

    locust -f loadtest/locustfile.py --headless -u 20 -r 5 -t 5m --host https://localhost:8443 \
        --csv loadtest/results/tc43 --html loadtest/results/tc43.html
"""
import uuid

import urllib3
from locust import HttpUser, between, task

urllib3.disable_warnings()  # the demo deployment uses a self-signed certificate

REQUIREMENTS = (
    "Librarians must be able to add, edit and remove books.\n"
    "Members can search the catalogue by title or author.\n"
    "Search results must load within 2 seconds."
)


class ReqTraceUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.client.verify = False
        email = f"load-{uuid.uuid4().hex[:12]}@example.com"
        password = "Load-Test-" + uuid.uuid4().hex[:8]
        self.client.post("/api/auth/register", json={"name": "Load User", "email": email, "password": password})
        token = self.client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {token}"
        self.project = self.client.post("/api/projects", json={"name": "Load test project"}).json()["id"]
        self.client.post(f"/api/projects/{self.project}/inputs/text", json={"content": REQUIREMENTS})

    @task(3)
    def dashboard(self) -> None:
        self.client.get("/api/projects", name="/api/projects")

    @task(2)
    def project_page(self) -> None:
        self.client.get(f"/api/projects/{self.project}", name="/api/projects/[id]")

    @task(2)
    def inputs(self) -> None:
        self.client.get(f"/api/projects/{self.project}/inputs", name="/api/projects/[id]/inputs")

    @task(1)
    def traceability(self) -> None:
        self.client.get(f"/api/projects/{self.project}/traceability", name="/api/projects/[id]/traceability")

    @task(1)
    def versions(self) -> None:
        self.client.get(f"/api/projects/{self.project}/srs/versions", name="/api/projects/[id]/srs/versions")

    @task(1)
    def app_shell(self) -> None:
        self.client.get("/", name="/ (SPA)")
