# Deployment

| File | Purpose |
|---|---|
| `../docker-compose.yml` | One-command local start (`docker compose up --build`) |
| `k8s/` | Kubernetes manifests: namespace, config, PostgreSQL StatefulSet, back end (2 replicas), front end (NodePort) |
| `k8s/deploy.sh` | Creates a kind cluster if needed, creates the secret from `.env`, applies the manifests and waits for rollout |
| `k8s/kind-config.yaml` | Maps the front end to `https://localhost:8443` |

```bash
DOCKERHUB_USER=hadesash ./deploy/k8s/deploy.sh  # images published by the CD workflow
./deploy/k8s/deploy.sh --build                   # build locally instead
kubectl -n reqtrace get pods                     # 1 postgres, 2 backend, 1 frontend
kubectl -n reqtrace scale deployment/backend --replicas=3   # scale the API/agent layer (NFR-07)
kind delete cluster --name reqtrace              # remove everything
```

## Secrets

`deploy.sh` turns `.env` into the Kubernetes secret `reqtrace-secrets`. The keys it needs are
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET`, `LLM_PROVIDER` and, for real generation,
`GEMINI_API_KEY` and `GEMINI_MODEL`. `ADMIN_EMAIL` / `ADMIN_PASSWORD` create the first Administrator.

## Ports

| URL | Service |
|---|---|
| https://localhost:8443 | Front end (NodePort 30443) |
| http://localhost:9080 | Redirects to HTTPS (NodePort 30080) |
