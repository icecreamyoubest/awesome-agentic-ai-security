let catalog = { meta: {}, tools: [] };
let controlsCatalog = { control_matrix: [], use_cases: [], mcp_benchmark: [], evidence_levels: {} };
let currentView = "grid";

const $ = (id) => document.getElementById(id);

function titleCase(s) {
  return String(s || "").replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
}

function scoreForPersona(tool, personaName) {
  const weights = catalog.meta.personas?.[personaName] || {};
  let weighted = 0;
  let total = 0;
  for (const [dim, weight] of Object.entries(weights)) {
    const value = Number(tool.scores?.[dim] ?? 0);
    if (value > 0) {
      weighted += value * weight;
      total += weight;
    }
  }
  if (!total) return 0;
  return Math.round((weighted / total) * 20);
}

function score100(rawFivePointScore) {
  return Math.round(Math.max(0, Math.min(5, Number(rawFivePointScore || 0))) * 20);
}

function compatClass(v) {
  if (!v) return "none";
  if (v === "native") return "native";
  return v;
}

function compatText(v) {
  if (!v) return "—";
  const map = { native: "✅ native", generic: "◐ generic", integration: "◐ integration", partial: "◐ partial", gateway: "◐ gateway" };
  return map[v] || `◐ ${v}`;
}

function unique(values) {
  return [...new Set(values)].filter(Boolean).sort((a,b) => String(a).localeCompare(String(b)));
}

function populateFilters() {
  const tools = catalog.tools;
  const categories = catalog.meta.categories || unique(tools.flatMap(t => t.category || []));
  const types = unique(tools.map(t => t.vendor_type));
  const frameworks = catalog.meta.frameworks || unique(tools.flatMap(t => Object.keys(t.frameworks || {})));
  const deployments = unique(tools.flatMap(t => t.deployment || []));
  const lifecycleStages = Object.entries(catalog.meta.lifecycle_stages || {}).map(([code, name]) => `${code} — ${name}`);
  const personas = Object.keys(catalog.meta.personas || {});
  const agenticRisks = Object.entries(catalog.meta.agentic_owasp || {}).map(([code, name]) => `${code} — ${name}`);

  fillSelect($("categoryFilter"), categories, "All categories");
  fillSelect($("typeFilter"), types, "All types", titleCase);
  fillSelect($("frameworkFilter"), frameworks, "All frameworks");
  fillSelect($("deploymentFilter"), deployments, "All modes", titleCase);
  fillSelect($("lifecycleFilter"), lifecycleStages, "All lifecycle stages", x => x, x => x.split(" — ")[0]);
  fillSelect($("agenticFilter"), agenticRisks, "All Agentic OWASP risks", x => x, x => x.slice(0,5));
  fillSelect($("personaFilter"), personas, "", x => x);
}

function fillSelect(el, values, firstLabel, labeler = x => x, valueFn = x => x) {
  el.innerHTML = firstLabel ? `<option value="">${escapeHtml(firstLabel)}</option>` : "";
  values.forEach(v => {
    const opt = document.createElement("option");
    opt.value = valueFn(v);
    opt.textContent = labeler(v);
    el.appendChild(opt);
  });
}

function getFilteredTools() {
  const q = $("search").value.trim().toLowerCase();
  const cat = $("categoryFilter").value;
  const type = $("typeFilter").value;
  const fw = $("frameworkFilter").value;
  const dep = $("deploymentFilter").value;
  const agenticRisk = $("agenticFilter").value;
  const lifecycleStage = $("lifecycleFilter").value;
  const persona = $("personaFilter").value;
  const sortBy = $("sortBy").value;

  let items = catalog.tools.filter(t => {
    const agenticLabels = (t.agentic_owasp || []).map(code => `${code} ${catalog.meta.agentic_owasp?.[code] || ""}`);
    const haystack = [
      t.name, t.org, t.vendor_type, t.license, t.description, t.maintainer_notes,
      ...(t.category || []), ...(t.owasp || []), ...(t.atlas || []), ...(t.targets || []),
      ...(t.agentic_owasp || []), ...agenticLabels,
      ...(t.lifecycle_stages || []), ...((t.lifecycle_stages || []).map(code => catalog.meta.lifecycle_stages?.[code] || "")),
      ...(t.source_basis || []),
      ...Object.keys(t.frameworks || {}), ...(t.deployment || [])
    ].join(" ").toLowerCase();
    return (!q || haystack.includes(q))
      && (!cat || (t.category || []).includes(cat))
      && (!type || t.vendor_type === type)
      && (!fw || Object.prototype.hasOwnProperty.call(t.frameworks || {}, fw))
      && (!dep || (t.deployment || []).includes(dep))
      && (!lifecycleStage || (t.lifecycle_stages || []).includes(lifecycleStage))
      && (!agenticRisk || (t.agentic_owasp || []).includes(agenticRisk));
  });

  items.sort((a,b) => {
    if (sortBy === "name") return a.name.localeCompare(b.name);
    if (sortBy === "persona") return scoreForPersona(b, persona) - scoreForPersona(a, persona) || a.name.localeCompare(b.name);
    return (b.scores?.[sortBy] || 0) - (a.scores?.[sortBy] || 0) || a.name.localeCompare(b.name);
  });
  return items;
}

