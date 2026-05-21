#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "data" / "tools.json"
CONTROLS = ROOT / "data" / "controls.json"
README = ROOT / "README.md"
VALID_ASI = {f"ASI{i:02d}" for i in range(1, 10)} | {"ASI10"}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def check_score_dict(tool_id, name, values):
    if not isinstance(values, dict):
        fail(f"{tool_id}: {name} must be an object")
    for k, v in values.items():
        if not isinstance(v, (int, float)) or not (0 <= float(v) <= 5):
            fail(f"{tool_id}: {name}.{k} must be a number between 0 and 5")


def main():
    catalog = json.loads(TOOLS.read_text(encoding="utf-8"))
    controls = json.loads(CONTROLS.read_text(encoding="utf-8"))
    tools = catalog.get("tools", [])
    meta = catalog.get("meta", {})
    valid_stages = set(meta.get("lifecycle_stages", {}).keys())
    ids = set()

    if not tools:
        fail("tools list is empty")

    for t in tools:
        tid = t.get("id")
        if not tid or not re.match(r"^[a-z0-9][a-z0-9-]*$", tid):
            fail(f"invalid tool id: {tid}")
        if tid in ids:
            fail(f"duplicate tool id: {tid}")
        ids.add(tid)

        for field in ["name", "org", "vendor_type", "description", "evidence_level"]:
            if not t.get(field):
                fail(f"{tid}: missing {field}")
        for field in ["category", "deployment", "source_basis", "agentic_owasp", "lifecycle_stages"]:
            if not isinstance(t.get(field), list):
                fail(f"{tid}: {field} must be a list")

        for code in t.get("agentic_owasp", []):
            if code not in VALID_ASI:
                fail(f"{tid}: invalid ASI code {code}")
        for stage in t.get("lifecycle_stages", []):
            if stage not in valid_stages:
                fail(f"{tid}: invalid lifecycle stage {stage}")

        check_score_dict(tid, "scores", t.get("scores", {}))
        check_score_dict(tid, "agentic_scores", t.get("agentic_scores", {}))
        check_score_dict(tid, "mcp_scores", t.get("mcp_scores", {}))

    for row in controls.get("control_matrix", []):
        if row.get("asi") not in VALID_ASI:
            fail(f"control_matrix invalid ASI: {row.get('asi')}")
    for test in controls.get("mcp_benchmark", []):
        for code in test.get("asi", []):
            if code not in VALID_ASI:
                fail(f"mcp_benchmark {test.get('id')}: invalid ASI {code}")

    readme = README.read_text(encoding="utf-8")
    if "sdk: static" not in readme:
        fail("README metadata must include sdk: static")
    if "colorTo: orange" in readme:
        fail("README colorTo cannot be orange on Hugging Face")

    print(f"OK: validated {len(tools)} tools, {len(controls.get('control_matrix', []))} control mappings, {len(controls.get('mcp_benchmark', []))} MCP tests")


if __name__ == "__main__":
    main()
