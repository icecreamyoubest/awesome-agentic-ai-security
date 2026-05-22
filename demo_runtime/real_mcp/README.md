
# Real MCP Gateway Demo

This module implements a lightweight MCP-compatible JSON-RPC demo with `initialize`, `tools/list`, `tools/register`, and `tools/call` methods.

It is designed to demonstrate security controls before tool execution:

- descriptor poisoning detection
- tool allowlist and schema checks
- high-impact action gating
- unsafe argument detection
- audit logging

Run:

```bash
python -m demo_runtime.real_mcp.benchmark_runner
```
