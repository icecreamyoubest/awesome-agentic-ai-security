
from __future__ import annotations

import re
from typing import Any, Dict, List

from adapters.base_adapter import SecurityToolAdapter

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
]
INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore (all )?(previous|prior) instructions"),
    re.compile(r"(?i)system prompt"),
    re.compile(r"(?i)developer message"),
    re.compile(r"(?i)exfiltrate|send.*secret|leak.*data"),
]
PII_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b\+?65\s?[689]\d{3}\s?\d{4}\b"),
]

class LLMGuardAdapter(SecurityToolAdapter):
    """Lightweight adapter for LLM Guard style input/output scanning.

    If the optional `llm_guard` package is installed, this class can be extended to call
    native scanners. To keep the demo stable on Hugging Face CPU Spaces, the default
    implementation uses deterministic scanner rules for prompt injection, secrets, and PII.
    """

    name = "llm_guard_adapter"

    def _scan_text(self, text: str) -> Dict[str, Any]:
        findings: List[Dict[str, str]] = []
        for p in INJECTION_PATTERNS:
            if p.search(text or ""):
                findings.append({"type":"prompt_injection", "pattern": p.pattern})
        for p in SECRET_PATTERNS:
            if p.search(text or ""):
                findings.append({"type":"secret", "pattern": p.pattern})
        for p in PII_PATTERNS:
            if p.search(text or ""):
                findings.append({"type":"pii", "pattern": p.pattern})
        decision = "block" if any(f["type"] in {"prompt_injection", "secret"} for f in findings) else ("redact" if findings else "allow")
        return {"adapter": self.name, "decision": decision, "findings": findings, "sanitized": decision != "block"}

    def scan_input(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._scan_text(str(payload.get("text") or payload.get("prompt") or payload))

    def scan_output(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._scan_text(str(payload.get("text") or payload.get("output") or payload))

    def validate_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        text = " ".join([str(tool_call.get("tool_name", "")), str(tool_call.get("arguments", "")), str(tool_call.get("tool_output", ""))])
        return self._scan_text(text)

    def run_benchmark_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        text = " ".join(str(case.get(k, "")) for k in ["malicious_descriptor", "payload", "objective", "attack_type"])
        res = self._scan_text(text)
        expected_block = str(case.get("expected_control", "")).lower() or str(case.get("pass_condition", "")).lower()
        should_block = any(w in expected_block for w in ["block", "quarantine", "reject", "deny"])
        passed = (res["decision"] == "block") if should_block else (res["decision"] in {"allow", "redact"})
        return {"case_id": case.get("id"), "adapter": self.name, "passed": passed, "decision": res["decision"], "findings": res["findings"]}
