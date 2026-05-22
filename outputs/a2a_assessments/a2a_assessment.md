# A2A / Agent-to-Agent Risk Assessment Report

## Executive Summary

- Agents assessed: `3`
- High-risk agents: `1`
- Average risk score: `4.33`
- Risk level: **high**
- Mapped ASI: ASI02, ASI03, ASI04, ASI07, ASI08, ASI10

## Agent-Level Findings

| Agent | Risk | Signals | ASI | Required controls |
|---|---:|---|---|---|
| Planner Agent | low (0.0) |  |  | agent identity registry, immutable agent action audit |
| Finance Worker | medium (5.0) | delegation_enabled, high_impact_capability_claim, unsigned_agent_card | ASI02, ASI03, ASI04, ASI07, ASI08, ASI10 | agent identity registry, capability allowlist, delegation depth limit, descriptor provenance verification, human approval for high-impact actions, immutable agent action audit, per-action authorization, signed agent cards |
| External Observer | high (8.0) | external_routing_or_webhook, missing_or_weak_agent_auth, open_agent_registration, unencrypted_agent_endpoint, unsigned_agent_card | ASI03, ASI04, ASI07, ASI08, ASI10 | TLS enforcement, agent identity registry, closed registration, descriptor provenance verification, egress allowlist, immutable agent action audit, mTLS or token-bound agent auth, message integrity validation, per-agent scoped credentials, protocol pinning, registry approval workflow, signed agent cards |

## Trust Graph

- Nodes: `3`
- Edges: `2`
- Risky edges: `2`
