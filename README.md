---
title: Awesome Agentic AI Security
emoji: 🛡️
colorFrom: yellow
colorTo: red
sdk: static
pinned: false
license: mit
---

<p align="center">
  <img src="https://img.shields.io/badge/Agentic%20AI-Security-red?style=for-the-badge" alt="Agentic AI Security" />
  <img src="https://img.shields.io/badge/MCP-Security-orange?style=for-the-badge" alt="MCP Security" />
  <img src="https://img.shields.io/badge/OWASP-GenAI%20Mapping-blue?style=for-the-badge" alt="OWASP GenAI Mapping" />
</p>

<h1 align="center">Awesome Agentic AI Security</h1>

<p align="center">
  A static, data-driven product catalog for comparing AI security, LLM security, agentic security, MCP security, guardrails, red-team, AI-SPM, observability, data security, and governance tools.
</p>

<p align="center">
  <a href="https://huggingface.co/spaces/Coraaaa/awesome-agentic-ai-security">
    <img src="https://img.shields.io/badge/🤗%20Open%20in-Hugging%20Face%20Spaces-yellow?style=for-the-badge" alt="Open in Hugging Face Spaces" />
  </a>
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT License" />
  </a>
  <a href="./CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/contributions-welcome-brightgreen?style=for-the-badge" alt="Contributions Welcome" />
  </a>
</p>

---

## Overview

**Awesome Agentic AI Security** is a lightweight web catalog for security architects, AI platform teams, red-team engineers, and governance owners who need to evaluate the rapidly growing AI security tooling landscape.

The project runs as a **Hugging Face Static Space** and uses only:

- `index.html`
- `styles.css`
- `app.js`
- JSON data files under `data/`
- optional benchmark files under `benchmarks/`

The product is intentionally static-first: no backend, no database, no server-side dependency, and easy to mirror into GitLab Pages, GitHub Pages, Hugging Face Spaces, or an internal security portal.

---

## Live Demo

