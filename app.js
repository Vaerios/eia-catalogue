"use strict";

const form = document.getElementById("filters");
const search = document.getElementById("search");
const chapter = document.getElementById("chapter");
const field = document.getElementById("field");
const entries = [...document.querySelectorAll(".entry")];
const resultCount = document.getElementById("result-count");
const emptyState = document.getElementById("empty-state");
const moreArea = document.getElementById("more-area");
const shownCount = document.getElementById("shown-count");
const loadMore = document.getElementById("load-more");
const pageSize = 12;
let visibleCount = pageSize;

function clean(value) {
  return value.normalize("NFKC").toLowerCase().replace(/\s+/g, "");
}

const index = entries.map((node) => ({
  node,
  text: clean(node.textContent),
  number: node.dataset.number,
  oldNumbers: node.dataset.old.split(" "),
  chapter: node.dataset.chapter,
  fields: new Set(node.dataset.fields.split(" ")),
}));

function readQuery(value) {
  const query = clean(value);
  const oldNumber = query.match(/^(?:旧版?|2021(?:年版)?)(?:第)?(\d+)(?:项)?$/);
  if (oldNumber) return (entry) => entry.oldNumbers.includes(oldNumber[1]);
  const newNumber = query.match(/^(?:新版?|2027(?:年版)?|第|#)(?:第)?(\d+)(?:项)?$/);
  if (newNumber) return (entry) => entry.number === newNumber[1];
  const terms = value.trim().split(/\s+/).filter(Boolean).map(clean);
  return (entry) => terms.every((term) => entry.text.includes(term));
}

function selectValue(control, value) {
  control.value = [...control.options].some((option) => option.value === value) ? value : "";
}

function readURL() {
  const params = new URLSearchParams(location.search);
  search.value = params.get("q") ?? "";
  selectValue(chapter, params.get("chapter"));
  selectValue(field, params.get("field"));
}

function saveURL() {
  // Local file previews still filter normally. Their URL cannot be rewritten in every browser.
  if (!/^https?:$/.test(location.protocol)) return;
  const url = new URL(location.href);
  for (const control of [search, chapter, field]) {
    const value = control.value.trim();
    if (value) url.searchParams.set(control.name, value);
    else url.searchParams.delete(control.name);
  }
  if (/^#item-\d+$/.test(url.hash)) url.hash = "items";
  if (url.href !== location.href) history.replaceState(null, "", url);
}

function render({ focusNew = false, pin = null } = {}) {
  const matchesQuery = readQuery(search.value);
  const matching = index.filter((entry) => (
    matchesQuery(entry) &&
    (!chapter.value || entry.chapter === chapter.value) &&
    (!field.value || entry.fields.has(field.value))
  ));
  const visible = new Set(matching.slice(0, visibleCount));
  if (pin) visible.add(pin);
  for (const entry of index) entry.node.hidden = !visible.has(entry);

  const filtering = Boolean(search.value.trim() || chapter.value || field.value);
  resultCount.textContent = filtering
    ? `找到 ${matching.length} 项修订条目`
    : `${index.length} 项修订条目`;
  emptyState.hidden = matching.length > 0 || Boolean(pin);
  moreArea.hidden = matching.length <= visibleCount;
  shownCount.textContent = `已显示 ${Math.min(visibleCount, matching.length)} / ${matching.length} 项`;
  if (focusNew) matching[visibleCount - pageSize]?.node.querySelector("summary").focus();
}

function resetPage() {
  visibleCount = pageSize;
  saveURL();
  render();
}

function revealLinkedEntry() {
  const id = location.hash.match(/^#item-(\d+)$/)?.[1];
  const pinned = index.find((entry) => entry.number === id);
  render({ pin: pinned });
  if (pinned) {
    pinned.node.open = true;
    requestAnimationFrame(() => pinned.node.scrollIntoView({ block: "start" }));
  }
}

form.hidden = false;
readURL();
revealLinkedEntry();
search.addEventListener("input", resetPage);
chapter.addEventListener("change", resetPage);
field.addEventListener("change", resetPage);
form.addEventListener("submit", (event) => event.preventDefault());
form.addEventListener("reset", () => requestAnimationFrame(resetPage));
loadMore.addEventListener("click", () => {
  visibleCount += pageSize;
  render({ focusNew: true });
});
document.getElementById("search-jump").addEventListener("click", () => {
  requestAnimationFrame(() => search.focus({ preventScroll: true }));
});
window.addEventListener("hashchange", revealLinkedEntry);
window.addEventListener("popstate", () => {
  readURL();
  visibleCount = pageSize;
  revealLinkedEntry();
});
