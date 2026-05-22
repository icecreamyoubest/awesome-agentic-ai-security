from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

def load_a2a_input(path_or_text: str) -> Dict[str, Any]:
    p = Path(path_or_text)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(path_or_text)

def normalize_cards(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    for key in ("agents", "agent_cards", "cards", "items"):
        val = raw.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]
    if raw.get("name") or raw.get("id") or raw.get("agent_id"):
        return [raw]
    return []

def required_controls(signals: List[str]) -> List[str]:
    controls = {"immutable agent action audit", "agent identity registry"}
    if "unsigned_agent_card" in signals:
        controls.update(["signed agent cards", "descriptor provenance verification"])
    if "open_agent_registration" in signals:
        controls.update(["closed registration", "registry approval workflow"])
    if "missing_or_weak_agent_auth" in signals:
        controls.update(["mTLS or token-bound agent auth", "per-agent scoped credentials"])
    if "delegation_enabled" in signals:
        controls.update(["delegation depth limit", "per-action authorization"])
    if "high_impact_capability_claim" in signals:
        controls.update(["human approval for high-impact actions", "capability allowlist"])
    if "unencrypted_agent_endpoint" in signals:
        controls.update(["TLS enforcement", "protocol pinning"])
    if "external_routing_or_webhook" in signals:
        controls.update(["egress allowlist", "message integrity validation"])
    return sorted(controls)

def scan_agent_card(card: Dict[str, Any]) -> Dict[str, Any]:
    name = str(card.get("name") or card.get("id") or card.get("agent_id") or "unknown-agent")
    capabilities = card.get("capabilities") or card.get("skills") or card.get("tools") or []
    if isinstance(capabilities, str): capabilities = [capabilities]
    endpoint = str(card.get("endpoint") or card.get("url") or "")
    auth = str(card.get("auth") or card.get("authentication") or card.get("auth_type") or "").lower()
    signed = bool(card.get("signed") or card.get("signature") or card.get("attested"))
    allow_delegation = bool(card.get("allow_delegation") or card.get("delegation") or card.get("can_delegate"))
    public_registration = bool(card.get("public_registration") or card.get("open_registration"))
    joined = " ".join([name, endpoint, auth] + [str(c) for c in capabilities]).lower()
    signals=[]; mapped_asi=[]; risk=0.0
    if not signed:
        signals.append("unsigned_agent_card"); mapped_asi += ["ASI04","ASI07","ASI10"]; risk += 2.0
    if public_registration:
        signals.append("open_agent_registration"); mapped_asi += ["ASI03","ASI07","ASI10"]; risk += 2.0
    if not auth or auth in {"none","anonymous","public"}:
        signals.append("missing_or_weak_agent_auth"); mapped_asi += ["ASI03","ASI07"]; risk += 1.5
    if allow_delegation:
        signals.append("delegation_enabled"); mapped_asi += ["ASI03","ASI08"]; risk += 1.0
    if any(k in joined for k in ["admin","root","payment","refund","delete","transfer","execute","shell"]):
        signals.append("high_impact_capability_claim"); mapped_asi += ["ASI02","ASI03","ASI10"]; risk += 2.0
    if endpoint.startswith("http://"):
        signals.append("unencrypted_agent_endpoint"); mapped_asi += ["ASI07"]; risk += 1.5
    if "external" in joined or "webhook" in joined:
        signals.append("external_routing_or_webhook"); mapped_asi += ["ASI07","ASI08"]; risk += 1.0
    risk = min(10.0, risk)
    level = "high" if risk >= 7 else ("medium" if risk >= 4 else "low")
    return {"agent":name,"endpoint":endpoint,"capabilities":capabilities,"signals":sorted(set(signals)),"mapped_asi":sorted(set(mapped_asi)),"risk_score":round(risk,2),"risk_level":level,"required_controls":required_controls(sorted(set(signals)))}

def scan_a2a(raw: Dict[str, Any]) -> Dict[str, Any]:
    cards = normalize_cards(raw)
    scanned = [scan_agent_card(c) for c in cards]
    mapped = sorted({asi for c in scanned for asi in c.get("mapped_asi", [])})
    high = sum(1 for c in scanned if c.get("risk_level") == "high")
    avg = round(sum(c.get("risk_score", 0) for c in scanned) / max(1, len(scanned)), 2)
    return {"assessment_type":"a2a_agent_card_assessment","summary":{"agents":len(scanned),"high_risk_agents":high,"average_risk_score":avg,"risk_level":"high" if high else ("medium" if avg >= 4 else "low"),"mapped_asi":mapped},"agents":scanned}
