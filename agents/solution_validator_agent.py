#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

if __package__ is None or __package__ == "":
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from agents.benchmark_planner import runtime_checks_for_risks, score_update_suggestions, select_benchmark_cases
from agents.evidence_validator import build_evidence_checks
from agents.report_writer import render_report
from agents.risk_mapper import map_scenario_to_risks
from agents.schemas import Scenario
from agents.tool_recommender import recommend_tools

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(scenario_path: Path, output_path: Path, json_output_path: Path | None = None, limit: int = 12) -> Dict[str, Any]:
    scenario = Scenario.from_dict(load_json(scenario_path))
    tools = load_json(ROOT / "data" / "tools.json")
    evidence = load_json(ROOT / "data" / "evidence.json")
    benchmark = load_json(ROOT / "benchmarks" / "mcp_security_benchmark_v01.json")

    risks, lifecycle = map_scenario_to_risks(scenario)
    risk_codes = [r.asi for r in risks]
    recommendations = recommend_tools(
        tools,
        risk_codes,
        lifecycle,
        scenario.frameworks,
        scenario.constraints,
        limit=limit,
    )
    tools_by_id = {t["id"]: t for t in tools.get("tools", [])}
    selected_cases = select_benchmark_cases(benchmark, risk_codes, scenario.architecture, max_cases=8)
    validation_plan = {
        "benchmark_cases": selected_cases,
        "runtime_checks": runtime_checks_for_risks(risk_codes),
        "evidence_checks": build_evidence_checks(recommendations, tools_by_id, evidence),
        "score_update_suggestions": score_update_suggestions(recommendations, selected_cases),
    }
    report = render_report(scenario, risks, lifecycle, recommendations, validation_plan)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    payload = {
        "scenario": scenario.__dict__,
        "risks": [r.__dict__ for r in risks],
        "lifecycle": lifecycle,
        "recommendations": [r.__dict__ for r in recommendations],
        "validation_plan": validation_plan,
        "report_path": str(output_path),
    }
    if json_output_path:
        json_output_path.parent.mkdir(parents=True, exist_ok=True)
        json_output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Rule-based Agentic AI Security Solution & Tool Validation Agent")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON")
    parser.add_argument("--output", default="outputs/solution_report.md", help="Markdown report output path")
    parser.add_argument("--json-output", default="outputs/solution_report.json", help="Structured JSON output path")
    parser.add_argument("--limit", type=int, default=12, help="Maximum number of recommended tools")
    args = parser.parse_args()

    result = run(Path(args.scenario), Path(args.output), Path(args.json_output) if args.json_output else None, limit=args.limit)
    print(f"Report written to: {result['report_path']}")
    print(f"Mapped risks: {', '.join(r['asi'] for r in result['risks'])}")
    print(f"Recommended tools: {', '.join(r['name'] for r in result['recommendations'][:5])}")


if __name__ == "__main__":
    main()
