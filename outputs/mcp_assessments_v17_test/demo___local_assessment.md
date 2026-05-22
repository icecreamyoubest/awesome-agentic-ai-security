# Universal MCP Risk Assessment Report

## 1. Target Summary
- Target: `demo://local`
- Assessment type: `universal_mcp_risk_assessment`
- Endpoint type: `demo`
- Mode: `auto`
- Profile: `safe_probe`
- Status: `schema_discovered`
- Confidence: `medium-high`
- Safety boundary: schema/config review by default; runtime probing requires explicit authorization and is restricted to safe/read-only calls unless allow_high_risk is enabled.

## 2. Executive Summary
The assessor discovered MCP/Gradio tool schemas, classified tool capability risks, mapped OWASP ASI coverage, and generated benchmark recommendations. Runtime probing was performed only if explicitly authorized by the selected profile.

- Risk level: `high`
- Risk score: `0.575`
- Tools discovered: `4`
- High-risk tools: `1`
- Mapped ASI: ASI01, ASI02, ASI04, ASI05, ASI06, ASI07, ASI09

## 3. Endpoint Classification
- Input: `demo://local`
- Normalized URL: `demo://local`
- App root: `None`
- Note: Local demo endpoint; no network discovery required.

## 4. Discovery Attempts
No live endpoint discovery attempts were required or recorded.

## 5. Tool Inventory and Risk Table
| Tool | Capability Class | Level | Score | ASI | Benchmarks |
|---|---|---:|---:|---|---|
| `crm.lookup` | read_only | low | 0.043 | - | - |
| `email.send` | write_external_or_mutating | low | 0.24 | ASI02 | MCP-ASI02-004 |
| `shell.run` | code_or_command_execution | high | 0.575 | ASI01, ASI02, ASI04, ASI05, ASI07, ASI09 | A2A-ASI07-006, HITL-ASI09-010, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-001, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003 |
| `memory.search` | memory_or_rag | low | 0.173 | ASI06 | RAG-ASI06-007 |

## 6. Tool-Level Findings
### crm.lookup
- Capability class: `read_only`
- Required controls: n/a
- Risk dimensions:
  - capability_risk: 0.05
  - descriptor_injection_risk: 0.0
  - input_schema_risk: 0.0
  - output_data_risk: 0.1
  - identity_oauth_risk: 0.0
  - network_egress_risk: 0.0
  - human_approval_gap: 0.0
  - auditability_gap: 0.4

### email.send
- Capability class: `write_external_or_mutating`
- Required controls: human approval, pre-execution policy gate, tool allowlist
- Risk dimensions:
  - capability_risk: 0.6
  - descriptor_injection_risk: 0.0
  - input_schema_risk: 0.0
  - output_data_risk: 0.7
  - identity_oauth_risk: 0.0
  - network_egress_risk: 0.0
  - human_approval_gap: 0.0
  - auditability_gap: 0.4
- Static findings:
  - high_risk_verb: send

### shell.run
- Capability class: `code_or_command_execution`
- Required controls: command/path validation, descriptor sanitization, egress allowlist, egress restriction, explicit approval UX for high-impact actions, human approval, pre-execution policy gate, remote server allowlist, sandbox, schema validation, tool allowlist, tool provenance validation
- Risk dimensions:
  - capability_risk: 1.0
  - descriptor_injection_risk: 1.0
  - input_schema_risk: 0.4
  - output_data_risk: 0.1
  - identity_oauth_risk: 0.0
  - network_egress_risk: 0.7
  - human_approval_gap: 0.7
  - auditability_gap: 0.0
- Static findings:
  - high_risk_verb: exec, execute, run, shell
  - descriptor_injection_signal: exfiltrate, ignore previous, silent
  - sensitive_input_fields: command, url

### memory.search
- Capability class: `memory_or_rag`
- Required controls: memory segmentation, provenance scoring, tenant isolation
- Risk dimensions:
  - capability_risk: 0.45
  - descriptor_injection_risk: 0.0
  - input_schema_risk: 0.2
  - output_data_risk: 0.1
  - identity_oauth_risk: 0.0
  - network_egress_risk: 0.0
  - human_approval_gap: 0.0
  - auditability_gap: 0.4
- Static findings:
  - sensitive_input_fields: query

## 8. Runtime Probe / Execution Measurement
- Probe status: `not_supported`
- Reason: runtime probe supports live HTTP MCP endpoints only in this module

## 9. OWASP ASI Mapping
- ASI01: Agent Goal Hijack
- ASI02: Tool Misuse and Exploitation
- ASI04: Agentic Supply Chain Vulnerabilities
- ASI05: Unexpected Code Execution (RCE)
- ASI06: Memory & Context Poisoning
- ASI07: Insecure Inter-Agent Communication
- ASI09: Human-Agent Trust Exploitation

## 10. Findings
No major findings were generated.
## 11. Recommended Next Steps
- Review high-risk tools and mapped OWASP ASI risks.
- Run recommended benchmark cases before accepting tool or vendor security claims.
- Enable runtime probing only in owned or explicitly authorized environments.

## 12. Safety Boundary
Schema discovery and config review are safe by default. Runtime probing must only be used against systems you own or are explicitly authorized to test. Do not execute destructive tools on third-party MCP servers.