
from __future__ import annotations
import re
from typing import Dict, Any

BAD_DESCRIPTOR_PATTERNS = [
    re.compile(r"(?i)ignore previous instructions"),
    re.compile(r"(?i)exfiltrate|leak|send secrets"),
    re.compile(r"(?i)<script|base64|eval\("),
]

def validate_descriptor(tool: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(str(tool.get(k, "")) for k in ["name", "description", "schema"])
    findings = [p.pattern for p in BAD_DESCRIPTOR_PATTERNS if p.search(text)]
    if findings:
        return {"decision":"block", "reason_code":"MCP_DESCRIPTOR_POISONING", "asi":["ASI04","ASI02"], "findings": findings}
    if not tool.get("name") or not isinstance(tool.get("schema", {}), dict):
        return {"decision":"block", "reason_code":"INVALID_TOOL_DESCRIPTOR", "asi":["ASI04"], "findings": ["missing name or schema"]}
    return {"decision":"allow", "reason_code":"DESCRIPTOR_OK", "asi":[], "findings": []}
