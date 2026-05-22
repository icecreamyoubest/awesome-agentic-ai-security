# Update Review & PR Automation

This v1.1 layer closes the maintenance loop for the Agentic AI Security catalog.

Pipeline:

```text
update_monitor -> update_triage_agent -> benchmark_recommender -> evidence_diff_builder -> pr_generator -> human review PR
```

Key principle: automated updates generate **review candidates**, not canonical score changes. Maintainers must verify official sources, ASI mapping, and benchmark evidence before merging.

Manual run:

```bash
python agents/auto_update_pipeline.py --offline
python agents/benchmark_recommender.py
python agents/evidence_diff_builder.py
python agents/pr_generator.py
python agents/update_review_report.py
```

GitHub Action:

```text
.github/workflows/auto-update-pr.yml
```

The workflow creates a PR using generated evidence diffs and benchmark recommendations.