function render() {
  const items = getFilteredTools();
  const persona = $("personaFilter").value;
  $("resultCount").textContent = `Showing ${items.length} of ${catalog.tools.length} tools`;
  renderCards(items, persona);
  renderTable(items, persona);
}

function renderCards(items, persona) {
  $("cards").innerHTML = items.map(t => {
    const pScore = scoreForPersona(t, persona);
    const dims = [
      ["Agentic", t.scores.agentic_readiness],
      ["MCP", t.scores.mcp_security],
      ["Runtime", t.scores.runtime],
      ["Lifecycle", t.scores.lifecycle_coverage]
    ];
    const agenticTags = (t.agentic_owasp || []).slice(0,5).map(code => `<span class="tag agentic" title="${escapeAttr(catalog.meta.agentic_owasp?.[code] || "")}">${escapeHtml(code)}</span>`).join("");
    const lifecycleTags = (t.lifecycle_stages || []).slice(0,4).map(code => `<span class="tag stage" title="${escapeAttr(catalog.meta.lifecycle_stages?.[code] || "")}">${escapeHtml(catalog.meta.lifecycle_stages?.[code] || code)}</span>`).join("");
    return `
      <article class="card">
        <div class="card-top">
          <div class="logo">${iconFor(t)}</div>
          <div class="card-title"><h3 title="${escapeHtml(t.name)}">${escapeHtml(t.name)}</h3><span>${escapeHtml(t.org)} · ${escapeHtml(t.license || "")}</span></div>
          <span class="type ${t.vendor_type}">${titleCase(t.vendor_type)}</span>
        </div>
        <p class="desc">${escapeHtml(t.description)}</p>
        <div class="tags">
          ${(t.category || []).slice(0,4).map(c => `<span class="tag">${escapeHtml(c)}</span>`).join("")}
          ${agenticTags}
          ${lifecycleTags}
          ${(t.deployment || []).map(d => `<span class="tag">${escapeHtml(titleCase(d))}</span>`).join("")}
        </div>
        <div class="scorebar">
          ${dims.map(([label,value]) => scoreRow(label,value)).join("")}
        </div>
        <div class="card-footer">
          <div class="links">
            ${t.url ? `<a href="${escapeAttr(t.url)}" target="_blank" rel="noopener">Site/GitHub ↗</a>` : ""}
            ${t.docs && t.docs !== t.url ? `<a href="${escapeAttr(t.docs)}" target="_blank" rel="noopener">Docs ↗</a>` : ""}
          </div>
          <div class="persona-score" title="Persona score for ${escapeHtml(persona)}">${pScore}/100</div>
        </div>
      </article>
    `;
  }).join("");
}

function scoreRow(label, value) {
  const safe = Math.max(0, Math.min(5, Number(value || 0)));
  const pct = safe * 20;
  return `<div class="score-row"><span>${escapeHtml(label)}</span><div class="bar"><div class="fill" style="width:${pct}%"></div></div><strong>${safe.toFixed(safe % 1 ? 1 : 0)}/5</strong></div>`;
}

function renderTable(items, persona) {
  $("toolRows").innerHTML = items.map(t => {
    const fws = Object.entries(t.frameworks || {}).map(([k,v]) => `${k} (${v})`).join(", ");
    const risks = (t.agentic_owasp || []).map(code => `<span class="tag agentic" title="${escapeAttr(catalog.meta.agentic_owasp?.[code] || "")}">${escapeHtml(code)}</span>`).join(" ") || "—";
    return `<tr>
      <td><strong>${escapeHtml(t.name)}</strong><br><span class="small">${escapeHtml(t.org)}</span></td>
      <td class="small">${escapeHtml(titleCase(t.vendor_type))}</td>
      <td>${(t.category || []).slice(0,4).map(c => `<span class="tag">${escapeHtml(c)}</span>`).join(" ")}</td>
      <td>${risks}</td>
      <td class="small">${escapeHtml(fws)}</td>
      <td><strong>${score100(t.scores.agentic_readiness)}</strong>/100</td>
      <td><strong>${score100(t.scores.mcp_security)}</strong>/100</td>
      <td>${t.scores.runtime}/5</td>
      <td>${t.scores.red_team}/5</td>
      <td><strong>${scoreForPersona(t, persona)}</strong>/100</td>
    </tr>`;
  }).join("");
}


