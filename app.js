const form = document.getElementById("chatForm");
const questionInput = document.getElementById("question");
const messagesEl = document.getElementById("messages");
const sendBtn = document.getElementById("sendBtn");
const apiBaseUrlInput = document.getElementById("apiBaseUrl");
const refreshBtn = document.getElementById("refreshBtn");
const clearBtn = document.getElementById("clearBtn");
const statsCardsEl = document.getElementById("statsCards");
const insightListEl = document.getElementById("insightList");
const promptChipsEl = document.getElementById("promptChips");
const connectionPill = document.getElementById("connectionPill");
const topRiskSegmentEl = document.getElementById("topRiskSegment");

const chartInstances = new Map();
const promptQuestions = [
  "Find the churn rate for each type of InternetService. Which one is the highest?",
  "Compare churn by Contract type and explain the biggest difference.",
  "List the number of customers and their total MonthlyCharges, grouped by tenure under 12 months vs 12 months and above.",
  "Which churned customers had the highest MonthlyCharges? Based on their Contract type, suggest a simple retention plan.",
];

const savedUrl = localStorage.getItem("apiBaseUrl") || "http://127.0.0.1:8000";
apiBaseUrlInput.value = savedUrl;

function addMessage(kind, text) {
  const div = document.createElement("div");
  div.className = `msg ${kind}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setConnectionStatus(kind, text) {
  connectionPill.className = `status-pill status-${kind}`;
  connectionPill.textContent = text;
}

function formatNumber(value, decimals = 0) {
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

function formatPercent(value) {
  return `${formatNumber(value, 1)}%`;
}

function formatCardValue(card) {
  if (card.suffix === "%") {
    return formatNumber(card.value, 1);
  }

  if (card.suffix === "$") {
    return formatNumber(card.value, 2);
  }

  if (card.suffix === " months") {
    return formatNumber(card.value, 1);
  }

  return formatNumber(card.value, Number.isInteger(card.value) ? 0 : 1);
}

function destroyChart(id) {
  const existing = chartInstances.get(id);
  if (existing) {
    existing.destroy();
    chartInstances.delete(id);
  }
}

function renderStatCards(cards) {
  statsCardsEl.innerHTML = cards
    .map(
      (card) => `
        <article class="stat-card">
          <span class="stat-label">${card.label}</span>
          <span class="stat-value">${formatCardValue(card)}<span class="stat-suffix">${card.suffix}</span></span>
        </article>
      `,
    )
    .join("");
}

function renderInsightList(stats) {
  const items = [
    `Highest-risk segment: ${stats.topRiskSegment}`,
    `Internet service, contract, and tenure charts refresh from the live API.`,
    `Use the prompt chips to jump straight into the most useful questions.`,
  ];

  insightListEl.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
  topRiskSegmentEl.textContent = stats.topRiskSegment;
}

function chartDataset(rows, color) {
  return {
    labels: rows.map((row) => row.label),
    datasets: [
      {
        label: "Churn rate",
        data: rows.map((row) => row.churn_rate * 100),
        backgroundColor: color,
        borderRadius: 10,
        borderSkipped: false,
      },
    ],
  };
}

function renderBarChart(canvasId, rows, color, title) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !window.Chart) {
    return;
  }

  destroyChart(canvasId);

  const chart = new Chart(canvas, {
    type: "bar",
    data: chartDataset(rows, color),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label(context) {
              return `${title}: ${formatPercent(context.parsed.y)}`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#516072",
          },
          grid: {
            display: false,
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: "#516072",
            callback(value) {
              return `${value}%`;
            },
          },
          grid: {
            color: "rgba(82, 102, 124, 0.12)",
          },
        },
      },
    },
  });

  chartInstances.set(canvasId, chart);
}

function renderPromptChips() {
  promptChipsEl.innerHTML = promptQuestions
    .map(
      (question) => `
        <button type="button" class="chip" data-question="${question.replace(/"/g, '&quot;')}">${question}</button>
      `,
    )
    .join("");

  promptChipsEl.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      questionInput.value = chip.dataset.question || "";
      questionInput.focus();
    });
  });
}

function formatCategoryRows(rows) {
  return rows.map((row) => ({
    ...row,
    churn_rate: Number(row.churn_rate || 0),
  }));
}

async function fetchJson(path, options = {}) {
  const apiBaseUrl = apiBaseUrlInput.value.trim();
  if (!apiBaseUrl) {
    throw new Error("Set an API Base URL first.");
  }

  const normalizedBaseUrl = apiBaseUrl.replace(/\/$/, "");
  const response = await fetch(`${normalizedBaseUrl}${path}`, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }

  return response.json();
}

async function loadDashboard() {
  setConnectionStatus("waiting", "Loading API");

  try {
    await fetchJson("/health");
    const stats = await fetchJson("/stats");

    renderStatCards(stats.cards || []);
    renderInsightList(stats);
    renderBarChart("internetChart", formatCategoryRows(stats.internet_service || []), "rgba(162, 134, 255, 0.88)", "Internet service churn");
    renderBarChart("contractChart", formatCategoryRows(stats.contract || []), "rgba(118, 100, 255, 0.88)", "Contract churn");
    renderBarChart("tenureChart", formatCategoryRows(stats.tenure_band || []), "rgba(85, 72, 204, 0.88)", "Tenure churn");

    setConnectionStatus("ready", "API connected");
  } catch (error) {
    setConnectionStatus("error", "API offline");
    statsCardsEl.innerHTML = `
      <article class="stat-card">
        <span class="stat-label">Dashboard unavailable</span>
        <span class="stat-value">Check backend</span>
      </article>
    `;
    insightListEl.innerHTML = `
      <li>${error.message}</li>
      <li>Start the FastAPI backend and point the API Base URL at it.</li>
      <li>Make sure GROQ_API_KEY and the MySQL settings in .env are valid.</li>
    `;
    topRiskSegmentEl.textContent = "Waiting for API data";
  }
}

apiBaseUrlInput.addEventListener("change", () => {
  const value = apiBaseUrlInput.value.trim();
  localStorage.setItem("apiBaseUrl", value);
  loadDashboard();
});

refreshBtn.addEventListener("click", () => {
  loadDashboard();
});

clearBtn.addEventListener("click", () => {
  messagesEl.innerHTML = "";
  addMessage("bot", "Conversation cleared. Ask another question when ready.");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = questionInput.value.trim();
  const apiBaseUrl = apiBaseUrlInput.value.trim();

  if (!question) {
    return;
  }

  if (!apiBaseUrl) {
    addMessage("bot", "Set an API Base URL first.");
    return;
  }

  addMessage("user", question);
  questionInput.value = "";

  sendBtn.disabled = true;
  sendBtn.textContent = "Thinking...";

  try {
    const data = await fetchJson("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    addMessage("bot", data.output || "No output returned.");
  } catch (error) {
    addMessage("bot", `Request failed: ${error.message}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Ask";
  }
});

addMessage(
  "bot",
  "Ready. Point API Base URL at the FastAPI backend, then ask a question. The backend needs a working MySQL connection and GROQ_API_KEY."
);

renderPromptChips();
loadDashboard();
