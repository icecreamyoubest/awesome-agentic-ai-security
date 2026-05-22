#!/usr/bin/env python3
"""Generate a human-readable update review report."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def load(path, default):
    p = ROOT / path
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='outputs/update_review_report.md')
    args = ap.parse_args()
    status = load('data/updates/auto_update_status.json', {})
    recs = load('data/updates/benchmark_recommendations.json', {'recommendations': []}).get('recommendations', [])
    diffs = load('data/updates/evidence_diffs.json', {'diffs': []}).get('diffs', [])
    prs = load('data/updates/pr_candidates.json', {'candidates': []}).get('candidates', [])
    board = load('data/roadmap_board.json', {'columns': {}}).get('columns', {})
    lines = ['# Update Review Report', '', f"- Last update mode: `{status.get('mode','unknown')}`", f"- Pending updates: `{status.get('pending_updates', 0)}`", f"- Triaged updates: `{status.get('triaged_updates', 0)}`", f"- Benchmark recommendations: `{len(recs)}`", f"- Evidence diffs: `{len(diffs)}`", f"- PR candidates: `{len(prs)}`", '']
    lines.append('## PR Candidates')
    for p in prs[:10]: lines.append(f"- `{p.get('tool_id')}` — {p.get('title')} ({p.get('status')})")
    lines.append('\n## Benchmark Recommendations')
    for r in recs[:10]: lines.append(f"- `{r.get('update_id')}` → {', '.join(r.get('recommended_benchmarks', []))}")
    lines.append('\n## Roadmap Board')
    for col, items in board.items():
        lines.append(f"### {col.replace('_',' ').title()}")
        for item in items: lines.append(f"- {item.get('title')} — `{item.get('status')}`")
    out = ROOT / args.output; out.parent.mkdir(parents=True, exist_ok=True); out.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Wrote report to {out}")
if __name__ == '__main__': main()
