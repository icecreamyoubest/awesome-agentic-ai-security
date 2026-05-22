from __future__ import annotations

from typing import Any, Dict, List, Set

CAPABILITY_WEIGHTS = {
    "read": 0.05,
    "write": 0.18,
    "execute": 0.25,
    "destructive": 0.25,
    "financial": 0.22,
    "identity": 0.20,
    "network": 0.15,
    "memory": 0.13,
    "unknown": 0.10,
}

BENCHMARK_BY_ASI = {
    "ASI01": ["MCP-ASI01-005"],
    "ASI02": ["MCP-ASI02-004"],
    "ASI03": ["MCP-ASI07-003"],
    "ASI04": ["MCP-ASI04-001", "MCP-ASI04-009"],
    "ASI05": ["MCP-ASI05-002"],
    "ASI06": ["RAG-ASI06-007"],
    "ASI07": ["MCP-ASI07-003", "A2A-ASI07-006"],
    "ASI08": ["MCP-ASI08-008"],
    "ASI09": ["HITL-ASI09-010"],
    "ASI10": ["A2A-ASI07-006"],
}


def classify_scan(scan: Dict[str, Any]) -> Dict[str, Any]:
    capabilities = set(scan.get("capabilities", []))
    signals = scan.get("risk_signals", {}) or {}
    findings = scan.get("findings", [])

    asi: Set[str] = set()
    controls: Set[str] = set()

    if signals.get("descriptor_injection"):
        asi.update(["ASI01", "ASI04"])
        controls.update(["descriptor sanitization", "tool provenance validation"])
    if signals.get("high_risk_verbs") or capabilities.intersection({"write", "destructive", "financial"}):
        asi.update(["ASI02"])
        controls.update(["tool allowlist", "pre-execution policy gate", "human approval"])
    if capabilities.intersection({"identity"}) or any("token" in x.lower() or "auth" in x.lower() for x in signals.get("sensitive_fields", [])):
        asi.update(["ASI03", "ASI07"])
        controls.update(["scoped credentials", "OAuth response validation", "per-action authorization"])
    if capabilities.intersection({"execute"}):
        asi.update(["ASI05"])
        controls.update(["sandbox", "command/path validation", "egress restriction"])
    if capabilities.intersection({"memory"}):
        asi.update(["ASI06"])
        controls.update(["memory segmentation", "tenant isolation", "provenance scoring"])
    if capabilities.intersection({"network"}):
        asi.update(["ASI02", "ASI07"])
        controls.update(["egress allowlist", "schema validation"])

    base = sum(CAPABILITY_WEIGHTS.get(c, 0.1) for c in capabilities)
    signal_weight = 0.0
    signal_weight += 0.18 if signals.get("descriptor_injection") else 0.0
    signal_weight += 0.10 if signals.get("sensitive_fields") else 0.0
    signal_weight += 0.08 if signals.get("external_access") else 0.0
    signal_weight += 0.08 if signals.get("high_risk_verbs") else 0.0
    score = min(1.0, base + signal_weight)

    if score >= 0.75:
        level = "critical"
    elif score >= 0.50:
        level = "high"
    elif score >= 0.25:
        level = "medium"
    else:
        level = "low"

    benchmarks: Set[str] = set()
    for code in asi:
        benchmarks.update(BENCHMARK_BY_ASI.get(code, []))

    return {
        "tool_name": scan.get("tool_name"),
        "risk_score": round(score, 3),
        "risk_level": level,
        "mapped_asi": sorted(asi),
        "recommended_controls": sorted(controls),
        "recommended_benchmarks": sorted(benchmarks),
        "capabilities": sorted(capabilities),
        "findings": findings,
    }


def summarize_server(classified_tools: List[Dict[str, Any]], *, discovery_status: str = "success", errors: List[str] | None = None) -> Dict[str, Any]:
    errors = errors or []
    if not classified_tools:
        if discovery_status != "success" or errors:
            return {
                "risk_level": "inconclusive",
                "risk_score": None,
                "assessment_status": discovery_status or "discovery_failed",
                "assessment_confidence": "low",
                "high_risk_tools": None,
                "tools": 0,
                "tools_discovered": 0,
                "mapped_asi": [],
                "unassessed_asi_due_to_discovery_failure": ["ASI02", "ASI03", "ASI04", "ASI05", "ASI06", "ASI07", "ASI09"],
            }
        return {"risk_level": "low", "risk_score": 0, "assessment_status": "success", "assessment_confidence": "medium", "high_risk_tools": 0, "tools": 0, "tools_discovered": 0, "mapped_asi": []}
    max_score = max(t.get("risk_score", 0) for t in classified_tools)
    high = sum(1 for t in classified_tools if t.get("risk_level") in ("high", "critical"))
    asi = sorted({a for t in classified_tools for a in t.get("mapped_asi", [])})
    if max_score >= 0.75 or high >= 2:
        level = "critical" if max_score >= 0.85 else "high"
    elif max_score >= 0.5:
        level = "high"
    elif max_score >= 0.25:
        level = "medium"
    else:
        level = "low"
    return {"risk_level": level, "risk_score": round(max_score, 3), "assessment_status": discovery_status or "success", "assessment_confidence": "medium-high", "high_risk_tools": high, "tools": len(classified_tools), "tools_discovered": len(classified_tools), "mapped_asi": asi}
