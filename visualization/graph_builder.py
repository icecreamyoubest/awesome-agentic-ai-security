from __future__ import annotations

from typing import Any, Dict, List

RISK_COLOR = {
    "low": "#22c55e",
    "medium": "#f59e0b",
    "high": "#ef4444",
    "critical": "#7f1d1d",
}

TYPE_COLOR = {
    "agent": "#2563eb",
    "tool": "#64748b",
    "policy": "#7c3aed",
    "audit": "#059669",
    "memory": "#0891b2",
    "external": "#f97316",
    "attacker": "#dc2626",
}

HIGH_RISK_TOOLS = {"crm.refund", "email.send", "file.delete", "shell.run", "package.install", "unknown.admin_helper"}


def _agent_label(agent: Dict[str, Any]) -> str:
    return agent.get("name") or agent.get("id") or "agent"


def _tool_risk(tool: str) -> str:
    if tool in HIGH_RISK_TOOLS:
        return "high"
    if any(x in tool for x in ["send", "refund", "delete", "install", "shell"]):
        return "high"
    if any(x in tool for x in ["memory", "email"]):
        return "medium"
    return "low"


def build_graph(report: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Build agent/tool/policy/audit network graph data from demo report."""
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    for agent in report.get("agents", []):
        agent_id = agent.get("id")
        if not agent_id:
            continue
        nodes[agent_id] = {
            "id": agent_id,
            "label": _agent_label(agent),
            "type": "agent",
            "role": agent.get("role", ""),
            "trust_zone": agent.get("trust_zone", ""),
            "capabilities": agent.get("capabilities", []),
            "allowed_tools": agent.get("allowed_tools", []),
            "risk_level": "medium" if agent.get("allowed_tools") else "low",
            "asi": [],
            "color": TYPE_COLOR["agent"],
        }

    nodes["policy_engine"] = {
        "id": "policy_engine",
        "label": "Policy Engine / PEP-PDP",
        "type": "policy",
        "role": "Pre-execution policy gate for tool calls and high-impact actions.",
        "risk_level": "control",
        "asi": ["ASI02", "ASI03", "ASI09"],
        "color": TYPE_COLOR["policy"],
    }
    nodes["audit_log"] = {
        "id": "audit_log",
        "label": "Audit Log",
        "type": "audit",
        "role": "Evidence sink for agent messages, tool calls, decisions, and controls.",
        "risk_level": "control",
        "asi": ["ASI08", "ASI10"],
        "color": TYPE_COLOR["audit"],
    }

    edge_id = 1
    # Trust graph edges from scenario
    for edge in report.get("trust_graph", []):
        source = edge.get("from")
        target = edge.get("to")
        if not source or not target:
            continue
        edges.append({
            "id": f"trust_{edge_id}",
            "source": source,
            "target": target,
            "relation": "delegates_to",
            "label": edge.get("scope", "delegates"),
            "decision": "allow" if edge.get("signed") else "blocked",
            "signed": bool(edge.get("signed")),
            "mapped_asi": ["ASI07"],
            "reason": "Signed trust edge." if edge.get("signed") else "Unsigned trust edge.",
        })
        edge_id += 1

    # Tool nodes and call edges from flows
    tool_seen = set()
    for flow in report.get("flows", []):
        flow_id = flow.get("flow_id")
        for ev in flow.get("tool_events", []):
            agent = ev.get("agent")
            tool = ev.get("tool")
            decision = (ev.get("decision") or {}).get("decision", "unknown")
            asi = (ev.get("decision") or {}).get("asi", []) or []
            reason = (ev.get("decision") or {}).get("reason", "")
            if tool and tool not in tool_seen:
                risk = _tool_risk(tool)
                nodes[tool] = {
                    "id": tool,
                    "label": tool,
                    "type": "tool",
                    "role": "MCP-style tool exposed to agents.",
                    "risk_level": risk,
                    "asi": asi,
                    "color": RISK_COLOR.get(risk, TYPE_COLOR["tool"]),
                }
                tool_seen.add(tool)
            if agent and tool:
                edges.append({
                    "id": f"tool_{flow_id}_{ev.get('step')}_{tool}",
                    "source": agent,
                    "target": tool,
                    "relation": "calls_tool",
                    "label": decision,
                    "decision": decision,
                    "flow_id": flow_id,
                    "step": ev.get("step"),
                    "mapped_asi": asi,
                    "reason": reason,
                })
                edges.append({
                    "id": f"policy_{flow_id}_{ev.get('step')}_{tool}",
                    "source": tool,
                    "target": "policy_engine",
                    "relation": "checked_by_policy",
                    "label": decision,
                    "decision": decision,
                    "flow_id": flow_id,
                    "step": ev.get("step"),
                    "mapped_asi": asi,
                    "reason": reason,
                })
                edges.append({
                    "id": f"audit_{flow_id}_{ev.get('step')}_{tool}",
                    "source": "policy_engine",
                    "target": "audit_log",
                    "relation": "writes_audit",
                    "label": "audit",
                    "decision": "audit",
                    "flow_id": flow_id,
                    "step": ev.get("step"),
                    "mapped_asi": asi,
                })

        # Blocked forged A2A messages become red graph edges
        for msg in flow.get("messages", []):
            if msg.get("allowed") is False:
                source = msg.get("sender") or "unknown_agent"
                target = msg.get("recipient") or "unknown_target"
                if source not in nodes:
                    nodes[source] = {
                        "id": source,
                        "label": source.replace("_", " ").title(),
                        "type": "attacker",
                        "role": "Untrusted or forged peer agent.",
                        "risk_level": "high",
                        "asi": msg.get("mapped_asi", []),
                        "color": TYPE_COLOR["attacker"],
                    }
                edges.append({
                    "id": f"blocked_a2a_{flow_id}_{msg.get('step')}",
                    "source": source,
                    "target": target,
                    "relation": "blocked_delegation",
                    "label": "blocked",
                    "decision": "blocked",
                    "flow_id": flow_id,
                    "step": msg.get("step"),
                    "mapped_asi": msg.get("mapped_asi", []),
                    "reason": msg.get("reason", ""),
                })

    return {"nodes": list(nodes.values()), "edges": edges}
