#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <gcp-project-id> <gcs-bucket-name>"
  echo "Example: $0 my-project hdfc-agentic-kb-my-project"
  exit 1
fi

PROJECT_ID="$1"
BUCKET_NAME="$2"
REGION="${GCP_REGION:-us-central1}"

gcloud config set project "$PROJECT_ID"
gcloud services enable storage.googleapis.com

if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="$PROJECT_ID" \
    --location="$REGION" \
    --uniform-bucket-level-access
fi

gcloud storage rsync data/knowledge_base "gs://${BUCKET_NAME}/knowledge_base" --recursive

echo "Knowledge base uploaded to gs://${BUCKET_NAME}/knowledge_base"
