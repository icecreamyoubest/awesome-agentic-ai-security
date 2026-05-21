# Contributing

Thanks for improving **Awesome Agentic AI Security**.

## What this catalog accepts

Contributions should improve at least one of these areas:

- New AI / LLM / agentic / MCP security tool entry
- Better evidence for an existing score
- OWASP Agentic Top 10 / ASI mapping corrections
- Agentic SecOps lifecycle mapping corrections
- MCP benchmark test cases
- Broken link or vendor-status updates
- Better control mapping or scoring methodology

## Evidence policy

Use conservative scoring. Prefer one of these evidence levels:

| Evidence level | Meaning |
|---|---|
| `official_owasp_landscape` | Appears in OWASP AI Security Solutions Landscape or ASI taxonomy-support material |
| `official_vendor_docs` | Vendor or project documentation explicitly claims the capability |
| `community_verified` | A contributor verified it with reproducible notes |
| `benchmark_backed` | A reproducible benchmark or test-harness result exists |
| `inferred_mapping` | Reasonable inference; needs validation |

## Adding a tool

Edit `data/tools.json`. Required fields include:

- `id`, `name`, `org`, `vendor_type`, `category`, `description`
- `frameworks`, `deployment`, `targets`
- `scores`, `agentic_scores`, `mcp_scores`
- `agentic_owasp`, `lifecycle_stages`
- `source_basis`, `evidence_level`, `maintainer_notes`

Keep raw scores on a 0–5 scale.

## Valid ASI codes

Only these are valid:

`ASI01`, `ASI02`, `ASI03`, `ASI04`, `ASI05`, `ASI06`, `ASI07`, `ASI08`, `ASI09`, `ASI10`.

## Valid lifecycle stages

Use the keys defined in `data/tools.json > meta.lifecycle_stages`:

- `scope_plan`
- `augment_finetune_data`
- `develop_experiment`
- `test_evaluate`
- `release`
- `deploy`
- `operate`
- `monitor`
- `govern`

## Local validation

```bash
python -m json.tool data/tools.json > /tmp/tools.validated.json
python -m json.tool data/controls.json > /tmp/controls.validated.json
python scripts/validate_catalog.py
python -m http.server 7860
```

Open `http://localhost:7860`.

## Pull request checklist

- [ ] JSON parses successfully
- [ ] No duplicate tool IDs
- [ ] ASI codes are valid
- [ ] Lifecycle stages are valid
- [ ] Scores are between 0 and 5
- [ ] Evidence level and maintainer notes are included
- [ ] README or methodology updated if scoring logic changes
