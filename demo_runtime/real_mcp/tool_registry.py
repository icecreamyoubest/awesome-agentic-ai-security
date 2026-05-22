
from __future__ import annotations
from typing import Dict, Any, List
from demo_runtime.real_mcp.descriptor_validator import validate_descriptor

DEFAULT_TOOLS = [
    {"name":"crm.lookup", "description":"Read-only customer order lookup", "schema":{"type":"object", "properties":{"order_id":{"type":"string"}}, "required":["order_id"]}, "scopes":["crm:read"]},
    {"name":"email.draft", "description":"Create an email draft without sending", "schema":{"type":"object", "properties":{"to":{"type":"string"}, "body":{"type":"string"}}, "required":["to","body"]}, "scopes":["email:draft"]},
    {"name":"ticket.create", "description":"Create support ticket", "schema":{"type":"object", "properties":{"title":{"type":"string"}}, "required":["title"]}, "scopes":["ticket:write"]},
]

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        for t in DEFAULT_TOOLS:
            self.register(t)
    def register(self, descriptor: Dict[str, Any]) -> Dict[str, Any]:
        verdict = validate_descriptor(descriptor)
        if verdict["decision"] == "allow":
            self.tools[descriptor["name"]] = descriptor
        return verdict
    def list_tools(self) -> List[Dict[str, Any]]:
        return list(self.tools.values())
    def get(self, name: str) -> Dict[str, Any] | None:
        return self.tools.get(name)