function renderControlMatrix() {
  const body = $("controlMatrixBody");
  if (!body) return;
  const risks = catalog.meta.agentic_owasp || {};
  body.innerHTML = (controlsCatalog.control_matrix || []).map(row => {
    const mappedTools = catalog.tools
      .filter(t => (t.agentic_owasp || []).includes(row.asi))
      .sort((a,b) => (b.scores?.agentic_readiness || 0) - (a.scores?.agentic_readiness || 0))
      .slice(0, 8);
    return `<tr>
      <td><strong>${escapeHtml(row.asi)}</strong><br><span class="small">${escapeHtml(risks[row.asi] || "")}</span></td>
      <td>${(row.controls || []).map(x => `<span class="tag control">${escapeHtml(x)}</span>`).join(" ")}</td>
      <td>${(row.capabilities || []).map(x => `<span class="tag capability">${escapeHtml(x)}</span>`).join(" ")}</td>
      <td>${mappedTools.map(t => `<span class="tag">${escapeHtml(t.name)}</span>`).join(" ") || "—"}</td>
    </tr>`;
  }).join("");
}

function renderLifecycleHeatmap() {
  const head = $("heatmapHead");
  const body = $("heatmapBody");
  if (!head || !body) return;
  const stages = Object.entries(catalog.meta.lifecycle_stages || {});
  const tools = [...catalog.tools]
    .sort((a,b) => (b.scores?.lifecycle_coverage || 0) - (a.scores?.lifecycle_coverage || 0))
    .slice(0, 35);
  head.innerHTML = `<tr><th>Tool</th>${stages.map(([code,name]) => `<th title="${escapeAttr(name)}">${escapeHtml(shortStage(name))}</th>`).join("")}</tr>`;
  body.innerHTML = tools.map(t => `<tr>
    <td><strong>${escapeHtml(t.name)}</strong><br><span class="small">${escapeHtml(t.org)}</span></td>
    ${stages.map(([code,name]) => {
      const active = (t.lifecycle_stages || []).includes(code);
      const strength = active ? Math.max(1, Math.min(5, Number(t.scores?.lifecycle_coverage || 1))) : 0;
      return `<td class="heat-cell level-${Math.round(strength)}" title="${escapeAttr(t.name + ' · ' + name)}">${active ? '●' : ''}</td>`;
    }).join("")}
  </tr>`).join("");
}

function shortStage(name) {
  return String(name).replace("Augment / Fine-tune Data", "Data").replace("Develop & Experiment", "Dev").replace("Test & Evaluate", "Test").replace("Scope & Plan", "Plan");
}

function renderUseCases() {
  const el = $("useCaseGrid");
  if (!el) return;
  el.innerHTML = (controlsCatalog.use_cases || []).map(uc => {
    const candidates = catalog.tools
      .filter(t => (uc.asi || []).some(code => (t.agentic_owasp || []).includes(code)))
      .sort((a,b) => (b.scores?.agentic_readiness || 0) - (a.scores?.agentic_readiness || 0))
      .slice(0, 7);
    return `<div class="risk-card usecase-card">
      <div class="risk-code">${escapeHtml(uc.id.replaceAll("_", " "))}</div>
      <h3>${escapeHtml(uc.title)}</h3>
      <p>${escapeHtml(uc.description)}</p>
      <div class="mini-title">Capabilities</div>
      <div class="risk-tools">${(uc.required_capabilities || []).map(x => `<span>${escapeHtml(x)}</span>`).join("")}</div>
      <div class="mini-title">Candidate tools</div>
      <div class="risk-tools">${candidates.map(t => `<span>${escapeHtml(t.name)}</span>`).join("")}</div>
    </div>`;
  }).join("");
}

