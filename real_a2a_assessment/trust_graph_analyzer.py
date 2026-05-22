from __future__ import annotations
from typing import Any, Dict, List

def analyze_trust_graph(raw: Dict[str, Any]) -> Dict[str, Any]:
    edges = raw.get("edges") or raw.get("delegations") or raw.get("trust_edges") or []
    nodes=set(); risky_edges=[]
    for e in edges if isinstance(edges, list) else []:
        if not isinstance(e, dict): continue
        src=e.get("from") or e.get("source"); dst=e.get("to") or e.get("target")
        if src: nodes.add(str(src))
        if dst: nodes.add(str(dst))
        scopes=e.get("scopes") or e.get("permissions") or []
        scopes_text=" ".join(scopes if isinstance(scopes, list) else [str(scopes)]).lower()
        signed=bool(e.get("signed") or e.get("attested"))
        if not signed or any(k in scopes_text for k in ["admin","write","delete","transfer","*"]):
            risky_edges.append({"from":src,"to":dst,"scopes":scopes,"signals":[s for s in ["unsigned_delegation" if not signed else None,"broad_or_write_scope" if scopes_text else None] if s]})
    return {"nodes":sorted(nodes),"edges":len(edges) if isinstance(edges,list) else 0,"risky_edges":risky_edges,"mapped_asi":sorted({"ASI03","ASI07","ASI08"} if risky_edges else [])}
