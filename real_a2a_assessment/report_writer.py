from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json

def write_a2a_reports(report: Dict[str, Any], output_prefix: str) -> Dict[str, str]:
    prefix=Path(output_prefix); prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path=prefix.with_suffix('.json'); md_path=prefix.with_suffix('.md')
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    s=report.get('summary', {})
    lines=["# A2A / Agent-to-Agent Risk Assessment Report", "", "## Executive Summary", "", f"- Agents assessed: `{s.get('agents',0)}`", f"- High-risk agents: `{s.get('high_risk_agents',0)}`", f"- Average risk score: `{s.get('average_risk_score','n/a')}`", f"- Risk level: **{s.get('risk_level','unknown')}**", f"- Mapped ASI: {', '.join(s.get('mapped_asi', [])) or 'None'}", "", "## Agent-Level Findings", "", "| Agent | Risk | Signals | ASI | Required controls |", "|---|---:|---|---|---|"]
    for a in report.get('agents', []):
        lines.append(f"| {a.get('agent')} | {a.get('risk_level')} ({a.get('risk_score')}) | {', '.join(a.get('signals', []))} | {', '.join(a.get('mapped_asi', []))} | {', '.join(a.get('required_controls', []))} |")
    graph=report.get('trust_graph') or {}
    if graph:
        lines += ["", "## Trust Graph", "", f"- Nodes: `{len(graph.get('nodes', []))}`", f"- Edges: `{graph.get('edges', 0)}`", f"- Risky edges: `{len(graph.get('risky_edges', []))}`"]
    md_path.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return {"json":str(json_path), "markdown":str(md_path)}
