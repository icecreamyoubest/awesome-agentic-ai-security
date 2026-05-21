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

A static, data-driven catalog and validation hub for comparing **AI security, LLM security, agentic security, MCP security, guardrails, red-team, AI-SPM, observability, data security, and governance tools**.

This project is designed to run as a **Hugging Face Static Space**. It uses plain HTML, CSS, JavaScript, and maintainable JSON data files.

## v1.0 additions

v0.9 upgrades the project from grounded Q&A into an auditable **Agentic Security Evaluation Platform**:

- **Web Q&A Advisor Panel**: browser-side retrieval over `data/source_index.json` with source-linked answers.
- **Answer Audit Panel**: shows retrieved sources, used citations, unsupported citations, confidence, and validation suggestions.
- **Tool Claim Verifier**: decomposes vendor/tool claims into ASI risks, required evidence, benchmark tests, and current evidence status.
- **Validation Agent Loop**: scenario → ASI risks → recommended tools → benchmark plan → score update suggestions.
- **Architecture Generator**: scenario signals → reference architecture patterns → controls → Mermaid diagram text.
- **Quarterly Evidence Update Pipeline**: release records under `data/releases/` for maintaining catalog changes over time.



## v1.0 additions

v1.0 adds an **Automated Update Intelligence Pipeline** for keeping the catalog current with tool releases, top-company AI security features, roadmap signals, and evidence changes.

- **Update source registry**: `data/update_sources.json` tracks official blogs, release feeds, GitHub repositories, security pages, and roadmap pages.
- **Update monitor**: `agents/update_monitor.py` fetches sources, deduplicates by hash, and creates `data/updates/pending_updates.json`.
- **Update triage agent**: `agents/update_triage_agent.py` maps updates to tools, vendors, ASI risks, lifecycle stages, feature categories, and priority.
- **Roadmap update agent**: `agents/roadmap_update_agent.py` converts triaged updates into roadmap items and catalog patch suggestions.
- **End-to-end auto update pipeline**: `agents/auto_update_pipeline.py` runs monitor → triage → roadmap.
- **GitHub scheduled workflow**: `.github/workflows/auto-update-intelligence.yml` runs on schedule and opens a PR with update suggestions.
- **Static update dashboard**: the Hugging Face page shows latest pending updates, roadmap signals, watched sources, and manual commands.

Recommended command:

```bash
python agents/auto_update_pipeline.py --network --max-per-source 5
```

Offline smoke test:

```bash
python agents/auto_update_pipeline.py --offline
```

## Core workflows

### 1. Run grounded Q&A without an LLM

```bash
python agents/grounded_qa_agent.py \
  --question "Which tools should I evaluate for MCP runtime security and ASI02 tool misuse?" \
  --provider none \
  --output outputs/qa_sample_answer.md \
  --json-output outputs/qa_sample_answer.json
```

### 2. Run grounded Q&A with an OpenAI-compatible LLM

```bash
export OPENAI_API_KEY="..."
python agents/grounded_qa_agent.py \
  --question "Design a validation plan for a LangGraph + MCP + RAG customer support agent" \
  --provider openai-compatible \
  --model gpt-4o-mini \
  --fallback-on-uncited \
  --output outputs/qa_llm_answer.md
```

Grounding rule: the LLM receives only retrieved indexed records and must cite source IDs such as `[S001]`. If the index does not contain enough evidence, it must say what evidence is missing.

### 3. Audit an answer

```bash
python agents/answer_auditor.py \
  --question "Which tools should I evaluate for MCP runtime security?" \
  --answer-file outputs/qa_sample_answer.md \
  --output outputs/answer_audit_sample.json
```

### 4. Verify a tool claim

```bash
python agents/claim_verifier.py \
  --tool noma-security \
  --claim "MCP discovery and runtime policy enforcement" \
  --output outputs/claim_verification_sample.json
```

### 5. Run the validation loop

```bash
python agents/validation_loop.py \
  --scenario examples/mcp_rag_agent_scenario.json \
  --output outputs/validation_loop_sample.md \
  --json-output outputs/validation_loop_sample.json
```

### 6. Generate a reference architecture

```bash
python agents/architecture_generator.py \
  --scenario examples/mcp_rag_agent_scenario.json \
  --output outputs/generated_architecture_sample.md \
  --json-output outputs/generated_architecture_sample.json
```

## Project structure

```text
.
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── index.html
├── styles.css
├── app.js
├── agents/
│   ├── solution_validator_agent.py
│   ├── grounded_qa_agent.py
│   ├── answer_auditor.py
│   ├── claim_verifier.py
│   ├── validation_loop.py
│   ├── architecture_generator.py
│   ├── build_source_index.py
│   ├── retriever.py
│   ├── llm_client.py
│   ├── risk_mapper.py
│   ├── tool_recommender.py
│   ├── evidence_validator.py
│   ├── benchmark_planner.py
│   ├── report_writer.py
│   └── schemas.py
├── data/
│   ├── tools.json
│   ├── controls.json
│   ├── evidence.json
│   ├── source_index.json
│   ├── claims.json
│   ├── incidents.json
│   ├── reference_architectures.json
│   ├── architecture_templates.json
│   ├── tool_submission_template.json
│   ├── schema.json
│   └── releases/
│       ├── q2-2026.json
│       └── change_log.json
├── benchmarks/
│   ├── mcp_security_benchmark_v01.jsonl
│   ├── mcp_security_benchmark_v01.json
│   └── runner/
├── examples/
├── outputs/
├── scripts/
└── .github/workflows/
```

## References and attribution

This catalog references public OWASP GenAI Security Project materials, including:

- OWASP AI Security Solutions Landscape Q2 2026: https://genai.owasp.org/ai-security-solutions-landscape/
- OWASP Top 10 for Agentic Applications 2026: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- OWASP Agentic Security Initiative: https://genai.owasp.org/initiatives/agentic-security-initiative/
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/

OWASP materials are licensed by OWASP under Creative Commons terms as stated in their documents. This repository is a community-maintained derived catalog and does **not** imply OWASP endorsement or vendor certification.

## Local validation

```bash
python scripts/validate_catalog.py
python -m py_compile agents/*.py benchmarks/runner/*.py
node --check app.js
python -m http.server 7860
```

Then open `http://localhost:7860`.

## Deployment

For Hugging Face Static Space, keep the YAML metadata at the top of this README and commit the repository contents. If using GitHub Actions sync, set these GitHub secrets:

```text
HF_TOKEN = your Hugging Face write token
HF_SPACE = Coraaaa/awesome-agentic-ai-security
```


## v1.1 Update Review & PR Automation

This release adds a review-first maintenance loop:

```text
discover update -> triage -> recommend benchmark -> build evidence diff -> generate PR candidate -> human review -> merge -> sync to Hugging Face
```

Run locally:

```bash
python agents/auto_update_pipeline.py --offline
python agents/benchmark_recommender.py
python agents/evidence_diff_builder.py
python agents/pr_generator.py
python agents/update_review_report.py
```

GitHub workflow: `.github/workflows/auto-update-pr.yml`.

Automation policy: the pipeline can propose evidence and benchmark recommendations, but it must not automatically increase scores or ASI coverage depth without human approval and benchmark-backed evidence.
