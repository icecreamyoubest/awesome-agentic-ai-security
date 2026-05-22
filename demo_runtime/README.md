# Demo MCP Runtime

This is a minimal, runnable MCP-style agent tool runtime used to turn the catalog into a real validation demo.

It demonstrates:

- Policy Enforcement Point before tool execution
- Tool descriptor poisoning detection
- Tool allowlisting and high-impact action approval
- Argument-level RCE pattern blocking
- OAuth/tool-output injection handling
- Audit log generation
- Benchmark-backed validation report generation

Run locally:

```bash
python -m demo_runtime.benchmark_runner
```

The generated report is written to:

```text
validation_reports/demo_runtime_validation_report.json
```
