"use strict";

let DATA = { summary: {}, opportunities: [] };
const state = { search: "", type: "", agency: "", minScore: 0, sortKey: "posted_date", sortDir: -1 };

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function init() {
  try {
    const res = await fetch("./data.json", { cache: "no-store" });
    DATA = await res.json();
  } catch (e) {
    $("#subtitle").textContent = "Could not load data.json.";
    return;
  }
  renderSummary(DATA.summary || {});
  populateFilters(DATA.opportunities || []);
  wireControls();
  render();
}

function renderSummary(s) {
  const total = s.total_kept || 0;
  $("#subtitle").textContent =
    `${total} kept opportunities · evaluated ${s.evaluated_total || 0} · updated ${s.last_updated || "—"}`
    + (s.any_ai ? "" : " · scores are keyword pre-filter (AI not yet applied)");
  const list = (obj) => Object.entries(obj || {}).sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `<li><span>${esc(k)}</span><span>${v}</span></li>`).join("");
  const dl = s.deadlines_within || {};
  $("#summary").innerHTML = `
    <div class="card"><h3>Total kept</h3><div class="big">${total}</div></div>
    <div class="card"><h3>By notice type</h3><ul>${list(s.by_notice_type)}</ul></div>
    <div class="card"><h3>By score band</h3><ul>${list(s.by_score_band)}</ul></div>
    <div class="card"><h3>Top agencies</h3><ul>${
      (s.top_agencies || []).map(a => `<li><span>${esc(a.name)}</span><span>${a.count}</span></li>`).join("")
    }</ul></div>
    <div class="card"><h3>Deadlines within</h3><ul>${
      Object.keys(dl).map(d => `<li><span>${d} days</span><span>${dl[d]}</span></li>`).join("")
    }</ul></div>`;
}

function populateFilters(opps) {
  const types = [...new Set(opps.map(o => o.notice_type).filter(Boolean))].sort();
  const agencies = [...new Set(opps.map(o => o.agency_group).filter(Boolean))].sort();
  $("#filter-type").innerHTML = '<option value="">All notice types</option>'
    + types.map(t => `<option>${esc(t)}</option>`).join("");
  $("#filter-agency").innerHTML = '<option value="">All agencies</option>'
    + agencies.map(a => `<option>${esc(a)}</option>`).join("");
}

function wireControls() {
  let t;
  $("#search").addEventListener("input", (e) => {
    clearTimeout(t); t = setTimeout(() => { state.search = e.target.value.toLowerCase(); render(); }, 150);
  });
  $("#filter-type").addEventListener("change", (e) => { state.type = e.target.value; render(); });
  $("#filter-agency").addEventListener("change", (e) => { state.agency = e.target.value; render(); });
  $("#min-score").addEventListener("input", (e) => {
    state.minScore = +e.target.value; $("#min-score-val").textContent = e.target.value; render();
  });
  $("#clear").addEventListener("click", () => {
    Object.assign(state, { search: "", type: "", agency: "", minScore: 0 });
    $("#search").value = ""; $("#filter-type").value = ""; $("#filter-agency").value = "";
    $("#min-score").value = 0; $("#min-score-val").textContent = "0"; render();
  });
  document.querySelectorAll("thead th[data-key]").forEach(th => {
    th.addEventListener("click", () => {
      const k = th.dataset.key;
      if (state.sortKey === k) state.sortDir *= -1; else { state.sortKey = k; state.sortDir = 1; }
      render();
    });
  });
  $("#modal").addEventListener("click", (e) => { if (e.target.dataset.close !== undefined) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
}

function applyFilters(opps) {
  return opps.filter(o => {
    if (state.type && o.notice_type !== state.type) return false;
    if (state.agency && o.agency_group !== state.agency) return false;
    if ((o.score || 0) < state.minScore) return false;
    if (state.search) {
      const hay = `${o.title} ${o.agency_short} ${o.agency_full}`.toLowerCase();
      if (!hay.includes(state.search)) return false;
    }
    return true;
  });
}

function sortRows(rows) {
  const k = state.sortKey, dir = state.sortDir;
  return rows.slice().sort((a, b) => {
    let x = a[k], y = b[k];
    if (x == null) return 1; if (y == null) return -1;
    if (typeof x === "string") { x = x.toLowerCase(); y = String(y).toLowerCase(); }
    return x < y ? -dir : x > y ? dir : 0;
  });
}

function deadlineCell(o) {
  if (!o.response_deadline) return "—";
  const d = o.deadline_in_days;
  const soon = d != null && d >= 0 && d <= 14 ? " class='deadline-soon'" : "";
  const tail = d != null ? ` (${d}d)` : "";
  return `<span${soon}>${esc(o.response_deadline)}${tail}</span>`;
}

function render() {
  const rows = sortRows(applyFilters(DATA.opportunities || []));
  $("#empty").hidden = (DATA.opportunities || []).length > 0;
  $("#count").textContent = `${rows.length} of ${(DATA.opportunities || []).length} shown`;
  $("#rows").innerHTML = rows.map((o, i) => {
    const idx = DATA.opportunities.indexOf(o);
    const badge = o.ai_generated ? '<span class="badge ai">AI</span>' : '<span class="badge kw">Keyword</span>';
    const sam = o.ui_link ? `<a href="${esc(o.ui_link)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">open</a>` : "";
    return `<tr data-idx="${idx}" onclick="openModal(${idx})">
      <td>${esc(o.posted_date)}</td>
      <td class="title-cell">${esc(o.title)}</td>
      <td>${esc(o.agency_short)}</td>
      <td>${esc(o.notice_type)}</td>
      <td><span class="score">${o.score == null ? "—" : o.score}</span>${badge}</td>
      <td>${deadlineCell(o)}</td>
      <td>${sam}</td>
    </tr>`;
  }).join("");
}

window.openModal = function (idx) {
  const o = DATA.opportunities[idx];
  if (!o) return;
  $("#m-title").textContent = o.title;
  const naics = (o.naics || []).join(", ") || "—";
  const scoreLbl = o.ai_generated ? "AI relevance" : "Keyword score";
  $("#m-meta").innerHTML = [
    `<div><b>Agency:</b> ${esc(o.agency_full)}</div>`,
    `<div><b>Notice type:</b> ${esc(o.notice_type)}</div>`,
    `<div><b>NAICS:</b> ${esc(naics)}</div>`,
    `<div><b>Posted:</b> ${esc(o.posted_date)} &nbsp; <b>Deadline:</b> ${esc(o.response_deadline || "—")}</div>`,
    `<div><b>${scoreLbl}:</b> ${o.score == null ? "—" : o.score}/100</div>`,
  ].join("");
  const link = $("#m-link");
  if (o.ui_link) { link.href = o.ui_link; link.hidden = false; } else { link.hidden = true; }
  $("#m-writeup").innerHTML = o.writeup_html || "<p class='muted'>No write-up available.</p>";
  $("#modal").hidden = false;
};

function closeModal() { $("#modal").hidden = true; }

init();
