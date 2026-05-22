from __future__ import annotations

from typing import Any, Dict, List

ASI_NAMES = {
    "ASI01": "Agent Goal Hijack",
    "ASI02": "Tool Misuse and Exploitation",
    "ASI03": "Identity and Privilege Abuse",
    "ASI04": "Agentic Supply Chain Vulnerabilities",
    "ASI05": "Unexpected Code Execution",
    "ASI06": "Memory & Context Poisoning",
    "ASI07": "Insecure Inter-Agent Communication",
    "ASI08": "Cascading Failures",
    "ASI09": "Human-Agent Trust Exploitation",
    "ASI10": "Rogue Agents",
}


def build_risk_dashboard(report: Dict[str, Any]) -> Dict[str, Any]:
    asi_counts = {k: 0 for k in ASI_NAMES}
    event_evidence: Dict[str, List[str]] = {k: [] for k in ASI_NAMES}
    by_agent: Dict[str, Dict[str, int]] = {}
    by_tool: Dict[str, Dict[str, int]] = {}
    decision_counts = {"allowed": 0, "blocked": 0, "other": 0}

    for flow in report.get("flows", []):
        for msg in flow.get("messages", []):
            for asi in msg.get("mapped_asi", []) or []:
                asi_counts[asi] = asi_counts.get(asi, 0) + 1
                event_evidence.setdefault(asi, []).append(f"{flow.get('flow_name')}: A2A {msg.get('sender')} → {msg.get('recipient')} {msg.get('decision')}")
        for ev in flow.get("tool_events", []):
            d = ev.get("decision") or {}
            decision = d.get("decision") or ("allowed" if ev.get("allowed") else "blocked")
            if decision in {"allowed", "allow"}:
                decision_counts["allowed"] += 1
            elif decision in {"blocked", "denied", "deny"}:
                decision_counts["blocked"] += 1
            else:
                decision_counts["other"] += 1
            agent = ev.get("agent") or "unknown"
            tool = ev.get("tool") or "unknown"
            by_agent.setdefault(agent, {"allowed": 0, "blocked": 0, "other": 0})
            by_tool.setdefault(tool, {"allowed": 0, "blocked": 0, "other": 0})
            key = "allowed" if decision in {"allowed", "allow"} else "blocked" if decision in {"blocked", "denied", "deny"} else "other"
            by_agent[agent][key] += 1
            by_tool[tool][key] += 1
            for asi in d.get("asi", []) or []:
                asi_counts[asi] = asi_counts.get(asi, 0) + 1
                event_evidence.setdefault(asi, []).append(f"{flow.get('flow_name')}: {agent} → {tool} {decision}")

    coverage = []
    for asi, name in ASI_NAMES.items():
        count = asi_counts.get(asi, 0)
        coverage.append({
            "asi": asi,
            "name": name,
            "count": count,
            "status": "covered" if count else "not_observed",
            "evidence": event_evidence.get(asi, [])[:5],
        })

    return {
        "asi_coverage": coverage,
        "decision_counts": decision_counts,
        "risk_by_agent": by_agent,
        "risk_by_tool": by_tool,
        "summary": report.get("summary", {}),
    }
