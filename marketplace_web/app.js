const normalize = (value) => value.toLocaleLowerCase().trim();

function selected(name, values) {
  const checked = [...document.querySelectorAll(`input[name="${name}"]:checked`)].map(
    (input) => input.value,
  );
  if (checked.length === 0) return true;
  const available = normalize(values).split(/\s+/);
  return checked.some((value) => available.includes(value));
}

function applyFilters() {
  const query = normalize(document.querySelector("#skill-search")?.value ?? "");
  let visible = 0;
  document.querySelectorAll("[data-skill-card]").forEach((card) => {
    const matchesText = normalize(card.textContent).includes(query);
    const matchesTier = selected("tier", card.dataset.tier);
    const matchesClient = selected("client", card.dataset.clients);
    const matchesWrite = selected("write", card.dataset.writeCapable);
    card.hidden = !(matchesText && matchesTier && matchesClient && matchesWrite);
    if (!card.hidden) visible += 1;
  });
  const count = document.querySelector("#visible-count");
  if (count) count.textContent = String(visible);
  const empty = document.querySelector("#empty-result");
  if (empty) empty.hidden = visible !== 0;
}

function clearFilters() {
  document.querySelectorAll(".filter-index input[type='checkbox']").forEach((input) => {
    input.checked = false;
  });
  const search = document.querySelector("#skill-search");
  if (search) search.value = "";
  applyFilters();
  search?.focus();
}

function activateTab(tab, focus = false) {
  const tablist = tab.closest('[role="tablist"]');
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];
  tabs.forEach((candidate) => {
    const active = candidate === tab;
    candidate.setAttribute("aria-selected", String(active));
    candidate.tabIndex = active ? 0 : -1;
    const panel = document.getElementById(candidate.getAttribute("aria-controls"));
    if (panel) panel.hidden = !active;
  });
  if (focus) tab.focus();
}

function initializeTabs() {
  document.querySelectorAll("[data-tabs]").forEach((group) => {
    const tabs = [...group.querySelectorAll('[role="tab"]')];
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => activateTab(tab));
      tab.addEventListener("keydown", (event) => {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        const offset = event.key === "ArrowRight" ? 1 : -1;
        const next = tabs[(tabs.indexOf(tab) + offset + tabs.length) % tabs.length];
        activateTab(next, true);
      });
    });
    const initial = tabs.find((tab) => tab.getAttribute("aria-selected") === "true") ?? tabs[0];
    if (initial) activateTab(initial);
  });
}

let statusTimer;

function announceCopy(message) {
  const status = document.querySelector("#copy-status");
  if (!status) return;
  status.textContent = message;
  status.dataset.visible = "true";
  window.clearTimeout(statusTimer);
  statusTimer = window.setTimeout(() => {
    status.dataset.visible = "false";
  }, 1800);
}

async function copyTarget(button) {
  const target = document.getElementById(button.dataset.copyTarget);
  if (!target) return;
  try {
    await navigator.clipboard.writeText(target.textContent);
    announceCopy("Copied to clipboard.");
  } catch (_error) {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(target);
    selection.removeAllRanges();
    selection.addRange(range);
    announceCopy("Clipboard unavailable. Command selected for manual copy.");
  }
}

document.querySelector("#skill-search")?.addEventListener("input", applyFilters);
document.querySelectorAll(".filter-index input").forEach((input) => {
  input.addEventListener("change", applyFilters);
});
document.querySelector("#clear-filters")?.addEventListener("click", clearFilters);
document.querySelectorAll("[data-copy-target]").forEach((button) => {
  button.addEventListener("click", () => copyTarget(button));
});

initializeTabs();
applyFilters();
