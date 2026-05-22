from __future__ import annotations

from typing import Any, Dict, List


def build_trust_graph(report: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    nodes = []
    for agent in report.get("agents", []):
        nodes.append({
            "id": agent.get("id"),
            "label": agent.get("name", agent.get("id")),
            "trust_zone": agent.get("trust_zone", ""),
            "type": "agent",
            "capabilities": agent.get("capabilities", []),
        })
    edges = []
    i = 1
    for edge in report.get("trust_graph", []):
        edges.append({
            "id": f"trust_edge_{i}",
            "source": edge.get("from"),
            "target": edge.get("to"),
            "scope": edge.get("scope"),
            "signed": bool(edge.get("signed")),
            "decision": "trusted" if edge.get("signed") else "untrusted",
        })
        i += 1
    # add blocked untrusted edges discovered during attack flows
    for flow in report.get("flows", []):
        for msg in flow.get("messages", []):
            if msg.get("allowed") is False:
                edges.append({
                    "id": f"blocked_{flow.get('flow_id')}_{msg.get('step')}",
                    "source": msg.get("sender"),
                    "target": msg.get("recipient"),
                    "scope": msg.get("intent"),
                    "signed": bool(msg.get("signed")),
                    "decision": "blocked",
                    "reason": msg.get("reason", ""),
                    "mapped_asi": msg.get("mapped_asi", []),
                })
    return {"nodes": nodes, "edges": edges}
