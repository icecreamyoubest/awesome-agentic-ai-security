from __future__ import annotations

import json
from typing import Any, Dict, List, Set

from .tool_schema_scanner import scan_tool_schema, DEFAULT_RULES
from .risk_classifier import BENCHMARK_BY_ASI

CAPABILITY_CLASS_PRIORITY = [
    ("execute", "code_or_command_execution"),
    ("destructive", "destructive_action"),
    ("financial", "financial_or_transactional"),
    ("identity", "identity_or_authorization"),
    ("write", "write_external_or_mutating"),
    ("network", "network_or_egress"),
    ("memory", "memory_or_rag"),
    ("read", "read_only"),
]

DIMENSION_WEIGHTS = {
    "capability_risk": 0.25,
    "descriptor_injection_risk": 0.15,
    "input_schema_risk": 0.15,
    "output_data_risk": 0.10,
    "identity_oauth_risk": 0.15,
    "network_egress_risk": 0.10,
    "human_approval_gap": 0.05,
    "auditability_gap": 0.05,
}


def _as_text(x: Any) -> str:
    if isinstance(x, str):
        return x.lower()
    return json.dumps(x, ensure_ascii=False).lower()


def classify_capability(capabilities: List[str]) -> str:
    cset = set(capabilities)
    for cap, label in CAPABILITY_CLASS_PRIORITY:
        if cap in cset:
            return label
    return "unknown"


def assess_tool(tool: Dict[str, Any], rules: Dict[str, Any] | None = None) -> Dict[str, Any]:
    scan = scan_tool_schema(tool, rules or DEFAULT_RULES)
    signals = scan.get("risk_signals", {}) or {}
    capabilities = set(scan.get("capabilities", []))
    text = _as_text(tool)

    dims: Dict[str, float] = {}
    capability = classify_capability(sorted(capabilities))
    cap_score = 0.05
    if capabilities.intersection({"execute", "destructive"}):
        cap_score = 1.0
    elif capabilities.intersection({"financial", "identity"}):
        cap_score = 0.8
    elif capabilities.intersection({"write", "network"}):
        cap_score = 0.6
    elif capabilities.intersection({"memory"}):
        cap_score = 0.45
    dims["capability_risk"] = cap_score
    dims["descriptor_injection_risk"] = 1.0 if signals.get("descriptor_injection") else 0.0
    dims["input_schema_risk"] = min(1.0, 0.2 * len(signals.get("sensitive_fields", [])))
    dims["output_data_risk"] = 0.7 if any(x in text for x in ["secret", "credential", "email", "pii", "file", "content"]) else 0.1
    dims["identity_oauth_risk"] = 0.8 if capabilities.intersection({"identity"}) or any("auth" in str(x).lower() or "token" in str(x).lower() for x in signals.get("sensitive_fields", [])) else 0.0
    dims["network_egress_risk"] = 0.7 if capabilities.intersection({"network"}) or signals.get("external_access") else 0.0
    dims["human_approval_gap"] = 0.7 if capabilities.intersection({"write", "destructive", "financial", "execute"}) and "approval" not in text else 0.0
    dims["auditability_gap"] = 0.4 if "audit" not in text and "log" not in text else 0.0

    score = sum(DIMENSION_WEIGHTS[k] * dims.get(k, 0.0) for k in DIMENSION_WEIGHTS)
    if score >= 0.75:
        level = "critical"
    elif score >= 0.5:
        level = "high"
    elif score >= 0.25:
        level = "medium"
    else:
        level = "low"

    asi: Set[str] = set()
    controls: Set[str] = set()
    if dims["descriptor_injection_risk"] > 0:
        asi.update(["ASI01", "ASI04"])
        controls.update(["descriptor sanitization", "tool provenance validation"])
    if capabilities.intersection({"write", "destructive", "financial"}) or signals.get("high_risk_verbs"):
        asi.add("ASI02")
        controls.update(["tool allowlist", "pre-execution policy gate", "human approval"])
    if dims["identity_oauth_risk"] > 0:
        asi.update(["ASI03", "ASI07"])
        controls.update(["OAuth scope review", "short-lived scoped credentials", "per-action authorization"])
    if capabilities.intersection({"execute"}):
        asi.add("ASI05")
        controls.update(["sandbox", "command/path validation", "egress restriction"])
    if capabilities.intersection({"memory"}):
        asi.add("ASI06")
        controls.update(["memory segmentation", "tenant isolation", "provenance scoring"])
    if dims["network_egress_risk"] > 0:
        asi.add("ASI07")
        controls.update(["egress allowlist", "remote server allowlist", "schema validation"])
    if dims["human_approval_gap"] > 0:
        asi.add("ASI09")
        controls.add("explicit approval UX for high-impact actions")

    benchmarks: Set[str] = set()
    for code in asi:
        benchmarks.update(BENCHMARK_BY_ASI.get(code, []))

    return {
        "tool_name": scan.get("tool_name"),
        "capability_class": capability,
        "capabilities": sorted(capabilities),
        "risk_score": round(score, 3),
        "risk_level": level,
        "risk_dimensions": {k: round(v, 3) for k, v in dims.items()},
        "mapped_asi": sorted(asi),
        "required_controls": sorted(controls),
        "recommended_benchmarks": sorted(benchmarks),
        "findings": scan.get("findings", []),
        "schema_keys": scan.get("schema_keys", []),
        "raw_source": tool.get("source"),
    }


def summarize_tools(tools: List[Dict[str, Any]], discovery_status: str = "schema_discovered", errors: List[str] | None = None) -> Dict[str, Any]:
    errors = errors or []
    if not tools:
        if errors or discovery_status not in ("schema_discovered", "success"):
            timeout = any("timeout" in str(e).lower() for e in errors)
            return {
                "risk_level": "inconclusive",
                "risk_score": None,
                "assessment_status": "discovery_timeout" if timeout else discovery_status,
                "assessment_confidence": "low",
                "tools_discovered": 0,
                "high_risk_tools": None,
                "mapped_asi": [],
                "unassessed_asi_due_to_discovery_failure": ["ASI02", "ASI03", "ASI04", "ASI05", "ASI06", "ASI07", "ASI09"],
            }
        return {"risk_level": "low", "risk_score": 0.0, "assessment_status": discovery_status, "assessment_confidence": "medium", "tools_discovered": 0, "high_risk_tools": 0, "mapped_asi": []}
    max_score = max(t.get("risk_score", 0.0) for t in tools)
    high = sum(1 for t in tools if t.get("risk_level") in ("high", "critical"))
    mapped = sorted({a for t in tools for a in t.get("mapped_asi", [])})
    if max_score >= 0.75:
        level = "critical"
    elif max_score >= 0.5:
        level = "high"
    elif max_score >= 0.25:
        level = "medium"
    else:
        level = "low"
    return {
        "risk_level": level,
        "risk_score": round(max_score, 3),
        "assessment_status": discovery_status,
        "assessment_confidence": "medium-high",
        "tools_discovered": len(tools),
        "high_risk_tools": high,
        "mapped_asi": mapped,
    }
