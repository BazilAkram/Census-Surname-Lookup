const DATA_URL = "./data/surnames.lookup.json";
const LOOKUP_SCHEMA = [
  "rank",
  "count",
  "prop100k",
  "countwhite",
  "countblack",
  "countaian",
  "countapi",
  "count2prace",
  "counthispanic",
];
const NOT_FOUND_MESSAGE =
  "Not found in the 2020 Census last-name file; this usually means fewer than 100 occurrences.";
const DEMOGRAPHIC_FIELDS = [
  ["countwhite", "Non-Hispanic White alone"],
  ["countblack", "Non-Hispanic Black alone"],
  ["countaian", "Non-Hispanic American Indian / Alaska Native alone"],
  ["countapi", "Non-Hispanic Asian / NHPI alone"],
  ["count2prace", "Non-Hispanic two or more races"],
  ["counthispanic", "Hispanic or Latino"],
];

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

function formatDecimal(value, maximumFractionDigits = 2) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  }).format(value);
}

function formatProp100k(value) {
  if (value == null) {
    return "Unavailable";
  }
  return formatDecimal(value);
}

function formatPercentFromCount(groupCount, totalCount) {
  if (!totalCount) {
    return "0%";
  }

  return `${formatDecimal((groupCount / totalCount) * 100)}%`;
}

function parseLookupPayload(payload) {
  if (
    payload &&
    typeof payload === "object" &&
    !Array.isArray(payload) &&
    payload.surnames &&
    Array.isArray(payload.schema)
  ) {
    return {
      entries: payload.surnames,
      schema: payload.schema,
    };
  }

  return {
    entries: payload,
    schema: LOOKUP_SCHEMA,
  };
}

function materializeEntry(rawEntry, schema) {
  if (!rawEntry) {
    return null;
  }

  if (!Array.isArray(rawEntry)) {
    return rawEntry;
  }

  return Object.fromEntries(schema.map((key, index) => [key, rawEntry[index] ?? null]));
}

async function loadLookup() {
  if (!lookupPromise) {
    lookupPromise = fetch(DATA_URL).then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to load lookup data (${response.status}).`);
      }

      const payload = await response.json();
      return parseLookupPayload(payload);
    });
  }

  return lookupPromise;
}

function showCard(html) {
  resultCard.innerHTML = html;
  resultCard.classList.remove("hidden");
}

function renderFound(normalized, match) {
  const demographicItems = DEMOGRAPHIC_FIELDS.map(
    ([countKey, label]) => `
      <div class="result-item">
        <dt>${label}</dt>
        <dd class="result-value-stack">
          <span class="result-value-main">${formatPercentFromCount(match[countKey], match.count)}</span>
          <span class="result-value-sub">${formatNumber(match[countKey])}</span>
        </dd>
      </div>
    `
  ).join("");

  showCard(`
    <p class="result-state">Match found in the official 2020 Census last-name file.</p>
    <dl class="result-grid">
      <div class="result-item">
        <dt>Normalized surname</dt>
        <dd>${normalized}</dd>
      </div>
      <div class="result-item">
        <dt>Count</dt>
        <dd>${formatNumber(match.count)}</dd>
      </div>
      <div class="result-item">
        <dt>Rank</dt>
        <dd>${formatNumber(match.rank)}</dd>
      </div>
      <div class="result-item">
        <dt>PROP100K</dt>
        <dd>${formatProp100k(match.prop100k)}</dd>
      </div>
    </dl>
    <div class="result-section">
      <p class="result-section-title">Race / Hispanic breakdown</p>
      <dl class="result-grid demographic-grid">
        ${demographicItems}
      </dl>
    </div>
  `);
}

function renderNotFound(normalized) {
  showCard(`
    <p class="result-state">No published 2020 Census match.</p>
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
    const match = materializeEntry(lookup.entries[normalized], lookup.schema);

    if (match) {
      renderFound(normalized, match);
    } else {
      renderNotFound(normalized);
    }
  } catch (error) {
    console.error(error);
    renderError(
      "Could not load the local lookup dataset. Run this app through a local server or check that data/surnames.lookup.json is present."
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
