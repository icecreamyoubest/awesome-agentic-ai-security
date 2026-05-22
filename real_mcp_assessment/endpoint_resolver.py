from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class EndpointCandidate:
    mode: str
    url: str
    purpose: str


@dataclass
class EndpointResolution:
    input: str
    endpoint_type: str
    app_root: Optional[str]
    normalized_url: str
    candidate_endpoints: List[EndpointCandidate]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "endpoint_type": self.endpoint_type,
            "app_root": self.app_root,
            "normalized_url": self.normalized_url,
            "candidate_endpoints": [asdict(x) for x in self.candidate_endpoints],
            "notes": self.notes,
        }


def _dedupe(candidates: List[EndpointCandidate]) -> List[EndpointCandidate]:
    seen = set()
    out: List[EndpointCandidate] = []
    for c in candidates:
        key = (c.mode, c.url)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def hf_space_to_runtime_url(url: str) -> str:
    m = re.match(r"https?://huggingface\.co/spaces/([^/]+)/([^/?#]+)", url.strip())
    if not m:
        return url.strip()
    owner, space = m.group(1), m.group(2)
    safe_owner = owner.replace("_", "-").lower()
    safe_space = space.replace("_", "-").lower()
    return f"https://{safe_owner}-{safe_space}.hf.space"


def infer_app_root(url: str) -> str:
    u = hf_space_to_runtime_url(url).strip()
    for marker in ("/gradio_api/mcp", "/api/mcp", "/mcp", "/sse"):
        if marker in u:
            return u.split(marker, 1)[0].rstrip("/")
    parsed = urlparse(u)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return u.rstrip("/")


def looks_like_json_config(value: str) -> bool:
    s = (value or "").strip()
    if not s:
        return False
    if s.startswith("{") and s.endswith("}"):
        try:
            json.loads(s)
            return True
        except Exception:
            return False
    return any(k in s for k in ('"server_url"', '"connector_id"', "server_url:", "connector_id:"))


def resolve_endpoint(input_value: str) -> EndpointResolution:
    original = (input_value or "demo://local").strip() or "demo://local"
    notes: List[str] = []

    if original.startswith("demo://"):
        return EndpointResolution(original, "demo", None, original, [], ["Local demo endpoint; no network discovery required."])

    if looks_like_json_config(original):
        return EndpointResolution(original, "openai_connector_config", None, "inline_config", [], ["Input looks like OpenAI MCP connector configuration."])

    if "developers.openai.com" in original and "tools-connectors-mcp" in original:
        return EndpointResolution(original, "openai_mcp_docs_reference", None, original, [], ["Documentation URL; perform integration-pattern review, not live MCP discovery."])

    runtime = hf_space_to_runtime_url(original).strip().rstrip("/")
    app_root = infer_app_root(runtime)
    candidates: List[EndpointCandidate] = []

    def add(mode: str, url: str, purpose: str) -> None:
        if url:
            candidates.append(EndpointCandidate(mode=mode, url=url, purpose=purpose))

    endpoint_type = "generic_remote_mcp"
    if "huggingface.co/spaces/" in original or ".hf.space" in runtime or "/gradio_api/mcp" in runtime:
        endpoint_type = "huggingface_gradio_mcp"
        # Preserve slash-first order for Gradio MCP.
        add("jsonrpc_streamable_http", app_root + "/gradio_api/mcp/", "Gradio MCP Streamable HTTP endpoint with trailing slash")
        add("jsonrpc_streamable_http", app_root + "/gradio_api/mcp", "Gradio MCP endpoint without trailing slash")
        add("sse", app_root + "/gradio_api/mcp/sse", "Potential Gradio MCP SSE endpoint")
        add("gradio_config", app_root + "/config", "Gradio app config fallback")
        add("gradio_info", app_root + "/gradio_api/info", "Gradio API info fallback")
    else:
        # Respect user-provided URL first.
        base = runtime
        add("jsonrpc_streamable_http", base, "User-provided endpoint")
        add("jsonrpc_streamable_http", base + "/", "User-provided endpoint with slash")
        add("jsonrpc_streamable_http", app_root + "/mcp", "Common /mcp endpoint")
        add("jsonrpc_streamable_http", app_root + "/mcp/", "Common /mcp/ endpoint")
        add("jsonrpc_streamable_http", app_root + "/api/mcp", "Common /api/mcp endpoint")
        add("jsonrpc_streamable_http", app_root + "/api/mcp/", "Common /api/mcp/ endpoint")
        add("sse", app_root + "/sse", "Common SSE MCP endpoint")
        add("sse", app_root + "/mcp/sse", "Common MCP SSE endpoint")

    candidates = _dedupe(candidates)
    if endpoint_type == "huggingface_gradio_mcp":
        notes.append("Hugging Face / Gradio MCP endpoints may cold start, redirect, or use streamable HTTP/SSE responses.")
    return EndpointResolution(original, endpoint_type, app_root, runtime, candidates, notes)
