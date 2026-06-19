#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <gcp-project-id>"
  echo "Optional env: GCP_REGION=us-central1 FRONTEND_SERVICE_NAME=hdfc-banking-chatbot"
  exit 1
fi

PROJECT_ID="$1"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${FRONTEND_SERVICE_NAME:-hdfc-banking-chatbot}"
REPOSITORY="${ARTIFACT_REPOSITORY:-cloud-run-source-deploy}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}:latest"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

if ! gcloud artifacts repositories describe "$REPOSITORY" --location "$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPOSITORY" \
    --repository-format docker \
    --location "$REGION"
fi

gcloud builds submit . \
  --region "$REGION" \
  --config cloudbuild.frontend.yaml \
  --substitutions "_IMAGE=${IMAGE}"

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --allow-unauthenticated

echo "Frontend deployed. Open the Cloud Run service URL in your browser."
