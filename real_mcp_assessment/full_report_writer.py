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


def _score(v: Any) -> str:
    return "N/A" if v is None else str(v)


def build_findings(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for i, attempt in enumerate(report.get("discovery_attempts", [])[:20], 1):
        status = attempt.get("status")
        if status in ("error", "timeout", "http_error"):
            severity = "low_medium"
            if status == "timeout":
                severity = "medium"
            findings.append({
                "id": f"FINDING-DISCOVERY-{i:03d}",
                "title": "MCP discovery issue",
                "severity": severity,
                "category": "discovery_failure",
                "evidence": f"{attempt.get('mode')} {attempt.get('url')}: {attempt.get('error') or status}",
                "impact": "The scanner may not have retrieved all tool schemas; assessment confidence is reduced.",
                "recommendation": "Verify endpoint URL, preserve trailing slashes where required, support streamable HTTP/SSE, increase timeout for cold starts, and retry fallback discovery modes.",
            })
    if not report.get("tools") and report.get("assessment_status") in ("discovery_failed", "discovery_timeout"):
        findings.append({
            "id": "FINDING-ASSESSMENT-001",
            "title": "No MCP tool schemas discovered",
            "severity": "high_for_assessment_quality",
            "category": "incomplete_assessment",
            "evidence": "tools=[], raw_tool_count=0",
            "impact": "The scanner cannot calculate a tool-level risk score. The result is inconclusive, not low risk.",
            "recommendation": "Fix endpoint discovery or provide a valid MCP endpoint, then rerun schema discovery before drawing security conclusions.",
        })
    cr = report.get("connector_review") or {}
    for f in cr.get("findings", []) if isinstance(cr, dict) else []:
        findings.append({
            "id": f.get("id", "FINDING-CONNECTOR-001"),
            "title": f.get("title", "Connector configuration risk"),
            "severity": f.get("severity", "medium"),
            "category": "connector_config",
            "evidence": f.get("evidence", "connector config"),
            "impact": "Connector configuration may affect data sharing, approval, identity, or remote-server trust boundaries.",
            "recommendation": f.get("recommendation", "Review connector configuration and apply least-privilege controls."),
        })
    return findings


def write_full_json_report(report: Dict[str, Any], path: str | Path) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    enriched = dict(report)
    enriched["findings"] = build_findings(enriched)
    p.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)


