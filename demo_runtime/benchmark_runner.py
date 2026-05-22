from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any, Dict, List
from .runtime import DemoAgentRuntime, request_from_benchmark_case


def load_cases(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if p.suffix == ".jsonl":
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("cases", data if isinstance(data, list) else [])


def expected_block(case: Dict[str, Any]) -> bool:
    return case.get("expected_result", "block_or_quarantine") in {"block", "blocked", "block_or_quarantine"}


def run_demo_benchmark(
    suite: str = "benchmarks/mcp_security_benchmark_v01.jsonl",
    output: str = "validation_reports/demo_runtime_validation_report.json",
) -> Dict[str, Any]:
    runtime = DemoAgentRuntime()
    cases = load_cases(suite)
    results = []
    for case in cases:
        request = request_from_benchmark_case(case)
        response = runtime.execute(request)
        should_block = expected_block(case)
        passed = (not response.get("allowed", False)) if should_block else bool(response.get("allowed"))
        results.append({
            "case_id": case.get("id"),
            "attack_type": case.get("attack_type"),
            "asi": case.get("asi", case.get("risk", [])),
            "severity": case.get("severity"),
            "expected": "blocked" if should_block else "allowed",
            "observed": "allowed" if response.get("allowed") else "blocked",
            "passed": passed,
            "decision": response.get("decision"),
        })
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    by_asi: Dict[str, Dict[str, int]] = {}
    for r in results:
        for asi in r.get("asi", []):
            by_asi.setdefault(asi, {"total": 0, "passed": 0, "failed": 0})
            by_asi[asi]["total"] += 1
            by_asi[asi]["passed" if r["passed"] else "failed"] += 1
    report = {
        "report_type": "benchmark_backed_validation_report",
        "target": "demo_mcp_runtime",
        "benchmark_suite": Path(suite).name,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "total_cases": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 4) if total else 0,
            "asi_breakdown": by_asi,
        },
        "claim_to_test_to_evidence": {
            "claim": "The demo runtime enforces MCP/tool-call policy gates before tool execution.",
            "tests": [r["case_id"] for r in results],
            "evidence": ["validation_reports/demo_runtime_audit.jsonl", output],
            "status": "benchmark-backed demo evidence",
        },
        "results": results,
    }
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

if __name__ == "__main__":
    print(json.dumps(run_demo_benchmark(), indent=2))
