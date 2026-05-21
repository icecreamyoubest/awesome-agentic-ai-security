---
title: Open AI Agentic Security Tools Catalog
emoji: 🛡️
colorFrom: yellow
colorTo: orange
sdk: static
pinned: false
license: mit
---

# Open AI / Agentic Security Tools Catalog

A static, data-driven catalog for comparing AI, LLM, agentic, and MCP security tools.

This project is designed to run as a **Hugging Face Static Space**. It uses plain HTML, CSS, JavaScript, and a maintainable `data/tools.json` file.

## v0.2 additions

- OWASP Top 10 for Agentic Applications / ASI mapping
- Agentic Readiness Score
- MCP Security Score
- Agentic OWASP risk filter
- Agent Platform Architect and MCP Security Reviewer personas
- MCP-specific scoring dimensions
- Data model fields for `agentic_owasp`, `agentic_scores`, and `mcp_scores`

## References

- OWASP Top 10 for Agentic Applications 2026: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- OWASP Agentic Security Initiative: https://genai.owasp.org/initiatives/agentic-security-initiative/
- OWASP GenAI Security Project: https://genai.owasp.org/
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/

## Project structure

```text
.
├── README.md
├── LICENSE
├── index.html
├── styles.css
├── app.js
└── data/
    └── tools.json
```

## How to update tools

Edit `data/tools.json`. Each tool should include:

```json
{
  "id": "example-tool",
  "name": "Example Tool",
  "org": "Example Org",
  "vendor_type": "open_source",
  "license": "Apache-2.0",
  "category": ["Guardrails", "Agent Security"],
  "description": "Short description.",
  "frameworks": {
    "LangChain/LangGraph": "generic",
    "MCP": "partial"
  },
  "owasp": ["LLM01", "LLM02"],
  "agentic_owasp": ["ASI01", "ASI02"],
  "deployment": ["self_host", "cloud"],
  "targets": ["LLM app", "Agent runtime", "MCP server"],
  "scores": {
    "red_team": 3,
    "runtime": 4,
    "agent_security": 4,
    "data_security": 3,
    "observability": 3,
    "compliance": 3,
    "enterprise": 4,
    "oss_maturity": 3,
    "self_host": 4,
    "ease": 3,
    "agentic_readiness": 3.75,
    "mcp_security": 3.10
  },
  "agentic_scores": {
    "goal_integrity": 4,
    "tool_security": 4,
    "identity_control": 3,
    "memory_security": 3,
    "runtime_enforcement": 4,
    "auditability": 4,
    "multi_agent_coverage": 3,
    "mcp_security": 3
  },
  "mcp_scores": {
    "server_inventory": 3,
    "third_party_server_risk": 3,
    "tool_permissioning": 4,
    "authn_authz": 3,
    "input_output_sanitization": 4,
    "audit_trace": 4,
    "sandboxing": 3,
    "supply_chain": 3
  },
  "url": "https://example.com",
  "docs": "https://docs.example.com",
  "maintainer_notes": "Use conservative scoring unless integration evidence is available."
}
```

## Scoring guidance

All raw dimensions use a 1–5 scale:

- 1 = weak, indirect, or not a primary use case
- 3 = usable, partial, or integration-dependent
- 5 = strong/default candidate with clear evidence

### Agentic Readiness Score

Weighted 1–5 composite:

```text
tool_security 20%
runtime_enforcement 15%
identity_control 15%
auditability 15%
memory_security 10%
goal_integrity 10%
multi_agent_coverage 10%
mcp_security 5%
```

### MCP Security Score

Weighted 1–5 composite:

```text
server_inventory 15%
third_party_server_risk 15%
tool_permissioning 15%
authn_authz 15%
input_output_sanitization 15%
audit_trace 10%
sandboxing 10%
supply_chain 5%
```

## Local validation

```bash
python -m json.tool data/tools.json > /tmp/tools.validated.json
python -m http.server 7860
```

Then open `http://localhost:7860`.

## Deploy to Hugging Face Spaces

1. Create a new Hugging Face Space.
2. Select **Static** as the SDK.
3. Upload the files in this repository.
4. The Space will serve `index.html` automatically.

## Disclaimer

This is a community-maintained shortlist and scoring aid, not a certification or procurement decision. Verify vendor claims, product status, licenses, data handling, deployment topology, and integration depth before relying on any tool in production.
