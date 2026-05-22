from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None

READ_ONLY_HINTS = ["get", "list", "search", "lookup", "read", "fetch", "query", "find", "info", "status"]
HIGH_RISK_HINTS = ["delete", "send", "transfer", "refund", "write", "update", "execute", "run", "shell", "install", "deploy", "admin", "create"]


def is_read_only_tool(tool: Dict[str, Any]) -> bool:
    name = str(tool.get("name") or tool.get("tool_name") or "").lower()
    text = json.dumps(tool, ensure_ascii=False).lower()
    if any(x in name or x in text for x in HIGH_RISK_HINTS):
        return False
    return any(x in name for x in READ_ONLY_HINTS) or "read-only" in text or "readonly" in text


def benign_args_from_schema(schema: Any) -> Dict[str, Any]:
    props = {}
    if isinstance(schema, dict):
        props = schema.get("properties") or {}
    args: Dict[str, Any] = {}
    if isinstance(props, dict):
        for k, spec in props.items():
            name = str(k)
            lname = name.lower()
            ptype = spec.get("type") if isinstance(spec, dict) else "string"
            if "query" in lname:
                args[name] = "test"
            elif "id" in lname:
                args[name] = "test-id"
            elif "email" in lname or "to" == lname:
                args[name] = "noreply@example.com"
            elif ptype == "integer":
                args[name] = 1
            elif ptype == "number":
                args[name] = 1.0
            elif ptype == "boolean":
                args[name] = False
            elif ptype == "array":
                args[name] = []
            elif ptype == "object":
                args[name] = {}
            else:
                args[name] = "test"
    return args


def _jsonrpc_payload(method: str, request_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        payload["params"] = params
    return payload


def run_runtime_probe(server_url: str, tools: List[Dict[str, Any]], *, token: str = "", profile: str = "schema_only", authorized: bool = False, allow_high_risk: bool = False, timeout: float = 20.0) -> Dict[str, Any]:
    if profile in ("schema_only", "connector_config_review", "offline_docs_review"):
        return {"probe_status": "not_run", "reason": f"profile={profile} does not allow tool execution", "results": []}
    if not authorized:
        return {"probe_status": "blocked", "reason": "authorized execution acknowledgement is required", "results": []}
    if not server_url.startswith("http"):
        return {"probe_status": "not_supported", "reason": "runtime probe supports live HTTP MCP endpoints only in this module", "results": []}
    if httpx is None:
        return {"probe_status": "error", "reason": "httpx is not installed", "results": []}

    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "User-Agent": "awesome-agentic-ai-security-runtime-probe/1.7"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results: List[Dict[str, Any]] = []
    call_count = 0
    max_calls = 1 if profile == "safe_probe" else 5
    for t in tools:
        name = str(t.get("name") or t.get("tool_name") or "")
        if not name:
            continue
        high = not is_read_only_tool(t)
        if high and not allow_high_risk:
            results.append({"tool_name": name, "status": "skipped_high_risk", "reason": "Tool is not classified as read-only; pass allow_high_risk only in authorized staging environments."})
            continue
        if call_count >= max_calls:
            break
        args = benign_args_from_schema(t.get("input_schema") or t.get("inputSchema") or {})
        payload = _jsonrpc_payload("tools/call", 100 + call_count, {"name": name, "arguments": args})
        start = time.time()
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout) as client:
                resp = client.post(server_url, json=payload, headers=headers)
                text = resp.text[:500]
                results.append({
                    "tool_name": name,
                    "status": "called" if resp.status_code < 400 else "http_error",
                    "http_status": resp.status_code,
                    "duration_ms": int((time.time() - start) * 1000),
                    "arguments": args,
                    "response_preview": text,
                })
        except Exception as e:
            results.append({"tool_name": name, "status": "error", "error": str(e), "duration_ms": int((time.time() - start) * 1000), "arguments": args})
        call_count += 1

    if not results:
        return {"probe_status": "no_eligible_tools", "reason": "No read-only or explicitly allowed tools were eligible for execution", "results": []}
    return {"probe_status": "completed", "profile": profile, "authorized": authorized, "allow_high_risk": allow_high_risk, "results": results}
