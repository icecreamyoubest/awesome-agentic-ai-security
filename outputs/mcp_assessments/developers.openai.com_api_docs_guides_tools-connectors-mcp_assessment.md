# MCP Server Risk Assessment Report

## Target
- Server URL: `https://developers.openai.com/api/docs/guides/tools-connectors-mcp`
- Resolved URL: `https://developers.openai.com/api/docs/guides/tools-connectors-mcp`
- Mode: `documentation`
- Discovery method: `openai_docs`
- Assessment profile: `schema_only`
- Safety boundary: schema-only unless explicitly configured for authorized controlled execution

## Executive Summary
The target is a documentation/reference URL, not a live MCP server. The report summarizes MCP/connector risk-relevant references discovered from the documentation and maps them to review controls.

## Assessment Status
- Status: `documentation_reference`
- Risk Level: `high`
- Risk Score: `0.63`
- Tools Discovered: `10`
- Raw Tool Count: `10`
- High-risk Tools: `3`
- Assessment Confidence: `medium-high`
- Mapped ASI: ASI02, ASI03, ASI07

## Discovery Notes / Errors
- `documentation fetch failed: [Errno -3] Temporary failure in name resolution`

## Findings

### FINDING-DISCOVERY-001: MCP discovery issue
- Severity: low_medium
- Category: discovery_failure
- Evidence: `documentation fetch failed: [Errno -3] Temporary failure in name resolution`
- Impact: The scanner may not have retrieved all tool schemas; risk assessment confidence is reduced.
- Recommendation: Verify the endpoint URL, preserve trailing slash for Gradio MCP endpoints, follow redirects, and retry supported discovery modes.

## Tool Risk Table
| Tool | Level | Score | Capabilities | ASI | Recommended Benchmarks |
|---|---:|---:|---|---|---|
| `openai.remote_mcp_server_reference` | high | 0.53 | identity, network | ASI02, ASI03, ASI07 | A2A-ASI07-006, MCP-ASI02-004, MCP-ASI07-003 |
| `openai.remote_mcp_server_reference` | high | 0.53 | identity, network | ASI02, ASI03, ASI07 | A2A-ASI07-006, MCP-ASI02-004, MCP-ASI07-003 |
| `openai.connector.connector_dropbox` | high | 0.63 | destructive, identity | ASI02, ASI03, ASI07 | A2A-ASI07-006, MCP-ASI02-004, MCP-ASI07-003 |
| `openai.connector.connector_gmail` | medium | 0.3 | identity | ASI03, ASI07 | A2A-ASI07-006, MCP-ASI07-003 |
| `openai.connector.connector_googlecalendar` | medium | 0.3 | identity | ASI03, ASI07 | A2A-ASI07-006, MCP-ASI07-003 |
| `openai.connector.connector_googledrive` | medium | 0.3 | identity | ASI03, ASI07 | A2A-ASI07-006, MCP-ASI07-003 |
| `openai.connector.connector_microsoftteams` | medium | 0.3 | identity | ASI03, ASI07 | A2A-ASI07-006, MCP-ASI07-003 |
| `openai.connector.connector_outlookcalendar` | medium | 0.3 | identity | ASI03, ASI07 | A2A-ASI07-006, MCP-ASI07-003 |
| `openai.connector.connector_outlookemail` | medium | 0.3 | identity | ASI03, ASI07 | A2A-ASI07-006, MCP-ASI07-003 |
| `openai.connector.connector_sharepoint` | medium | 0.3 | identity | ASI03, ASI07 | A2A-ASI07-006, MCP-ASI07-003 |

## Tool-Level Findings

### openai.remote_mcp_server_reference
- **sensitive_input_fields**: authorization, server_url
- **external_access_signal**: https://
- Recommended controls: OAuth response validation, egress allowlist, per-action authorization, schema validation, scoped credentials

### openai.remote_mcp_server_reference
- **sensitive_input_fields**: authorization, server_url
- **external_access_signal**: https://
- Recommended controls: OAuth response validation, egress allowlist, per-action authorization, schema validation, scoped credentials

### openai.connector.connector_dropbox
- **high_risk_verb**: drop
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, human approval, per-action authorization, pre-execution policy gate, scoped credentials, tool allowlist

### openai.connector.connector_gmail
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, per-action authorization, scoped credentials

### openai.connector.connector_googlecalendar
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, per-action authorization, scoped credentials

### openai.connector.connector_googledrive
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, per-action authorization, scoped credentials

### openai.connector.connector_microsoftteams
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, per-action authorization, scoped credentials

### openai.connector.connector_outlookcalendar
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, per-action authorization, scoped credentials

### openai.connector.connector_outlookemail
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, per-action authorization, scoped credentials

### openai.connector.connector_sharepoint
- **sensitive_input_fields**: authorization
- Recommended controls: OAuth response validation, per-action authorization, scoped credentials

## OWASP ASI Coverage
- ASI02: Tool Misuse and Exploitation
- ASI03: Identity and Privilege Abuse
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