#!/usr/bin/env python3
"""Build reviewable evidence diffs from update intelligence outputs."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any, Dict, List
ROOT = Path(__file__).resolve().parents[1]

def load(path: str, default: Any) -> Any:
    p = ROOT / path
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def slug(s: str) -> str:
    return re.sub(r'[^a-z0-9]+','-', (s or 'unknown').lower()).strip('-')

def find_tool_id(tools: List[Dict[str,Any]], vendor: str, title: str) -> str:
    needle = f"{vendor} {title}".lower()
    best = ''
    for t in tools:
        hay = f"{t.get('id')} {t.get('name')} {t.get('org')}".lower()
        if t.get('id') and (str(t.get('id')).lower() in needle or str(t.get('name','')).lower() in needle or str(t.get('org','')).lower() in needle):
            return t.get('id')
        if not best and any(tok and tok in hay for tok in slug(vendor).split('-')):
            best = t.get('id','')
    return best or slug(vendor or title)

def build_diff(item: Dict[str,Any], tools: List[Dict[str,Any]], bench_recs: Dict[str,Any]) -> Dict[str,Any]:
    uid = item.get('id') or slug(item.get('title','candidate'))
    vendor = item.get('vendor') or item.get('vendor_name') or ''
    tool_id = find_tool_id(tools, vendor, item.get('title',''))
    asi = item.get('candidate_asi') or item.get('mapped_asi') or []
    rec = next((r for r in bench_recs.get('recommendations', []) if r.get('update_id') == uid), {})
    return {
        'id': f'diff-{uid}',
        'update_id': uid,
        'tool_id': tool_id,
        'change_type': 'evidence_added',
        'status': 'pending_review',
        'source_url': item.get('url',''),
        'source_title': item.get('title',''),
        'before': {'evidence_records': 'unchanged', 'score_change': 'none'},
        'after': {
            'proposed_evidence': {
                'type': 'official_vendor_docs' if item.get('url') else 'update_candidate',
                'source': vendor or item.get('source','unknown'),
                'claim': item.get('summary') or item.get('suggested_change') or item.get('title',''),
                'supports': asi,
                'confidence': 'medium',
                'url': item.get('url',''),
                'last_verified': item.get('detected_at') or item.get('created_at') or ''
            },
            'proposed_asi_depth_change': {a: 'review 1→2 only if official docs explicitly support the control' for a in asi},
            'recommended_benchmarks': rec.get('recommended_benchmarks', [])
        },
        'reason': 'Generated from automated update intelligence. Requires human review before modifying canonical evidence or scores.',
        'review_checklist': [
            'Source is official or independently verified',
            'Claim is not marketing-only',
            'ASI mapping is supported by text evidence',
            'No score increase unless benchmark-backed or implementation-verified',
            'Relevant benchmark recommendation exists for runtime/security claims'
        ]
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--triaged', default='data/updates/triaged_updates.json')
    ap.add_argument('--pending', default='data/updates/pending_updates.json')
    ap.add_argument('--tools', default='data/tools.json')
    ap.add_argument('--bench-recs', default='data/updates/benchmark_recommendations.json')
    ap.add_argument('--output', default='data/updates/evidence_diffs.json')
    args = ap.parse_args()
    items = load(args.triaged, {'triaged_updates': []}).get('triaged_updates', []) or load(args.pending, {'updates': []}).get('updates', [])
    tools = load(args.tools, {'tools': []}).get('tools', [])
    bench_recs = load(args.bench_recs, {'recommendations': []})
    diffs = [build_diff(i, tools, bench_recs) for i in items]
    out = {'meta': {'version':'v1.1','generated_by':'agents/evidence_diff_builder.py','count':len(diffs)}, 'diffs': diffs}
    p = ROOT / args.output; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Wrote {len(diffs)} evidence diffs to {p}")
if __name__ == '__main__': main()