function renderMcpBenchmark() {
  const body = $("mcpBenchmarkBody");
  if (!body) return;
  const risks = catalog.meta.agentic_owasp || {};
  body.innerHTML = (controlsCatalog.mcp_benchmark || []).map(test => `<tr>
    <td><strong>${escapeHtml(test.id)}</strong></td>
    <td>${escapeHtml(test.scenario)}</td>
    <td>${(test.asi || []).map(code => `<span class="tag agentic" title="${escapeAttr(risks[code] || "")}">${escapeHtml(code)}</span>`).join(" ")}</td>
    <td>${(test.expected_controls || []).map(x => `<span class="tag control">${escapeHtml(x)}</span>`).join(" ")}</td>
    <td class="small">${escapeHtml(test.status || "planned")}</td>
  </tr>`).join("");
}

function renderEvidenceModel() {
  const el = $("evidenceGrid");
  if (!el) return;
  el.innerHTML = Object.entries(controlsCatalog.evidence_levels || {}).map(([k,v]) => `
    <div class="dimension"><strong>${escapeHtml(titleCase(k))}</strong><span>${escapeHtml(v)}</span></div>
  `).join("");
}

function renderMatrix() {
  const frameworks = catalog.meta.frameworks || [];
  $("matrixHead").innerHTML = `<tr><th>Tool</th><th>Type</th>${frameworks.map(f => `<th>${escapeHtml(f)}</th>`).join("")}</tr>`;
  $("matrixBody").innerHTML = catalog.tools.map(t => `
    <tr>
      <td><strong>${escapeHtml(t.name)}</strong><br><span class="small">${escapeHtml(t.org)}</span></td>
      <td class="small">${escapeHtml(titleCase(t.vendor_type))}</td>
      ${frameworks.map(f => {
        const v = t.frameworks?.[f];
        return `<td class="compat ${compatClass(v)}">${compatText(v)}</td>`;
      }).join("")}
    </tr>
  `).join("");
}

function renderDimensions() {
  const dims = catalog.meta.dimensions || {};
  $("dimensionGrid").innerHTML = Object.entries(dims).map(([k,v]) => `
    <div class="dimension"><strong>${escapeHtml(titleCase(k))}</strong><span>${escapeHtml(v)}</span></div>
  `).join("");
}


function renderLifecycle() {
  const stages = catalog.meta.lifecycle_stages || {};
  const descs = catalog.meta.lifecycle_stage_descriptions || {};
  const toolsByStage = {};
  for (const t of catalog.tools) {
    for (const code of (t.lifecycle_stages || [])) {
      toolsByStage[code] ||= [];
      toolsByStage[code].push(t);
    }
  }
  const el = $("lifecycleGrid");
  if (!el) return;
  el.innerHTML = Object.entries(stages).map(([code, name]) => {
    const tools = (toolsByStage[code] || []).sort((a,b) => (b.scores.lifecycle_coverage || 0) - (a.scores.lifecycle_coverage || 0)).slice(0,8);
    return `<div class="risk-card lifecycle-card">
      <div class="risk-code">${escapeHtml(code.replaceAll("_", " "))}</div>
      <h3>${escapeHtml(name)}</h3>
      <p>${escapeHtml(descs[code] || "Agentic SecOps lifecycle stage.")}</p>
      <div class="risk-tools">${tools.map(t => `<span>${escapeHtml(t.name)}</span>`).join("") || "<span>No mapped tools yet</span>"}</div>
    </div>`;
  }).join("");
}

function renderAgenticOwasp() {
  const risks = catalog.meta.agentic_owasp || {};
  const toolsByRisk = {};
  for (const t of catalog.tools) {
    for (const code of (t.agentic_owasp || [])) {
      toolsByRisk[code] ||= [];
      toolsByRisk[code].push(t);
    }
  }
  $("agenticGrid").innerHTML = Object.entries(risks).map(([code, name]) => {
    const tools = (toolsByRisk[code] || []).sort((a,b) => (b.scores.agentic_readiness || 0) - (a.scores.agentic_readiness || 0)).slice(0,6);
    return `<div class="risk-card">
      <div class="risk-code">${escapeHtml(code)}</div>
      <h3>${escapeHtml(name)}</h3>
      <p>${escapeHtml(agenticRiskDescription(code))}</p>
      <div class="risk-tools">${tools.map(t => `<span>${escapeHtml(t.name)}</span>`).join("") || "<span>No mapped tools yet</span>"}</div>
    </div>`;
  }).join("");
}

