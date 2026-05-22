---
title: Awesome Agentic AI Security
emoji: 🛡️
colorFrom: yellow
colorTo: red
sdk: gradio
app_file: app.py
pinned: false
license: mit
---

# Awesome Agentic AI Security

## v1.3 additions — Full Lifecycle Validation Platform

This release connects the previous catalog, grounded Q&A, solution advisor, real demo runtime, benchmark runner, evidence review, and update intelligence into a single end-to-end lifecycle.

The new default flow is:

```text
Start Here
→ Full Lifecycle
→ Scenario risk mapping
→ Tool recommendation
→ Reference architecture
→ Runtime policy gate
→ MCP benchmark validation
→ Tool claim / evidence review
→ Continuous update / PR review
→ Exportable lifecycle report
```

### New capabilities

- **Start Here tab**: guides users into the golden path demo.
- **Full Lifecycle tab**: runs the complete scenario-to-evidence workflow from the WebUI.
- **Lifecycle Orchestrator**: `agents/lifecycle_orchestrator.py` composes risk mapping, architecture generation, runtime smoke tests, benchmark validation, claim verification, and update review.
- **Lifecycle Config**: `data/lifecycle_config.json` defines lifecycle stages, inputs, outputs, objectives, and recommended checks.
- **Exportable lifecycle reports**: generated under `outputs/lifecycle_run/`.
- **Demo Evidence Report**: the WebUI can export a concise evidence report for the golden path demo.
- **Fixed tools.json compatibility**: Gradio now supports both list-style and `{ "tools": [...] }` catalog formats.

### Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:7860
```

### Run the full lifecycle from CLI

```bash
python agents/lifecycle_orchestrator.py   --scenario scenario_templates/enterprise_copilot_with_rag.json   --output-dir outputs/lifecycle_run
```

### Run the benchmark without the UI

```bash
python -m demo_runtime.benchmark_runner
```

### Generated validation evidence

```text
outputs/lifecycle_run/end_to_end_lifecycle_report.md
outputs/lifecycle_run/end_to_end_lifecycle_report.json
validation_reports/demo_runtime_validation_report.json
validation_reports/demo_runtime_audit.jsonl
outputs/demo_evidence_report.md
```

### Suggested product path

Use the **Full Lifecycle** tab first. It gives the cleanest demonstration of the platform value:

1. Select the enterprise MCP + RAG scenario.
2. Run the lifecycle.
3. Review the ASI risk map and recommended stack.
4. Review runtime policy decisions.
5. Review benchmark-backed validation evidence.
6. Export the lifecycle report.

---



## v1.4 Full Validation Platform additions

- Validation Status Board with validated / partially validated / evidence-only states.
- Real MCP JSON-RPC gateway demo with descriptor validation and policy-gated tool calls.
- LLM Guard adapter smoke test with deterministic fallback scanners for demo reliability.
- Enterprise Architecture Review Pack export.
- Claim → Test → Evidence mapping for reviewable score updates.

Run additional validations:

```bash
python -m demo_runtime.real_mcp.benchmark_runner
python adapters/adapter_test_runner.py
python agents/enterprise_report_pack.py --scenario scenario_templates/enterprise_copilot_with_rag.json
```

## v1.5 — Real MCP Server Risk Assessment

This release adds a schema-only risk assessment connector for real MCP-compatible servers and Hugging Face / Gradio-style Spaces.

### WebUI

Open the Gradio app and use:

```text
12. Real MCP Server Assessment
```

Supported inputs:

```text
demo://local
https://huggingface.co/spaces/OWNER/SPACE
https://your-mcp-server.example.com/mcp
```

Discovery modes:

- `auto`: try HTTP JSON-RPC MCP-style discovery, then Gradio config discovery.
- `jsonrpc`: call `initialize` and `tools/list` on an MCP-style JSON-RPC endpoint.
- `gradio_config`: inspect `/config` from a Gradio / Hugging Face Space runtime URL.

### CLI

```bash
python -m real_mcp_assessment.assess_mcp_server --server-url demo://local
python -m real_mcp_assessment.assess_mcp_server --server-url https://huggingface.co/spaces/OWNER/SPACE --mode gradio_config
python -m real_mcp_assessment.assess_mcp_server --server-url https://your-mcp-server.example.com/mcp --mode jsonrpc
```

### Safety boundary

The default assessment is **schema-only**. It lists tools, parses descriptors and input schemas, maps risk signals to OWASP ASI categories, recommends controls and benchmark cases, and exports Markdown/JSON reports. It does **not** execute third-party MCP tools by default. Controlled execution should only be used against systems you own or are explicitly authorized to test.

Generated reports are written to:

```text
outputs/mcp_assessments/
```

## v1.6 Real MCP Endpoint Assessment Improvements

The Real MCP Server Assessment connector now supports generic JSON-RPC MCP endpoints, Hugging Face / Gradio MCP endpoints, Hugging Face Space URLs, Gradio `/config` and `/gradio_api/info` fallbacks, and documentation-reference URLs such as OpenAI's MCP and connectors guide. Discovery failures are reported as `inconclusive` with `risk_score: null` to avoid false low-risk results.
