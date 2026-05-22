from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple

DANGEROUS_PATTERNS = [
    r"ignore\s+previous",
    r"exfiltrat(e|ion)",
    r"send\s+.*\s+to\s+https?://",
    r"rm\s+-rf",
    r"curl\s+.*\|\s*sh",
    r"reverse\s+shell",
    r"bcc\s+.*attacker",
    r"delete\s+production",
    r"eval\s*\(",
    r"subprocess",
    r"/etc/passwd",
    r"api[_-]?key|secret|token",
]

HIGH_IMPACT_TOOLS = {"email.send", "crm.refund", "file.delete", "shell.run", "package.install"}
ALLOWED_TOOLS = {"crm.lookup", "email.draft", "file.read", "memory.search", "ticket.create"}

@dataclass
class PolicyDecision:
    decision: str
    reason_code: str
    reason: str
    asi: List[str]
    controls: List[str]
    trace_id: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PolicyEngine:
    """Small deterministic PEP/PDP used by the demo runtime.

    It is intentionally simple but demonstrates real enforcement before tool execution:
    descriptor sanitization, tool allowlisting, argument validation, high-impact approval,
    OAuth/tool-output sanitization, and audit-oriented decisions.
    """

    def __init__(self) -> None:
        self.patterns = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

    def _contains_dangerous_text(self, text: str) -> Tuple[bool, str]:
        for pattern in self.patterns:
            if pattern.search(text or ""):
                return True, pattern.pattern
        return False, ""

    def evaluate(self, request: Dict[str, Any]) -> PolicyDecision:
        trace_id = request.get("trace_id") or f"trace_{uuid.uuid4().hex[:12]}"
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        tool_name = request.get("tool_name", "")
        descriptor = request.get("tool_descriptor", "")
        user_prompt = request.get("user_prompt", "")
        args = request.get("arguments", {}) or {}
        tool_output = request.get("tool_output", "")
        auth_context = request.get("auth_context", {}) or {}
        approved = bool(request.get("human_approved", False))

        combined = "\n".join([
            str(user_prompt), str(descriptor), str(tool_output), str(args), str(auth_context)
        ])

        # ASI04 / ASI01: descriptor or input attempts to carry hidden instructions.
        has_bad, matched = self._contains_dangerous_text(str(descriptor))
        if has_bad:
            return PolicyDecision(
                "blocked", "TOOL_DESCRIPTOR_POISONING",
                f"Tool descriptor contains suspicious instruction or secret pattern: {matched}",
                ["ASI04", "ASI01"],
                ["descriptor_sanitization", "server_provenance_validation", "registration_quarantine"],
                trace_id, now,
            )

        # ASI02: only allow known tool names in demo runtime.
        if tool_name not in ALLOWED_TOOLS and tool_name not in HIGH_IMPACT_TOOLS:
            return PolicyDecision(
                "blocked", "UNKNOWN_TOOL",
                f"Tool '{tool_name}' is not registered in the runtime allowlist.",
                ["ASI02", "ASI04"],
                ["tool_allowlist", "typed_tool_registry"],
                trace_id, now,
            )

        # ASI02 / ASI09: high-impact actions need human approval.
        if tool_name in HIGH_IMPACT_TOOLS and not approved:
            return PolicyDecision(
                "blocked", "HITL_REQUIRED",
                f"High-impact tool '{tool_name}' requires explicit human approval.",
                ["ASI02", "ASI09"],
                ["human_in_the_loop", "pre_execution_approval", "least_agency"],
                trace_id, now,
            )

        # ASI05: argument-level RCE patterns.
        has_bad, matched = self._contains_dangerous_text(str(args))
        if has_bad:
            return PolicyDecision(
                "blocked", "UNSAFE_TOOL_ARGUMENT",
                f"Tool argument contains unsafe execution or exfiltration pattern: {matched}",
                ["ASI05", "ASI02"],
                ["argument_schema_validation", "sandboxed_execution", "deny_shell_expansion"],
                trace_id, now,
            )

        # ASI07 / ASI03: OAuth response poisoning / unbound token signals.
        if auth_context.get("oauth_response_text"):
            has_bad, matched = self._contains_dangerous_text(str(auth_context.get("oauth_response_text")))
            if has_bad:
                return PolicyDecision(
                    "blocked", "OAUTH_RESPONSE_POISONING",
                    f"OAuth/tool authentication response contains instruction-like content: {matched}",
                    ["ASI07", "ASI03"],
                    ["oauth_audience_binding", "post_auth_intent_validation", "signed_server_identity"],
                    trace_id, now,
                )

        # ASI01 / ASI02: tool output injection should be treated as data only.
        has_bad, matched = self._contains_dangerous_text(str(tool_output))
        if has_bad:
            return PolicyDecision(
                "blocked", "TOOL_OUTPUT_INJECTION",
                f"Tool output contains instruction-like payload and cannot influence planning: {matched}",
                ["ASI01", "ASI02"],
                ["tool_output_sanitization", "intent_diffing", "planner_boundary"],
                trace_id, now,
            )

        # ASI03: crude scope binding demo.
        requested_scope = auth_context.get("requested_scope")
        allowed_scope = auth_context.get("allowed_scope")
        if requested_scope and allowed_scope and requested_scope != allowed_scope:
            return PolicyDecision(
                "blocked", "SCOPE_MISMATCH",
                f"Requested scope '{requested_scope}' does not match allowed scope '{allowed_scope}'.",
                ["ASI03", "ASI02"],
                ["task_scoped_token", "per_action_authorization", "scope_binding"],
                trace_id, now,
            )

        return PolicyDecision(
            "allowed", "POLICY_OK",
            "Request passed demo runtime policy gates.",
            [],
            ["tool_allowlist", "argument_validation", "audit_logging"],
            trace_id, now,
        )
