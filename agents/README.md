# Solution & Tool Validation Agent

This module turns the static catalog into a deterministic advisor for agentic AI security solution design.

## Design principles

- **Rule engine decides risk, coverage, and scoring.**
- **Evidence store supports claims.**
- **Benchmark runner validates controls.**
- **LLMs, if added later, should only parse requirements or polish reports.**

## Run

```bash
python agents/solution_validator_agent.py \
  --scenario examples/mcp_rag_agent_scenario.json \
  --output outputs/mcp_rag_agent_solution_report.md \
  --json-output outputs/mcp_rag_agent_solution_report.json
```

## Inputs

Scenario JSON fields:

```json
{
  "name": "MCP RAG customer support agent",
  "description": "...",
  "frameworks": ["LangGraph", "MCP"],
  "architecture": ["rag", "mcp", "tool_use", "long_term_memory"],
  "lifecycle_stage": ["develop_experiment", "test_evaluate", "deploy"],
  "risk_focus": ["ASI01", "ASI02"],
  "constraints": {"self_host": true, "enterprise_ready": true},
  "external_integrations": ["CRM", "Email"],
  "high_impact_actions": ["refund", "email_send"]
}
```

## Outputs

- Markdown solution validation report
- Structured JSON containing risk mapping, recommendation scores, benchmark plan, and evidence checks

## v0.8 Grounded Q&A Agent

Build the source index:

```bash
python agents/build_source_index.py --output data/source_index.json
```

Ask without an LLM:

```bash
python agents/grounded_qa_agent.py \
  --question "Which tools should I evaluate for MCP runtime security and ASI02 tool misuse?" \
  --provider none \
  --output outputs/qa_sample_answer.md
```

Ask with an OpenAI-compatible LLM:

```bash
export OPENAI_API_KEY="..."
python agents/grounded_qa_agent.py \
  --question "Design a validation plan for a LangGraph + MCP + RAG customer support agent" \
  --provider openai-compatible \
  --model gpt-4o-mini \
  --fallback-on-uncited
```

The LLM can explain and synthesize, but it must cite retrieved source IDs. The deterministic retriever and citation audit remain the source-of-truth layer.
