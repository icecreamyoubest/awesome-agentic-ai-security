#!/usr/bin/env python3
"""Answer audit utilities for grounded Q&A outputs.

This module checks whether an answer only cites source IDs that were retrieved
from the local `data/source_index.json` and provides a lightweight confidence
assessment for UI display and CI-friendly JSON output.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

try:
    from .retriever import SourceRetriever, load_index
except ImportError:
    from retriever import SourceRetriever, load_index

ROOT = Path(__file__).resolve().parents[1]
CITATION_RE = re.compile(r"\[S\d{3}\]")


def extract_citations(answer: str) -> List[str]:
    return sorted({m.group(0).strip("[]") for m in CITATION_RE.finditer(answer or "")})


def audit_answer(question: str, answer: str, top_k: int = 10, index_path: str = "data/source_index.json") -> Dict[str, Any]:
    index = load_index(index_path)
    retriever = SourceRetriever(index)
    sources = retriever.search(question, top_k=top_k)
    retrieved_ids = {s["source_id"] for s in sources}
    used = extract_citations(answer)
    unsupported = [sid for sid in used if sid not in retrieved_ids]
    missing_citations = not used
    evidence_scores = []
    for src in sources:
        meta = src.get("metadata", {}) if isinstance(src.get("metadata"), dict) else {}
        conf = meta.get("evidence_confidence", {}) if isinstance(meta.get("evidence_confidence"), dict) else {}
        if "confidence_score" in conf:
            try:
                evidence_scores.append(float(conf["confidence_score"]))
            except Exception:
                pass
    avg_conf = round(sum(evidence_scores) / len(evidence_scores), 2) if evidence_scores else None
    if missing_citations or unsupported:
        confidence = "low"
    elif avg_conf is not None and avg_conf >= 3.5:
        confidence = "medium-high"
    else:
        confidence = "medium"
    return {
        "question": question,
        "retrieved_sources": [
            {
                "source_id": s["source_id"],
                "title": s.get("title"),
                "type": s.get("type"),
                "object_id": s.get("object_id"),
                "url": s.get("url") or s.get("local_path"),
                "score": s.get("score"),
            }
            for s in sources
        ],
        "used_citations": used,
        "unsupported_citations": unsupported,
        "missing_citations": missing_citations,
        "evidence_confidence_average": avg_conf,
        "confidence": confidence,
        "recommended_validation": suggest_validation(question, sources),
    }


def suggest_validation(question: str, sources: List[Dict[str, Any]]) -> List[str]:
    text = " ".join([question] + [s.get("text", "") for s in sources]).lower()
    suggestions = []
    if "mcp" in text or "tool" in text:
        suggestions += ["Run MCP-ASI04-001 descriptor poisoning", "Run MCP-ASI02-004 over-permissioned tool test"]
    if "oauth" in text or "identity" in text or "privilege" in text:
        suggestions += ["Run MCP-ASI07-003 OAuth response poisoning", "Review per-action authorization evidence"]
    if "memory" in text or "rag" in text or "vector" in text:
        suggestions += ["Run RAG-ASI06-007 cross-tenant memory bleed test", "Check memory provenance and isolation evidence"]
    if "code" in text or "rce" in text or "coding" in text:
        suggestions += ["Run MCP-ASI05-002 RCE-style payload", "Check sandbox and egress controls"]
    return list(dict.fromkeys(suggestions))[:8]


def main() -> None:
    p = argparse.ArgumentParser(description="Audit a grounded answer against retrieved source context")
    p.add_argument("--question", required=True)
    p.add_argument("--answer-file", required=True)
    p.add_argument("--output", default="")
    p.add_argument("--top-k", type=int, default=10)
    args = p.parse_args()
    answer = Path(args.answer_file).read_text(encoding="utf-8")
    result = audit_answer(args.question, answer, top_k=args.top_k)
    out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
