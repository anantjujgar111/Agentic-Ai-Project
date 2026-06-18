# Part 2: Deploy The Public Chatbot Website

Part 2 connects the existing chatbot UI to the deployed Cloud Run backend and publishes the website with Firebase Hosting.

## 1. Current backend URL

Cloud Run backend:

```text
https://hdfc-banking-api-33622648493.us-central1.run.app
```

Frontend config file:

```text
frontend/config.js
```

Current value:

```javascript
window.CHAT_API_BASE_URL = "https://hdfc-banking-api-33622648493.us-central1.run.app";
```

## 2. Pull the latest repo changes in Cloud Shell

Run:

```bash
cd ~/Agentic-Ai-Project/Agentic-Ai-Project
git checkout cursor/agentic-banking-poc-88e6
git pull origin cursor/agentic-banking-poc-88e6
```

## 3. Redeploy backend once after the Vertex fallback fix

This is needed because the first live `/chat` test showed the service health endpoint working but `/chat` returned an internal error when `USE_VERTEX=true`. The backend now falls back to deterministic agent responses if Vertex response polishing fails.

Run:

```bash
export GCP_PROJECT_ID=project-687fc909-6531-45c6-950
export GCP_REGION=us-central1
export USE_VERTEX=true
bash scripts/deploy_backend_cloud_run.sh "$GCP_PROJECT_ID"
```

## 4. Test backend after redeploy

Health:

```bash
curl https://hdfc-banking-api-33622648493.us-central1.run.app/health
```

Balance:

```bash
curl -X POST https://hdfc-banking-api-33622648493.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"cust_001","message":"Show my balance"}'
```

Payment:

```bash
curl -X POST https://hdfc-banking-api-33622648493.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"cust_001","message":"Schedule my electricity bill"}'
```

## 5. Enable Firebase API

Run:

```bash
gcloud services enable firebase.googleapis.com firebasehosting.googleapis.com
```

## 6. Install Firebase CLI in Cloud Shell

Run:

```bash
npm install -g firebase-tools
```

Check:

```bash
firebase --version
```

## 7. Login to Firebase

Run:

```bash
firebase login --no-localhost
```

Cloud Shell gives a login link. Open it, sign in with your Google account, copy the code, and paste it back.

## 8. Select the Firebase/GCP project

Run:

```bash
firebase use --add project-687fc909-6531-45c6-950
```

When it asks for an alias, use:

```text
default
```

This creates a local `.firebaserc` file. It is okay if this file stays local.

## 9. Deploy frontend

Run:

```bash
firebase deploy --only hosting
```

Expected result:

```text
Hosting URL: https://project-687fc909-6531-45c6-950.web.app
```

Open that URL in the browser. You should see the chatbot UI.

## 10. Demo prompts

Try these:

```text
Show my balance
Schedule my electricity bill
Create wedding goal for 5 lakh in 18 months
Book RM appointment
What is debit card annual fee?
```

## 11. What Part 2 completes

After Firebase deploy:

```text
Cloud Run backend is live
Static chatbot website is public
Frontend calls backend /chat API
End-to-end POC is demoable in browser
```
