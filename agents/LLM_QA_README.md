# Grounded LLM Q&A Agent

This module adds retrieval-grounded Q&A on top of the catalog.

## Why this exists

A plain LLM can hallucinate vendor capabilities, OWASP mappings, scores, or tool links. The Q&A agent therefore uses this flow:

```text
Question
  -> retrieve from data/source_index.json
  -> build a bounded source context
  -> optional LLM call
  -> citation validation
  -> answer with source links
```

## Build the source index

```bash
python agents/build_source_index.py --output data/source_index.json
```

The generated index contains tool profiles, evidence records, control mappings, lifecycle mappings, incidents, reference architectures, and MCP benchmark cases.

## Offline extractive mode

```bash
python agents/grounded_qa_agent.py \
  --question "Which tools should I evaluate for MCP runtime security and ASI02 tool misuse?" \
  --provider none \
  --output outputs/qa_sample_answer.md \
  --json-output outputs/qa_sample_answer.json
```

No API key is required.

## LLM mode

Any OpenAI-compatible chat-completions endpoint can be used.

```bash
export OPENAI_API_KEY="..."
python agents/grounded_qa_agent.py \
  --question "Design a validation plan for a LangGraph + MCP + RAG customer support agent" \
  --provider openai-compatible \
  --model gpt-4o-mini \
  --output outputs/qa_llm_answer.md \
  --json-output outputs/qa_llm_answer.json \
  --fallback-on-uncited
```

For a custom endpoint:

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://your-gateway.example.com/v1"
python agents/grounded_qa_agent.py --question "..." --provider openai-compatible --model your-model
```

## Anti-hallucination controls

- The LLM receives only the retrieved source records.
- The system prompt forbids unindexed claims.
- Every non-trivial factual claim must cite a source ID such as `[S001]`.
- The CLI checks that cited source IDs were actually present in the retrieved context.
- `--fallback-on-uncited` replaces uncited LLM output with an extractive answer.
- If evidence is missing, the answer should say the evidence is insufficient.

## Source ID design

Source IDs are generated into `data/source_index.json`. They are stable as long as the indexed data order is stable. When the catalog changes, rebuild the index and commit it together with the data changes.
