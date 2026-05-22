from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from .graph_builder import build_graph
from .timeline_builder import build_timeline
from .audit_view_builder import build_audit_table
from .risk_dashboard_builder import build_risk_dashboard
from .trust_graph_builder import build_trust_graph

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "outputs" / "multi_agent_demo" / "multi_agent_demo_report.json"
DEFAULT_AUDIT = ROOT / "outputs" / "multi_agent_demo" / "multi_agent_tool_audit.jsonl"
DEFAULT_OUT = ROOT / "outputs" / "visualizations"


def load_report(report_path: str | Path = DEFAULT_REPORT) -> Dict[str, Any]:
    path = Path(report_path)
    if not path.exists():
        # Generate demo report if missing.
        from multi_agent_demo.run_multi_agent_demo import run_demo
        report, _, _ = run_demo(ROOT / "examples" / "multi_agent_refund_scenario.json", ROOT / "outputs" / "multi_agent_demo")
        return report
    return json.loads(path.read_text(encoding="utf-8"))


def build_visualization_bundle(report_path: str | Path = DEFAULT_REPORT, output_dir: str | Path = DEFAULT_OUT) -> Dict[str, Any]:
    report = load_report(report_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    graph = build_graph(report)
    timeline = build_timeline(report)
    audit = build_audit_table(report, str(DEFAULT_AUDIT))
    risk = build_risk_dashboard(report)
    trust = build_trust_graph(report)
    bundle = {
        "scenario_id": report.get("scenario_id"),
        "scenario_name": report.get("scenario_name"),
        "summary": report.get("summary", {}),
        "graph": graph,
        "timeline": timeline,
        "audit_table": audit,
        "risk_dashboard": risk,
        "trust_graph": trust,
    }
    (out / "graph_nodes.json").write_text(json.dumps(graph["nodes"], indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "graph_edges.json").write_text(json.dumps(graph["edges"], indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "timeline_events.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "audit_table.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "risk_dashboard.json").write_text(json.dumps(risk, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "trust_graph.json").write_text(json.dumps(trust, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "interactive_dashboard.html").write_text(render_interactive_dashboard(bundle), encoding="utf-8")
    (out / "visualization_bundle.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    return bundle


def _json_script(data: Any) -> str:
    return html.escape(json.dumps(data, ensure_ascii=False), quote=False)


def render_interactive_dashboard(bundle: Dict[str, Any]) -> str:
    """Return a self-contained HTML dashboard with SVG graph, replay, filters, and drill-down."""
    data_json = json.dumps(bundle, ensure_ascii=False)
    # Escape closing script edge case.
    data_json = data_json.replace("</", "<\\/")
    return f"""
<div id="viz-root" style="font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#0f172a;">
  <style>
    #viz-root .viz-grid {{ display:grid; grid-template-columns: 1.25fr .85fr; gap:16px; }}
    #viz-root .viz-card {{ border:1px solid #e2e8f0; border-radius:16px; padding:14px; background:#fff; box-shadow:0 4px 14px rgba(15,23,42,.06); }}
    #viz-root .toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:12px; }}
    #viz-root select, #viz-root button {{ border:1px solid #cbd5e1; border-radius:10px; padding:8px 10px; background:#f8fafc; }}
    #viz-root button {{ cursor:pointer; }}
    #viz-root button:hover {{ background:#e2e8f0; }}
    #viz-root .pill {{ display:inline-flex; align-items:center; gap:5px; padding:3px 8px; border-radius:999px; font-size:12px; background:#e2e8f0; margin:2px; }}
    #viz-root .blocked {{ color:#991b1b; background:#fee2e2; }}
    #viz-root .allowed {{ color:#166534; background:#dcfce7; }}
    #viz-root .warn {{ color:#92400e; background:#fef3c7; }}
    #viz-root .node {{ cursor:pointer; transition:opacity .15s, transform .15s; }}
    #viz-root .node:hover {{ opacity:.85; }}
    #viz-root .edge {{ stroke:#94a3b8; stroke-width:2.2; opacity:.75; }}
    #viz-root .edge.blocked-edge {{ stroke:#dc2626; stroke-width:3.2; opacity:.95; stroke-dasharray:6 4; }}
    #viz-root .edge.allowed-edge {{ stroke:#16a34a; }}
    #viz-root .edge.audit-edge {{ stroke:#059669; stroke-dasharray:3 3; }}
    #viz-root .timeline-list {{ max-height:340px; overflow:auto; border:1px solid #e2e8f0; border-radius:12px; }}
    #viz-root .timeline-event {{ padding:9px 11px; border-bottom:1px solid #e2e8f0; cursor:pointer; }}
    #viz-root .timeline-event.active {{ background:#eff6ff; border-left:4px solid #2563eb; }}
    #viz-root .audit-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    #viz-root .audit-table th, #viz-root .audit-table td {{ padding:7px 6px; border-bottom:1px solid #e2e8f0; text-align:left; vertical-align:top; }}
    #viz-root .audit-table tbody tr {{ cursor:pointer; }}
    #viz-root .audit-table tbody tr:hover {{ background:#f8fafc; }}
    #viz-root pre {{ white-space:pre-wrap; word-break:break-word; background:#0f172a; color:#e2e8f0; padding:12px; border-radius:12px; max-height:320px; overflow:auto; }}
    #viz-root .mini-bar {{ height:9px; border-radius:999px; background:#e2e8f0; overflow:hidden; min-width:90px; }}
    #viz-root .mini-bar > span {{ display:block; height:100%; background:#2563eb; }}
  </style>
  <div class="viz-card" style="margin-bottom:16px;">
    <h2 style="margin:0 0 4px;">Interactive Agentic Security Visualization</h2>
    <div style="color:#475569;">Scenario: <b>{html.escape(str(bundle.get('scenario_name')))}</b> · Containment: <b>{bundle.get('summary',{}).get('containment_rate',0):.0%}</b> · Status: <b>{html.escape(str(bundle.get('summary',{}).get('overall_status','')))}</b></div>
  </div>

  <div class="toolbar viz-card">
    <label>Flow <select id="flowFilter"><option value="all">All flows</option></select></label>
    <label>Decision <select id="decisionFilter"><option value="all">All</option><option value="allowed">Allowed</option><option value="blocked">Blocked</option></select></label>
    <label>ASI <select id="asiFilter"><option value="all">All ASI</option></select></label>
    <button id="prevBtn">◀ Previous</button><button id="nextBtn">Next ▶</button><button id="playBtn">▶ Auto-play</button>
    <button id="resetBtn">Reset filters</button>
  </div>

  <div class="viz-grid">
    <div class="viz-card">
      <h3 style="margin-top:0;">Multi-Agent Network Graph</h3>
      <svg id="graphSvg" width="100%" viewBox="0 0 1000 620" role="img" aria-label="multi-agent graph"></svg>
      <div style="font-size:12px;color:#64748b;">Click nodes, edges, timeline events, or audit rows to drill into evidence.</div>
    </div>
    <div class="viz-card">
      <h3 style="margin-top:0;">Selected Object Detail</h3>
      <div id="detailPanel"><span style="color:#64748b;">Select a node, edge, event, ASI, or audit row.</span></div>
      <h3>Risk Coverage</h3>
      <div id="riskCoverage"></div>
    </div>
  </div>

  <div class="viz-grid" style="margin-top:16px; align-items:start;">
    <div class="viz-card">
      <h3 style="margin-top:0;">Execution Timeline Replay</h3>
      <div id="timelineList" class="timeline-list"></div>
    </div>
    <div class="viz-card">
      <h3 style="margin-top:0;">Tool Call Audit Explorer</h3>
      <div id="auditTable"></div>
    </div>
  </div>

  <script>
    const DATA = {data_json};
    const nodes = DATA.graph.nodes;
    const edges = DATA.graph.edges;
    const timeline = DATA.timeline;
    const auditRows = DATA.audit_table;
    const risk = DATA.risk_dashboard;
    let activeEventIndex = 0;
    let playTimer = null;

    function esc(x) {{ return String(x ?? '').replace(/[&<>"']/g, m => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}}[m])); }}
    function badge(x, cls='') {{ return `<span class="pill ${{cls}}">${{esc(x)}}</span>`; }}
    function nodeById(id) {{ return nodes.find(n => n.id === id); }}
    function flowIds() {{ return [...new Set(timeline.map(e => e.flow_id).filter(Boolean))]; }}
    function asiIds() {{ return [...new Set([].concat(...timeline.map(e => e.mapped_asi || []), ...edges.map(e => e.mapped_asi || [])))].sort(); }}

    function initFilters() {{
      const f = document.getElementById('flowFilter');
      flowIds().forEach(id => {{ const o=document.createElement('option'); o.value=id; o.textContent=id; f.appendChild(o); }});
      const a = document.getElementById('asiFilter');
      asiIds().forEach(id => {{ const o=document.createElement('option'); o.value=id; o.textContent=id; a.appendChild(o); }});
      ['flowFilter','decisionFilter','asiFilter'].forEach(id => document.getElementById(id).addEventListener('change', renderAll));
      document.getElementById('resetBtn').onclick = () => {{ document.getElementById('flowFilter').value='all'; document.getElementById('decisionFilter').value='all'; document.getElementById('asiFilter').value='all'; renderAll(); }};
      document.getElementById('nextBtn').onclick = () => {{ const evs=filteredTimeline(); activeEventIndex=(activeEventIndex+1)%Math.max(evs.length,1); showEvent(evs[activeEventIndex]); }};
      document.getElementById('prevBtn').onclick = () => {{ const evs=filteredTimeline(); activeEventIndex=(activeEventIndex-1+Math.max(evs.length,1))%Math.max(evs.length,1); showEvent(evs[activeEventIndex]); }};
      document.getElementById('playBtn').onclick = () => {{ if(playTimer){{clearInterval(playTimer);playTimer=null;document.getElementById('playBtn').textContent='▶ Auto-play';return;}} document.getElementById('playBtn').textContent='⏸ Stop'; playTimer=setInterval(()=>document.getElementById('nextBtn').click(), 1200); }};
    }}
    function passesFilters(obj) {{
      const flow = document.getElementById('flowFilter').value;
      const dec = document.getElementById('decisionFilter').value;
      const asi = document.getElementById('asiFilter').value;
      if(flow !== 'all' && obj.flow_id && obj.flow_id !== flow) return false;
      if(dec !== 'all') {{ const d = (obj.decision || obj.status || '').toLowerCase(); if(dec==='blocked' && !(d.includes('block')||d.includes('deny'))) return false; if(dec==='allowed' && !(d.includes('allow'))) return false; }}
      if(asi !== 'all') {{ const arr = obj.mapped_asi || []; if(!arr.includes(asi)) return false; }}
      return true;
    }}
    function filteredTimeline() {{ return timeline.filter(passesFilters); }}
    function filteredAudit() {{ return auditRows.filter(r => passesFilters({{flow_id:r.flow_id, decision:r.decision, mapped_asi:String(r.mapped_asi||'').split(/,\s*/).filter(Boolean)}})); }}

    function renderGraph() {{
      const svg = document.getElementById('graphSvg'); svg.innerHTML='';
      const positions = {{
        coordinator_agent:[500,70], support_agent:[180,205], finance_agent:[500,205], compliance_agent:[760,205], notification_agent:[820,375],
        'crm.lookup':[105,380], 'ticket.create':[275,390], 'crm.refund':[500,385], 'memory.search':[690,385], 'email.draft':[860,500], 'email.send':[760,500], 'unknown.admin_helper':[385,500],
        policy_engine:[500,535], audit_log:[500,600], unknown_admin_helper:[350,90]
      }};
      const visibleEdges = edges.filter(passesFilters);
      visibleEdges.forEach(e => {{
        const s=positions[e.source]||[100,100], t=positions[e.target]||[900,500];
        const line=document.createElementNS('http://www.w3.org/2000/svg','line');
        line.setAttribute('x1',s[0]); line.setAttribute('y1',s[1]); line.setAttribute('x2',t[0]); line.setAttribute('y2',t[1]);
        let cls='edge'; if((e.decision||'').includes('block') || (e.relation||'').includes('blocked')) cls+=' blocked-edge'; else if((e.decision||'').includes('allow')) cls+=' allowed-edge'; else if((e.relation||'').includes('audit')) cls+=' audit-edge';
        line.setAttribute('class',cls); line.onclick=()=>showEdge(e); svg.appendChild(line);
      }});
      nodes.forEach(n => {{
        const p=positions[n.id]||[120+Math.random()*760,120+Math.random()*400];
        const g=document.createElementNS('http://www.w3.org/2000/svg','g'); g.setAttribute('class','node'); g.onclick=()=>showNode(n);
        const rect=document.createElementNS('http://www.w3.org/2000/svg','rect'); rect.setAttribute('x',p[0]-62); rect.setAttribute('y',p[1]-24); rect.setAttribute('rx',14); rect.setAttribute('width',124); rect.setAttribute('height',48); rect.setAttribute('fill', n.color || '#64748b'); rect.setAttribute('opacity','.92');
        const text=document.createElementNS('http://www.w3.org/2000/svg','text'); text.setAttribute('x',p[0]); text.setAttribute('y',p[1]+4); text.setAttribute('text-anchor','middle'); text.setAttribute('font-size','11'); text.setAttribute('fill','white'); text.textContent=(n.label||n.id).slice(0,19);
        g.appendChild(rect); g.appendChild(text); svg.appendChild(g);
      }});
    }}
    function showNode(n) {{
      const related = timeline.filter(e => e.actor===n.id || e.target===n.id).slice(0,8);
      document.getElementById('detailPanel').innerHTML = `<h4>${{esc(n.label||n.id)}}</h4>${{badge(n.type)}} ${{badge(n.risk_level||'n/a', n.risk_level==='high'?'blocked':'')}}<p>${{esc(n.role||'')}}</p><p><b>Trust zone:</b> ${{esc(n.trust_zone||'n/a')}}</p><p><b>Capabilities:</b> ${{(n.capabilities||[]).map(x=>badge(x)).join(' ')}}</p><p><b>Allowed tools:</b> ${{(n.allowed_tools||[]).map(x=>badge(x)).join(' ') || 'none'}}</p><h4>Related events</h4><ul>${{related.map(e=>`<li>Step ${{e.global_step}} · ${{esc(e.action)}} → ${{esc(e.decision)}}</li>`).join('')}}</ul><pre>${{esc(JSON.stringify(n,null,2))}}</pre>`;
    }}
    function showEdge(e) {{ document.getElementById('detailPanel').innerHTML = `<h4>Edge: ${{esc(e.source)}} → ${{esc(e.target)}}</h4>${{badge(e.relation)}} ${{badge(e.decision||'n/a', String(e.decision||'').includes('block')?'blocked':'allowed')}}<p>${{esc(e.reason||'')}}</p><p><b>ASI:</b> ${{(e.mapped_asi||[]).map(x=>badge(x,'warn')).join(' ')||'none'}}</p><pre>${{esc(JSON.stringify(e,null,2))}}</pre>`; }}
    function showEvent(e) {{ if(!e) return; document.querySelectorAll('.timeline-event').forEach(x=>x.classList.remove('active')); const el=document.getElementById('ev_'+e.global_step); if(el) el.classList.add('active'); document.getElementById('detailPanel').innerHTML = `<h4>Event ${{e.global_step}} · ${{esc(e.event_type)}}</h4>${{badge(e.decision, e.status==='blocked'?'blocked':'allowed')}} <p><b>Flow:</b> ${{esc(e.flow_name)}}</p><p><b>Actor:</b> ${{esc(e.actor)}} → <b>Target:</b> ${{esc(e.target)}}</p><p><b>Action:</b> ${{esc(e.action)}}</p><p><b>Reason:</b> ${{esc(e.reason||'')}}</p><p><b>ASI:</b> ${{(e.mapped_asi||[]).map(x=>badge(x,'warn')).join(' ')||'none'}}</p><pre>${{esc(JSON.stringify(e.raw,null,2))}}</pre>`; }}
    function renderTimeline() {{ const box=document.getElementById('timelineList'); const evs=filteredTimeline(); box.innerHTML=evs.map((e,i)=>`<div id="ev_${{e.global_step}}" class="timeline-event" onclick='window.__showEvent(${{e.global_step}})'><b>Step ${{e.global_step}}</b> · ${{esc(e.actor)}} → ${{esc(e.target)}}<br/><span class="pill ${{e.status==='blocked'?'blocked':'allowed'}}">${{esc(e.decision)}}</span> <span style="color:#64748b">${{esc(e.flow_id)}} · ${{esc(e.action)}}</span></div>`).join('') || '<div style="padding:10px;color:#64748b">No events for current filters.</div>'; window.__eventMap = Object.fromEntries(evs.map(e=>[e.global_step,e])); window.__showEvent=(id)=>showEvent(window.__eventMap[id]); }}
    function renderAudit() {{ const rows=filteredAudit().slice(0,80); document.getElementById('auditTable').innerHTML = `<table class="audit-table"><thead><tr><th>Step</th><th>Agent</th><th>Tool</th><th>Decision</th><th>ASI</th></tr></thead><tbody>${{rows.map((r,i)=>`<tr onclick='window.__showAudit(${{i}})'><td>${{esc(r.step)}}</td><td>${{esc(r.agent)}}</td><td>${{esc(r.tool)}}</td><td><span class="pill ${{String(r.decision).includes('block')?'blocked':'allowed'}}">${{esc(r.decision)}}</span></td><td>${{esc(r.mapped_asi)}}</td></tr>`).join('')}}</tbody></table>`; window.__auditRows=rows; window.__showAudit=(i)=>{{ const r=window.__auditRows[i]; document.getElementById('detailPanel').innerHTML=`<h4>Audit Row</h4><p><b>${{esc(r.agent)}} → ${{esc(r.tool)}}</b></p>${{badge(r.decision, String(r.decision).includes('block')?'blocked':'allowed')}}<p><b>Reason:</b> ${{esc(r.reason||r.reason_code)}}</p><p><b>ASI:</b> ${{esc(r.mapped_asi||'none')}}</p><p><b>Controls:</b> ${{esc(r.controls||'')}}</p><pre>${{esc(JSON.stringify(r.raw,null,2))}}</pre>`; }}; }}
    function renderRisk() {{
      const rows = risk.asi_coverage;
      document.getElementById('riskCoverage').innerHTML = rows.map(r => {{ const width=Math.min(100, r.count*25); return `<div style="margin:7px 0; cursor:pointer" onclick='window.__showAsi("${{r.asi}}")'><b>${{r.asi}}</b> <span style="color:#64748b">${{esc(r.name)}}</span><div class="mini-bar"><span style="width:${{width}}%"></span></div><span class="pill ${{r.count?'allowed':'warn'}}">${{r.count}} event(s)</span></div>`; }}).join('');
      window.__showAsi=(asi)=>{{ const r=rows.find(x=>x.asi===asi); document.getElementById('asiFilter').value=asi; renderAll(false); document.getElementById('detailPanel').innerHTML=`<h4>${{asi}} · ${{esc(r.name)}}</h4>${{badge(r.status, r.count?'allowed':'warn')}}<p><b>Evidence events:</b></p><ul>${{(r.evidence||[]).map(x=>`<li>${{esc(x)}}</li>`).join('') || '<li>No observed event in this demo.</li>'}}</ul><pre>${{esc(JSON.stringify(r,null,2))}}</pre>`; }};
    }}
    function renderAll(resetDetail=true) {{ renderGraph(); renderTimeline(); renderAudit(); renderRisk(); if(resetDetail) document.getElementById('detailPanel').innerHTML='<span style="color:#64748b;">Select a node, edge, event, ASI, or audit row.</span>'; }}
    initFilters(); renderAll();
  </script>
</div>
"""


def build_dashboard_markdown(bundle: Dict[str, Any]) -> str:
    s = bundle.get("summary", {})
    lines = ["# Interactive Visualization Bundle", "", f"Scenario: **{bundle.get('scenario_name')}**", "", f"Containment rate: **{s.get('containment_rate', 0):.0%}**", f"Overall status: `{s.get('overall_status')}`", "", "## Generated files", "", "- `outputs/visualizations/interactive_dashboard.html`", "- `outputs/visualizations/visualization_bundle.json`", "- `outputs/visualizations/graph_nodes.json`", "- `outputs/visualizations/graph_edges.json`", "- `outputs/visualizations/timeline_events.json`", "- `outputs/visualizations/audit_table.json`", "- `outputs/visualizations/risk_dashboard.json`", "- `outputs/visualizations/trust_graph.json`", ""]
    return "\n".join(lines)
