from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .discovery_engine import DiscoveryEngine
from .endpoint_resolver import looks_like_json_config
from .openai_connector_reviewer import review_openai_connector_config
from .tool_risk_model import assess_tool, summarize_tools
from .runtime_probe import run_runtime_probe
from .full_report_writer import write_full_json_report, write_full_markdown_report


def _safe_name(value: str) -> str:
    return (value or "demo").replace("https://", "").replace("http://", "").replace("/", "_").replace(":", "_").replace("{", "config_").replace("}", "")[:100]


def load_connector_config(path_or_text: str) -> Any:
    if not path_or_text:
        return None
    p = Path(path_or_text)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return path_or_text


def assess_mcp_server(
    server_url: str = "demo://local",
    token: str = "",
    mode: str = "auto",
    profile: str = "schema_only",
    output_dir: str = "outputs/mcp_assessments",
    rules_path: str = "data/mcp_risk_rules.json",
    timeout: float = 45.0,
    connector_config: Any = None,
    data_sensitivity: str = "medium",
    authorized: bool = False,
    allow_high_risk: bool = False,
) -> Dict[str, Any]:
    target = connector_config if connector_config is not None else server_url
    engine = DiscoveryEngine(server_url=str(target or server_url), token=token, timeout=timeout)
    discovery = engine.discover(mode=mode, connector_config=connector_config, data_sensitivity=data_sensitivity)

    tools = [assess_tool(t) for t in discovery.tools]
    summary = summarize_tools(tools, discovery_status=discovery.status, errors=discovery.errors)

    connector_review = discovery.connector_review
    if connector_config and not connector_review:
        connector_review = review_openai_connector_config(connector_config, data_sensitivity=data_sensitivity)

    if connector_review and not tools:
        summary = {
            "risk_level": connector_review.get("risk_level", "medium"),
            "risk_score": connector_review.get("risk_score"),
            "assessment_status": "config_review_only",
            "assessment_confidence": "medium",
            "tools_discovered": 0,
            "high_risk_tools": None,
            "mapped_asi": connector_review.get("mapped_asi", []),
        }

    runtime_probe = run_runtime_probe(
        server_url=discovery.endpoint_resolution.get("normalized_url") or server_url,
        tools=discovery.tools,
        token=token,
        profile=profile,
        authorized=authorized,
        allow_high_risk=allow_high_risk,
        timeout=timeout,
    )

    next_steps: List[str] = []
    if discovery.status in ("discovery_failed", "discovery_timeout"):
        next_steps.extend([
            "Retry after the target service is warm, especially for Hugging Face Spaces that may cold start.",
            "Increase timeout and preserve trailing slash for Gradio MCP endpoints.",
            "Try Streamable HTTP, SSE, /config, and /gradio_api/info fallback discovery.",
            "Do not treat this result as low risk; no tool schema was retrieved.",
        ])
    if connector_review:
        next_steps.extend([
            "Review server_url / connector_id provenance and OAuth scopes.",
            "Set explicit approval policy for write, identity, financial, and external-sharing tools.",
            "Use tool allowlists and minimize context sent to remote MCP servers.",
        ])
    if tools:
        next_steps.extend([
            "Review high-risk tools and mapped OWASP ASI risks.",
            "Run recommended benchmark cases before accepting tool or vendor security claims.",
            "Enable runtime probing only in owned or explicitly authorized environments.",
        ])
    if runtime_probe.get("probe_status") in ("blocked", "not_run"):
        next_steps.append("For real execution measurement, rerun with profile=safe_probe or authorized_runtime_validation and explicit authorization acknowledgement.")

    report: Dict[str, Any] = {
        "assessment_type": "universal_mcp_risk_assessment",
        "server_url": server_url,
        "mode": mode,
        "assessment_profile": profile,
        "assessment_status": summary.get("assessment_status", discovery.status),
        "assessment_confidence": summary.get("assessment_confidence", "medium"),
        "endpoint_resolution": discovery.endpoint_resolution,
        "discovery_method": discovery.discovery_method,
        "discovery_attempts": discovery.discovery_attempts,
        "summary": summary,
        "tools": tools,
        "raw_tool_count": len(discovery.tools),
        "errors": discovery.errors,
        "connector_review": connector_review,
        "runtime_probe": runtime_probe,
        "raw_discovery": discovery.raw,
        "risk_interpretation": {
            "can_conclude_low_risk": bool(tools) and summary.get("risk_level") == "low",
            "reason": "Tool schemas were discovered and classified." if tools else ("Connector configuration was reviewed." if connector_review else "No tool schemas were discovered; live server risk cannot be scored."),
            "next_required_step": "Run recommended benchmarks and runtime probes in an authorized environment." if tools else "Fix discovery or provide a valid MCP endpoint/config, then rerun assessment.",
        },
        "recommended_next_steps": next_steps,
        "safety_boundary": "schema/config review by default; runtime probing requires explicit authorization and is restricted to safe/read-only calls unless allow_high_risk is enabled.",
    }

    out_dir = Path(output_dir)
    safe = _safe_name(server_url if server_url else "connector_config")
    json_path = out_dir / f"{safe}_assessment.json"
    md_path = out_dir / f"{safe}_assessment.md"
    report["json_report"] = write_full_json_report(report, json_path)
    report["markdown_report"] = write_full_markdown_report(report, md_path)
    write_full_json_report(report, json_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal MCP risk assessment with schema/config review and optional authorized runtime probing.")
    parser.add_argument("--server-url", default="demo://local", help="MCP server URL, HF Space URL, OpenAI docs URL, or demo://local")
    parser.add_argument("--connector-config", default="", help="OpenAI-style MCP connector config JSON string or file path")
    parser.add_argument("--token", default="", help="Optional bearer token. Do not commit tokens.")
    parser.add_argument("--mode", choices=["auto", "jsonrpc_streamable_http", "sse", "gradio_config", "gradio_info"], default="auto")
    parser.add_argument("--profile", choices=["schema_only", "connector_config_review", "safe_probe", "authorized_runtime_validation", "offline_docs_review"], default="schema_only")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--data-sensitivity", choices=["low", "medium", "high", "regulated"], default="medium")
    parser.add_argument("--authorized", action="store_true", help="I confirm I own or am authorized to test this MCP server.")
    parser.add_argument("--allow-high-risk", action="store_true", help="Allow high-risk tool calls during authorized runtime validation. Do not use on third-party servers.")
    parser.add_argument("--output-dir", default="outputs/mcp_assessments")
    args = parser.parse_args()

    connector_config = load_connector_config(args.connector_config) if args.connector_config else None
    server_url = args.server_url
    if connector_config and (not server_url or server_url == "demo://local"):
        server_url = connector_config if looks_like_json_config(str(connector_config)) else "inline_connector_config"

    report = assess_mcp_server(
        server_url=server_url,
        token=args.token,
        mode=args.mode,
        profile=args.profile,
        output_dir=args.output_dir,
        timeout=args.timeout,
        connector_config=connector_config,
        data_sensitivity=args.data_sensitivity,
        authorized=args.authorized,
        allow_high_risk=args.allow_high_risk,
    )
    print(json.dumps({
        "summary": report.get("summary"),
        "assessment_status": report.get("assessment_status"),
        "runtime_probe": report.get("runtime_probe", {}).get("probe_status"),
        "json_report": report.get("json_report"),
        "markdown_report": report.get("markdown_report"),
    }, indent=2))


if __name__ == "__main__":
    main()
