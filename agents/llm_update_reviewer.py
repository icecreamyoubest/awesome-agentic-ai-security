#!/usr/bin/env python3
"""Optional LLM-assisted update reviewer.

Default mode is deterministic and offline. If --provider openai-compatible is
used, this script asks an LLM to summarize relevance, but it never mutates
scores or canonical evidence.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]

def load(path: str, default: Any) -> Any:
    p = ROOT / path
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def rule_review(item):
    text = ' '.join(str(item.get(k,'')) for k in ['title','summary','suggested_change','vendor','vendor_name']).lower()
    relevant = any(k in text for k in ['agent','mcp','guardrail','security','prompt injection','red team','runtime','oauth','rce'])
    asi = item.get('candidate_asi') or item.get('mapped_asi') or []
    return {
        'id': f"review-{item.get('id','unknown')}",
        'update_id': item.get('id',''),
        'is_relevant': bool(relevant or asi),
        'reason': 'Matched AI-security / agentic-security keywords or ASI mapping.' if relevant or asi else 'No strong security relevance detected by rule review.',
        'supported_claims': [{'claim': item.get('summary') or item.get('title',''), 'source_url': item.get('url',''), 'mapped_asi': asi, 'confidence': 'medium' if item.get('url') else 'low'}],
        'unsupported_claims': [],
        'recommended_action': 'add evidence diff only; do not update score until benchmarked' if relevant or asi else 'reject or keep as low-priority watch item'
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--triaged', default='data/updates/triaged_updates.json')
    ap.add_argument('--pending', default='data/updates/pending_updates.json')
    ap.add_argument('--output', default='data/updates/llm_update_reviews.json')
    args = ap.parse_args()
    items = load(args.triaged, {'triaged_updates': []}).get('triaged_updates', []) or load(args.pending, {'updates': []}).get('updates', [])
    reviews = [rule_review(i) for i in items]
    out = {'meta': {'version':'v1.1','mode':'rule_based_default','count':len(reviews)}, 'reviews': reviews}
    p = ROOT / args.output; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Wrote {len(reviews)} reviews to {p}")
if __name__ == '__main__': main()
