#!/usr/bin/env python3
"""Scenario-based reference architecture generator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str) -> Dict[str, Any]:
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def score_template(scenario: Dict[str, Any], template: Dict[str, Any]) -> int:
    hay = " ".join([scenario.get("description", ""), " ".join(scenario.get("frameworks", [])), " ".join(scenario.get("architecture", [])), " ".join(scenario.get("risk_focus", []))]).lower()
    score = 0
    for trig in template.get("triggers", []):
        if trig.lower() in hay:
            score += 3
    for asi in template.get("asi", []):
        if asi in scenario.get("risk_focus", []):
            score += 2
    return score


def generate_architecture(scenario_path: str) -> Dict[str, Any]:
    scenario = json.load(open(ROOT / scenario_path, encoding="utf-8")) if not str(scenario_path).startswith("/") else json.load(open(scenario_path, encoding="utf-8"))
    templates = load_json("data/architecture_templates.json").get("templates", [])
    ranked = sorted(templates, key=lambda t: score_template(scenario, t), reverse=True)
    selected = [t for t in ranked if score_template(scenario, t) > 0][:2] or ranked[:1]
    all_asi = sorted(set(sum([t.get("asi", []) for t in selected], [])) | set(scenario.get("risk_focus", [])))
    controls = list(dict.fromkeys(sum([t.get("controls", []) for t in selected], [])))
    components = list(dict.fromkeys(sum([t.get("components", []) for t in selected], [])))
    mermaid = selected[0].get("mermaid", "")
    md = [f"# Reference Architecture: {scenario.get('name', 'Scenario')}\n"]
    md.append(f"**Scenario:** {scenario.get('description', '')}\n")
    md.append("## Recommended architecture patterns")
    for t in selected:
        md.append(f"- **{t['title']}** (`{t['id']}`) — covers {', '.join(t.get('asi', []))}")
    md.append("\n## Mermaid diagram")
    md.append("```mermaid\n" + mermaid + "\n```")
    md.append("\n## Core components")
    for c in components:
        md.append(f"- {c}")
    md.append("\n## Security controls")
    for c in controls:
        md.append(f"- {c}")
    md.append("\n## ASI risk coverage")
    md.append(", ".join(all_asi))
    md.append("\n## Open validation tasks")
    md.append("- Verify each tool claim with `agents/claim_verifier.py`.")
    md.append("- Run benchmark cases selected by `agents/validation_loop.py`.")
    md.append("- Attach benchmark-backed evidence before increasing coverage depth to 3.")
    return {"scenario": scenario, "selected_templates": selected, "asi": all_asi, "components": components, "controls": controls, "mermaid": mermaid, "markdown": "\n".join(md) + "\n"}


def main() -> None:
    p = argparse.ArgumentParser(description="Generate scenario-based reference architecture")
    p.add_argument("--scenario", required=True)
    p.add_argument("--output", default="")
    p.add_argument("--json-output", default="")
    args = p.parse_args()
    result = generate_architecture(args.scenario)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(result["markdown"], encoding="utf-8")
    if args.json_output:
        clean = dict(result)
        clean["selected_templates"] = [{k:v for k,v in t.items() if k != "mermaid"} for t in result["selected_templates"]]
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result["markdown"])


if __name__ == "__main__":
    main()
