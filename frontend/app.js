const messagesEl = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");

const API_BASE_URL =
  window.CHAT_API_BASE_URL ||
  new URLSearchParams(window.location.search).get("api") ||
  "http://localhost:8080";

function addMessage(role, text, agent) {
  const bubble = document.createElement("article");
  bubble.className = `message ${role}`;
  if (agent) {
    const label = document.createElement("span");
    label.className = "agent-label";
    label.textContent = agent;
    bubble.appendChild(label);
  }
  bubble.append(document.createTextNode(text));
  messagesEl.appendChild(bubble);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(message) {
  addMessage("user", message);
  addMessage("bot", "Thinking through the right banking agent...");
  const pending = messagesEl.lastElementChild;

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "cust_001", message }),
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const data = await response.json();
    pending.remove();
    addMessage("bot", data.response, data.agent);
  } catch (error) {
    pending.remove();
    addMessage(
      "bot",
      `I could not reach the chatbot API at ${API_BASE_URL}. Deploy the backend to Cloud Run and set the Firebase config to that URL.`
    );
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  sendMessage(message);
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    input.focus();
  });
});

addMessage(
  "bot",
  "Hi Aarav, I am your Smart Banking Assistant. I can answer bank information questions, summarize your mock account, schedule mock payments, create savings goals, and book RM appointments.",
  "Orchestrator Agent"
);
