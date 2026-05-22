from __future__ import annotations

from typing import Any, Dict, List


def evidence_for_tool(evidence_data: Dict[str, Any], tool_id: str) -> List[Dict[str, Any]]:
    return list(evidence_data.get("tools", {}).get(tool_id, []))


def validate_tool_claim(tool: Dict[str, Any], evidence_data: Dict[str, Any]) -> Dict[str, Any]:
    tool_id = tool["id"]
    evidence = evidence_for_tool(evidence_data, tool_id)
    confidence = float(tool.get("evidence_confidence", {}).get("confidence_score", 0))
    depths = tool.get("asi_coverage_depth", {})
    benchmark_backed = [asi for asi, depth in depths.items() if int(depth) >= 3]
    explicit = [asi for asi, depth in depths.items() if int(depth) == 2]
    inferred = [asi for asi, depth in depths.items() if int(depth) == 1]

    if confidence >= 4 or benchmark_backed:
        level = "High"
    elif confidence >= 2.5 or explicit:
        level = "Medium"
    else:
        level = "Needs validation"

    gaps = []
    if not evidence:
        gaps.append("No external evidence records found in data/evidence.json")
    if not benchmark_backed:
        gaps.append("No benchmark-backed ASI coverage yet")
    if not tool.get("url") and not tool.get("docs"):
        gaps.append("Missing public URL/docs for verification")

    return {
        "tool_id": tool_id,
        "name": tool.get("name", tool_id),
        "confidence_score": confidence,
        "validation_level": level,
        "evidence_count": len(evidence),
        "benchmark_backed_asi": benchmark_backed,
        "explicit_asi": explicit,
        "inferred_asi": inferred,
        "evidence": evidence,
        "gaps": gaps,
    }


def build_evidence_checks(recommendations: List[Any], tools_by_id: Dict[str, Dict[str, Any]], evidence_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks = []
    for rec in recommendations:
        tool = tools_by_id.get(rec.tool_id)
        if not tool:
            continue
        validation = validate_tool_claim(tool, evidence_data)
        checks.append({
            "tool_id": rec.tool_id,
            "tool_name": rec.name,
            "validation_level": validation["validation_level"],
            "confidence_score": validation["confidence_score"],
            "required_next_evidence": validation["gaps"],
        })
    return checks
