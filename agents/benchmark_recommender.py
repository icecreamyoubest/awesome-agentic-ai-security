#!/usr/bin/env python3
"""Recommend benchmark cases for update candidates.

This module maps official-source update candidates to benchmark cases without
changing catalog scores. It is designed for review-first maintenance: detected
vendor claims become validation tasks, not automatic endorsements.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]

KEYWORD_TO_BENCH = [
    (re.compile(r"mcp|descriptor|manifest|tool schema|tool metadata", re.I), ["MCP-ASI04-001", "MCP-ASI02-004"]),
    (re.compile(r"oauth|token|credential|identity|permission|scope|delegat", re.I), ["MCP-ASI07-003", "MCP-ASI02-004"]),
    (re.compile(r"rce|code execution|sandbox|command|shell|package install", re.I), ["MCP-ASI05-002", "MCP-ASI04-009"]),
    (re.compile(r"rag|memory|vector|context|retrieval", re.I), ["RAG-ASI06-007"]),
    (re.compile(r"a2a|agent card|agent-card|inter-agent|registry|discovery", re.I), ["A2A-ASI07-006"]),
    (re.compile(r"human|approval|consent|hitl|trust|preview", re.I), ["HITL-ASI09-010"]),
    (re.compile(r"loop|rate|cascade|cost|budget|fan-out", re.I), ["MCP-ASI08-008"]),
    (re.compile(r"prompt injection|tool output|indirect", re.I), ["MCP-ASI01-005"]),
]
ASI_TO_BENCH = {
    "ASI01": ["MCP-ASI01-005"],
    "ASI02": ["MCP-ASI02-004"],
    "ASI03": ["MCP-ASI07-003"],
    "ASI04": ["MCP-ASI04-001", "MCP-ASI04-009"],
    "ASI05": ["MCP-ASI05-002"],
    "ASI06": ["RAG-ASI06-007"],
    "ASI07": ["A2A-ASI07-006", "MCP-ASI07-003"],
    "ASI08": ["MCP-ASI08-008"],
    "ASI09": ["HITL-ASI09-010"],
    "ASI10": ["A2A-ASI07-006"],
}

def load_json(path: str, default: Any) -> Any:
    p = ROOT / path
    if not p.exists(): return default
    return json.loads(p.read_text(encoding='utf-8'))

def text_of(item: Dict[str, Any]) -> str:
    parts = []
    for k in ("title","summary","suggested_change","vendor","vendor_name","priority"):
        if item.get(k): parts.append(str(item[k]))
    for k in ("candidate_features","signals","candidate_asi","mapped_asi"):
        v = item.get(k)
        if isinstance(v, list): parts.extend(map(str, v))
    return " ".join(parts)

def recommend_for_update(item: Dict[str, Any], benchmark_ids: Set[str]) -> Dict[str, Any]:
    text = text_of(item)
    recs: List[str] = []
    reasons: List[str] = []
    for pattern, ids in KEYWORD_TO_BENCH:
        if pattern.search(text):
            for bid in ids:
                if bid in benchmark_ids and bid not in recs: recs.append(bid)
            reasons.append(f"Matched keyword pattern: {pattern.pattern}")
    for asi in item.get('candidate_asi') or item.get('mapped_asi') or []:
        for bid in ASI_TO_BENCH.get(asi, []):
            if bid in benchmark_ids and bid not in recs: recs.append(bid)
    if not recs:
        recs = ["MCP-ASI02-004"] if "MCP-ASI02-004" in benchmark_ids else []
        reasons.append("No specific pattern matched; default to tool-misuse validation if available.")
    return {
        "id": f"benchrec-{item.get('id','unknown')}",
        "update_id": item.get('id',''),
        "title": item.get('title',''),
        "vendor": item.get('vendor') or item.get('vendor_name',''),
        "recommended_benchmarks": recs,
        "validation_goal": "Validate whether the detected update changes runtime protection, MCP/A2A trust, tool permissions, identity handling, or memory safety before changing catalog scores.",
        "reasons": reasons,
        "status": "needs_human_review"
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--triaged', default='data/updates/triaged_updates.json')
    ap.add_argument('--pending', default='data/updates/pending_updates.json')
    ap.add_argument('--benchmarks', default='benchmarks/mcp_security_benchmark_v01.json')
    ap.add_argument('--output', default='data/updates/benchmark_recommendations.json')
    args = ap.parse_args()
    triaged = load_json(args.triaged, {'triaged_updates': []}).get('triaged_updates', [])
    pending = load_json(args.pending, {'updates': []}).get('updates', [])
    items = triaged or pending
    benches = load_json(args.benchmarks, {'cases': []}).get('cases', [])
    bench_ids = {c.get('id') for c in benches}
    recs = [recommend_for_update(i, bench_ids) for i in items]
    out = {'meta': {'version':'v1.1', 'generated_by':'agents/benchmark_recommender.py', 'count':len(recs)}, 'recommendations': recs}
    p = ROOT / args.output; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Wrote {len(recs)} benchmark recommendations to {p}")
if __name__ == '__main__': main()