def write_full_markdown_report(report: Dict[str, Any], path: str | Path) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    summary = report.get("summary", {}) or {}
    tools = report.get("tools", []) or []
    connector_review = report.get("connector_review") or {}
    runtime_probe = report.get("runtime_probe") or {}
    findings = build_findings(report)

    lines: List[str] = []
    lines.append("# Universal MCP Risk Assessment Report")
    lines.append("")
    lines.append("## 1. Target Summary")
    lines.append(f"- Target: `{report.get('server_url')}`")
    lines.append(f"- Assessment type: `{report.get('assessment_type', 'universal_mcp_assessment')}`")
    lines.append(f"- Endpoint type: `{(report.get('endpoint_resolution') or {}).get('endpoint_type', 'unknown')}`")
    lines.append(f"- Mode: `{report.get('mode')}`")
    lines.append(f"- Profile: `{report.get('assessment_profile')}`")
    lines.append(f"- Status: `{report.get('assessment_status')}`")
    lines.append(f"- Confidence: `{report.get('assessment_confidence')}`")
    lines.append(f"- Safety boundary: {report.get('safety_boundary')}")
    lines.append("")

    lines.append("## 2. Executive Summary")
    if tools:
        lines.append("The assessor discovered MCP/Gradio tool schemas, classified tool capability risks, mapped OWASP ASI coverage, and generated benchmark recommendations. Runtime probing was performed only if explicitly authorized by the selected profile.")
    elif connector_review:
        lines.append("The target was assessed as an OpenAI-style MCP connector configuration or documentation/integration pattern. This is a config-level risk review, not live server schema validation.")
    else:
        lines.append("The assessment is inconclusive because no MCP tool schemas were discovered. This must not be interpreted as low risk.")
    lines.append("")
    lines.append(f"- Risk level: `{summary.get('risk_level', 'unknown')}`")
    lines.append(f"- Risk score: `{_score(summary.get('risk_score'))}`")
    lines.append(f"- Tools discovered: `{summary.get('tools_discovered', 0)}`")
    lines.append(f"- High-risk tools: `{_score(summary.get('high_risk_tools'))}`")
    lines.append(f"- Mapped ASI: {', '.join(summary.get('mapped_asi', [])) or 'n/a'}")
    lines.append("")

    lines.append("## 3. Endpoint Classification")
    er = report.get("endpoint_resolution") or {}
    lines.append(f"- Input: `{er.get('input', report.get('server_url'))}`")
    lines.append(f"- Normalized URL: `{er.get('normalized_url', '')}`")
    lines.append(f"- App root: `{er.get('app_root', '')}`")
    for n in er.get("notes", []) or []:
        lines.append(f"- Note: {n}")
    lines.append("")

    lines.append("## 4. Discovery Attempts")
    attempts = report.get("discovery_attempts", []) or []
    if attempts:
        lines.append("| Mode | URL | Status | HTTP | Duration | Purpose / Error |")
        lines.append("|---|---|---|---:|---:|---|")
        for a in attempts:
            purpose_error = a.get("error") or a.get("purpose") or ""
            lines.append(f"| {a.get('mode','')} | `{a.get('url','')}` | {a.get('status','')} | {a.get('http_status','')} | {a.get('duration_ms','')} ms | {purpose_error} |")
    else:
        lines.append("No live endpoint discovery attempts were required or recorded.")
    lines.append("")

    lines.append("## 5. Tool Inventory and Risk Table")
    if tools:
        lines.append("| Tool | Capability Class | Level | Score | ASI | Benchmarks |")
        lines.append("|---|---|---:|---:|---|---|")
        for t in tools:
            lines.append(f"| `{t.get('tool_name')}` | {t.get('capability_class','')} | {t.get('risk_level')} | {t.get('risk_score')} | {', '.join(t.get('mapped_asi', [])) or '-'} | {', '.join(t.get('recommended_benchmarks', [])) or '-'} |")
    else:
        lines.append("No live tool schemas were discovered.")
    lines.append("")

    if tools:
        lines.append("## 6. Tool-Level Findings")
        for t in tools:
            lines.append(f"### {t.get('tool_name')}")
            lines.append(f"- Capability class: `{t.get('capability_class')}`")
            lines.append(f"- Required controls: {', '.join(t.get('required_controls', [])) or 'n/a'}")
            dims = t.get("risk_dimensions", {}) or {}
            if dims:
                lines.append("- Risk dimensions:")
                for k, v in dims.items():
                    lines.append(f"  - {k}: {v}")
            if t.get("findings"):
                lines.append("- Static findings:")
                for f in t.get("findings", []):
                    lines.append(f"  - {f.get('type')}: {', '.join(map(str, f.get('matches', [])))}")
            lines.append("")

    if connector_review:
        lines.append("## 7. OpenAI MCP / Connector Config Risk Review")
        lines.append(f"- Type: `{connector_review.get('assessment_type')}`")
        lines.append(f"- Risk level: `{connector_review.get('risk_level')}`")
        lines.append(f"- Risk score: `{connector_review.get('risk_score')}`")
        lines.append(f"- Mapped ASI: {', '.join(connector_review.get('mapped_asi', [])) or 'n/a'}")
        lines.append(f"- Required controls: {', '.join(connector_review.get('required_controls', [])) or 'n/a'}")
        lines.append("### Connector Findings")
        for f in connector_review.get("findings", []) or []:
            lines.append(f"- **{f.get('id')} {f.get('title')}** ({f.get('severity')}): {f.get('recommendation')}")
        lines.append("")

    lines.append("## 8. Runtime Probe / Execution Measurement")
    if runtime_probe:
        lines.append(f"- Probe status: `{runtime_probe.get('probe_status')}`")
        lines.append(f"- Reason: {runtime_probe.get('reason', 'n/a')}")
        for r in runtime_probe.get("results", []) or []:
            lines.append(f"- `{r.get('tool_name')}` → {r.get('status')} ({r.get('http_status','')})")
    else:
        lines.append("Runtime probe was not run.")
    lines.append("")

    lines.append("## 9. OWASP ASI Mapping")
    mapped = summary.get("mapped_asi", []) or connector_review.get("mapped_asi", []) or []
    if mapped:
        for code in mapped:
            lines.append(f"- {code}: {ASI_NAMES.get(code, code)}")
    else:
        lines.append("No confirmed ASI mapping was possible from live tool schemas. If discovery failed, the assessment remains inconclusive.")
    if summary.get("unassessed_asi_due_to_discovery_failure"):
        lines.append("\nUnassessed due to discovery failure:")
        for code in summary.get("unassessed_asi_due_to_discovery_failure", []):
            lines.append(f"- {code}: {ASI_NAMES.get(code, code)}")
    lines.append("")

    lines.append("## 10. Findings")
    if findings:
        for f in findings:
            lines.append(f"### {f.get('id')}: {f.get('title')}")
            lines.append(f"- Severity: {f.get('severity')}")
            lines.append(f"- Category: {f.get('category')}")
            lines.append(f"- Evidence: `{f.get('evidence')}`")
            lines.append(f"- Impact: {f.get('impact')}")
            lines.append(f"- Recommendation: {f.get('recommendation')}")
            lines.append("")
    else:
        lines.append("No major findings were generated.")

    lines.append("## 11. Recommended Next Steps")
    for s in report.get("recommended_next_steps", []) or []:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## 12. Safety Boundary")
    lines.append("Schema discovery and config review are safe by default. Runtime probing must only be used against systems you own or are explicitly authorized to test. Do not execute destructive tools on third-party MCP servers.")

    p.write_text("\n".join(lines), encoding="utf-8")
    return str(p)
