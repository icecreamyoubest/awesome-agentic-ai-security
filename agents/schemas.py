from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


VALID_ASI = {f"ASI{i:02d}" for i in range(1, 11)}

ASI_TITLES = {
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

LIFECYCLE_TITLES = {
    "scope_plan": "Scope & Plan",
    "augment_finetune_data": "Augment / Fine-tune Data",
    "develop_experiment": "Develop & Experiment",
    "test_evaluate": "Test & Evaluate",
    "release": "Release",
    "deploy": "Deploy",
    "operate": "Operate",
    "monitor": "Monitor",
    "govern": "Govern",
}


@dataclass
class Scenario:
    name: str
    description: str
    frameworks: List[str] = field(default_factory=list)
    architecture: List[str] = field(default_factory=list)
    lifecycle_stage: List[str] = field(default_factory=list)
    risk_focus: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    high_impact_actions: List[str] = field(default_factory=list)
    external_integrations: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        return cls(
            name=data.get("name", "Unnamed scenario"),
            description=data.get("description", ""),
            frameworks=list(data.get("frameworks", [])),
            architecture=list(data.get("architecture", [])),
            lifecycle_stage=list(data.get("lifecycle_stage", [])),
            risk_focus=list(data.get("risk_focus", [])),
            constraints=dict(data.get("constraints", {})),
            high_impact_actions=list(data.get("high_impact_actions", [])),
            external_integrations=list(data.get("external_integrations", [])),
        )


@dataclass
class RiskFinding:
    asi: str
    title: str
    relevance: str
    reason: str
    source_signals: List[str]


@dataclass
class ToolRecommendation:
    tool_id: str
    name: str
    org: str
    category: List[str]
    score: float
    matched_risks: List[str]
    matched_lifecycle: List[str]
    matched_frameworks: List[str]
    deployment_fit: List[str]
    evidence_confidence: float
    rationale: str


@dataclass
class ValidationPlan:
    benchmark_cases: List[Dict[str, Any]]
    evidence_checks: List[Dict[str, Any]]
    runtime_checks: List[str]
    score_update_suggestions: List[Dict[str, Any]]
