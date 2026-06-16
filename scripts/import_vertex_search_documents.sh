#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <gcp-project-id> <data-store-id> <gcs-bucket-name>"
  echo "Example: $0 my-project hdfc-banking-kb hdfc-agentic-kb-my-project"
  exit 1
fi

PROJECT_ID="$1"
DATA_STORE_ID="$2"
BUCKET_NAME="$3"
LOCATION="${VERTEX_SEARCH_LOCATION:-global}"

gcloud config set project "$PROJECT_ID"
gcloud services enable discoveryengine.googleapis.com

ACCESS_TOKEN="$(gcloud auth print-access-token)"
IMPORT_URL="https://discoveryengine.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/${DATA_STORE_ID}/branches/0/documents:import"

curl -X POST \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  "${IMPORT_URL}" \
  -d "{
    \"gcsSource\": {
      \"inputUris\": [\"gs://${BUCKET_NAME}/knowledge_base/*\"],
      \"dataSchema\": \"content\"
    },
    \"reconciliationMode\": \"INCREMENTAL\",
    \"autoGenerateIds\": true,
    \"errorConfig\": {
      \"gcsPrefix\": \"gs://${BUCKET_NAME}/vertex_search_import_errors\"
    }
  }"

echo
echo "Import requested. Check Vertex AI Search / Agent Builder data store indexing status in GCP Console."