| Entry point | Link |
|---|---|
| Hugging Face Space | [![Open in Hugging Face Spaces](https://img.shields.io/badge/🤗%20Launch-Space-yellow)](https://huggingface.co/spaces/Coraaaa/awesome-agentic-ai-security) |
| Local preview | `python -m http.server 7860` |
| Main app file | [`index.html`](./index.html) |
| Catalog data | [`data/tools.json`](./data/tools.json) |
| Benchmark data | [`benchmarks/mcp_security_benchmark_v01.jsonl`](./benchmarks/mcp_security_benchmark_v01.jsonl) |

---

## Product Value

This catalog helps teams answer practical architecture and procurement questions:

| Question | Supported view |
|---|---|
| Which tools cover agentic security risks? | ASI / Agentic OWASP mapping |
| Which tools are suitable for MCP security? | MCP security score and benchmark scaffold |
| Which tools support runtime guardrails? | Runtime and deployment filters |
| Which tools are better for red-team evaluation? | Red-team and benchmark-oriented dimensions |
| Which tools are enterprise-ready? | Compliance, observability, deployment, evidence, and maturity fields |
| Which controls map to AI lifecycle stages? | Lifecycle coverage and ASI × Lifecycle matrix |

---

## Key Features

### Catalog and Filtering

- 45-tool AI security catalog.
- Category filtering for guardrails, red-team, AI-SPM, MCP, RAG/memory security, observability, and governance.
- Lifecycle-stage filtering across develop, test, deploy, and operate phases.
- Framework mapping for LangChain/LangGraph, MCP, and other agentic runtimes.
- Deployment filters for cloud, self-hosted, and enterprise environments.

### Scoring and Comparison

- Lifecycle Coverage Score.
- Agentic Readiness Score.
- MCP Security Score.
- Supply-chain risk dimension.
- Compare mode for up to four tools.
- Evidence Confidence Score for transparent evaluation.

### Agentic Security Mapping

- OWASP Top 10 for Agentic Applications 2026 alignment.
- Agentic Security Initiative risk mapping.
- ASI Risk → Control → Tool matrix.
- ASI × Lifecycle architecture review matrix.
- ASI Coverage Depth from `0` to `3`.

### Evidence Hub

- Per-tool evidence records in `data/evidence.json`.
- Evidence-level labels for confidence tracking.
- Source-basis field for maintainability.
- Conservative scoring model to avoid overclaiming vendor capability.

### MCP Security Benchmark

The project includes a benchmark scaffold for MCP security review, covering test areas such as:

- descriptor poisoning
- OAuth response poisoning
- tool permission overreach
- sandbox escape
- remote code execution
- tool-output injection
- cross-agent trust abuse

---

## Target Users

| User | Main use case |
|---|---|
| AI security architect | Build an enterprise AI security reference architecture |
| Platform security team | Compare runtime guardrail and observability tools |
| Red-team engineer | Identify tooling for adversarial testing and benchmark execution |
| AI governance owner | Map tools to lifecycle controls and evidence levels |
| MCP / agent framework builder | Validate tool permissioning, sandboxing, and auditability |
| Procurement / vendor review team | Shortlist tools before POC and architecture review |

---

## Product Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│                        Static Web UI                            │
│                  index.html + styles.css + app.js               │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                         Data Layer                              │
│  data/tools.json                                                │
│  data/evidence.json                                             │
│  data/controls.json                                             │
│  data/incidents.json                                            │
│  data/reference_architectures.json                              │
│  data/schema.json                                               │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                     Validation and Benchmark                    │
│  scripts/validate_catalog.py                                    │
│  benchmarks/mcp_security_benchmark_v01.jsonl                    │
│  benchmarks/runner/run_benchmark.py                             │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────┐
│                         Deployment                              │
│  Hugging Face Static Space                                      │
│  GitLab Pages / GitHub Pages                                    │
│  Internal static hosting                                        │
└────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```text
.
├── README.md
├── LICENSE
├── index.html
├── styles.css
├── app.js
├── CONTRIBUTING.md
├── .github/
│   └── workflows/
│       ├── validate-catalog.yml
│       └── sync-to-huggingface.yml
├── benchmarks/
│   ├── mcp_security_benchmark_v01.jsonl
│   └── runner/
│       └── run_benchmark.py
├── data/
│   ├── tools.json
│   ├── evidence.json
│   ├── controls.json
│   ├── incidents.json
│   ├── reference_architectures.json
│   └── schema.json
└── scripts/
    └── validate_catalog.py
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd awesome-agentic-ai-security
```

### 2. Validate the catalog data

```bash
python -m json.tool data/tools.json > /tmp/tools.validated.json
python -m json.tool data/controls.json > /tmp/controls.validated.json
python scripts/validate_catalog.py
```

### 3. Run the static site locally

```bash
python -m http.server 7860
```

Open:

```text
http://localhost:7860
```

---

## Data Model

Each tool entry in `data/tools.json` follows a transparent, reviewable schema.

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
  "evidence_level": "official_vendor_docs",
  "url": "https://example.com",
  "docs": "https://docs.example.com",
  "maintainer_notes": "Use conservative scoring unless integration evidence is available."
}
```

---

## Scoring Guidance

All raw dimensions use a `1–5` scale.

| Score | Meaning |
|---:|---|
| 1 | Weak, indirect, experimental, or not a primary use case |
| 2 | Limited coverage or unclear production fit |
| 3 | Usable, partial, or integration-dependent |
| 4 | Strong coverage with public evidence |
| 5 | Default candidate with clear technical or operational evidence |

Scores are heuristic and community-maintained. They are designed to support shortlisting and architecture review, not vendor certification.

---

## Evidence Levels

Use these labels when updating or reviewing entries:

| Evidence level | Meaning |
|---|---|
| `official_owasp_landscape` | Appears in OWASP AI Security Solutions Landscape or ASI taxonomy-support material |
| `official_vendor_docs` | Explicit public vendor or project documentation |
| `community_verified` | Reproducible community verification through PR notes |
| `benchmark_backed` | Reproducible benchmark or test evidence |
| `inferred_mapping` | Reasonable inference from public capabilities; needs validation |

---

## MCP Benchmark Runner

Run the benchmark runner locally:

```bash
python benchmarks/runner/run_benchmark.py \
  --suite benchmarks/mcp_security_benchmark_v01.jsonl \
  --mode mock \
  --output benchmarks/results/example_report.json
```

Recommended future benchmark extensions:

- real MCP server adapter
- tool descriptor poisoning tests
- OAuth callback and response poisoning tests
- tool-output injection tests
- sandbox boundary tests
- cross-agent delegation and trust-abuse tests
- signed tool manifest verification

---

## Deploy to Hugging Face Spaces

This repository is compatible with Hugging Face Static Spaces.

### Required Space configuration

```yaml
sdk: static
license: mit
```

### Manual deployment

1. Create a new Hugging Face Space.
2. Select **Static** as the SDK.
3. Upload the repository files.
4. Hugging Face serves `index.html` automatically.

### GitHub / GitLab to Hugging Face sync

Create the following repository secrets:

| Secret | Example |
|---|---|
| `HF_TOKEN` | Hugging Face write token |
| `HF_SPACE` | `Coraaaa/awesome-agentic-ai-security` |

Then enable the sync workflow:

```text
.github/workflows/sync-to-huggingface.yml
```

---

## GitLab Pages Deployment

For GitLab Pages, add a `.gitlab-ci.yml` file:

```yaml
pages:
  stage: deploy
  script:
    - mkdir -p public
    - cp -r index.html styles.css app.js data benchmarks public/
    - cp README.md LICENSE CONTRIBUTING.md public/ || true
  artifacts:
    paths:
      - public
  only:
    - main
```

After the pipeline succeeds, GitLab will publish the static site from the `public/` directory.

---

## Roadmap

| Version | Focus |
|---|---|
| v0.6 | Evidence Hub, compare mode, lifecycle coverage, MCP benchmark scaffold |
| v0.7 | Executable MCP adapters and benchmark result viewer |
| v0.8 | Enterprise reference architecture templates and control export |
| v0.9 | Vendor submission workflow and signed evidence records |
| v1.0 | Stable public catalog with reproducible scoring and benchmark reports |

---

## Contribution Guide

Contributions should follow three rules:

1. **Do not overclaim vendor capability.** Use conservative scoring unless there is public documentation or reproducible evidence.
2. **Always include evidence.** Add `source_basis`, `evidence_level`, and notes for non-obvious mappings.
3. **Keep the catalog architecture-review friendly.** Prefer structured fields over long prose.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for contribution details.

---

## References and Attribution

This catalog references public OWASP GenAI Security Project materials, including:

- [OWASP AI Security Solutions Landscape Q2 2026](https://genai.owasp.org/ai-security-solutions-landscape/)
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
- [OWASP Agentic Security Initiative](https://genai.owasp.org/initiatives/agentic-security-initiative/)
- [OWASP GenAI Security Project](https://genai.owasp.org/)
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)

OWASP materials are licensed by OWASP under Creative Commons terms as stated in their documents. This repository is a community-maintained derived catalog and does **not** imply OWASP endorsement or vendor certification.

---

## Disclaimer

This is a community-maintained shortlist and scoring aid, not a certification, compliance attestation, or procurement decision. Before using any tool in production, verify vendor claims, product status, license terms, data handling, deployment topology, evidence quality, and integration depth.
