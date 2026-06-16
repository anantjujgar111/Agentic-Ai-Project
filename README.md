# Agentic AI Banking Assistant POC

This repository contains an end-to-end HDFC-like Agentic AI banking chatbot POC.

It demonstrates:

- Customer service information retrieval from a synthetic knowledge base
- Smart payments agent for mock bill payment, recurring payment, rent split, due-date reminders, and payment rail recommendation
- Account service agent for balance, statement summary, charge explanation, card controls, and limits
- Goal agent for emergency fund, vacation, education, wedding, home down payment, and retirement planning
- RM appointment booking agent
- MCP-style controlled banking tools
- Optional Vertex AI Gemini response polishing
- GCP deployment path with Cloud Run, Cloud Storage, Vertex AI Search, and Firebase Hosting

No real banking action happens. All customer, account, bill, and appointment data is synthetic.

## Project structure

```text
backend/
  app/
    agents/           # Orchestrator and ADK integration point
    mcp/              # Controlled MCP-style banking tools
    services/         # Knowledge retrieval and optional Vertex wrapper
    main.py           # FastAPI app
data/
  knowledge_base/     # Synthetic markdown documents for GCS/Vertex AI Search
  mock/               # Synthetic banking data
frontend/             # Static chatbot UI for Firebase Hosting
scripts/              # GCP deployment and indexing scripts
docs/                 # Step-by-step lifecycle and GCP setup
```

## First things to read

1. [Lifecycle guide](docs/lifecycle-guide.md)
2. [GCP setup checklist](docs/gcp-setup.md)

## Backend API

Endpoint:

```text
POST /chat
```

Example:

```json
{
  "user_id": "cust_001",
  "message": "Schedule my electricity bill"
}
```

Response includes:

- chatbot response
- selected agent
- tool traces
- next steps

## Optional local smoke run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8080
```

## GCP deployment summary

Upload and index knowledge base:

```bash
bash scripts/upload_knowledge_to_gcs.sh YOUR_PROJECT_ID YOUR_BUCKET
bash scripts/import_vertex_search_documents.sh YOUR_PROJECT_ID hdfc-banking-kb YOUR_BUCKET
```

Deploy backend:

```bash
bash scripts/deploy_backend_cloud_run.sh YOUR_PROJECT_ID
```

Deploy website:

```bash
firebase deploy --only hosting
```
