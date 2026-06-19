const messagesEl = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");

const API_BASE_URL =
  window.CHAT_API_BASE_URL ||
  new URLSearchParams(window.location.search).get("api") ||
  "http://localhost:8080";

const SESSION_STORAGE_KEY = "banking-chat-session-id";
let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
if (!sessionId) {
  sessionId = crypto.randomUUID
    ? crypto.randomUUID()
    : `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

function addMessage(role, text) {
  const bubble = document.createElement("article");
  bubble.className = `message ${role}`;
  bubble.append(document.createTextNode(text));
  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(message) {
  addMessage("user", message);
  addMessage("bot", "Let me check that for you...");
  const pending = messagesEl.lastElementChild;

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const data = await response.json();
    pending.remove();
    addMessage("bot", data.response);
  } catch (error) {
    pending.remove();
    const detail =
      error instanceof Error && error.message.startsWith("API returned")
        ? `The chatbot API responded with an error (${error.message.replace("API returned ", "")}). If you just deployed, redeploy the backend with the latest script so Firestore permissions and session fallback are applied.`
        : `I could not reach the chatbot API at ${API_BASE_URL}. Check that the backend Cloud Run service is deployed and that frontend/config.js points to it.`;
    addMessage("bot", detail);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  sendMessage(message);
});

addMessage(
  "bot",
  "Hi, I am your Smart Banking Assistant. You can type naturally. For account-specific help, I will verify your session with your account number first."
);
