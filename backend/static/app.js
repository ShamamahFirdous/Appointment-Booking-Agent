const messages = document.getElementById("messages");
const input = document.getElementById("input");
const sessionId = "demo-session";

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.innerText = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: text
      })
    });

    const data = await response.json();
    addMessage(data.reply, "bot");

  } catch (err) {
    addMessage("⚠️ Error talking to server.", "bot");
    console.error(err);
  }
}

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
// Show welcome message on page load
window.addEventListener("DOMContentLoaded", () => {
  addMessage(
    "👋 Hi! I can help you book, reschedule, or cancel an appointment.\n\nJust tell me what you'd like to do.",
    "bot"
  );
});

