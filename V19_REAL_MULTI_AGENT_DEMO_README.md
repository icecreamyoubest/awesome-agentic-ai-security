# v1.9 Real Multi-Agent Demo

This version adds an executable multi-agent enterprise workflow demo.

## Scenario

A customer refund workflow with five agents:

- Coordinator Agent: plans and delegates tasks.
- Support Agent: performs CRM lookup and creates a support ticket.
- Finance Agent: prepares and executes refund only after approval.
- Compliance Agent: checks policy/memory and approval conditions.
- Notification Agent: drafts customer email.

## Security controls demonstrated

- Signed A2A trust graph and delegation checks.
- MCP-style tool calls through a runtime PEP/PDP.
- Tool allowlist and typed tool registry.
- Tool descriptor poisoning defense.
- High-impact action human approval.
- Tool-output injection isolation.
- Scope mismatch detection.
- Audit log generation.

## Attack flows covered

- Forged admin/helper agent card.
- Tool output injection from CRM/memory-like content.
- Unapproved refund attempt.
- Delegated token scope mismatch.

## Run CLI

```bash
python -m multi_agent_demo.run_multi_agent_demo \
  --scenario examples/multi_agent_refund_scenario.json \
  --output-dir outputs/multi_agent_demo
```

## Output

- `outputs/multi_agent_demo/multi_agent_demo_report.md`
- `outputs/multi_agent_demo/multi_agent_demo_report.json`
- `outputs/multi_agent_demo/multi_agent_tool_audit.jsonl`

## WebUI

Open the Gradio app and use:

`13. Real Multi-Agent Demo`

