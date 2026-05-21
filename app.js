let updateStatus = null;
let pendingUpdates = null;
let roadmapUpdates = null;
let updateSources = null;
let benchmarkRecommendations = null;
let evidenceDiffs = null;
let prCandidates = null;
let roadmapBoard = null;
let catalog = { meta: {}, tools: [] };
let controlsCatalog = { control_matrix: [], use_cases: [], mcp_benchmark: [], evidence_levels: {}, asi_lifecycle_matrix: [] };
let evidenceCatalog = { meta: {}, tools: {} };
let benchmarkCases = [];
let incidentCatalog = { meta: {}, incidents: [] };
let architectureCatalog = { meta: {}, architectures: [] };
let sourceIndex = { meta: {}, sources: [] };
let claimsCatalog = { meta: {}, claims: [] };
let architectureTemplates = { meta: {}, templates: [] };
let releaseLog = { meta: {}, releases: [] };
let selectedCompare = new Set();
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
            <button class="link-button" type="button" data-tool-detail="${escapeAttr(t.id)}">Details</button>
            <label class="compare-toggle"><input type="checkbox" data-compare-id="${escapeAttr(t.id)}" ${selectedCompare.has(t.id) ? "checked" : ""}> Compare</label>
            ${t.url ? `<a href="${escapeAttr(t.url)}" target="_blank" rel="noopener">Site/GitHub ↗</a>` : ""}
            ${t.docs && t.docs !== t.url ? `<a href="${escapeAttr(t.docs)}" target="_blank" rel="noopener">Docs ↗</a>` : ""}
          </div>
          <div class="persona-score" title="Persona score for ${escapeHtml(persona)}">${pScore}/100</div>
        </div>
      </article>
    `;
  }).join("");
  bindToolCardActions();
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


function bindToolCardActions() {
  document.querySelectorAll("[data-tool-detail]").forEach(btn => {
    btn.addEventListener("click", () => openToolDetail(btn.getAttribute("data-tool-detail")));
  });
  document.querySelectorAll("[data-compare-id]").forEach(cb => {
    cb.addEventListener("change", () => toggleCompare(cb.getAttribute("data-compare-id"), cb.checked, cb));
  });
}

function toggleCompare(id, checked, checkboxEl) {
  if (checked) {
    if (selectedCompare.size >= 4 && !selectedCompare.has(id)) {
      checkboxEl.checked = false;
      alert("Compare mode supports up to 4 tools.");
      return;
    }
    selectedCompare.add(id);
  } else {
    selectedCompare.delete(id);
  }
  renderCompare();
}

function openToolDetail(id) {
  const tool = catalog.tools.find(t => t.id === id);
  if (!tool) return;
  const risks = catalog.meta.agentic_owasp || {};
  const stages = catalog.meta.lifecycle_stages || {};
  const evidence = evidenceCatalog.tools?.[id] || tool.evidence || [];
  const topPersonas = Object.keys(catalog.meta.personas || {})
    .map(p => [p, scoreForPersona(tool, p)])
    .sort((a,b)=>b[1]-a[1]).slice(0,3);
  const scores = tool.scores || {};
  $("toolModalContent").innerHTML = `
    <div class="modal-title-row">
      <div class="logo big">${iconFor(tool)}</div>
      <div>
        <h2 id="toolModalTitle">${escapeHtml(tool.name)}</h2>
        <p>${escapeHtml(tool.org)} · ${escapeHtml(titleCase(tool.vendor_type))} · ${escapeHtml(tool.license || "")}</p>
      </div>
    </div>
    <p class="modal-desc">${escapeHtml(tool.description)}</p>
    <div class="detail-grid">
      <div class="detail-box"><strong>Scores</strong>${scoreRow("Agentic", scores.agentic_readiness)}${scoreRow("MCP", scores.mcp_security)}${scoreRow("Lifecycle", scores.lifecycle_coverage)}${scoreRow("Evidence confidence", tool.evidence_confidence?.confidence_score)}${scoreRow("Runtime", scores.runtime)}${scoreRow("Red-team", scores.red_team)}</div>
      <div class="detail-box"><strong>Best-fit personas</strong><div class="risk-tools">${topPersonas.map(([p,s])=>`<span>${escapeHtml(p)} · ${s}/100</span>`).join("")}</div></div>
      <div class="detail-box"><strong>ASI coverage depth</strong><div class="risk-tools">${(tool.agentic_owasp||[]).map(c=>`<span title="${escapeAttr(risks[c]||"")}">${escapeHtml(c)} · depth ${escapeHtml(tool.asi_coverage_depth?.[c] ?? 1)}/3 · ${escapeHtml(risks[c]||"")}</span>`).join("") || "—"}</div></div>
      <div class="detail-box"><strong>Lifecycle coverage</strong><div class="risk-tools">${(tool.lifecycle_stages||[]).map(c=>`<span>${escapeHtml(stages[c]||c)}</span>`).join("") || "—"}</div></div>
      <div class="detail-box"><strong>Framework support</strong><div class="risk-tools">${Object.entries(tool.frameworks||{}).map(([k,v])=>`<span>${escapeHtml(k)} · ${escapeHtml(v)}</span>`).join("") || "—"}</div></div>
      <div class="detail-box"><strong>Deployment</strong><div class="risk-tools">${(tool.deployment||[]).map(x=>`<span>${escapeHtml(titleCase(x))}</span>`).join("") || "—"}</div></div>
    </div>
    <h3>Evidence</h3>
    <div class="evidence-list compact">${evidence.map(evidenceItemHtml).join("") || "<p>No evidence records yet.</p>"}</div>
    <h3>Maintainer notes</h3>
    <p>${escapeHtml(tool.maintainer_notes || "No notes yet.")}</p>
  `;
  $("toolModal").classList.remove("hidden");
}

function closeToolModal() { $("toolModal")?.classList.add("hidden"); }

function renderCompare() {
  const wrap = $("compareWrap");
  const hint = $("compareHint");
  if (!wrap || !hint) return;
  const tools = [...selectedCompare].map(id => catalog.tools.find(t=>t.id===id)).filter(Boolean);
  if (!tools.length) {
    hint.textContent = "No tools selected yet. Use the Compare checkbox on a tool card.";
    wrap.classList.add("hidden");
    return;
  }
  hint.textContent = `${tools.length}/4 selected. Compare mode is intentionally lightweight; use evidence records before procurement decisions.`;
  wrap.classList.remove("hidden");
  $("compareHead").innerHTML = `<tr><th>Dimension</th>${tools.map(t=>`<th>${escapeHtml(t.name)}<br><span class="small">${escapeHtml(t.org)}</span></th>`).join("")}</tr>`;
  const rows = [
    ["Vendor type", t=>titleCase(t.vendor_type)],
    ["Deployment", t=>(t.deployment||[]).map(titleCase).join(", ")],
    ["Agentic readiness", t=>`${score100(t.scores?.agentic_readiness)}/100`],
    ["MCP security", t=>`${score100(t.scores?.mcp_security)}/100`],
    ["Lifecycle coverage", t=>`${score100(t.scores?.lifecycle_coverage)}/100`],
    ["Runtime", t=>`${t.scores?.runtime || 0}/5`],
    ["Red-team", t=>`${t.scores?.red_team || 0}/5`],
    ["Enterprise", t=>`${t.scores?.enterprise || 0}/5`],
    ["Self-host", t=>`${t.scores?.self_host || 0}/5`],
    ["ASI risks", t=>(t.agentic_owasp||[]).join(", ")],
    ["Lifecycle stages", t=>(t.lifecycle_stages||[]).map(c=>catalog.meta.lifecycle_stages?.[c]||c).join(", ")],
    ["Evidence confidence", t=>`${t.evidence_confidence?.confidence_score || 0}/5`],
    ["Evidence types", t=>(evidenceCatalog.tools?.[t.id]||t.evidence||[]).map(e=>titleCase(e.type)).slice(0,3).join(", ")],
    ["Best-fit personas", t=>Object.keys(catalog.meta.personas||{}).map(p=>[p,scoreForPersona(t,p)]).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([p,s])=>`${p} ${s}`).join(", ")]
  ];
  $("compareBody").innerHTML = rows.map(([label,fn]) => `<tr><td><strong>${escapeHtml(label)}</strong></td>${tools.map(t=>`<td>${escapeHtml(fn(t) || "—")}</td>`).join("")}</tr>`).join("");
}

function renderEvidenceHub() {
  const typeFilter = $("evidenceTypeFilter");
  const input = $("evidenceSearch");
  if (!typeFilter || !input) return;
  const all = [];
  for (const t of catalog.tools) {
    const evs = evidenceCatalog.tools?.[t.id] || t.evidence || [];
    evs.forEach(ev => all.push({tool:t, ev}));
  }
  const types = unique(all.map(x=>x.ev.type));
  fillSelect(typeFilter, types, "All evidence types", titleCase);
  const renderList = () => {
    const q = input.value.trim().toLowerCase();
    const typ = typeFilter.value;
    const filtered = all.filter(({tool,ev}) => {
      const hay = [tool.name, tool.org, ...(tool.agentic_owasp||[]), ...(tool.lifecycle_stages||[]), ev.type, ev.source, ev.claim, ev.confidence].join(" ").toLowerCase();
      return (!q || hay.includes(q)) && (!typ || ev.type === typ);
    }).slice(0,120);
    $("evidenceList").innerHTML = filtered.map(({tool,ev}) => evidenceItemHtml(ev, tool)).join("") || "<p>No matching evidence records.</p>";
  };
  input.addEventListener("input", renderList);
  typeFilter.addEventListener("input", renderList);
  renderList();
}

function evidenceItemHtml(ev, tool=null) {
  return `<div class="evidence-item">
    <div><strong>${tool ? escapeHtml(tool.name) + " · " : ""}${escapeHtml(titleCase(ev.type || "evidence"))}</strong><span>${escapeHtml(ev.confidence || "")}</span></div>
    <p>${escapeHtml(ev.claim || "")}</p>
    <small>${escapeHtml(ev.source || "")}${ev.last_verified ? " · verified " + escapeHtml(ev.last_verified) : ""}${ev.url ? ` · <a href="${escapeAttr(ev.url)}" target="_blank" rel="noopener">source ↗</a>` : ""}</small>
  </div>`;
}

function renderAsiLifecycleMatrix() {
  const head = $("asiLifecycleHead");
  const body = $("asiLifecycleBody");
  if (!head || !body) return;
  const stages = Object.entries(catalog.meta.lifecycle_stages || {});
  const keyStages = stages.filter(([code]) => ["scope_plan","augment_finetune_data","develop_experiment","test_evaluate","release","deploy","operate","monitor","govern"].includes(code));
  head.innerHTML = `<tr><th>ASI Risk</th>${keyStages.map(([c,n])=>`<th title="${escapeAttr(n)}">${escapeHtml(shortStage(n))}</th>`).join("")}</tr>`;
  body.innerHTML = (controlsCatalog.asi_lifecycle_matrix || []).map(row => `<tr>
    <td><strong>${escapeHtml(row.asi)}</strong><br><span class="small">${escapeHtml(row.risk || "")}</span></td>
    ${keyStages.map(([c,n]) => `<td>${row.cells?.[c] ? `<span class="cell-control">${escapeHtml(row.cells[c])}</span>` : "—"}</td>`).join("")}
  </tr>`).join("");
}


function renderReferenceArchitectures() {
  const el = $("architectureGrid");
  if (!el) return;
  el.innerHTML = (architectureCatalog.architectures || []).map(a => `
    <div class="arch-card">
      <div class="risk-code">${escapeHtml(a.id.replaceAll("_", " "))}</div>
      <h3>${escapeHtml(a.title)}</h3>
      <p>${escapeHtml(a.best_for || "")}</p>
      <div class="mini-title">Threats</div>
      <div class="risk-tools">${(a.threats || []).map(x => `<span>${escapeHtml(x)}</span>`).join("")}</div>
      <div class="mini-title">Components</div>
      <ol class="compact-list">${(a.components || []).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ol>
      <div class="mini-title">Controls</div>
      <div class="risk-tools">${(a.controls || []).map(x => `<span>${escapeHtml(x)}</span>`).join("")}</div>
      <div class="mini-title">Candidate tools</div>
      <div class="risk-tools">${(a.candidate_tools || []).map(x => `<span>${escapeHtml(x)}</span>`).join("")}</div>
      <div class="mini-title">Open gaps</div>
      <p class="small">${escapeHtml((a.open_gaps || []).join(" · "))}</p>
    </div>
  `).join("");
}

function renderIncidentMapping() {
  const body = $("incidentMappingBody");
  if (!body) return;
  const risks = catalog.meta.agentic_owasp || {};
  body.innerHTML = (incidentCatalog.incidents || []).map(i => `<tr>
    <td><strong>${escapeHtml(i.name)}</strong><br><span class="small">${escapeHtml(i.date || "")} · ${escapeHtml(i.summary || "")}</span></td>
    <td>${(i.asi || []).map(code => `<span class="tag agentic" title="${escapeAttr(risks[code] || "")}">${escapeHtml(code)}</span>`).join(" ")}</td>
    <td>${(i.benchmark_cases || []).map(x => `<span class="tag capability">${escapeHtml(x)}</span>`).join(" ")}</td>
    <td>${(i.controls || []).map(x => `<span class="tag control">${escapeHtml(x)}</span>`).join(" ")}</td>
  </tr>`).join("");
}

function bindSubmissionGenerator() {
  const btn = $("generateSubmission");
  if (!btn) return;
  const output = $("submissionOutput");
  const generate = () => {
    const asi = ($("submitAsi").value || "").split(/[ ,]+/).map(x => x.trim().toUpperCase()).filter(Boolean);
    const obj = {
      name: $("submitName").value || "",
      org: $("submitOrg").value || "",
      vendor_type: $("submitType").value || "open_source",
      url: $("submitUrl").value || "",
      category: [],
      description: "",
      frameworks: {},
      agentic_owasp: asi,
      lifecycle_stages: [],
      deployment: [],
      scores: { red_team: 1, runtime: 1, agent_security: 1, data_security: 1, observability: 1, compliance: 1, enterprise: 1, oss_maturity: 1, self_host: 1, ease: 1, supply_chain: 1 },
      evidence: [{ type: "official_vendor_docs", source: "", claim: $("submitClaim").value || "", url: $("submitUrl").value || "", last_verified: new Date().toISOString().slice(0,10), confidence: "medium" }],
      maintainer_notes: "Submitted via static JSON generator. Maintainers should validate mappings and scores before merge."
    };
    output.textContent = JSON.stringify(obj, null, 2);
  };
  btn.addEventListener("click", generate);
  $("copySubmission")?.addEventListener("click", async () => {
    if (!output.textContent.trim()) generate();
    try { await navigator.clipboard.writeText(output.textContent); alert("Submission JSON copied."); } catch { alert("Copy failed. Select the JSON and copy manually."); }
  });
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


function simpleTokens(text) {
  const stop = new Set(["the","and","or","for","to","of","in","on","with","by","is","are","a","an","agent","agents","tool","tools","security","ai","llm","how","should","can","we","our"]);
  return String(text || "").toLowerCase().match(/[a-z0-9_\-]+/g)?.filter(t => t.length > 1 && !stop.has(t)) || [];
}

function sourceText(src) {
  return [src.title, src.type, src.object_id, src.text, ...(src.tags || [])].join(" ");
}

function searchSources(query, topK = 8) {
  const qTokens = simpleTokens(query);
  if (!qTokens.length || !sourceIndex.sources) return [];
  const qSet = new Set(qTokens);
  const results = sourceIndex.sources.map(src => {
    const text = sourceText(src).toLowerCase();
    let score = 0;
    qTokens.forEach(tok => {
      if (text.includes(tok)) score += tok.startsWith("asi") ? 4 : 1;
    });
    const qLower = String(query).toLowerCase();
    if (qLower.includes("mcp") && text.includes("mcp")) score += 3;
    if (qLower.includes("runtime") && text.includes("runtime")) score += 2;
    if (qLower.includes("rag") && (text.includes("rag") || text.includes("memory"))) score += 2;
    return { ...src, score, snippet: makeUiSnippet(src.text || "", [...qSet]) };
  }).filter(x => x.score > 0).sort((a,b) => b.score - a.score).slice(0, topK);
  return results;
}

function makeUiSnippet(text, tokens, maxChars = 320) {
  const s = String(text || "");
  if (s.length <= maxChars) return s;
  const lower = s.toLowerCase();
  const positions = tokens.map(t => lower.indexOf(t)).filter(i => i >= 0);
  const start = positions.length ? Math.max(0, Math.min(...positions) - 60) : 0;
  return (start > 0 ? "…" : "") + s.slice(start, start + maxChars) + (start + maxChars < s.length ? "…" : "");
}

function sourceUrl(src) {
  return src.url || src.local_path || "#";
}

function runQaAdvisor() {
  const question = $("qaQuestion")?.value?.trim();
  if (!question) return;
  const sources = searchSources(question, 10);
  const toolSources = sources.filter(s => s.type === "tool_profile").slice(0, 5);
  const riskSources = sources.filter(s => String(s.type || "").includes("control") || String(s.type || "").includes("lifecycle")).slice(0, 4);
  let html = `<h3>Grounded answer</h3><p><strong>Question:</strong> ${escapeHtml(question)}</p>`;
  if (!sources.length) {
    html += `<p>Insufficient indexed evidence. Add more records to <code>data/source_index.json</code> and retry.</p>`;
  } else {
    html += `<h4>Evidence-based findings</h4><ul>` + sources.slice(0,6).map(s => `<li>${escapeHtml(s.snippet || s.text)} <a href="${escapeAttr(sourceUrl(s))}" target="_blank">[${escapeHtml(s.source_id)}]</a></li>`).join("") + `</ul>`;
    if (toolSources.length) {
      html += `<h4>Candidate tools</h4><ul>` + toolSources.map(s => {
        const meta = s.metadata || {}; const scores = meta.scores || {};
        return `<li><strong>${escapeHtml(String(s.title || "").replace("Tool profile: ", ""))}</strong> — Agentic ${escapeHtml(scores.agentic_readiness ?? "n/a")}, MCP ${escapeHtml(scores.mcp_security ?? "n/a")} <a href="${escapeAttr(sourceUrl(s))}" target="_blank">[${escapeHtml(s.source_id)}]</a></li>`;
      }).join("") + `</ul>`;
    }
    if (riskSources.length) {
      html += `<h4>Risk / control context</h4><ul>` + riskSources.map(s => `<li>${escapeHtml(s.title)} <a href="${escapeAttr(sourceUrl(s))}" target="_blank">[${escapeHtml(s.source_id)}]</a></li>`).join("") + `</ul>`;
    }
  }
  $("qaAdvisorOutput").innerHTML = html;
  renderAnswerAudit(question, sources, sources.map(s => s.source_id));
}

function renderAnswerAudit(question, sources, usedIds) {
  const valid = new Set(sources.map(s => s.source_id));
  const unsupported = usedIds.filter(id => !valid.has(id));
  const suggestions = [];
  const q = question.toLowerCase();
  if (q.includes("mcp") || q.includes("tool")) suggestions.push("Run MCP-ASI04-001 and MCP-ASI02-004.");
  if (q.includes("rag") || q.includes("memory")) suggestions.push("Run RAG-ASI06-007 and review memory provenance.");
  if (q.includes("identity") || q.includes("oauth")) suggestions.push("Run MCP-ASI07-003 and verify scoped credentials.");
  if (q.includes("code") || q.includes("rce")) suggestions.push("Run MCP-ASI05-002 in a sandboxed target.");
  $("answerAuditPanel").innerHTML = `<h3>Answer audit</h3>
    <p><strong>Retrieved sources:</strong> ${sources.length}</p>
    <p><strong>Used citations:</strong> ${usedIds.map(id => `<span class="source-chip">${escapeHtml(id)}</span>`).join(" ") || "none"}</p>
    <p><strong>Unsupported citations:</strong> ${unsupported.length ? unsupported.map(escapeHtml).join(", ") : "none"}</p>
    <p><strong>Confidence:</strong> ${sources.length && !unsupported.length ? "medium" : "low"}</p>
    <p><strong>Recommended validation:</strong></p><ul>${(suggestions.length ? suggestions : ["Review evidence records and run relevant benchmark cases before updating scores."]).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>`;
}

function populateClaimTools() {
  const select = $("claimToolSelect");
  if (!select) return;
  select.innerHTML = catalog.tools.slice().sort((a,b) => a.name.localeCompare(b.name)).map(t => `<option value="${escapeAttr(t.id)}">${escapeHtml(t.name)} — ${escapeHtml(t.org)}</option>`).join("");
  const input = $("claimText");
  if (input && !input.value) input.value = "MCP discovery and runtime policy enforcement";
}

function matchClaimTemplatesUi(claim) {
  const q = simpleTokens(claim).join(" ");
  return (claimsCatalog.claims || []).map(c => {
    const hay = simpleTokens([c.title, c.claim, ...(c.required_evidence || [])].join(" ")).join(" ");
    let score = 0;
    q.split(" ").forEach(tok => { if (tok && hay.includes(tok)) score += 1; });
    ["mcp","runtime","red","memory","rag","identity","coding","rce","sandbox"].forEach(term => { if (q.includes(term) && hay.includes(term)) score += 3; });
    return { ...c, score };
  }).filter(c => c.score > 0).sort((a,b) => b.score - a.score).slice(0,3);
}

function runClaimVerifier() {
  const toolId = $("claimToolSelect")?.value;
  const claim = $("claimText")?.value?.trim() || "";
  const tool = catalog.tools.find(t => t.id === toolId);
  if (!tool || !claim) return;
  const matched = matchClaimTemplatesUi(claim);
  const ev = evidenceCatalog.tools?.[tool.id] || [];
  const evTypes = [...new Set(ev.map(e => e.type || "unknown"))];
  const mappedAsi = [...new Set([...(tool.agentic_owasp || []), ...matched.flatMap(m => m.mapped_asi || [])])].sort();
  const required = [...new Set(matched.flatMap(m => m.required_evidence || []))];
  const tests = [...new Set(matched.flatMap(m => m.validation_tests || []))];
  const status = ev.length && evTypes.includes("official_vendor_docs") && evTypes.includes("benchmark_backed") ? "high_confidence" : ev.length ? "partial_evidence" : "needs_validation";
  $("claimVerifierOutput").innerHTML = `<h3>Claim verification result</h3>
    <p><strong>Tool:</strong> ${escapeHtml(tool.name)} · ${escapeHtml(tool.org)}</p>
    <p><strong>Claim:</strong> ${escapeHtml(claim)}</p>
    <p><strong>Status:</strong> <span class="status-${status}">${escapeHtml(titleCase(status))}</span></p>
    <p><strong>Mapped ASI:</strong> ${mappedAsi.map(x => `<span class="risk-pill">${escapeHtml(x)}</span>`).join(" ")}</p>
    <h4>Required evidence</h4><ul>${(required.length ? required : ["Attach official vendor docs, benchmark output, and audit evidence."]).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
    <h4>Existing evidence types</h4><p>${evTypes.map(x => `<span class="source-chip">${escapeHtml(x)}</span>`).join(" ") || "none"}</p>
    <h4>Suggested benchmark tests</h4><ul>${(tests.length ? tests : ["Select benchmark cases based on mapped ASI risks."]).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
    <p><strong>Next step:</strong> Run suggested benchmark cases and add <code>benchmark_backed</code> evidence before upgrading claim confidence.</p>`;
}

function runArchitectureGeneratorUi() {
  const signals = $("archSignals")?.value?.toLowerCase() || "";
  const matched = (architectureTemplates.templates || []).map(t => {
    let score = 0;
    (t.triggers || []).forEach(tr => { if (signals.includes(tr.toLowerCase())) score += 3; });
    (t.asi || []).forEach(asi => { if (signals.includes(asi.toLowerCase())) score += 2; });
    return { ...t, score };
  }).filter(t => t.score > 0).sort((a,b) => b.score - a.score).slice(0,2);
  const selected = matched.length ? matched : (architectureTemplates.templates || []).slice(0,1);
  const controls = [...new Set(selected.flatMap(t => t.controls || []))];
  const components = [...new Set(selected.flatMap(t => t.components || []))];
  const asi = [...new Set(selected.flatMap(t => t.asi || []))].sort();
  $("architectureOutput").innerHTML = `<h3>Generated architecture</h3>
    <h4>Recommended patterns</h4><ul>${selected.map(t => `<li><strong>${escapeHtml(t.title)}</strong> — ${escapeHtml((t.asi || []).join(", "))}</li>`).join("")}</ul>
    <h4>Components</h4><p>${components.map(c => `<span class="source-chip">${escapeHtml(c)}</span>`).join(" ")}</p>
    <h4>Controls</h4><ul>${controls.map(c => `<li>${escapeHtml(c)}</li>`).join("")}</ul>
    <h4>ASI coverage</h4><p>${asi.map(x => `<span class="risk-pill">${escapeHtml(x)}</span>`).join(" ")}</p>
    <h4>Mermaid diagram text</h4><pre class="mermaid-text">${escapeHtml(selected[0]?.mermaid || "")}</pre>`;
}

function renderReleaseTimeline() {
  const el = $("releaseTimeline");
  if (!el) return;
  el.innerHTML = (releaseLog.releases || []).map(r => `<div class="dimension-card">
    <h3>${escapeHtml(r.release)} · ${escapeHtml(r.version || "")}</h3>
    <p>${escapeHtml(r.summary || "")}</p>
    <strong>Added features</strong>
    <ul>${(r.added_features || []).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
    <strong>Evidence updates</strong>
    <ul>${(r.evidence_updated || []).map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
  </div>`).join("");
}

function bindV09AdvisorEvents() {
  $("runQaAdvisor")?.addEventListener("click", runQaAdvisor);
  $("sampleQaAdvisor")?.addEventListener("click", () => { $("qaQuestion").value = "How should I secure a LangGraph + MCP + RAG customer support agent?"; runQaAdvisor(); });
  $("runClaimVerifier")?.addEventListener("click", runClaimVerifier);
  $("runArchitectureGenerator")?.addEventListener("click", runArchitectureGeneratorUi);
  if ($("archSignals") && !$("archSignals").value) $("archSignals").value = "mcp rag vector_db external_api identity monitor";
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
  $("clearCompare")?.addEventListener("click", () => { selectedCompare.clear(); render(); renderCompare(); });
  document.querySelectorAll("[data-close-modal]").forEach(el => el.addEventListener("click", closeToolModal));
  document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeToolModal(); });
}

function setView(view) {
  currentView = view;
  $("gridView").classList.toggle("active", view === "grid");
  $("tableView").classList.toggle("active", view === "table");
  $("cards").classList.toggle("hidden", view !== "grid");
  $("tableWrap").classList.toggle("hidden", view !== "table");
}

function renderUpdateIntelligence() {
  const cards = $("updateStatusCards");
  if (!cards || !updateStatus) return;
  const watched = updateStatus.watched_sources || (updateSources?.vendors || []).reduce((n, v) => n + (v.sources || []).length, 0);
  cards.innerHTML = [
    [watched, "Watched sources"],
    [updateStatus.pending_updates || 0, "Pending candidates"],
    [updateStatus.triaged_updates || 0, "Triaged updates"],
    [updateStatus.mode || "not_run", "Last mode"]
  ].map(([num,label]) => `<div class="metric-card"><div class="num">${escapeHtml(String(num))}</div><div class="label">${escapeHtml(label)}</div></div>`).join("");

  const pendingEl = $("pendingUpdatesList");
  const updates = (pendingUpdates?.updates || []).slice(0, 8);
  pendingEl.innerHTML = updates.length ? updates.map(u => `<div class="compact-item"><strong>${escapeHtml(u.title || "Untitled update")}</strong><div>${escapeHtml((u.summary || "").slice(0, 180))}</div><div class="meta">${escapeHtml(u.vendor_name || "unknown")} · ${escapeHtml(u.priority || "low")} · ${(u.candidate_asi || []).map(a=>`<span>${escapeHtml(a)}</span>`).join(" ")}</div></div>`).join("") : `<p class="small">No pending candidates yet. Run the update pipeline to populate this section.</p>`;

  const roadmapEl = $("roadmapUpdatesList");
  const roadmaps = (roadmapUpdates?.roadmap_items || []).slice(0, 8);
  roadmapEl.innerHTML = roadmaps.length ? roadmaps.map(r => `<div class="compact-item"><strong>${escapeHtml(r.title || "Roadmap item")}</strong><div class="meta">${escapeHtml(r.vendor || "unknown")} · ${escapeHtml(r.priority || "medium")} · ${escapeHtml(r.status || "needs_review")}</div></div>`).join("") : `<p class="small">No roadmap candidates yet. Roadmap items are generated from triaged official-source updates.</p>`;

  const srcEl = $("updateSourcesList");
  const types = new Map();
  (updateSources?.vendors || []).forEach(v => (v.sources || []).forEach(s => types.set(s.type, (types.get(s.type)||0)+1)));
  srcEl.innerHTML = Array.from(types.entries()).map(([k,v]) => `<span>${escapeHtml(k)}: ${v}</span>`).join("");
}


function renderUpdateReviewAutomation() {
  const cards = $("updateReviewCards");
  if (!cards) return;
  const recs = benchmarkRecommendations?.recommendations || [];
  const diffs = evidenceDiffs?.diffs || [];
  const prs = prCandidates?.candidates || [];
  const boardCols = roadmapBoard?.columns || {};
  const boardCount = Object.values(boardCols).reduce((n, arr) => n + (Array.isArray(arr) ? arr.length : 0), 0);
  cards.innerHTML = [
    [recs.length, "Benchmark recommendations"],
    [diffs.length, "Evidence diffs"],
    [prs.length, "PR candidates"],
    [boardCount, "Roadmap items"]
  ].map(([num,label]) => `<div class="metric-card"><div class="num">${escapeHtml(String(num))}</div><div class="label">${escapeHtml(label)}</div></div>`).join("");

  const recEl = $("benchmarkRecommendationsList");
  if (recEl) recEl.innerHTML = recs.length ? recs.slice(0, 8).map(r => `<div class="compact-item"><strong>${escapeHtml(r.title || r.update_id)}</strong><div class="meta">${escapeHtml(r.vendor || "unknown")} · ${(r.recommended_benchmarks || []).map(b => `<span>${escapeHtml(b)}</span>`).join(" ")}</div><div>${escapeHtml(r.validation_goal || "")}</div></div>`).join("") : `<p class="small">No benchmark recommendations yet.</p>`;

  const diffEl = $("evidenceDiffsList");
  if (diffEl) diffEl.innerHTML = diffs.length ? diffs.slice(0, 8).map(d => `<div class="compact-item"><strong>${escapeHtml(d.tool_id || d.id)}</strong><div>${escapeHtml(d.reason || "")}</div><div class="meta">${escapeHtml(d.change_type || "diff")} · ${escapeHtml(d.status || "pending")}</div></div>`).join("") : `<p class="small">No evidence diffs yet.</p>`;

  const prEl = $("prCandidatesList");
  if (prEl) prEl.innerHTML = prs.length ? prs.slice(0, 8).map(p => `<div class="compact-item"><strong>${escapeHtml(p.title || p.id)}</strong><div class="meta">${escapeHtml(p.tool_id || "unknown tool")} · ${escapeHtml(p.status || "ready")}</div></div>`).join("") : `<p class="small">No PR candidates yet.</p>`;

  const boardEl = $("roadmapBoard");
  if (boardEl) boardEl.innerHTML = Object.entries(boardCols).map(([col, items]) => `<div class="roadmap-column"><h4>${escapeHtml(titleCase(col))}</h4>${(items || []).slice(0,5).map(item => `<div class="roadmap-item">${escapeHtml(item.title || item.id)}<br><span class="status-pill">${escapeHtml(item.status || "planned")}</span></div>`).join("") || `<p class="small">Empty</p>`}</div>`).join("");
}

async function init() {
  try {
    const [res, controlsRes, evidenceRes, incidentsRes, architecturesRes, sourceIndexRes, claimsRes, archTemplatesRes, releaseLogRes, updateStatusRes, pendingUpdatesRes, roadmapUpdatesRes, updateSourcesRes, benchmarkRecommendationsRes, evidenceDiffsRes, prCandidatesRes, roadmapBoardRes] = await Promise.all([
      fetch("./data/tools.json", { cache: "no-store" }),
      fetch("./data/controls.json", { cache: "no-store" }),
      fetch("./data/evidence.json", { cache: "no-store" }),
      fetch("./data/incidents.json", { cache: "no-store" }),
      fetch("./data/reference_architectures.json", { cache: "no-store" }),
      fetch("./data/source_index.json", { cache: "no-store" }),
      fetch("./data/claims.json", { cache: "no-store" }),
      fetch("./data/architecture_templates.json", { cache: "no-store" }),
      fetch("./data/releases/change_log.json", { cache: "no-store" }),
      fetch("./data/updates/auto_update_status.json", { cache: "no-store" }),
      fetch("./data/updates/pending_updates.json", { cache: "no-store" }),
      fetch("./data/updates/roadmap.json", { cache: "no-store" }),
      fetch("./data/update_sources.json", { cache: "no-store" }),
      fetch("./data/updates/benchmark_recommendations.json", { cache: "no-store" }),
      fetch("./data/updates/evidence_diffs.json", { cache: "no-store" }),
      fetch("./data/updates/pr_candidates.json", { cache: "no-store" }),
      fetch("./data/roadmap_board.json", { cache: "no-store" })
    ]);
    catalog = await res.json();
    controlsCatalog = await controlsRes.json();
    evidenceCatalog = await evidenceRes.json();
    incidentCatalog = await incidentsRes.json();
    architectureCatalog = await architecturesRes.json();
    sourceIndex = await sourceIndexRes.json();
    claimsCatalog = await claimsRes.json();
    architectureTemplates = await archTemplatesRes.json();
    releaseLog = await releaseLogRes.json();
    updateStatus = await updateStatusRes.json();
    pendingUpdates = await pendingUpdatesRes.json();
    roadmapUpdates = await roadmapUpdatesRes.json();
    updateSources = await updateSourcesRes.json();
    benchmarkRecommendations = await benchmarkRecommendationsRes.json();
    evidenceDiffs = await evidenceDiffsRes.json();
    prCandidates = await prCandidatesRes.json();
    roadmapBoard = await roadmapBoardRes.json();
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
    renderAsiLifecycleMatrix();
    renderCompare();
    renderEvidenceHub();
    renderReferenceArchitectures();
    renderIncidentMapping();
    bindSubmissionGenerator();
    populateClaimTools();
    renderReleaseTimeline();
    renderUpdateIntelligence();
    renderUpdateReviewAutomation();
    bindV09AdvisorEvents();
  } catch (err) {
    document.body.insertAdjacentHTML("afterbegin", `<div class="note"><strong>Failed to load catalog:</strong> ${escapeHtml(err.message)}</div>`);
    console.error(err);
  }
}
init();
