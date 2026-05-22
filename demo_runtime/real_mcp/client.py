
from __future__ import annotations
from typing import Dict, Any
from demo_runtime.real_mcp.gateway import MCPGateway

class MCPDemoClient:
    def __init__(self):
        self.gateway = MCPGateway()
        self._id = 0
    def call(self, method: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self._id += 1
        return self.gateway.handle({"jsonrpc":"2.0", "id": self._id, "method": method, "params": params or {}})
