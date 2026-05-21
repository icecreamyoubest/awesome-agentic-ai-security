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


## v0.8 additions

- Added **Grounded LLM Q&A Agent** under `agents/grounded_qa_agent.py`.
- Added a generated `data/source_index.json` so answers can cite stable source IDs and links instead of relying on free-form model memory.
- Added retrieval-first Q&A: the agent retrieves catalog/tool/evidence/control/incident/benchmark/reference-architecture records before calling an optional LLM.
- Added citation validation: answers must cite retrieved source IDs such as `[S001]`; otherwise the CLI flags unsupported output and can fall back to extractive answers.
- Added optional OpenAI-compatible chat-completions integration through environment variables, while keeping the default mode fully offline and deterministic.

Build the source index:

```bash
python agents/build_source_index.py --output data/source_index.json
```

Ask a grounded question without an LLM:

```bash
python agents/grounded_qa_agent.py \
  --question "Which tools should I evaluate for MCP runtime security and ASI02 tool misuse?" \
  --provider none \
  --output outputs/qa_sample_answer.md
```

Ask with an OpenAI-compatible LLM endpoint:

```bash
export OPENAI_API_KEY="..."
python agents/grounded_qa_agent.py \
  --question "Design a validation plan for a LangGraph + MCP + RAG customer support agent" \
  --provider openai-compatible \
  --model gpt-4o-mini \
  --output outputs/qa_llm_answer.md
```

Grounding rule: the LLM receives only retrieved indexed records and is instructed to cite source IDs. If the index does not contain enough evidence, the agent must say so instead of inventing unsupported claims.

## v0.7 additions

- Added **Solution & Tool Validation Agent** under `agents/`.
- Added deterministic scenario parsing, ASI risk mapping, tool recommendation, evidence validation, benchmark planning, and Markdown report generation.
- Added 3 reusable example scenarios under `examples/`: MCP + RAG customer support, secure coding agent sandbox, and multi-agent finance workflow.
- Added sample generated reports under `outputs/`.
- Extended validation to check scenario files.
- Kept scoring rule-based so LLMs can be added later only for optional explanation or requirement extraction.

Run the agent:

```bash
python agents/solution_validator_agent.py \
  --scenario examples/mcp_rag_agent_scenario.json \
  --output outputs/mcp_rag_agent_solution_report.md \
  --json-output outputs/mcp_rag_agent_solution_report.json
```

## v0.6 additions

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
├── agents/
│   ├── solution_validator_agent.py
│   ├── risk_mapper.py
│   ├── tool_recommender.py
│   ├── evidence_validator.py
│   ├── benchmark_planner.py
│   ├── report_writer.py
│   └── schemas.py
├── examples/
│   ├── mcp_rag_agent_scenario.json
│   ├── coding_agent_scenario.json
│   └── multi_agent_finance_scenario.json
├── outputs/
│   ├── mcp_rag_agent_solution_report.md
│   ├── coding_agent_solution_report.md
│   └── multi_agent_finance_solution_report.md
├── benchmarks/
├── .github/workflows/validate-catalog.yml
└── data/
    ├── tools.json
    ├── controls.json
    ├── evidence.json
    ├── incidents.json
    ├── reference_architectures.json
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

## v0.6 roadmap notes

The current MCP benchmark is a manual test-plan scaffold. Future versions should add executable test harnesses for descriptor poisoning, OAuth response poisoning, tool permission overreach, sandbox escape, RCE, tool-output injection, and cross-agent trust abuse.



## v0.8 additions

- Added **Grounded LLM Q&A Agent** under `agents/grounded_qa_agent.py`.
- Added a generated `data/source_index.json` so answers can cite stable source IDs and links instead of relying on free-form model memory.
- Added retrieval-first Q&A: the agent retrieves catalog/tool/evidence/control/incident/benchmark/reference-architecture records before calling an optional LLM.
- Added citation validation: answers must cite retrieved source IDs such as `[S001]`; otherwise the CLI flags unsupported output and can fall back to extractive answers.
- Added optional OpenAI-compatible chat-completions integration through environment variables, while keeping the default mode fully offline and deterministic.

Build the source index:

```bash
python agents/build_source_index.py --output data/source_index.json
```

Ask a grounded question without an LLM:

```bash
python agents/grounded_qa_agent.py \
  --question "Which tools should I evaluate for MCP runtime security and ASI02 tool misuse?" \
  --provider none \
  --output outputs/qa_sample_answer.md
```

Ask with an OpenAI-compatible LLM endpoint:

```bash
export OPENAI_API_KEY="..."
python agents/grounded_qa_agent.py \
  --question "Design a validation plan for a LangGraph + MCP + RAG customer support agent" \
  --provider openai-compatible \
  --model gpt-4o-mini \
  --output outputs/qa_llm_answer.md
```

Grounding rule: the LLM receives only retrieved indexed records and is instructed to cite source IDs. If the index does not contain enough evidence, the agent must say so instead of inventing unsupported claims.

## v0.7 additions

- Added **Solution & Tool Validation Agent** under `agents/`.
- Added deterministic scenario parsing, ASI risk mapping, tool recommendation, evidence validation, benchmark planning, and Markdown report generation.
- Added 3 reusable example scenarios under `examples/`: MCP + RAG customer support, secure coding agent sandbox, and multi-agent finance workflow.
- Added sample generated reports under `outputs/`.
- Extended validation to check scenario files.
- Kept scoring rule-based so LLMs can be added later only for optional explanation or requirement extraction.

Run the agent:

```bash
python agents/solution_validator_agent.py \
  --scenario examples/mcp_rag_agent_scenario.json \
  --output outputs/mcp_rag_agent_solution_report.md \
  --json-output outputs/mcp_rag_agent_solution_report.json
```

## v0.6 additions

- Evidence Hub with `data/evidence.json` and per-tool evidence records.
- Tool detail modal with ASI coverage, lifecycle coverage, scores, framework support, and evidence.
- Compare mode for up to four tools.
- ASI × Lifecycle control matrix for architecture review.
- MCP Security Benchmark v0.1 in both JSON and JSONL formats under `benchmarks/`.
- GitHub Action template to sync this static site to a Hugging Face Space.

## GitHub to Hugging Face sync

Create repository secrets:

- `HF_TOKEN`: Hugging Face write token
- `HF_SPACE`: `Coraaaa/awesome-agentic-ai-security` or your target `username/space-name`

Then enable `.github/workflows/sync-to-huggingface.yml`.


## v0.6: Benchmark and Evidence Hub upgrades

v0.6 adds:

- Executable MCP Security Benchmark Runner under `benchmarks/runner/`
- Evidence Confidence Score for every tool
- ASI Coverage Depth (`0–3`) per mapped ASI risk
- Reference architectures in `data/reference_architectures.json`
- Incident → ASI → Benchmark mapping in `data/incidents.json`
- Static tool submission JSON generator in the Space UI

Run the benchmark runner locally:

```bash
python benchmarks/runner/run_benchmark.py   --suite benchmarks/mcp_security_benchmark_v01.jsonl   --mode mock   --output benchmarks/results/example_report.json
```

Validate the catalog:

```bash
python scripts/validate_catalog.py
```
