const DATA_URL = "./data/surnames-2010.lookup.json";
const NOT_FOUND_MESSAGE =
  "Not found in the 2010 Census surname file; this usually means fewer than 100 occurrences.";

const form = document.getElementById("lookup-form");
const input = document.getElementById("surname-input");
const resultCard = document.getElementById("result-card");
const searchButton = document.getElementById("search-button");
const exampleButtons = document.querySelectorAll(".example-chip");

let lookupPromise = null;

function normalizeSurname(value) {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .replace(/[^A-Z]/g, "");
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

async function loadLookup() {
  if (!lookupPromise) {
    lookupPromise = fetch(DATA_URL).then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to load lookup data (${response.status}).`);
      }
      return response.json();
    });
  }
  return lookupPromise;
}

function showCard(html) {
  resultCard.innerHTML = html;
  resultCard.classList.remove("hidden");
}

function renderFound(normalized, rank, count) {
  showCard(`
    <p class="result-state">Match found in the official 2010 Census surname file.</p>
    <dl class="result-grid">
      <div class="result-item">
        <dt>Normalized surname</dt>
        <dd>${normalized}</dd>
      </div>
      <div class="result-item">
        <dt>Count</dt>
        <dd>${formatNumber(count)}</dd>
      </div>
      <div class="result-item">
        <dt>Rank</dt>
        <dd>${formatNumber(rank)}</dd>
      </div>
    </dl>
  `);
}

function renderNotFound(normalized) {
  showCard(`
    <p class="result-state">No published 2010 Census match.</p>
    <dl class="result-grid">
      <div class="result-item">
        <dt>Normalized surname</dt>
        <dd>${normalized}</dd>
      </div>
    </dl>
    <p class="result-message">${NOT_FOUND_MESSAGE}</p>
  `);
}

function renderError(message) {
  showCard(`
    <p class="result-state">Lookup error.</p>
    <p class="result-message error">${message}</p>
  `);
}

async function runLookup(rawValue) {
  const normalized = normalizeSurname(rawValue);

  if (!normalized) {
    renderError("Enter at least one letter.");
    return;
  }

  searchButton.disabled = true;
  searchButton.textContent = "Searching...";

  try {
    const lookup = await loadLookup();
    const match = lookup[normalized];

    if (match) {
      const [rank, count] = match;
      renderFound(normalized, rank, count);
    } else {
      renderNotFound(normalized);
    }
  } catch (error) {
    console.error(error);
    renderError(
      "Could not load the local lookup dataset. Run this app through a local server or check that data/surnames-2010.lookup.json is present."
    );
  } finally {
    searchButton.disabled = false;
    searchButton.textContent = "Search";
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runLookup(input.value);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    runLookup(input.value);
  }
});

for (const button of exampleButtons) {
  button.addEventListener("click", () => {
    const example = button.dataset.example ?? "";
    input.value = example;
    runLookup(example);
    input.focus();
    input.select();
  });
}

window.addEventListener("DOMContentLoaded", () => {
  // Warm the cache after first paint without blocking interaction.
  loadLookup().catch(() => {});
});
