#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <gcp-project-id>"
  echo "Optional env: GCP_REGION=us-central1 SERVICE_NAME=hdfc-banking-api USE_VERTEX=false SESSION_BACKEND=memory"
  exit 1
fi

PROJECT_ID="$1"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-hdfc-banking-api}"
USE_VERTEX_VALUE="${USE_VERTEX:-false}"
VERTEX_MODEL_VALUE="${VERTEX_MODEL:-gemini-1.5-flash}"
SESSION_BACKEND_VALUE="${SESSION_BACKEND:-memory}"
SESSION_FIRESTORE_COLLECTION_VALUE="${SESSION_FIRESTORE_COLLECTION:-chat_sessions}"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com firestore.googleapis.com

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},USE_VERTEX=${USE_VERTEX_VALUE},VERTEX_MODEL=${VERTEX_MODEL_VALUE},SESSION_BACKEND=${SESSION_BACKEND_VALUE},SESSION_FIRESTORE_COLLECTION=${SESSION_FIRESTORE_COLLECTION_VALUE}"

echo "Backend deployed. Copy the Cloud Run service URL into frontend/config.js."
