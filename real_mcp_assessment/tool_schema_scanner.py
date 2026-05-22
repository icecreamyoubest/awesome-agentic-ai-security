from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Set

DEFAULT_RULES = {
    "high_risk_verbs": ["delete", "remove", "drop", "send", "transfer", "refund", "execute", "exec", "run", "shell", "install", "write", "update", "publish", "deploy", "admin"],
    "sensitive_fields": ["token", "secret", "password", "apikey", "api_key", "credential", "oauth", "auth", "email", "amount", "path", "url", "webhook", "command", "cmd", "code", "query", "file"],
    "descriptor_injection_patterns": ["ignore previous", "system prompt", "hidden instruction", "exfiltrate", "bypass", "jailbreak", "override", "secretly", "without user", "silent"],
    "external_access_patterns": ["http://", "https://", "webhook", "callback", "download", "upload", "curl", "wget"],
}


def _flatten_schema_keys(schema: Any, prefix: str = "") -> List[str]:
    keys: List[str] = []
    if isinstance(schema, dict):
        for k, v in schema.items():
            if k in ("properties", "$defs", "definitions") and isinstance(v, dict):
                for pk, pv in v.items():
                    keys.append(str(pk))
                    keys.extend(_flatten_schema_keys(pv, pk))
            else:
                keys.append(str(k))
                keys.extend(_flatten_schema_keys(v, k))
    elif isinstance(schema, list):
        for x in schema:
            keys.extend(_flatten_schema_keys(x, prefix))
    return keys


def _matches(text: str, patterns: List[str]) -> List[str]:
    lower = text.lower()
    return [p for p in patterns if p.lower() in lower]


def scan_tool_schema(tool: Dict[str, Any], rules: Dict[str, Any] | None = None) -> Dict[str, Any]:
    rules = rules or DEFAULT_RULES
    name = str(tool.get("name", ""))
    description = str(tool.get("description", ""))
    input_schema = tool.get("input_schema") or tool.get("inputSchema") or {}
    output_schema = tool.get("output_schema") or tool.get("outputSchema") or {}
    schema_text = json.dumps(input_schema, ensure_ascii=False).lower()
    output_text = json.dumps(output_schema, ensure_ascii=False).lower()
    combined = f"{name}\n{description}\n{schema_text}\n{output_text}".lower()

    high_risk_verbs = _matches(name + " " + description, rules.get("high_risk_verbs", []))
    descriptor_injection = _matches(description, rules.get("descriptor_injection_patterns", []))
    external_access = _matches(combined, rules.get("external_access_patterns", []))

    schema_keys = _flatten_schema_keys(input_schema)
    sensitive_fields = []
    for key in schema_keys:
        lk = key.lower()
        for pattern in rules.get("sensitive_fields", []):
            if pattern.lower() in lk:
                sensitive_fields.append(key)
                break

    capabilities: Set[str] = set()
    text = combined
    if any(v in text for v in ["delete", "remove", "drop", "refund", "transfer"]):
        capabilities.add("destructive")
    if any(v in text for v in ["send", "write", "update", "publish", "create"]):
        capabilities.add("write")
    if any(v in text for v in ["execute", "shell", "command", "code", "install", "run"]):
        capabilities.add("execute")
    if any(v in text for v in ["amount", "payment", "refund", "transfer", "invoice"]):
        capabilities.add("financial")
    if any(v in text for v in ["oauth", "token", "credential", "identity", "auth"]):
        capabilities.add("identity")
    if any(v in text for v in ["url", "webhook", "http", "download", "upload"]):
        capabilities.add("network")
    if any(v in text for v in ["memory", "vector", "rag", "tenant"]):
        capabilities.add("memory")
    if not capabilities:
        capabilities.add("read")

    findings = []
    if high_risk_verbs:
        findings.append({"type": "high_risk_verb", "matches": sorted(set(high_risk_verbs))})
    if descriptor_injection:
        findings.append({"type": "descriptor_injection_signal", "matches": sorted(set(descriptor_injection))})
    if sensitive_fields:
        findings.append({"type": "sensitive_input_fields", "matches": sorted(set(sensitive_fields))})
    if external_access:
        findings.append({"type": "external_access_signal", "matches": sorted(set(external_access))})

    return {
        "tool_name": name,
        "capabilities": sorted(capabilities),
        "schema_keys": sorted(set(schema_keys)),
        "findings": findings,
        "risk_signals": {
            "high_risk_verbs": sorted(set(high_risk_verbs)),
            "descriptor_injection": sorted(set(descriptor_injection)),
            "sensitive_fields": sorted(set(sensitive_fields)),
            "external_access": sorted(set(external_access)),
        },
    }
