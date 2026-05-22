from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple


def _parse_loose_config(text: str) -> Dict[str, Any]:
    s = (text or "").strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        pass
    out: Dict[str, Any] = {}
    patterns = {
        "server_url": r"server_url\s*[:=]\s*[\"']([^\"']+)[\"']",
        "connector_id": r"connector_id\s*[:=]\s*[\"']([^\"']+)[\"']",
        "require_approval": r"require_approval\s*[:=]\s*[\"']?([A-Za-z0-9_\-]+)[\"']?",
        "approval_policy": r"approval_policy\s*[:=]\s*[\"']?([A-Za-z0-9_\-]+)[\"']?",
        "authorization": r"authorization\s*[:=]\s*[\"']([^\"']+)[\"']",
    }
    for key, pat in patterns.items():
        m = re.search(pat, s)
        if m:
            out[key] = m.group(1)
    return out


def review_openai_connector_config(config_text_or_dict: Any, *, data_sensitivity: str = "medium") -> Dict[str, Any]:
    if isinstance(config_text_or_dict, dict):
        cfg = config_text_or_dict
    else:
        cfg = _parse_loose_config(str(config_text_or_dict or ""))

    findings: List[Dict[str, Any]] = []
    mapped_asi = set()
    required_controls = set()

    server_url = cfg.get("server_url") or cfg.get("serverUrl")
    connector_id = cfg.get("connector_id") or cfg.get("connectorId")
    require_approval = str(cfg.get("require_approval") or cfg.get("approval_policy") or cfg.get("approvalPolicy") or "unspecified").lower()
    authorization = cfg.get("authorization") or cfg.get("auth") or cfg.get("headers")
    allowed_tools = cfg.get("allowed_tools") or cfg.get("allowedTools")

    if server_url:
        mapped_asi.update(["ASI04", "ASI07"])
        required_controls.update(["remote server provenance review", "transport security", "context minimization"])
        if not str(server_url).startswith("https://"):
            findings.append({
                "id": "OPENAI-MCP-CONFIG-001",
                "title": "Remote MCP server is not HTTPS",
                "severity": "high",
                "mapped_asi": ["ASI04", "ASI07"],
                "evidence": str(server_url),
                "recommendation": "Use HTTPS remote MCP servers and verify server provenance before sharing model context.",
            })
        else:
            findings.append({
                "id": "OPENAI-MCP-CONFIG-001",
                "title": "Remote MCP server trust boundary requires review",
                "severity": "medium",
                "mapped_asi": ["ASI04", "ASI07"],
                "evidence": str(server_url),
                "recommendation": "Treat remote MCP servers as third-party execution/data-sharing boundaries; restrict context and verify provenance.",
            })

    if connector_id:
        mapped_asi.update(["ASI03", "ASI09"])
        required_controls.update(["OAuth scope review", "approval policy", "user consent UX"])
        findings.append({
            "id": "OPENAI-MCP-CONFIG-002",
            "title": "Connector uses delegated service access",
            "severity": "medium",
            "mapped_asi": ["ASI03", "ASI09"],
            "evidence": str(connector_id),
            "recommendation": "Review OAuth scopes, user consent, connector data-sharing, and approval policy for high-impact actions.",
        })

    if require_approval in ("never", "false", "none", "auto"):
        mapped_asi.update(["ASI02", "ASI09"])
        required_controls.update(["human approval for high-impact tools", "tool allowlist"])
        findings.append({
            "id": "OPENAI-MCP-CONFIG-003",
            "title": "Approval policy may allow automatic tool execution",
            "severity": "high" if data_sensitivity in ("high", "regulated") else "medium",
            "mapped_asi": ["ASI02", "ASI09"],
            "evidence": f"require_approval={require_approval}",
            "recommendation": "Require approval for write, send, delete, financial, identity, or external-sharing actions.",
        })
    elif require_approval in ("always", "true", "required"):
        required_controls.add("approval gate")
    else:
        findings.append({
            "id": "OPENAI-MCP-CONFIG-004",
            "title": "Approval policy is unspecified or ambiguous",
            "severity": "medium",
            "mapped_asi": ["ASI02", "ASI09"],
            "evidence": f"require_approval={require_approval}",
            "recommendation": "Declare explicit approval policy and fail closed for high-impact tools.",
        })
        mapped_asi.update(["ASI02", "ASI09"])

    if authorization:
        mapped_asi.update(["ASI03", "ASI07"])
        required_controls.update(["short-lived scoped credentials", "secret handling", "per-action authorization"])
        findings.append({
            "id": "OPENAI-MCP-CONFIG-005",
            "title": "Authorization material or headers present in connector config",
            "severity": "medium",
            "mapped_asi": ["ASI03", "ASI07"],
            "evidence": "authorization/header-like field present",
            "recommendation": "Do not hardcode long-lived credentials. Use scoped, short-lived tokens and avoid sending unnecessary secrets to remote MCP servers.",
        })

    if not allowed_tools:
        mapped_asi.add("ASI02")
        required_controls.add("allowed tool list")
        findings.append({
            "id": "OPENAI-MCP-CONFIG-006",
            "title": "Allowed tools are not explicitly constrained",
            "severity": "medium",
            "mapped_asi": ["ASI02"],
            "evidence": "allowed_tools missing or empty",
            "recommendation": "Use explicit tool allowlists and disable tools not required for the business workflow.",
        })

    risk_score = min(1.0, 0.15 * len(findings) + (0.15 if data_sensitivity in ("high", "regulated") else 0.0))
    if risk_score >= 0.75:
        risk_level = "high"
    elif risk_score >= 0.45:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "assessment_type": "openai_mcp_connector_config_review",
        "config_detected": cfg,
        "data_sensitivity": data_sensitivity,
        "risk_score": round(risk_score, 3),
        "risk_level": risk_level,
        "mapped_asi": sorted(mapped_asi),
        "required_controls": sorted(required_controls),
        "findings": findings,
        "recommended_benchmarks": sorted(set([
            "MCP-ASI02-004" if "ASI02" in mapped_asi else "",
            "MCP-ASI07-003" if "ASI03" in mapped_asi or "ASI07" in mapped_asi else "",
            "HITL-ASI09-010" if "ASI09" in mapped_asi else "",
            "MCP-ASI04-001" if "ASI04" in mapped_asi else "",
        ]) - {""}),
    }


def review_openai_docs_reference(url: str) -> Dict[str, Any]:
    return review_openai_connector_config({
        "server_url": "https://example.com/mcp",
        "connector_id": "connector_example",
        "require_approval": "unspecified",
    }) | {
        "assessment_type": "openai_mcp_docs_reference_review",
        "documentation_url": url,
        "note": "Documentation/reference URL reviewed as an integration pattern; live server schema discovery was not attempted against the docs URL.",
    }
