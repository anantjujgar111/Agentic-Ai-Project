# GCP Setup Checklist

## 1. Information to collect

Send these values before deployment:

```text
GCP_PROJECT_ID=
GCP_REGION=us-central1
GCS_KNOWLEDGE_BUCKET=
VERTEX_SEARCH_DATA_STORE_ID=hdfc-banking-kb
USE_VERTEX=true_or_false
```

Recommended first deployment:

```text
USE_VERTEX=false
```

Reason: deploy the mock tool flow first, then enable Vertex Gemini after Cloud Run is healthy.

## 2. APIs to enable

Required:

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com
```

For knowledge indexing:

```bash
gcloud services enable discoveryengine.googleapis.com
```

For Firebase Hosting:

```bash
gcloud services enable firebase.googleapis.com
```

## 3. Knowledge-base storage

Repo source:

```text
data/knowledge_base/**/*.md
```

GCP destination:

```text
gs://GCS_KNOWLEDGE_BUCKET/knowledge_base/
```

Upload:

```bash
bash scripts/upload_knowledge_to_gcs.sh "$GCP_PROJECT_ID" "$GCS_KNOWLEDGE_BUCKET"
```

## 4. Knowledge-base indexing

The professional path uses Vertex AI Search, exposed in Google Cloud as Agent Builder / Discovery Engine.

Console path:

```text
Google Cloud Console -> Agent Builder / Vertex AI Search -> Data stores -> Create data store
```

Choose:

- Source: Cloud Storage
- Data type: unstructured documents/content
- URI: `gs://GCS_KNOWLEDGE_BUCKET/knowledge_base/`
- Data store id: `hdfc-banking-kb`

API import path:

```bash
bash scripts/import_vertex_search_documents.sh \
  "$GCP_PROJECT_ID" \
  "$VERTEX_SEARCH_DATA_STORE_ID" \
  "$GCS_KNOWLEDGE_BUCKET"
```

Indexing is complete when the data store shows successful import and searchable documents.

## 5. Backend deployment

```bash
export GCP_REGION=us-central1
export USE_VERTEX=false
bash scripts/deploy_backend_cloud_run.sh "$GCP_PROJECT_ID"
```

After Cloud Run works, enable Gemini:

```bash
export USE_VERTEX=true
bash scripts/deploy_backend_cloud_run.sh "$GCP_PROJECT_ID"
```

## 6. Website deployment

Edit:

```text
frontend/config.js
```

Set the Cloud Run URL:

```javascript
window.CHAT_API_BASE_URL = "https://YOUR_CLOUD_RUN_SERVICE_URL";
```

Deploy:

```bash
npm install -g firebase-tools
firebase login
firebase use --add "$GCP_PROJECT_ID"
firebase deploy --only hosting
```

## 7. APIs not needed yet

No payment gateway, SMS, WhatsApp, email, or real banking API is needed for this POC cycle.

If you later want OTP, reminders, or notifications, ask before adding:

- Twilio or GCP Identity Platform for OTP
- Cloud Scheduler + Pub/Sub for reminders
- SendGrid or Gmail API for email

Reason: those add cost, credentials, and compliance concerns, so the first banking POC should prove the agent/tool/knowledge flow before adding them.
