from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ASI_NAMES = {
    "ASI01": "Agent Goal Hijack",
    "ASI02": "Tool Misuse and Exploitation",
    "ASI03": "Identity and Privilege Abuse",
    "ASI04": "Agentic Supply Chain Vulnerabilities",
    "ASI05": "Unexpected Code Execution (RCE)",
    "ASI06": "Memory & Context Poisoning",
    "ASI07": "Insecure Inter-Agent Communication",
    "ASI08": "Cascading Failures",
    "ASI09": "Human-Agent Trust Exploitation",
    "ASI10": "Rogue Agents",
}


def _fmt_score(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value)


def _assessment_findings(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    errors = report.get("errors") or []
    tools = report.get("tools") or []
    if errors:
        for i, e in enumerate(errors[:8], 1):
            severity = "medium" if "307" in str(e) or "redirect" in str(e).lower() else "low_medium"
            findings.append({
                "id": f"FINDING-DISCOVERY-{i:03d}",
                "title": "MCP discovery issue",
                "severity": severity,
                "category": "discovery_failure",
                "evidence": str(e),
                "impact": "The scanner may not have retrieved all tool schemas; risk assessment confidence is reduced.",
                "recommendation": "Verify the endpoint URL, preserve trailing slash for Gradio MCP endpoints, follow redirects, and retry supported discovery modes.",
            })
    if not tools:
        findings.append({
            "id": "FINDING-ASSESSMENT-001",
            "title": "No MCP tool schemas discovered",
            "severity": "high_for_assessment_quality",
            "category": "incomplete_assessment",
            "evidence": "tools=[], raw_tool_count=0",
            "impact": "The scanner cannot calculate a tool-level risk score. The result is inconclusive, not low risk.",
            "recommendation": "Fix endpoint discovery or provide a valid Streamable HTTP/SSE MCP endpoint, then rerun schema discovery before drawing security conclusions.",
        })
    return findings


def write_markdown_report(report: Dict[str, Any], path: str | Path) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    summary = report.get("summary", {}) or {}
    tools = report.get("tools", []) or []
    status = report.get("assessment_status", summary.get("assessment_status", "unknown"))
    confidence = report.get("assessment_confidence", summary.get("assessment_confidence", "unknown"))

    lines: List[str] = []
    lines.append("# MCP Server Risk Assessment Report")
    lines.append("")
    lines.append("## Target")
    lines.append(f"- Server URL: `{report.get('server_url')}`")
    lines.append(f"- Resolved URL: `{report.get('resolved_url')}`")
    lines.append(f"- Mode: `{report.get('mode')}`")
    lines.append(f"- Discovery method: `{report.get('discovery_method', 'unknown')}`")
    lines.append(f"- Assessment profile: `{report.get('assessment_profile', 'schema_only')}`")
    lines.append(f"- Safety boundary: {report.get('safety_boundary', 'schema-only')}")

    lines.append("\n## Executive Summary")
    if not tools:
        lines.append(
            "The assessment is **inconclusive**. The scanner did not discover any MCP tool schemas, "
            "so no tool-level security conclusion can be drawn. This must not be interpreted as low risk."
        )
    elif report.get("mode") == "documentation":
        lines.append(
            "The target is a documentation/reference URL, not a live MCP server. The report summarizes "
            "MCP/connector risk-relevant references discovered from the documentation and maps them to review controls."
        )
    else:
        lines.append(
            "The scanner discovered MCP/Gradio tool schemas and performed schema-only static risk classification. "
            "No third-party tool execution was performed."
        )

    lines.append("\n## Assessment Status")
    lines.append(f"- Status: `{status}`")
    lines.append(f"- Risk Level: `{summary.get('risk_level', 'unknown')}`")
    lines.append(f"- Risk Score: `{_fmt_score(summary.get('risk_score'))}`")
    lines.append(f"- Tools Discovered: `{summary.get('tools_discovered', summary.get('tools', 0))}`")
    lines.append(f"- Raw Tool Count: `{report.get('raw_tool_count', 0)}`")
    lines.append(f"- High-risk Tools: `{_fmt_score(summary.get('high_risk_tools'))}`")
    lines.append(f"- Assessment Confidence: `{confidence}`")
    lines.append(f"- Mapped ASI: {', '.join(summary.get('mapped_asi', [])) or 'n/a'}")

    if report.get("endpoint_candidates"):
        lines.append("\n## Endpoint Candidates Tried / Derived")
        for u in report.get("endpoint_candidates", [])[:20]:
            lines.append(f"- `{u}`")

    if report.get("errors"):
        lines.append("\n## Discovery Notes / Errors")
        for e in report.get("errors", []):
            lines.append(f"- `{e}`")

    lines.append("\n## Findings")
    assessment_findings = _assessment_findings(report)
    if assessment_findings:
        for f in assessment_findings:
            lines.append(f"\n### {f['id']}: {f['title']}")
            lines.append(f"- Severity: {f['severity']}")
            lines.append(f"- Category: {f['category']}")
            lines.append(f"- Evidence: `{f['evidence']}`")
            lines.append(f"- Impact: {f['impact']}")
            lines.append(f"- Recommendation: {f['recommendation']}")
    else:
        lines.append("No discovery-level findings were generated.")

    lines.append("\n## Tool Risk Table")
    if tools:
        lines.append("| Tool | Level | Score | Capabilities | ASI | Recommended Benchmarks |")
        lines.append("|---|---:|---:|---|---|---|")
        for t in tools:
            lines.append(
                f"| `{t.get('tool_name')}` | {t.get('risk_level')} | {t.get('risk_score')} | "
                f"{', '.join(t.get('capabilities', [])) or '-'} | {', '.join(t.get('mapped_asi', [])) or '-'} | "
                f"{', '.join(t.get('recommended_benchmarks', [])) or '-'} |"
            )
    else:
        lines.append("No tool schemas were discovered; tool-level risk classification was not possible.")

    if tools:
        lines.append("\n## Tool-Level Findings")
        for t in tools:
            lines.append(f"\n### {t.get('tool_name')}")
            if not t.get("findings"):
                lines.append("- No major static schema findings.")
            for f in t.get("findings", []):
                lines.append(f"- **{f.get('type')}**: {', '.join(map(str, f.get('matches', [])))}")
            if t.get("recommended_controls"):
                lines.append("- Recommended controls: " + ", ".join(t.get("recommended_controls", [])))

    lines.append("\n## OWASP ASI Coverage")
    mapped = summary.get("mapped_asi", []) or []
    if mapped:
        for code in mapped:
            lines.append(f"- {code}: {ASI_NAMES.get(code, code)}")
    else:
        lines.append("No confirmed ASI mapping was possible because no live tool schema was discovered or the target is a documentation reference.")
    unassessed = summary.get("unassessed_asi_due_to_discovery_failure", []) or []
    if unassessed:
        lines.append("\nUnassessed risk areas due to discovery failure:")
        for code in unassessed:
            lines.append(f"- {code}: {ASI_NAMES.get(code, code)}")

    lines.append("\n## Risk Interpretation")
    interp = report.get("risk_interpretation", {}) or {}
    lines.append(f"- Can conclude low risk: `{interp.get('can_conclude_low_risk', False)}`")
    lines.append(f"- Reason: {interp.get('reason', 'n/a')}")
    lines.append(f"- Next required step: {interp.get('next_required_step', 'n/a')}")

    lines.append("\n## Recommended Next Steps")
    for step in report.get("recommended_next_steps", []) or []:
        lines.append(f"- {step}")

    lines.append("\n## Safety Boundary")
    lines.append("This assessment is schema-only by default. It does not execute third-party MCP tools. Controlled execution should only be used against systems you own or are explicitly authorized to test.")
    p.write_text("\n".join(lines), encoding="utf-8")
    return str(p)


def write_json_report(report: Dict[str, Any], path: str | Path) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Add materialized findings to JSON so downstream UI can render complete risk reports.
    enriched = dict(report)
    enriched.setdefault("findings", _assessment_findings(report))
    p.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)
