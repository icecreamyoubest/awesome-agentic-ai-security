#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_ASI = {f"ASI{i:02d}" for i in range(1, 11)}
VALID_DEPTH = {0, 1, 2, 3}


def load(path):
    with open(ROOT / path, encoding="utf-8") as f:
        return json.load(f)


def assert_true(cond, msg):
    if not cond:
        raise SystemExit(f"Validation failed: {msg}")


def main():
    tools = load("data/tools.json")
    controls = load("data/controls.json")
    evidence = load("data/evidence.json")
    incidents = load("data/incidents.json")
    arch = load("data/reference_architectures.json")
    bench_json = load("benchmarks/mcp_security_benchmark_v01.json")

    ids = set()
    for t in tools["tools"]:
        assert_true(t.get("id"), "tool missing id")
        assert_true(t["id"] not in ids, f"duplicate tool id {t['id']}")
        ids.add(t["id"])
        assert_true(t.get("name"), f"{t['id']} missing name")
        for k, v in t.get("scores", {}).items():
            assert_true(0 <= float(v) <= 5, f"{t['id']} score {k} out of range: {v}")
        for code in t.get("agentic_owasp", []):
            assert_true(code in VALID_ASI, f"{t['id']} invalid ASI code {code}")
        for code, depth in t.get("asi_coverage_depth", {}).items():
            assert_true(code in VALID_ASI, f"{t['id']} invalid ASI depth code {code}")
            assert_true(int(depth) in VALID_DEPTH, f"{t['id']} invalid ASI depth {code}: {depth}")
        conf = t.get("evidence_confidence", {})
        assert_true(0 <= float(conf.get("confidence_score", 0)) <= 5, f"{t['id']} invalid confidence score")

    for row in controls.get("control_matrix", []):
        assert_true(row.get("asi") in VALID_ASI, f"invalid control matrix ASI {row.get('asi')}")
    for row in controls.get("asi_lifecycle_matrix", []):
        assert_true(row.get("asi") in VALID_ASI, f"invalid lifecycle matrix ASI {row.get('asi')}")
    for tid, evs in evidence.get("tools", {}).items():
        assert_true(tid in ids, f"evidence for unknown tool {tid}")
        assert_true(isinstance(evs, list), f"evidence for {tid} must be a list")
    cases = bench_json.get("cases", [])
    assert_true(cases, "benchmark cases missing")
    case_ids = {c.get("id") for c in cases}
    for c in cases:
        assert_true(c.get("id"), "benchmark case missing id")
        for code in c.get("asi", []):
            assert_true(code in VALID_ASI, f"benchmark {c.get('id')} invalid ASI {code}")
        assert_true(c.get("pass_condition"), f"benchmark {c.get('id')} missing pass_condition")
    for inc in incidents.get("incidents", []):
        for code in inc.get("asi", []):
            assert_true(code in VALID_ASI, f"incident {inc.get('id')} invalid ASI {code}")
        for bid in inc.get("benchmark_cases", []):
            assert_true(bid in case_ids, f"incident {inc.get('id')} references unknown benchmark {bid}")
    assert_true(arch.get("architectures"), "reference architectures missing")
    print(f"Validation passed: {len(ids)} tools, {len(cases)} benchmark cases, {len(incidents.get('incidents', []))} incidents, {len(arch.get('architectures', []))} architectures")

if __name__ == "__main__":
    main()
