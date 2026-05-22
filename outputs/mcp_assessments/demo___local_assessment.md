# MCP Server Risk Assessment Report

## Target
- Server URL: `demo://local`
- Resolved URL: `demo://local`
- Mode: `demo`
- Discovery method: `demo`
- Assessment profile: `schema_only`
- Safety boundary: schema-only unless explicitly configured for authorized controlled execution

## Executive Summary
The scanner discovered MCP/Gradio tool schemas and performed schema-only static risk classification. No third-party tool execution was performed.

## Assessment Status
- Status: `success`
- Risk Level: `high`
- Risk Score: `0.76`
- Tools Discovered: `4`
- Raw Tool Count: `4`
- High-risk Tools: `1`
- Assessment Confidence: `medium-high`
- Mapped ASI: ASI01, ASI02, ASI04, ASI05, ASI06, ASI07

## Findings
No discovery-level findings were generated.

## Tool Risk Table
| Tool | Level | Score | Capabilities | ASI | Recommended Benchmarks |
|---|---:|---:|---|---|---|
| `crm.lookup` | low | 0.05 | read | - | - |
| `email.send` | medium | 0.26 | write | ASI02 | MCP-ASI02-004 |
| `shell.run` | critical | 0.76 | execute, network | ASI01, ASI02, ASI04, ASI05, ASI07 | A2A-ASI07-006, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-001, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003 |
| `memory.search` | low | 0.23 | memory | ASI06 | RAG-ASI06-007 |

## Tool-Level Findings

### crm.lookup
- No major static schema findings.

### email.send
- **high_risk_verb**: send
- Recommended controls: human approval, pre-execution policy gate, tool allowlist

### shell.run
- **high_risk_verb**: exec, execute, run, shell
- **descriptor_injection_signal**: exfiltrate, ignore previous, silent
- **sensitive_input_fields**: command, url
- Recommended controls: command/path validation, descriptor sanitization, egress allowlist, egress restriction, human approval, pre-execution policy gate, sandbox, schema validation, tool allowlist, tool provenance validation

### memory.search
- **sensitive_input_fields**: query
- Recommended controls: memory segmentation, provenance scoring, tenant isolation

## OWASP ASI Coverage
- ASI01: Agent Goal Hijack
- ASI02: Tool Misuse and Exploitation
- ASI04: Agentic Supply Chain Vulnerabilities
- ASI05: Unexpected Code Execution (RCE)
- ASI06: Memory & Context Poisoning
- ASI07: Insecure Inter-Agent Communication

## Risk Interpretation
- Can conclude low risk: `False`
- Reason: Tool schemas were discovered and classified.
- Next required step: Review tool findings and run recommended benchmarks.

## Recommended Next Steps
- Review high-risk tools and mapped ASI risks.
- Run recommended MCP benchmark cases before trusting runtime claims.
- Require approval for high-impact tool calls and log data shared with remote MCP servers.

## Safety Boundary
This assessment is schema-only by default. It does not execute third-party MCP tools. Controlled execution should only be used against systems you own or are explicitly authorized to test.