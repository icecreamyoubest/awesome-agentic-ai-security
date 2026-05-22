from __future__ import annotations
from typing import Any, Dict

def draft(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return {"tool": "email.draft", "draft_id": "draft_demo_001", "to": arguments.get("to"), "body": arguments.get("body", "")[:240]}

def send(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return {"tool": "email.send", "status": "simulated_send", "to": arguments.get("to")}
