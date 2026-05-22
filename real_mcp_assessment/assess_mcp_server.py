from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .connector import MCPConnector
from .risk_classifier import classify_scan, summarize_server
from .tool_schema_scanner import DEFAULT_RULES, scan_tool_schema
from .report_writer import write_json_report, write_markdown_report


def load_rules(path: str | None) -> Dict[str, Any]:
    if not path:
        return DEFAULT_RULES
    p = Path(path)
    if not p.exists():
        return DEFAULT_RULES
    data = json.loads(p.read_text(encoding="utf-8"))
    merged = dict(DEFAULT_RULES)
    merged.update(data)
    return merged


def assess_mcp_server(server_url: str, token: str = "", mode: str = "auto", profile: str = "schema_only", output_dir: str = "outputs/mcp_assessments", rules_path: str = "data/mcp_risk_rules.json") -> Dict[str, Any]:
    rules = load_rules(rules_path)
    connector = MCPConnector(server_url=server_url, token=token)
    discovery = connector.discover(mode=mode)
    scans = [scan_tool_schema(t, rules) for t in discovery.tools]
    classified = [classify_scan(s) for s in scans]
    summary = summarize_server(classified, discovery_status=discovery.status, errors=discovery.errors)
    safe_name = (server_url or "demo").replace("https://", "").replace("http://", "").replace("/", "_").replace(":", "_")[:80]
    out_dir = Path(output_dir)
    next_steps = []
    if not classified:
        next_steps = [
            "Verify that the URL is a live MCP endpoint rather than a documentation page.",
            "For Hugging Face Gradio MCP Spaces, try the /gradio_api/mcp/ URL with trailing slash.",
            "For Gradio apps, retry app-root /config and /gradio_api/info discovery.",
            "For OpenAI Responses API MCP references, assess the actual server_url or connector_id used in your application.",
            "Do not enable controlled execution unless the server is owned by you or explicitly authorized.",
        ]
    else:
        next_steps = [
            "Review high-risk tools and mapped ASI risks.",
            "Run recommended MCP benchmark cases before trusting runtime claims.",
            "Require approval for high-impact tool calls and log data shared with remote MCP servers.",
        ]

    report = {
        "server_url": server_url,
        "resolved_url": discovery.server_url,
        "mode": discovery.mode,
        "assessment_profile": profile,
        "assessment_status": summary.get("assessment_status", discovery.status),
        "assessment_confidence": summary.get("assessment_confidence", "medium" if classified else "low"),
        "discovery_method": discovery.discovery_method,
        "endpoint_candidates": discovery.endpoint_candidates,
        "summary": summary,
        "tools": classified,
        "raw_tool_count": len(discovery.tools),
        "errors": discovery.errors,
        "raw_discovery": discovery.raw,
        "risk_interpretation": {
            "can_conclude_low_risk": bool(classified) and summary.get("risk_level") == "low",
            "reason": "Tool schemas were discovered and classified." if classified else "No tool schemas were discovered; risk cannot be scored.",
            "next_required_step": "Review tool findings and run recommended benchmarks." if classified else "Fix endpoint discovery or provide a valid Streamable HTTP/SSE MCP endpoint, then rerun schema discovery."
        },
        "recommended_next_steps": next_steps,
        "safety_boundary": "schema-only unless explicitly configured for authorized controlled execution",
    }
    json_path = out_dir / f"{safe_name or 'demo'}_assessment.json"
    md_path = out_dir / f"{safe_name or 'demo'}_assessment.md"
    report["json_report"] = write_json_report(report, json_path)
    report["markdown_report"] = write_markdown_report(report, md_path)
    # rewrite with paths included
    write_json_report(report, json_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Schema-only risk assessment for real MCP-compatible servers or Hugging Face Spaces.")
    parser.add_argument("--server-url", default="demo://local", help="MCP server URL, HF Space URL, or demo://local")
    parser.add_argument("--token", default="", help="Optional bearer token. Do not commit tokens to source control.")
    parser.add_argument("--mode", choices=["auto", "jsonrpc", "gradio_config"], default="auto")
    parser.add_argument("--profile", default="schema_only")
    parser.add_argument("--output-dir", default="outputs/mcp_assessments")
    args = parser.parse_args()
    report = assess_mcp_server(args.server_url, token=args.token, mode=args.mode, profile=args.profile, output_dir=args.output_dir)
    print(json.dumps({"summary": report["summary"], "json_report": report["json_report"], "markdown_report": report["markdown_report"]}, indent=2))


if __name__ == "__main__":
    main()
