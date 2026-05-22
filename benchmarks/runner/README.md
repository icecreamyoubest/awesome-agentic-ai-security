# MCP Security Benchmark Runner v0.1

This runner executes the benchmark seed cases in mock mode or sends them to a target HTTP endpoint.
It is intentionally lightweight so reviewers can adapt it for MCP gateways, agent runtimes, or CI pipelines.

```bash
python benchmarks/runner/run_benchmark.py \
  --suite benchmarks/mcp_security_benchmark_v01.jsonl \
  --mode mock \
  --output benchmarks/results/example_report.json
```

HTTP mode expects a target endpoint that accepts JSON POST requests and returns a JSON response with one of:
`decision`, `blocked`, `allowed`, `quarantined`, `requires_approval`, or `status`.
