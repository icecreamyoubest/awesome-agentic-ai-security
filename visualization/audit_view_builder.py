from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_audit_table(report: Dict[str, Any], audit_jsonl: str | None = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for flow in report.get("flows", []):
        for ev in flow.get("tool_events", []):
            d = ev.get("decision") or {}
            rows.append({
                "flow_id": flow.get("flow_id"),
                "flow_name": flow.get("flow_name"),
                "step": ev.get("step"),
                "agent": ev.get("agent"),
                "tool": ev.get("tool"),
                "decision": d.get("decision") or ("allowed" if ev.get("allowed") else "blocked"),
                "reason_code": d.get("reason_code", ""),
                "reason": d.get("reason", ""),
                "mapped_asi": ", ".join(d.get("asi", []) or []),
                "controls": ", ".join(d.get("controls", []) or []),
                "trace_id": d.get("trace_id", ""),
                "raw": ev,
            })
    # Optionally append raw audit lines if present and not already included.
    if audit_jsonl and Path(audit_jsonl).exists():
        for line in Path(audit_jsonl).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            # Keep raw line in separate field for drill-down use.
            rows.append({
                "flow_id": item.get("flow_id", "audit_log"),
                "flow_name": "Raw audit log",
                "step": item.get("step", ""),
                "agent": item.get("agent_id", ""),
                "tool": item.get("tool_name", ""),
                "decision": item.get("decision", ""),
                "reason_code": item.get("reason_code", ""),
                "reason": item.get("reason", ""),
                "mapped_asi": ", ".join(item.get("asi", []) or []),
                "controls": ", ".join(item.get("controls", []) or []),
                "trace_id": item.get("trace_id", ""),
                "raw": item,
            })
    return rows
