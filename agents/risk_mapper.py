from __future__ import annotations

from typing import Dict, List, Tuple

from .schemas import ASI_TITLES, LIFECYCLE_TITLES, RiskFinding, Scenario

ARCH_KEYWORDS = {
    "mcp": ["ASI02", "ASI04", "ASI05", "ASI07"],
    "tool_use": ["ASI02", "ASI03"],
    "tools": ["ASI02", "ASI03"],
    "external_api": ["ASI02", "ASI03", "ASI07"],
    "rag": ["ASI01", "ASI06"],
    "vector_db": ["ASI06"],
    "long_term_memory": ["ASI06", "ASI08"],
    "multi_agent": ["ASI07", "ASI08", "ASI10"],
    "a2a": ["ASI03", "ASI07", "ASI10"],
    "coding_agent": ["ASI04", "ASI05", "ASI09"],
    "browser_agent": ["ASI01", "ASI02", "ASI03", "ASI09"],
    "autonomous_workflow": ["ASI01", "ASI08", "ASI10"],
    "oauth": ["ASI03", "ASI07"],
    "human_approval": ["ASI09"],
    "hitl": ["ASI09"],
}

DEFAULT_LIFECYCLE_BY_RISK = {
    "ASI01": ["scope_plan", "test_evaluate", "deploy", "operate", "monitor"],
    "ASI02": ["develop_experiment", "test_evaluate", "deploy", "operate", "monitor"],
    "ASI03": ["scope_plan", "deploy", "operate", "monitor", "govern"],
    "ASI04": ["develop_experiment", "release", "deploy", "operate", "govern"],
    "ASI05": ["develop_experiment", "test_evaluate", "deploy", "operate"],
    "ASI06": ["augment_finetune_data", "test_evaluate", "operate", "monitor", "govern"],
    "ASI07": ["develop_experiment", "deploy", "operate", "monitor"],
    "ASI08": ["test_evaluate", "operate", "monitor", "govern"],
    "ASI09": ["scope_plan", "deploy", "operate", "govern"],
    "ASI10": ["scope_plan", "operate", "monitor", "govern"],
}

REASONS = {
    "ASI01": "Untrusted natural-language or external content can redirect agent goals, planning, or task selection.",
    "ASI02": "The system exposes tools or APIs that can be misused, over-invoked, or chained in unsafe ways.",
    "ASI03": "Delegated access, OAuth, service identities, or agent-to-agent trust can create privilege-abuse paths.",
    "ASI04": "Tools, MCP servers, packages, prompts, agent cards, or registries introduce a live supply-chain attack surface.",
    "ASI05": "The system can generate, execute, install, or route code/commands through tools or coding-agent workflows.",
    "ASI06": "Memory, RAG, vector stores, or long context can be poisoned and reused across future reasoning cycles.",
    "ASI07": "Inter-agent, MCP, A2A, or external protocol traffic requires authentication, integrity, and semantic validation.",
    "ASI08": "Autonomous delegation, retries, or multi-agent fan-out can amplify one fault into a system-wide failure.",
    "ASI09": "Human reviewers may over-trust confident explanations, previews, or recommendations from the agent.",
    "ASI10": "Autonomous agents can drift, collude, self-replicate, or deviate from declared behavioral boundaries.",
}


def map_scenario_to_risks(scenario: Scenario) -> Tuple[List[RiskFinding], List[str]]:
    scores: Dict[str, int] = {k: 0 for k in ASI_TITLES}
    signals: Dict[str, List[str]] = {k: [] for k in ASI_TITLES}

    combined = [s.lower().replace("-", "_") for s in scenario.frameworks + scenario.architecture + scenario.external_integrations]
    combined += [s.lower().replace("-", "_") for s in scenario.high_impact_actions]
    text = (scenario.description or "").lower().replace("-", "_")

    for key, risks in ARCH_KEYWORDS.items():
        if key in combined or key in text:
            for risk in risks:
                scores[risk] += 2
                signals[risk].append(key)

    for risk in scenario.risk_focus:
        if risk in scores:
            scores[risk] += 3
            signals[risk].append("explicit_risk_focus")

    if scenario.constraints.get("enterprise_ready"):
        for risk in ["ASI03", "ASI07", "ASI08", "ASI10"]:
            scores[risk] += 1
            signals[risk].append("enterprise_ready")
    if scenario.constraints.get("self_host"):
        for risk in ["ASI04", "ASI05"]:
            scores[risk] += 1
            signals[risk].append("self_hosted_runtime")

    findings: List[RiskFinding] = []
    for asi, score in sorted(scores.items(), key=lambda x: (-x[1], x[0])):
        if score <= 0:
            continue
        relevance = "High" if score >= 4 else "Medium" if score >= 2 else "Low"
        findings.append(
            RiskFinding(
                asi=asi,
                title=ASI_TITLES[asi],
                relevance=relevance,
                reason=REASONS[asi],
                source_signals=signals[asi],
            )
        )

    lifecycle = set(scenario.lifecycle_stage)
    for finding in findings:
        lifecycle.update(DEFAULT_LIFECYCLE_BY_RISK.get(finding.asi, []))
    return findings, [x for x in LIFECYCLE_TITLES if x in lifecycle]
