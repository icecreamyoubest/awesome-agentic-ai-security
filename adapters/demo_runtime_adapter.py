from __future__ import annotations
from typing import Any, Dict
from .base_adapter import SecurityToolAdapter
from demo_runtime.runtime import DemoAgentRuntime, request_from_benchmark_case

class DemoRuntimeAdapter(SecurityToolAdapter):
    name = "demo_mcp_runtime"

    def __init__(self) -> None:
        self.runtime = DemoAgentRuntime()

    def scan_input(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = {"tool_name": "crm.lookup", "user_prompt": payload.get("text", ""), "arguments": {"order_id": "ORD-1001"}}
        return self.runtime.execute(request)

    def scan_output(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = {"tool_name": "crm.lookup", "tool_output": payload.get("text", ""), "arguments": {"order_id": "ORD-1001"}}
        return self.runtime.execute(request)

    def validate_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        return self.runtime.execute(tool_call)

    def run_benchmark_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        return self.runtime.execute(request_from_benchmark_case(case))
