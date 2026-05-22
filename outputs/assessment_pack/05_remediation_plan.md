# Remediation Plan

Mapped ASI: ASI02, ASI03, ASI04, ASI07, ASI08, ASI10

## ASI02 — Tool Misuse

### Controls
- tool allowlist
- pre-execution PEP/PDP
- argument schema validation
- tool budget/rate limit

### Validation
- Run `MCP-ASI02-004`

## ASI03 — Identity and Privilege Abuse

### Controls
- per-agent identity
- short-lived scoped tokens
- per-action authorization
- delegation chain validation

### Validation
- Run `IDENTITY-ASI03-001`

## ASI04 — Agentic Supply Chain

### Controls
- descriptor provenance
- signed agent/tool manifests
- registry allowlist
- package scanning

### Validation
- Run `MCP-ASI04-001`
- Run `MCP-ASI04-009`

## ASI07 — Insecure Inter-Agent Communication

### Controls
- mTLS
- signed messages
- agent-card attestation
- anti-replay nonce

### Validation
- Run `A2A-ASI07-006`

## ASI08 — Cascading Failures

### Controls
- circuit breaker
- blast-radius cap
- delegation depth limit
- runtime anomaly detector

### Validation
- Run `A2A-ASI08-002`

## ASI10 — Rogue Agents

### Controls
- behavioral attestation
- kill switch
- agent quarantine
- watchdog agent

### Validation
- Run `A2A-ASI10-001`
