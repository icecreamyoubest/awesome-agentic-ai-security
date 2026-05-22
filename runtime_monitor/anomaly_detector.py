from __future__ import annotations
from collections import Counter
from typing import Any, Dict, List

def detect_anomalies(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    findings=[]; by_tool=Counter(e.get('tool_name') for e in events)
    for tool,count in by_tool.items():
        if tool and count >= 5: findings.append({'type':'rapid_tool_loop','severity':'medium','tool':tool,'count':count,'mapped_asi':['ASI08']})
    for e in events:
        tool=str(e.get('tool_name','')); decision=str(e.get('decision','')).lower(); approved=bool(e.get('human_approved')); args=str(e.get('arguments','')).lower()
        if tool in {'email.send','crm.refund','file.delete'} and decision in {'allow','allowed'} and not approved: findings.append({'type':'high_impact_without_approval','severity':'high','tool':tool,'mapped_asi':['ASI02','ASI09']})
        if any(k in args for k in ['token','secret','api_key']) and decision in {'allow','allowed'}: findings.append({'type':'sensitive_argument_allowed','severity':'high','tool':tool,'mapped_asi':['ASI03','ASI06']})
        if 'http://' in args or 'webhook' in args: findings.append({'type':'external_egress_signal','severity':'medium','tool':tool,'mapped_asi':['ASI07']})
    return findings
