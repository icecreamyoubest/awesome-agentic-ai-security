from __future__ import annotations

from typing import Any, Dict, List

from .schemas import ASI_TITLES, LIFECYCLE_TITLES, RiskFinding, Scenario, ToolRecommendation
from .tool_recommender import group_by_security_layer


def _md_list(items: List[str]) -> str:
    if not items:
        return "- None identified\n"
    return "\n".join(f"- {x}" for x in items) + "\n"


def render_report(
    scenario: Scenario,
    risks: List[RiskFinding],
    lifecycle: List[str],
    recommendations: List[ToolRecommendation],
    validation_plan: Dict[str, Any],
) -> str:
    risk_codes = [r.asi for r in risks]
    recommended_covered = sorted({asi for rec in recommendations for asi in rec.matched_risks})
    partial = sorted(set(risk_codes) - set(recommended_covered))

    lines: List[str] = []
    lines.append(f"# Agentic AI Security Solution Validation Report: {scenario.name}\n")
    lines.append("## 1. Scenario Summary\n")
    lines.append(f"{scenario.description}\n")
    lines.append("| Field | Value |\n|---|---|\n")
    lines.append(f"| Frameworks | {', '.join(scenario.frameworks) or 'Not specified'} |\n")
    lines.append(f"| Architecture | {', '.join(scenario.architecture) or 'Not specified'} |\n")
    lines.append(f"| External integrations | {', '.join(scenario.external_integrations) or 'Not specified'} |\n")
    lines.append(f"| High-impact actions | {', '.join(scenario.high_impact_actions) or 'Not specified'} |\n")
    lines.append(f"| Constraints | {scenario.constraints} |\n\n")

    lines.append("## 2. OWASP ASI Risk Mapping\n")
    lines.append("| ASI | Risk | Relevance | Reason | Signals |\n|---|---|---:|---|---|\n")
    for r in risks:
        lines.append(f"| {r.asi} | {r.title} | {r.relevance} | {r.reason} | {', '.join(r.source_signals)} |\n")
    lines.append("\n")

    lines.append("## 3. Lifecycle Focus\n")
    lines.append(_md_list([LIFECYCLE_TITLES.get(x, x) for x in lifecycle]))

    lines.append("## 4. Recommended Security Stack\n")
    grouped = group_by_security_layer(recommendations)
    layer_titles = {
        "red_team": "Red-team and evaluation",
        "runtime_guardrails": "Runtime guardrails",
        "mcp_security": "MCP / toolchain security",
        "observability": "Observability and tracing",
        "governance": "Governance and posture",
    }
    for layer, recs in grouped.items():
        if not recs:
            continue
        lines.append(f"### {layer_titles[layer]}\n")
        lines.append("| Tool | Org | Fit Score | Matched ASI | Evidence Confidence | Rationale |\n|---|---|---:|---|---:|---|\n")
        for rec in recs[:5]:
            lines.append(f"| {rec.name} | {rec.org} | {rec.score} | {', '.join(rec.matched_risks)} | {rec.evidence_confidence} | {rec.rationale} |\n")
        lines.append("\n")

    lines.append("## 5. Coverage Analysis\n")
    lines.append(f"- Covered by recommended tools: {', '.join(recommended_covered) or 'None'}\n")
    lines.append(f"- Residual / partially covered risks: {', '.join(partial) or 'None'}\n")
    if partial:
        lines.append("- Recommendation: require additional evidence or controls before production enforcement for residual risks.\n")
    lines.append("\n")

    lines.append("## 6. Validation Plan\n")
    lines.append("### Benchmark cases\n")
    lines.append("| Case ID | ASI | Attack Type | Pass Condition |\n|---|---|---|---|\n")
    for case in validation_plan.get("benchmark_cases", []):
        lines.append(f"| {case.get('id')} | {', '.join(case.get('asi', []))} | {case.get('attack_type')} | {case.get('pass_condition')} |\n")
    lines.append("\n### Runtime checks\n")
    lines.append(_md_list(validation_plan.get("runtime_checks", [])))

    lines.append("### Evidence checks\n")
    lines.append("| Tool | Validation Level | Confidence | Required Next Evidence |\n|---|---|---:|---|\n")
    for check in validation_plan.get("evidence_checks", [])[:10]:
        gaps = "; ".join(check.get("required_next_evidence", [])) or "No immediate gap"
        lines.append(f"| {check['tool_name']} | {check['validation_level']} | {check['confidence_score']} | {gaps} |\n")
    lines.append("\n")

    lines.append("## 7. Score Update Suggestions\n")
    for s in validation_plan.get("score_update_suggestions", []):
        lines.append(f"- **{s['tool_name']}**: run {', '.join(s['candidate_benchmark_cases'])}. {s['score_policy']}\n")
    if not validation_plan.get("score_update_suggestions"):
        lines.append("- No benchmark-backed score update suggestion yet.\n")

    lines.append("\n## 8. Implementation Notes\n")
    lines.append("- Treat this report as a validation plan, not a certification.\n")
    lines.append("- Keep the rule engine deterministic; use an LLM only for optional explanation or report polishing.\n")
    lines.append("- Raise scores only after evidence records or benchmark results are added to the repository.\n")
    return "".join(lines)
