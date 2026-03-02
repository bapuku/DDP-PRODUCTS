#!/usr/bin/env bash
# Migration script: Docker Compose -> Kubernetes
# Converts .env variables to K8s secrets and validates manifests.
set -euo pipefail

ENV_FILE="${1:-infrastructure/.env}"
NAMESPACE="${2:-dpp-production}"
OVERLAY="${3:-infrastructure/k8s/overlays/production}"

echo "=== EU DPP Platform: Docker Compose -> Kubernetes Migration ==="
echo "ENV: $ENV_FILE | Namespace: $NAMESPACE | Overlay: $OVERLAY"

# Step 1: Create namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Step 2: Create secrets from .env (never commit secrets to git)
if [[ -f "$ENV_FILE" ]]; then
  echo "Creating K8s secret from $ENV_FILE..."
  kubectl create secret generic dpp-api-secrets \
    --namespace="$NAMESPACE" \
    --from-env-file="$ENV_FILE" \
    --dry-run=client -o yaml | kubectl apply -f -
  echo "Secret created."
else
  echo "WARNING: $ENV_FILE not found - secret not created. Set secrets manually."
fi

# Step 3: Apply Kustomize overlay
echo "Applying Kustomize overlay: $OVERLAY"
kubectl apply -k "$OVERLAY"

# Step 4: Wait for rollout
echo "Waiting for deployment rollout..."
kubectl rollout status deployment/dpp-api -n "$NAMESPACE" --timeout=5m

# Step 5: Verify
echo "Verifying pods..."
kubectl get pods -n "$NAMESPACE" -l app=dpp-api

echo "=== Migration complete. Verify /health and /ready endpoints. ==="
