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

The POC keeps short in-memory session memory:

- verified customer id
- masked account number
- pending account-specific request
- pending failed-transaction support context
- recent chat memory entries

This is implemented in:

```text
backend/app/services/session.py
```

For production, replace this with Redis, Firestore, Cloud SQL, or another durable store with TTL, encryption, audit logs, and session expiry.

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
Session memory -> customer-specific chat state
Knowledge index -> approved banking documents and FAQs
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
