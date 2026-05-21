---
title: Awesome Agentic AI Security
emoji: 🛡️
colorFrom: yellow
colorTo: red
sdk: static
pinned: false
license: mit
---

# Awesome Agentic AI Security

A static, data-driven catalog for comparing **AI security, LLM security, agentic security, MCP security, guardrails, red-team, AI-SPM, observability, data security, and governance tools**.

This project is designed to run as a **Hugging Face Static Space**. It uses plain HTML, CSS, JavaScript, and a maintainable `data/tools.json` file.

## v0.4 additions

- Aligned ASI labels with **OWASP Top 10 for Agentic Applications 2026**.
- Added **OWASP AI Security Solutions Landscape Q2 2026** lifecycle mapping.
- Added `lifecycle_stages` and a Lifecycle stage filter.
- Added **Lifecycle Coverage Score**.
- Expanded the catalog from 27 to 45 tools using conservative OWASP-landscape-informed entries.
- Added `source_basis` and `evidence_level` fields for maintainability.
- Added `supply_chain` as a scoring dimension.
- Added **Agentic SecOps Lead** persona.
- Added evidence-level model for transparent confidence tracking.
- Added ASI Risk → Control → Tool matrix.
- Added lifecycle coverage heatmap.
- Added use-case decision view for MCP, red-team, production protection, enterprise governance, multi-agent monitoring, coding agents, and RAG/memory security.
- Added MCP Security Benchmark v0.1 test-plan scaffold in `data/controls.json`.
- Added `data/schema.json`, `CONTRIBUTING.md`, and GitHub Actions validation workflow.

## References and attribution

This catalog references public OWASP GenAI Security Project materials, including:

- OWASP AI Security Solutions Landscape Q2 2026: https://genai.owasp.org/ai-security-solutions-landscape/
- OWASP Top 10 for Agentic Applications 2026: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- OWASP Agentic Security Initiative: https://genai.owasp.org/initiatives/agentic-security-initiative/
- OWASP GenAI Security Project: https://genai.owasp.org/
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/

OWASP materials are licensed by OWASP under Creative Commons terms as stated in their documents. This repository is a community-maintained derived catalog and does **not** imply OWASP endorsement or vendor certification.

## Project structure

```text
.
├── README.md
├── LICENSE
├── index.html
├── styles.css
├── app.js
├── CONTRIBUTING.md
├── .github/workflows/validate-catalog.yml
└── data/
    ├── tools.json
    ├── controls.json
    └── schema.json
```

## Data model

Each tool in `data/tools.json` can include:

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
  "lifecycle_stages": ["develop_experiment", "test_evaluate", "deploy", "operate"],
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
    "supply_chain": 3,
    "lifecycle_coverage": 2.2,
    "agentic_readiness": 3.7,
    "mcp_security": 3.1
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
  "source_basis": ["OWASP AI Security Solutions Landscape Q2 2026"],
  "evidence_level": "OWASP landscape / vendor-public mapping",
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

Scores are heuristic and community-maintained. They are meant to help shortlist tools for POCs, not certify vendors.

## Local validation

```bash
python -m json.tool data/tools.json > /tmp/tools.validated.json
python -m json.tool data/controls.json > /tmp/controls.validated.json
python scripts/validate_catalog.py  # when using the GitHub workflow helper
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


## Evidence levels

Use the following confidence labels when updating entries:

- `official_owasp_landscape`: appears in OWASP AI Security Solutions Landscape or ASI taxonomy-support material.
- `official_vendor_docs`: explicit public vendor/project documentation.
- `community_verified`: reproducible community verification through PR notes.
- `benchmark_backed`: reproducible test or benchmark evidence.
- `inferred_mapping`: reasonable inference from public capabilities; needs validation.

## v0.4 roadmap notes

The current MCP benchmark is a manual test-plan scaffold. Future versions should add executable test harnesses for descriptor poisoning, OAuth response poisoning, tool permission overreach, sandbox escape, RCE, tool-output injection, and cross-agent trust abuse.
