# Architecture Review

## Scenario
Enterprise Copilot with RAG and MCP Tools

## Recommended control plane
Client / Agent → MCP Security Gateway → Descriptor Validator → PEP/PDP → Tool Runtime → Audit Log / SIEM.

## Control points
- Validate tool descriptors before registration.
- Enforce allowlists and typed schemas before tool execution.
- Require HITL for high-impact actions.
- Emit immutable audit logs for policy decisions and tool calls.
