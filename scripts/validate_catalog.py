#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data" / "tools.json"
CONTROLS = ROOT / "data" / "controls.json"
EVIDENCE = ROOT / "data" / "evidence.json"
BENCH_JSONL = ROOT / "benchmarks" / "mcp_security_benchmark_v01.jsonl"
README = ROOT / "README.md"

ALLOWED_ASI = {f"ASI{i:02d}" for i in range(1, 11)}
REQUIRED_TOOL_FIELDS = ["id", "name", "org", "vendor_type", "category", "description", "scores", "agentic_owasp", "lifecycle_stages", "agentic_scores", "mcp_scores"]
ALLOWED_COLORS = {"red", "yellow", "green", "blue", "indigo", "purple", "pink", "gray"}


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check_readme_metadata():
    txt = README.read_text(encoding="utf-8")
    if not txt.startswith("---"):
        raise SystemExit("README.md must start with Hugging Face YAML metadata")
    block = txt.split("---", 2)[1]
    meta = {}
    for line in block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    if meta.get("sdk") != "static":
        raise SystemExit("README.md metadata must contain sdk: static")
    for key in ["colorFrom", "colorTo"]:
        if meta.get(key) and meta[key] not in ALLOWED_COLORS:
            raise SystemExit(f"{key} must be one of {sorted(ALLOWED_COLORS)}")


def check_tools(catalog):
    seen = set()
    stages = set(catalog.get("meta", {}).get("lifecycle_stages", {}).keys())
    for tool in catalog["tools"]:
        for field in REQUIRED_TOOL_FIELDS:
            if field not in tool:
                raise SystemExit(f"Tool {tool.get('id')} missing required field: {field}")
        if tool["id"] in seen:
            raise SystemExit(f"Duplicate tool id: {tool['id']}")
        seen.add(tool["id"])
        for code in tool.get("agentic_owasp", []):
            if code not in ALLOWED_ASI:
                raise SystemExit(f"Tool {tool['id']} has invalid ASI code {code}")
        for code in tool.get("lifecycle_stages", []):
            if code not in stages:
                raise SystemExit(f"Tool {tool['id']} has invalid lifecycle stage {code}")
        for group in ["scores", "agentic_scores", "mcp_scores"]:
            for k, v in tool.get(group, {}).items():
                if not isinstance(v, (int, float)) or not (0 <= v <= 5):
                    raise SystemExit(f"Tool {tool['id']} has invalid {group}.{k}: {v}")


def check_controls(controls):
    for row in controls.get("control_matrix", []):
        if row.get("asi") not in ALLOWED_ASI:
            raise SystemExit(f"Invalid control matrix ASI: {row.get('asi')}")
    for row in controls.get("asi_lifecycle_matrix", []):
        if row.get("asi") not in ALLOWED_ASI:
            raise SystemExit(f"Invalid ASI lifecycle matrix ASI: {row.get('asi')}")
    for test in controls.get("mcp_benchmark", []):
        for code in test.get("asi", []):
            if code not in ALLOWED_ASI:
                raise SystemExit(f"Invalid MCP benchmark ASI: {code}")


def check_evidence(evidence, catalog):
    ids = {t["id"] for t in catalog["tools"]}
    for tool_id, records in evidence.get("tools", {}).items():
        if tool_id not in ids:
            raise SystemExit(f"Evidence references unknown tool id: {tool_id}")
        for rec in records:
            for field in ["type", "source", "claim", "last_verified", "confidence"]:
                if field not in rec:
                    raise SystemExit(f"Evidence record for {tool_id} missing {field}")


def check_benchmark_jsonl():
    if not BENCH_JSONL.exists():
        raise SystemExit("Missing benchmark JSONL file")
    ids = set()
    with BENCH_JSONL.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            for field in ["id", "risk", "attack_type", "objective", "expected_control", "pass_condition", "severity"]:
                if field not in row:
                    raise SystemExit(f"Benchmark line {line_no} missing {field}")
            if row["id"] in ids:
                raise SystemExit(f"Duplicate benchmark id: {row['id']}")
            ids.add(row["id"])
            for code in row.get("risk", []):
                if code not in ALLOWED_ASI:
                    raise SystemExit(f"Benchmark {row['id']} has invalid ASI {code}")


def main():
    catalog = load_json(TOOLS)
    controls = load_json(CONTROLS)
    evidence = load_json(EVIDENCE)
    check_readme_metadata()
    check_tools(catalog)
    check_controls(controls)
    check_evidence(evidence, catalog)
    check_benchmark_jsonl()
    print(f"validated {len(catalog['tools'])} tools, {len(controls.get('control_matrix', []))} control rows, {len(evidence.get('tools', {}))} evidence tool records")

if __name__ == "__main__":
    main()
