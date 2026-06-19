# Session And Memory Management In The POC

The chatbot now uses a browser session id instead of trusting a frontend-provided customer id.

## Why this was added

Earlier, the frontend always sent:

```json
{"user_id": "cust_001"}
```

That is not a good POC pattern because one user's data can be mixed with another user's data. The current flow uses:

```json
{"session_id": "browser-generated-session-id"}
```

The backend maps that session to a verified mock customer only after account-number verification.

## Synthetic accounts for testing

```text
Aarav Mehta -> 5010004321 -> cust_001 -> XXXXXX4321
Neha Rao    -> 5010007788 -> cust_002 -> XXXXXX7788
```

## Current session flow

```text
User asks account-specific question
        |
        v
Backend checks session_id
        |
        |-- session verified -> route to agent with verified customer_id
        |
        |-- session not verified -> ask for full mock account number
                                      store original user request as pending
```

Then:

```text
User enters account number
        |
        v
verify_account_number tool checks mock account data
        |
        |-- valid -> session stores customer_id and replays pending request
        |
        |-- invalid -> asks user to retry
```

## Memory management

The session store keeps short session memory:

- verified customer id
- masked account number
- pending account-specific request
- pending failed-transaction support context
- recent chat memory entries

This is implemented in:

```text
backend/app/services/session.py
```

The code supports two backends:

```text
SESSION_BACKEND=memory     -> local/in-memory POC default
SESSION_BACKEND=firestore  -> GCP Firestore-backed session store
```

Firestore collection:

```text
SESSION_FIRESTORE_COLLECTION=chat_sessions
```

The Firestore document shape is:

```json
{
  "session_id": "browser-session-id",
  "customer_id": "cust_001",
  "customer_name": "Aarav Mehta",
  "account_number_masked": "XXXXXX4321",
  "verified_at": "2026-06-19T12:00:00+00:00",
  "pending_message": "Show my balance",
  "pending_context": {
    "type": "transaction_issue",
    "initial_message": "my transaction failed"
  },
  "memory": [
    {
      "role": "user",
      "content": "Show my balance",
      "created_at": "2026-06-19T12:00:00+00:00"
    }
  ]
}
```

For a real production system, add TTL expiry, encryption policy, audit logging, logout/session reset, and PII retention controls.

## Firestore setup for persistent session memory

Enable the API:

```bash
gcloud services enable firestore.googleapis.com
```

Create a Firestore database if your project does not already have one:

```bash
gcloud firestore databases create \
  --database="(default)" \
  --location=us-central1
```

Deploy backend with Firestore sessions:

```bash
export SESSION_BACKEND=firestore
export SESSION_FIRESTORE_COLLECTION=chat_sessions
bash scripts/deploy_backend_cloud_run.sh "$GCP_PROJECT_ID"
```

If Firestore is not available, the app logs a warning and falls back to in-memory sessions so the POC remains usable.

## Transaction issue memory

If a user says:

```text
my transaction failed
```

the assistant asks for details. If the same session then says:

```text
my last payment amount 300 rs
```

the assistant treats it as failed-transaction follow-up, not as a new bill payment request.

## Indexing management

Knowledge-base indexing is not per user session. It is global/shared because policy, product, fee, and FAQ documents are not customer-private.

Session memory is separate from knowledge indexing:

```text
Session memory -> customer-specific chat state in memory or Firestore
Knowledge index -> approved banking documents and FAQs in Vertex AI Search
```

In production:

- stable policy documents can be indexed on release
- rates, fees, offers, and product pages should be re-indexed on schedule or on document-change events
- customer-specific account data should not be indexed into the public/global knowledge base

## Files involved

```text
frontend/app.js                       -> creates browser session id
backend/app/main.py                   -> verifies session before sensitive actions
backend/app/services/session.py       -> in-memory session state
backend/app/mcp/tools.py              -> verify_account_number tool
backend/app/agents/orchestrator.py    -> session-scoped follow-up memory
data/mock/accounts.json               -> synthetic account numbers
```
