from __future__ import annotations

from typing import Any, Dict, List

from .schemas import ToolRecommendation


LAYER_KEYWORDS = {
    "red_team": ["Red Teaming", "Evaluation", "Adversarial Testing"],
    "runtime_guardrails": ["Guardrails", "Runtime Defense", "Content Safety"],
    "mcp_security": ["MCP Security", "Supply Chain", "Agentic OWASP Mapping"],
    "observability": ["Observability", "Monitoring", "Tracing"],
    "governance": ["Governance", "AI-SPM", "Compliance", "Data Security"],
}


def _framework_match(tool: Dict[str, Any], scenario_frameworks: List[str]) -> List[str]:
    tf = tool.get("frameworks", {})
    matched = []
    for fw in scenario_frameworks:
        fw_l = fw.lower()
        for tool_fw in tf.keys():
            if fw_l in tool_fw.lower() or tool_fw.lower() in fw_l:
                matched.append(tool_fw)
    return sorted(set(matched))


def _deployment_fit(tool: Dict[str, Any], constraints: Dict[str, Any]) -> List[str]:
    deployment = [d.lower() for d in tool.get("deployment", [])]
    fit = []
    if constraints.get("self_host") and any(d in deployment for d in ["self-hosted", "self_hosted", "open_source", "local"]):
        fit.append("self-host capable")
    if constraints.get("enterprise_ready") and any(d in deployment for d in ["enterprise", "saas", "cloud"]):
        fit.append("enterprise deployment")
    if constraints.get("open_source_preferred") and tool.get("vendor_type") in {"open_source", "open-core", "open_core"}:
        fit.append("open-source preferred")
    return fit


def recommend_tools(tools_data: Dict[str, Any], risks: List[str], lifecycle: List[str], scenario_frameworks: List[str], constraints: Dict[str, Any], limit: int = 12) -> List[ToolRecommendation]:
    recommendations: List[ToolRecommendation] = []
    risk_set = set(risks)
    lifecycle_set = set(lifecycle)

    for tool in tools_data.get("tools", []):
        tool_risks = set(tool.get("agentic_owasp", []))
        tool_lifecycle = set(tool.get("lifecycle_stages", []))
        matched_risks = sorted(risk_set & tool_risks)
        matched_lifecycle = sorted(lifecycle_set & tool_lifecycle)
        matched_frameworks = _framework_match(tool, scenario_frameworks)
        deployment_fit = _deployment_fit(tool, constraints)
        scores = tool.get("scores", {})
        confidence = float(tool.get("evidence_confidence", {}).get("confidence_score", 0))

        base = 0.0
        base += len(matched_risks) * 1.8
        base += len(matched_lifecycle) * 0.45
        base += len(matched_frameworks) * 0.35
        base += len(deployment_fit) * 0.8
        base += float(scores.get("agentic_readiness", 0)) * 0.8
        base += float(scores.get("mcp_security", 0)) * (0.8 if "ASI02" in risk_set or "ASI04" in risk_set or "ASI07" in risk_set else 0.35)
        base += confidence * 0.4
        if constraints.get("self_host") and float(scores.get("self_host", 0)) >= 4:
            base += 1.0
        if constraints.get("open_source_preferred") and tool.get("vendor_type") in {"open_source", "open-core", "open_core"}:
            base += 1.5

        if not matched_risks and base < 5:
            continue

        rationale_bits = []
        if matched_risks:
            rationale_bits.append(f"covers {', '.join(matched_risks)}")
        if matched_lifecycle:
            rationale_bits.append(f"maps to {len(matched_lifecycle)} lifecycle stages")
        if matched_frameworks:
            rationale_bits.append(f"matches framework(s): {', '.join(matched_frameworks)}")
        if deployment_fit:
            rationale_bits.append(f"deployment fit: {', '.join(deployment_fit)}")
        if not rationale_bits:
            rationale_bits.append("general agentic security fit based on score profile")

        recommendations.append(
            ToolRecommendation(
                tool_id=tool["id"],
                name=tool.get("name", tool["id"]),
                org=tool.get("org", ""),
                category=list(tool.get("category", [])),
                score=round(base, 2),
                matched_risks=matched_risks,
                matched_lifecycle=matched_lifecycle,
                matched_frameworks=matched_frameworks,
                deployment_fit=deployment_fit,
                evidence_confidence=confidence,
                rationale="; ".join(rationale_bits),
            )
        )

    return sorted(recommendations, key=lambda x: (-x.score, -len(x.matched_risks), x.name))[:limit]


def group_by_security_layer(recommendations: List[ToolRecommendation]) -> Dict[str, List[ToolRecommendation]]:
    grouped = {k: [] for k in LAYER_KEYWORDS}
    for rec in recommendations:
        cats = set(rec.category)
        for layer, keywords in LAYER_KEYWORDS.items():
            if any(k in cats for k in keywords):
                grouped[layer].append(rec)
    return grouped
