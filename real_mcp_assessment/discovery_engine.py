from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None

from .endpoint_resolver import EndpointResolution, resolve_endpoint
from .connector import DEMO_TOOLS, normalize_jsonrpc_tools, normalize_gradio_config_tools, normalize_gradio_info_tools
from .openai_connector_reviewer import review_openai_docs_reference, review_openai_connector_config


@dataclass
class DiscoveryAttempt:
    mode: str
    url: str
    status: str
    purpose: str = ""
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    http_status: Optional[int] = None
    response_hint: Optional[str] = None


@dataclass
class DiscoveryEngineResult:
    server_url: str
    mode: str
    endpoint_resolution: Dict[str, Any]
    tools: List[Dict[str, Any]]
    discovery_attempts: List[Dict[str, Any]]
    errors: List[str]
    raw: Dict[str, Any] = field(default_factory=dict)
    status: str = "schema_discovered"
    discovery_method: str = "unknown"
    connector_review: Optional[Dict[str, Any]] = None


def _jsonrpc_payload(method: str, request_id: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        payload["params"] = params
    return payload


def _parse_sse_json(text: str) -> List[Dict[str, Any]]:
    objects: List[Dict[str, Any]] = []
    current: List[str] = []
    for line in (text or "").splitlines():
        if line.startswith("data:"):
            current.append(line[5:].strip())
        elif not line.strip() and current:
            payload = "\n".join(current).strip()
            current = []
            if payload and payload != "[DONE]":
                try:
                    parsed = json.loads(payload)
                    if isinstance(parsed, dict):
                        objects.append(parsed)
                except Exception:
                    pass
    if current:
        payload = "\n".join(current).strip()
        if payload and payload != "[DONE]":
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    objects.append(parsed)
            except Exception:
                pass
    return objects


def _extract_tools_from_text(text: str) -> List[Dict[str, Any]]:
    stripped = (text or "").strip()
    if not stripped:
        return []
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            return normalize_jsonrpc_tools(data)
    except Exception:
        pass
    tools: List[Dict[str, Any]] = []
    for obj in _parse_sse_json(stripped):
        tools.extend(normalize_jsonrpc_tools(obj))
    return tools


class DiscoveryEngine:
    def __init__(self, server_url: str, token: str = "", timeout: float = 30.0):
        self.server_url = server_url or "demo://local"
        self.token = token or ""
        self.timeout = timeout
        self.resolution: EndpointResolution = resolve_endpoint(self.server_url)
        self.attempts: List[DiscoveryAttempt] = []
        self.errors: List[str] = []

    def _headers(self) -> Dict[str, str]:
        h = {
            "Accept": "application/json, text/event-stream, */*",
            "Content-Type": "application/json",
            "User-Agent": "awesome-agentic-ai-security-universal-mcp-assessor/1.7",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _record(self, attempt: DiscoveryAttempt) -> None:
        self.attempts.append(attempt)
        if attempt.status in ("error", "timeout", "http_error"):
            self.errors.append(f"{attempt.mode} {attempt.url}: {attempt.error or attempt.status}")

    def _client(self):
        if httpx is None:
            raise RuntimeError("httpx is required for Universal MCP discovery. Add httpx to requirements.txt.")
        return httpx.Client(follow_redirects=True, timeout=self.timeout)

    def _warmup(self) -> None:
        root = self.resolution.app_root
        if not root or httpx is None:
            return
        if ".hf.space" not in root:
            return
        start = time.time()
        try:
            with httpx.Client(follow_redirects=True, timeout=min(20.0, max(5.0, self.timeout))) as client:
                r = client.get(root, headers={"User-Agent": "awesome-agentic-ai-security-warmup/1.7"})
                self._record(DiscoveryAttempt("warmup", root, "success" if r.status_code < 400 else "http_error", "Warm up HF Space root", duration_ms=int((time.time()-start)*1000), http_status=r.status_code, response_hint=r.text[:120]))
        except Exception as e:
            self._record(DiscoveryAttempt("warmup", root, "error", "Warm up HF Space root", error=str(e), duration_ms=int((time.time()-start)*1000)))

    def try_jsonrpc(self, url: str, purpose: str) -> List[Dict[str, Any]]:
        start = time.time()
        try:
            with self._client() as client:
                init = _jsonrpc_payload("initialize", 1, {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "agentic-security-assessor", "version": "1.7"},
                })
                try:
                    init_resp = client.post(url, json=init, headers=self._headers())
                    init_hint = init_resp.text[:120]
                except Exception:
                    init_hint = "initialize failed or unsupported; continuing to tools/list"

                list_payload = _jsonrpc_payload("tools/list", 2, {})
                resp = client.post(url, json=list_payload, headers=self._headers())
                text = resp.text or ""
                duration_ms = int((time.time() - start) * 1000)
                if resp.status_code >= 400:
                    self._record(DiscoveryAttempt("jsonrpc_streamable_http", url, "http_error", purpose, error=f"HTTP {resp.status_code}: {text[:200]}", duration_ms=duration_ms, http_status=resp.status_code))
                    return []
                tools = _extract_tools_from_text(text)
                self._record(DiscoveryAttempt("jsonrpc_streamable_http", url, "success" if tools else "no_tools", purpose, duration_ms=duration_ms, http_status=resp.status_code, response_hint=(text[:160] or init_hint)))
                return tools
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            status = "timeout" if "timed out" in str(e).lower() or "timeout" in str(e).lower() else "error"
            self._record(DiscoveryAttempt("jsonrpc_streamable_http", url, status, purpose, error=str(e), duration_ms=duration_ms))
            return []

    def try_get_json_tools(self, url: str, mode: str, purpose: str) -> List[Dict[str, Any]]:
        start = time.time()
        try:
            with self._client() as client:
                headers = self._headers()
                headers.pop("Content-Type", None)
                resp = client.get(url, headers=headers)
                text = resp.text or ""
                duration_ms = int((time.time() - start) * 1000)
                if resp.status_code >= 400:
                    self._record(DiscoveryAttempt(mode, url, "http_error", purpose, error=f"HTTP {resp.status_code}: {text[:200]}", duration_ms=duration_ms, http_status=resp.status_code))
                    return []
                data = json.loads(text)
                if mode == "gradio_config":
                    tools = normalize_gradio_config_tools(data)
                elif mode == "gradio_info":
                    tools = normalize_gradio_info_tools(data)
                else:
                    tools = _extract_tools_from_text(text)
                self._record(DiscoveryAttempt(mode, url, "success" if tools else "no_tools", purpose, duration_ms=duration_ms, http_status=resp.status_code, response_hint=text[:160]))
                return tools
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            status = "timeout" if "timed out" in str(e).lower() or "timeout" in str(e).lower() else "error"
            self._record(DiscoveryAttempt(mode, url, status, purpose, error=str(e), duration_ms=duration_ms))
            return []

    def discover(self, mode: str = "auto", connector_config: Any = None, data_sensitivity: str = "medium") -> DiscoveryEngineResult:
        endpoint_type = self.resolution.endpoint_type
        if endpoint_type == "demo":
            return DiscoveryEngineResult(self.server_url, mode, self.resolution.to_dict(), DEMO_TOOLS, [], [], {"demo": True}, "schema_discovered", "demo")
        if endpoint_type == "openai_connector_config":
            review = review_openai_connector_config(connector_config or self.server_url, data_sensitivity=data_sensitivity)
            return DiscoveryEngineResult(self.server_url, "connector_config_review", self.resolution.to_dict(), [], [], [], {"connector_review": review}, "config_review_only", "openai_connector_config", connector_review=review)
        if endpoint_type == "openai_mcp_docs_reference":
            review = review_openai_docs_reference(self.server_url)
            return DiscoveryEngineResult(self.server_url, "offline_docs_review", self.resolution.to_dict(), [], [], [], {"connector_review": review}, "documentation_reference", "openai_docs_reference", connector_review=review)

        self._warmup()
        tools: List[Dict[str, Any]] = []
        discovery_method = "none"
        for c in self.resolution.candidate_endpoints:
            if mode != "auto" and c.mode != mode:
                continue
            if c.mode == "jsonrpc_streamable_http":
                tools = self.try_jsonrpc(c.url, c.purpose)
            elif c.mode in ("gradio_config", "gradio_info"):
                tools = self.try_get_json_tools(c.url, c.mode, c.purpose)
            elif c.mode == "sse":
                tools = self.try_get_json_tools(c.url, "sse", c.purpose)
            if tools:
                discovery_method = c.mode
                break

        status = "schema_discovered" if tools else ("discovery_timeout" if any(a.status == "timeout" for a in self.attempts) else "discovery_failed")
        return DiscoveryEngineResult(
            self.server_url,
            mode,
            self.resolution.to_dict(),
            tools,
            [asdict(a) for a in self.attempts],
            self.errors,
            {"endpoint_resolution": self.resolution.to_dict()},
            status,
            discovery_method,
        )
