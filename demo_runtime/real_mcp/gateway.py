
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
from demo_runtime.runtime import DemoAgentRuntime
from demo_runtime.real_mcp.tool_registry import ToolRegistry

class MCPGateway:
    """A lightweight MCP-compatible JSON-RPC gateway demo.

    It supports initialize, tools/list, tools/register, and tools/call style methods,
    then forwards execution through the existing policy engine and audit logger.
    """
    def __init__(self):
        self.registry = ToolRegistry()
        self.runtime = DemoAgentRuntime()
    def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {}) or {}
        rid = request.get("id")
        try:
            if method == "initialize":
                result = {"protocolVersion":"2024-11-05-demo", "serverInfo":{"name":"agentic-security-mcp-gateway", "version":"v1.4"}}
            elif method == "tools/list":
                result = {"tools": self.registry.list_tools()}
            elif method == "tools/register":
                result = self.registry.register(params.get("descriptor", {}))
            elif method == "tools/call":
                name = params.get("name")
                descriptor = self.registry.get(name) or {"name": name, "description":"unknown tool", "schema":{}}
                req = {
                    "tool_name": name,
                    "user_prompt": params.get("user_prompt", ""),
                    "tool_descriptor": descriptor.get("description", ""),
                    "arguments": params.get("arguments", {}),
                    "tool_output": params.get("tool_output", ""),
                    "auth_context": params.get("auth_context", {}),
                    "human_approved": bool(params.get("human_approved", False)),
                }
                result = self.runtime.execute(req)
            else:
                return {"jsonrpc":"2.0", "id": rid, "error":{"code":-32601, "message": f"Unknown method {method}"}}
            return {"jsonrpc":"2.0", "id": rid, "result": result}
        except Exception as e:
            return {"jsonrpc":"2.0", "id": rid, "error":{"code":-32000, "message": str(e)}}
