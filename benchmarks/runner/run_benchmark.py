#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, time, urllib.request
from pathlib import Path
from typing import Any, Dict, List
from evaluators import evaluate_case
from mock_mcp_server import mock_target


def load_cases(path: Path) -> List[Dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("cases", data if isinstance(data, list) else [])


def post_json(url: str, payload: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {"status": str(resp.status)}


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    risk_breakdown: Dict[str, Dict[str, int]] = {}
    for r in results:
        for asi in r.get("asi", []):
            risk_breakdown.setdefault(asi, {"total": 0, "passed": 0, "failed": 0})
            risk_breakdown[asi]["total"] += 1
            risk_breakdown[asi]["passed" if r.get("passed") else "failed"] += 1
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else 0,
        "risk_breakdown": risk_breakdown,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run MCP / Agentic AI security benchmark cases.")
    ap.add_argument("--suite", default="benchmarks/mcp_security_benchmark_v01.jsonl")
    ap.add_argument("--mode", choices=["mock", "http"], default="mock")
    ap.add_argument("--target", help="HTTP endpoint for target mode")
    ap.add_argument("--output", default="benchmarks/results/example_report.json")
    args = ap.parse_args()

    cases = load_cases(Path(args.suite))
    results = []
    for case in cases:
        if args.mode == "mock":
            response = mock_target(case)
        else:
            if not args.target:
                raise SystemExit("--target is required in http mode")
            response = post_json(args.target, {"case": case})
        results.append(evaluate_case(case, response))

    report = {
        "benchmark": "mcp_security_benchmark_v01",
        "mode": args.mode,
        "target": args.target or "mock_target",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summarize(results),
        "results": results,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Report written to {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
