#!/usr/bin/env python3
"""Tool claim verifier.

Decomposes a tool claim into ASI risks, required evidence, suggested benchmark
cases, and current evidence status from the catalog.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str) -> Dict[str, Any]:
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def _norm(s: str) -> str:
    return (s or "").lower().replace("-", " ").replace("_", " ")


def find_tool(tools: List[Dict[str, Any]], name_or_id: str) -> Dict[str, Any] | None:
    q = _norm(name_or_id)
    for t in tools:
        if q in {_norm(t.get("id", "")), _norm(t.get("name", ""))}:
            return t
    for t in tools:
        if q in _norm(t.get("name", "")) or q in _norm(t.get("id", "")):
            return t
    return None


def match_claim_templates(claim: str, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    q = _norm(claim)
    scored = []
    for c in templates:
        hay = _norm(" ".join([c.get("title", ""), c.get("claim", ""), " ".join(c.get("required_evidence", []))]))
        score = sum(1 for tok in q.split() if len(tok) > 2 and tok in hay)
        # Boost common domains
        for term in ["mcp", "runtime", "red", "memory", "rag", "identity", "coding", "rce", "sandbox"]:
            if term in q and term in hay:
                score += 3
        if score:
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:3]]


def verify_claim(tool_name: str, claim: str) -> Dict[str, Any]:
    tools_doc = load_json("data/tools.json")
    evidence_doc = load_json("data/evidence.json")
    claims_doc = load_json("data/claims.json")
    benchmark_doc = load_json("benchmarks/mcp_security_benchmark_v01.json")
    tools = tools_doc.get("tools", [])
    tool = find_tool(tools, tool_name)
    if not tool:
        raise SystemExit(f"Unknown tool: {tool_name}")
    matched = match_claim_templates(claim, claims_doc.get("claims", []))
    ev = evidence_doc.get("tools", {}).get(tool["id"], [])
    existing_evidence_types = sorted({x.get("type", "unknown") for x in ev})
    mapped_asi = sorted(set(sum([m.get("mapped_asi", []) for m in matched], [])) | set(tool.get("agentic_owasp", [])))
    validation_tests = []
    required = []
    for m in matched:
        validation_tests.extend(m.get("validation_tests", []))
        required.extend(m.get("required_evidence", []))
    validation_tests = list(dict.fromkeys(validation_tests))
    required = list(dict.fromkeys(required))
    cases = {c["id"]: c for c in benchmark_doc.get("cases", [])}
    missing_evidence = []
    if not ev:
        missing_evidence.append("No evidence record in data/evidence.json")
    if "official_vendor_docs" not in existing_evidence_types:
        missing_evidence.append("Attach official vendor documentation for this claim")
    if "benchmark_backed" not in existing_evidence_types:
        missing_evidence.append("Run benchmark cases and attach result evidence")
    current_status = "needs_validation"
    conf = tool.get("evidence_confidence", {}).get("confidence_score", 0)
    if conf >= 4 and not missing_evidence:
        current_status = "high_confidence"
    elif ev:
        current_status = "partial_evidence"
    return {
        "tool": {"id": tool["id"], "name": tool["name"], "org": tool.get("org")},
        "claim": claim,
        "matched_claim_templates": [{"id": m["id"], "title": m["title"]} for m in matched],
        "mapped_asi": mapped_asi,
        "required_evidence": required,
        "existing_evidence_types": existing_evidence_types,
        "current_evidence_confidence": tool.get("evidence_confidence", {}),
        "current_status": current_status,
        "missing_evidence": missing_evidence,
        "validation_tests": [
            {"id": tid, "title": cases.get(tid, {}).get("title", tid), "asi": cases.get(tid, {}).get("asi", [])}
            for tid in validation_tests
        ],
        "next_step": "Run the suggested benchmark cases and add benchmark_backed evidence before upgrading the claim confidence."
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Verify a vendor/tool claim against catalog evidence and benchmark tests")
    p.add_argument("--tool", required=True)
    p.add_argument("--claim", required=True)
    p.add_argument("--output", default="")
    args = p.parse_args()
    result = verify_claim(args.tool, args.claim)
    out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
