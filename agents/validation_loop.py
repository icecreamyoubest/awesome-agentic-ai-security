#!/usr/bin/env python3
"""Validation loop: scenario -> risks -> tools -> benchmark plan -> score update hints."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

if __package__ is None or __package__ == "":
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.risk_mapper import map_scenario_to_risks
from agents.tool_recommender import recommend_tools
from agents.benchmark_planner import select_benchmark_cases, runtime_checks_for_risks, score_update_suggestions
from agents.schemas import Scenario

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str) -> Dict[str, Any]:
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def run_validation_loop(scenario_path: str) -> Dict[str, Any]:
    raw = json.load(open(ROOT / scenario_path, encoding="utf-8")) if not str(scenario_path).startswith("/") else json.load(open(scenario_path, encoding="utf-8"))
    scenario = Scenario.from_dict(raw)
    tools_doc = load_json("data/tools.json")
    benchmark_doc = load_json("benchmarks/mcp_security_benchmark_v01.json")
    risks, lifecycle = map_scenario_to_risks(scenario)
    risk_codes = [r.asi for r in risks]
    recommendations = recommend_tools(
        tools_doc,
        risk_codes,
        lifecycle,
        scenario.frameworks,
        scenario.constraints,
        limit=12,
    )
    selected_cases = select_benchmark_cases(benchmark_doc, risk_codes, scenario.architecture, max_cases=8)
    covered = sorted(set(sum([r.matched_risks for r in recommendations], [])) & set(risk_codes))
    required = sorted(set(risk_codes))
    gaps = sorted(set(required) - set(covered))
    return {
        "scenario": {"name": scenario.name, "description": scenario.description},
        "mapped_risks": [r.__dict__ for r in risks],
        "recommended_tools": [r.__dict__ for r in recommendations],
        "coverage": {"required": required, "covered_by_recommendations": covered, "gaps": gaps},
        "benchmark_plan": selected_cases,
        "runtime_checks": runtime_checks_for_risks(risk_codes),
        "score_update_suggestions": score_update_suggestions(recommendations, selected_cases),
        "next_actions": [
            "Run benchmark_plan cases against the target runtime or mock harness.",
            "Verify top vendor/tool claims using agents/claim_verifier.py.",
            "Generate architecture with agents/architecture_generator.py.",
            "Attach results to data/evidence.json and update confidence scores."
        ]
    }


def to_markdown(result: Dict[str, Any]) -> str:
    lines = [f"# Validation Loop Report: {result['scenario']['name']}\n", result['scenario'].get('description',''), "\n## Mapped ASI risks"]
    for r in result["mapped_risks"]:
        lines.append(f"- **{r['asi']}** — {r.get('title','')} ({r.get('relevance','')}) — {r.get('reason','')}")
    lines.append("\n## Recommended tools")
    for t in result["recommended_tools"][:8]:
        lines.append(f"- **{t['name']}** — score {t.get('score')} — {', '.join(t.get('matched_risks', [])[:6])}")
    lines.append("\n## Coverage")
    c = result["coverage"]
    lines.append(f"- Required: {', '.join(c['required'])}")
    lines.append(f"- Covered by recommendations: {', '.join(c['covered_by_recommendations']) or 'none'}")
    lines.append(f"- Gaps: {', '.join(c['gaps']) or 'none'}")
    lines.append("\n## Benchmark plan")
    for b in result["benchmark_plan"]:
        lines.append(f"- **{b['id']}** — {b.get('title','')} — ASI: {', '.join(b.get('asi', []))}")
    lines.append("\n## Score update suggestions")
    for s in result["score_update_suggestions"]:
        lines.append(f"- **{s['tool_name']}**: validate {', '.join(s.get('candidate_benchmark_cases', []))}. {s.get('suggestion', s.get('score_policy', ''))}")
    lines.append("\n## Next actions")
    for n in result["next_actions"]:
        lines.append(f"- {n}")
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="Run scenario-to-validation loop")
    p.add_argument("--scenario", required=True)
    p.add_argument("--output", default="")
    p.add_argument("--json-output", default="")
    args = p.parse_args()
    result = run_validation_loop(args.scenario)
    md = to_markdown(result)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(md, encoding="utf-8")
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
