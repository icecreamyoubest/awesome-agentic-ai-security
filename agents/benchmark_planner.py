from __future__ import annotations

from typing import Any, Dict, List


def select_benchmark_cases(benchmark_data: Dict[str, Any], risks: List[str], architecture: List[str], max_cases: int = 8) -> List[Dict[str, Any]]:
    risk_set = set(risks)
    arch = " ".join(architecture).lower()
    selected = []
    for case in benchmark_data.get("cases", []):
        case_risks = set(case.get("asi", []))
        score = len(risk_set & case_risks) * 2
        attack = (case.get("attack_type") or "").lower()
        if "mcp" in arch and "mcp" in case.get("id", "").lower():
            score += 2
        if "a2a" in arch and ("a2a" in case.get("id", "").lower() or "agent" in attack):
            score += 2
        if "rag" in arch or "memory" in arch:
            if "memory" in attack or "tool-output" in attack or "cross-tenant" in attack:
                score += 1
        if score > 0:
            c = dict(case)
            c["selection_score"] = score
            selected.append(c)
    return sorted(selected, key=lambda x: (-x["selection_score"], x.get("id", "")))[:max_cases]


def runtime_checks_for_risks(risks: List[str]) -> List[str]:
    checks = []
    risk_set = set(risks)
    if {"ASI01", "ASI02"} & risk_set:
        checks.append("Run intent-gate validation before high-impact tool calls and compare planned vs observed actions.")
    if "ASI03" in risk_set:
        checks.append("Verify per-agent identity, short-lived scoped tokens, and per-action authorization decisions.")
    if "ASI04" in risk_set:
        checks.append("Validate MCP/tool/server provenance, pin versions, and reject unsigned or untrusted descriptors.")
    if "ASI05" in risk_set:
        checks.append("Execute code/tool calls only in sandboxed runtimes with egress allowlists and file-system boundaries.")
    if "ASI06" in risk_set:
        checks.append("Test memory write controls, provenance labels, tenant namespaces, rollback, and quarantine flows.")
    if "ASI07" in risk_set:
        checks.append("Check A2A/MCP message authentication, schema validation, anti-replay, and signed agent cards.")
    if "ASI08" in risk_set:
        checks.append("Define blast-radius caps, circuit breakers, rate limits, queue-depth alarms, and kill-switch procedures.")
    if "ASI09" in risk_set:
        checks.append("Review human approval UX, side-effect previews, non-persuasive language, and provenance cues.")
    if "ASI10" in risk_set:
        checks.append("Add behavioral baselines, rogue-agent quarantine, credential revocation, and reintegration checks.")
    return checks


def score_update_suggestions(recommendations: List[Any], selected_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cases_by_asi = {}
    for case in selected_cases:
        for asi in case.get("asi", []):
            cases_by_asi.setdefault(asi, []).append(case["id"])
    suggestions = []
    for rec in recommendations[:6]:
        covered = set(rec.matched_risks) & set(cases_by_asi)
        if not covered:
            continue
        suggestions.append({
            "tool_id": rec.tool_id,
            "tool_name": rec.name,
            "candidate_benchmark_cases": sorted({cid for asi in covered for cid in cases_by_asi[asi]}),
            "score_policy": "If benchmark passes reproducibly, consider raising ASI coverage depth to 3 for the relevant risk and adding benchmark_backed evidence.",
        })
    return suggestions
