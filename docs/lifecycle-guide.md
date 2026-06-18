# Agentic Banking POC Lifecycle

This guide explains the project the same way you can explain it in an interview.

## What we are building

An HDFC-like Smart Banking Assistant POC with:

1. Customer service information agent
2. Banking agents:
   - Smart payments agent
   - Account service agent
   - Goal planning agent
3. RM appointment booking agent

The chatbot uses mock banking data for safety. No real money movement happens.

## Cycle 1: Local POC foundation

### What happened in code

- Created a FastAPI backend with `POST /chat`.
- Added an orchestrator agent that routes user messages to specialized agents.
- Added controlled banking tools under `backend/app/mcp/tools.py`.
- Added synthetic mock data under `data/mock`.
- Added synthetic knowledge-base markdown under `data/knowledge_base`.
- Added a static chatbot UI under `frontend`.
- Added scripts for Cloud Run, GCS upload, and Vertex AI Search import.

### What you learn in this cycle

- How agent orchestration works.
- Why tools/MCP are safer than letting the LLM directly touch data.
- How mock data supports a realistic banking POC without real customer data.
- How knowledge-base files become retrievable context.

### Run locally only if you want

You said you do not want to see the UI locally. That is fine. Local run is optional:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8080
```

Then open `frontend/index.html` only if you want a local check.

## Cycle 2: GCP project and APIs

### What you do in GCP

Open Google Cloud Console and select your project.

Enable these APIs:

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com
```

For professional knowledge indexing, also enable:

```bash
gcloud services enable discoveryengine.googleapis.com
```

### Values I need from you

When you are ready to deploy, provide:

- `GCP_PROJECT_ID`
- Preferred region, for example `us-central1` or `asia-south1`
- Whether to use Vertex Gemini immediately: `USE_VERTEX=true` or `false`

No non-GCP external API is required in this cycle.

## Cycle 3: Put the knowledge base in GCP

### Where the knowledge base lives in this repo

```text
data/knowledge_base/
  customer_service/
  banking_products/
  policies/
```

Each markdown file is a synthetic bank policy/product/support article.

### Where it goes in GCP

Upload these files to a Cloud Storage bucket:

```text
gs://YOUR_BUCKET/knowledge_base/
```

Use:

```bash
bash scripts/upload_knowledge_to_gcs.sh YOUR_PROJECT_ID YOUR_BUCKET
```

### What this means

At this point the files are stored in GCP, but they are not yet semantically indexed.

## Cycle 4: Index the knowledge base

### Professional path: Vertex AI Search / Agent Builder

Create a Vertex AI Search data store in Google Cloud Console:

1. Go to **Google Cloud Console**.
2. Search for **Agent Builder** or **Vertex AI Search**.
3. Create a new **Search data store**.
4. Choose **Cloud Storage** as the source.
5. Use the bucket path:

```text
gs://YOUR_BUCKET/knowledge_base/
```

6. Choose unstructured/content document import.
7. Name the data store, for example:

```text
hdfc-banking-kb
```

You can also request import with:

```bash
bash scripts/import_vertex_search_documents.sh YOUR_PROJECT_ID hdfc-banking-kb YOUR_BUCKET
```

### How you know it is indexed

In GCP Console, open the data store and check:

- Import operation status is successful.
- Document count is greater than zero.
- Preview/search test returns answers from savings, charges, FD/RD, payment methods, or policy docs.

### What code does today

The current code uses local retrieval from `data/knowledge_base` so the POC runs before GCP indexing is ready.

After the Vertex AI Search data store is created, set:

```bash
KNOWLEDGE_BACKEND=vertex_ai_search
VERTEX_SEARCH_DATA_STORE_ID=hdfc-banking-kb
```

Then the next code cycle can replace the placeholder with a Discovery Engine serving client.

## Cycle 5: Deploy backend to Cloud Run

Run:

```bash
bash scripts/deploy_backend_cloud_run.sh YOUR_PROJECT_ID
```

Useful environment variables:

```bash
export GCP_REGION=us-central1
export USE_VERTEX=true
export VERTEX_MODEL=gemini-1.5-flash
```

During the first deployment, Cloud Run source deploy may need IAM roles for the build service account. If source upload, Artifact Registry push, or Cloud Build logs fail, use the troubleshooting block in `docs/gcp-setup.md`.

Cloud Run prints a service URL like:

```text
https://hdfc-banking-api-xxxxx-uc.a.run.app
```

Copy this URL.

## Cycle 6: Deploy the chatbot website

Use Firebase Hosting:

```bash
npm install -g firebase-tools
firebase login
firebase use --add YOUR_PROJECT_ID
```

Edit:

```text
frontend/config.js
```

Set:

```javascript
window.CHAT_API_BASE_URL = "YOUR_CLOUD_RUN_URL";
```

Deploy:

```bash
firebase deploy --only hosting
```

Firebase gives a public URL:

```text
https://YOUR_PROJECT_ID.web.app
```

That is the free website where you can show the chatbot.

## Cycle 7: Interview explanation

Say:

> I built an Agentic AI banking assistant using a routed multi-agent architecture. The orchestrator identifies whether the request is customer service, account service, smart payment, goal planning, or RM appointment booking. Sensitive banking operations are implemented as controlled MCP-style tools, so the model cannot directly manipulate data. The POC uses synthetic account data and a synthetic knowledge base. The knowledge base starts as markdown files, is uploaded to Cloud Storage, and can be indexed in Vertex AI Search for semantic retrieval. The backend runs on Cloud Run, Gemini on Vertex AI can polish responses, and the frontend is hosted publicly on Firebase Hosting.
