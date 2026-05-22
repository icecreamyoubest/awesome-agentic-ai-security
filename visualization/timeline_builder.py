from __future__ import annotations

from typing import Any, Dict, List


def build_timeline(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    idx = 1
    for flow in report.get("flows", []):
        flow_id = flow.get("flow_id")
        flow_name = flow.get("flow_name")
        for msg in flow.get("messages", []):
            decision = "allowed" if msg.get("allowed") else "blocked"
            events.append({
                "global_step": idx,
                "flow_id": flow_id,
                "flow_name": flow_name,
                "local_step": msg.get("step"),
                "event_type": "a2a_message",
                "actor": msg.get("sender"),
                "target": msg.get("recipient"),
                "action": msg.get("intent"),
                "decision": decision,
                "status": decision,
                "reason": msg.get("reason", ""),
                "mapped_asi": msg.get("mapped_asi", []),
                "raw": msg,
            })
            idx += 1
        for ev in flow.get("tool_events", []):
            d = ev.get("decision") or {}
            decision = d.get("decision") or ("allowed" if ev.get("allowed") else "blocked")
            events.append({
                "global_step": idx,
                "flow_id": flow_id,
                "flow_name": flow_name,
                "local_step": ev.get("step"),
                "event_type": "tool_call",
                "actor": ev.get("agent"),
                "target": ev.get("tool"),
                "action": ev.get("tool"),
                "decision": decision,
                "status": "blocked" if decision in {"blocked", "denied"} else "allowed",
                "reason": d.get("reason") or d.get("reason_code", ""),
                "reason_code": d.get("reason_code"),
                "mapped_asi": d.get("asi", []) or [],
                "controls": d.get("controls", []) or [],
                "raw": ev,
            })
            idx += 1
    return sorted(events, key=lambda x: (x.get("flow_id") or "", x.get("local_step") or 0, x.get("global_step") or 0))