function renderScoreModels() {
  const ar = catalog.meta.agentic_readiness_formula || {};
  const mcp = catalog.meta.mcp_security_formula || {};
  $("agenticFormula").innerHTML = formulaHtml(ar, "Agentic Readiness");
  $("mcpFormula").innerHTML = formulaHtml(mcp, "MCP Security");
  const mcpDims = catalog.meta.mcp_score_dimensions || {};
  $("mcpDimensionGrid").innerHTML = Object.entries(mcpDims).map(([k,v]) => `
    <div class="dimension"><strong>${escapeHtml(titleCase(k))}</strong><span>${escapeHtml(v)}</span></div>
  `).join("");
}

function formulaHtml(formula, name) {
  const terms = Object.entries(formula).map(([k,w]) => `${Math.round(w*100)}% × ${titleCase(k)}`).join(" + ");
  return `<strong>${escapeHtml(name)}:</strong> <code>${escapeHtml(terms)}</code>`;
}

function agenticRiskDescription(code) {
  const map = {
    ASI01: "Goal, objective, or decision-path manipulation through prompts, retrieved content, or tool outputs.",
    ASI02: "Unsafe or exploited use of connected tools, functions, APIs, files, browsers, or automations.",
    ASI03: "Abuse of delegated identity, excessive privileges, long-lived credentials, or weak authorization boundaries.",
    ASI04: "Compromised models, agents, MCP servers, plugins, dependencies, prompts, or build artifacts.",
    ASI05: "Unexpected code execution via agent-generated code, interpreters, shells, plugins, or tool chains.",
    ASI06: "Poisoning or leaking memory, RAG context, vector stores, embeddings, and persistent state.",
    ASI07: "Unsafe handoffs, delegation, message passing, or trust assumptions across agents and services.",
    ASI08: "Failure propagation across chained tools, agents, retries, queues, and autonomous workflows.",
    ASI09: "Over-trust, deceptive outputs, unsafe approvals, or weak human-in-the-loop design.",
    ASI10: "Unauthorized, hidden, unmanaged, or adversarial agents acting outside governance controls."
  };
  return map[code] || "Agentic application risk.";
}

function iconFor(t) {
  const cats = (t.category || []).join(" ");
  if (cats.includes("MCP")) return "🔌";
  if (cats.includes("Agent")) return "🤖";
  if (cats.includes("Red Team")) return "🎯";
  if (cats.includes("Guardrails")) return "🛡️";
  if (cats.includes("Data")) return "🔒";
  if (cats.includes("Observability")) return "🔭";
  if (cats.includes("Supply")) return "⛓️";
  if (cats.includes("AI-SPM")) return "📊";
  return "⚙️";
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s); }

function bindEvents() {
  ["search","categoryFilter","typeFilter","frameworkFilter","deploymentFilter","lifecycleFilter","agenticFilter","personaFilter","sortBy"].forEach(id => $(id).addEventListener("input", render));
  $("resetFilters").addEventListener("click", () => {
    ["search","categoryFilter","typeFilter","frameworkFilter","deploymentFilter","lifecycleFilter","agenticFilter"].forEach(id => $(id).value = "");
    $("sortBy").value = "persona";
    render();
  });
  $("gridView").addEventListener("click", () => setView("grid"));
  $("tableView").addEventListener("click", () => setView("table"));
}

function setView(view) {
  currentView = view;
  $("gridView").classList.toggle("active", view === "grid");
  $("tableView").classList.toggle("active", view === "table");
  $("cards").classList.toggle("hidden", view !== "grid");
  $("tableWrap").classList.toggle("hidden", view !== "table");
}

async function init() {
  try {
    const [res, controlsRes] = await Promise.all([
      fetch("./data/tools.json", { cache: "no-store" }),
      fetch("./data/controls.json", { cache: "no-store" })
    ]);
    catalog = await res.json();
    controlsCatalog = await controlsRes.json();
    $("statTools").textContent = catalog.tools.length;
    $("statCategories").textContent = catalog.meta.categories.length;
    $("statFrameworks").textContent = catalog.meta.frameworks.length;
    $("statUpdated").textContent = catalog.meta.updated;
    $("versionBadge").textContent = catalog.meta.version || "v0.2";
    populateFilters();
    bindEvents();
    render();
    renderMatrix();
    renderDimensions();
    renderLifecycle();
    renderAgenticOwasp();
    renderControlMatrix();
    renderLifecycleHeatmap();
    renderUseCases();
    renderMcpBenchmark();
    renderEvidenceModel();
    renderScoreModels();
  } catch (err) {
    document.body.insertAdjacentHTML("afterbegin", `<div class="note"><strong>Failed to load catalog:</strong> ${escapeHtml(err.message)}</div>`);
    console.error(err);
  }
}
init();
