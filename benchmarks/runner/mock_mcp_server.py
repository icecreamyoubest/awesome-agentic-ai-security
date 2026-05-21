from __future__ import annotations
from typing import Any, Dict

DANGEROUS_HINTS = [
    "rm -rf", "reverse shell", "bcc", "exfiltrate", "oauth", "descriptor", "agent card",
    "workspace", "unbounded", "cross-tenant", "delete", "secret", "token"
]


def mock_target(case: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(str(v) for v in case.values()).lower()
    if any(h in text for h in DANGEROUS_HINTS):
        return {"decision": "quarantined", "reason": "mock policy matched dangerous MCP/agentic pattern"}
    return {"decision": "requires_approval", "reason": "mock default review for agentic benchmark case"}
