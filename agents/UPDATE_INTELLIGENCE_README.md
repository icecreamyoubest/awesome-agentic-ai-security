# Automated Update Intelligence Pipeline

This pipeline watches official sources for tool releases, top-company AI security feature changes, security incidents, roadmap signals, and standards updates. It creates reviewable JSON artifacts only; it does not mutate tool scores automatically.

## Offline smoke test

```bash
python agents/auto_update_pipeline.py --offline
```

## Network run

```bash
python agents/auto_update_pipeline.py --network --max-per-source 5
```

## Outputs

- `data/updates/pending_updates.json`
- `data/updates/triaged_updates.json`
- `data/updates/roadmap.json`
- `data/updates/catalog_patch_suggestions.json`
- `data/updates/auto_update_status.json`

## Human review rule

The monitor may detect candidate updates from official sources, but changes to `tools.json`, `evidence.json`, score fields, or benchmark cases should be made only after review.
