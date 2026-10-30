#!/usr/bin/env bash
# Deploy ReqTrace to Kubernetes (kind by default).
#
#   ./deploy/k8s/deploy.sh                       images from Docker Hub: $DOCKERHUB_USER/reqtrace-*:latest
#   IMAGE_TAG=sha-abc1234 ./deploy/k8s/deploy.sh a specific published build
#   ./deploy/k8s/deploy.sh --build               build images locally and load them into kind
#
# Secrets come from ENV_FILE (default: .env at the repo root) and are never committed.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cluster="${KIND_CLUSTER:-reqtrace}"
env_file="${ENV_FILE:-$root/.env}"
image_tag="${IMAGE_TAG:-latest}"

if [[ "${1:-}" == "--build" ]]; then
  image_repo="local"
  image_tag="dev"
else
  image_repo="docker.io/${DOCKERHUB_USER:?Set DOCKERHUB_USER to your Docker Hub username, or use --build}"
fi
[[ -f "$env_file" ]] || { echo "Missing $env_file (copy .env.example and fill it in)"; exit 1; }

if [[ "${SKIP_CLUSTER:-}" != "1" ]] && ! kind get clusters 2>/dev/null | grep -qx "$cluster"; then
  kind create cluster --name "$cluster" --config "$here/kind-config.yaml"
fi

if [[ "$image_repo" == "local" ]]; then
  docker build -t local/reqtrace-backend:dev "$root/backend"
  docker build -t local/reqtrace-frontend:dev "$root/frontend"
  kind load docker-image local/reqtrace-backend:dev local/reqtrace-frontend:dev --name "$cluster"
fi

kubectl apply -f "$here/namespace.yaml"
kubectl -n reqtrace create secret generic reqtrace-secrets --from-env-file="$env_file" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl kustomize "$here" | sed -e "s#IMAGE_REPO#$image_repo#g" -e "s#IMAGE_TAG#$image_tag#g" | kubectl apply -f -

# Pick up new images and secrets even when the tag (e.g. latest) did not change
kubectl -n reqtrace rollout restart deployment/backend deployment/frontend
kubectl -n reqtrace rollout status statefulset/postgres --timeout=180s
kubectl -n reqtrace rollout status deployment/backend --timeout=240s
kubectl -n reqtrace rollout status deployment/frontend --timeout=120s
kubectl -n reqtrace get pods,svc
echo
echo "ReqTrace is running: https://localhost:8443 (self-signed certificate)"
