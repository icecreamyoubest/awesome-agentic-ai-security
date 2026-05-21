#!/usr/bin/env python3
"""Build a compact source index for grounded Q&A.

The index is intentionally JSON-only so it can be inspected, versioned, and
served by a static site. Each document receives a stable source_id, local path,
optional external URL, and text used for retrieval.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> Dict[str, Any]:
    with open(ROOT / path, encoding="utf-8") as f:
        return json.load(f)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            if isinstance(v, (str, int, float, bool)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                parts.append(f"{k}: {', '.join(map(str, v))}")
        return clean_text("; ".join(parts))
    if isinstance(value, list):
        return clean_text("; ".join(map(str, value)))
    return str(value)


def make_doc(
    docs: List[Dict[str, Any]],
    *,
    title: str,
    doc_type: str,
    local_path: str,
    text: str,
    object_id: str = "",
    url: str = "",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    sid = f"S{len(docs) + 1:03d}"
    docs.append(
        {
            "source_id": sid,
            "title": title,
            "type": doc_type,
            "object_id": object_id,
            "local_path": local_path,
            "url": url or local_path,
            "tags": tags or [],
            "text": clean_text(text),
            "metadata": metadata or {},
        }
    )


def build_index() -> Dict[str, Any]:
    docs: List[Dict[str, Any]] = []

    tools = load_json("data/tools.json")
    evidence = load_json("data/evidence.json")
    controls = load_json("data/controls.json")
    incidents = load_json("data/incidents.json")
    architectures = load_json("data/reference_architectures.json")
    benchmarks = load_json("benchmarks/mcp_security_benchmark_v01.json")
    claims = load_json("data/claims.json")
    arch_templates = load_json("data/architecture_templates.json")
    release_log = load_json("data/releases/change_log.json")

    # Tool profiles.
    for tool in sorted(tools.get("tools", []), key=lambda x: x.get("id", "")):
        tid = tool.get("id", "")
        url = tool.get("docs") or tool.get("url") or "data/tools.json"
        scores = tool.get("scores", {})
        text = f"""
        Tool: {tool.get('name')} by {tool.get('org')}.
        Description: {tool.get('description')}.
        Vendor type: {tool.get('vendor_type')}. License: {tool.get('license')}.
        Categories: {clean_text(tool.get('category'))}.
        Framework support: {clean_text(tool.get('frameworks'))}.
        Agentic OWASP coverage: {clean_text(tool.get('agentic_owasp'))}.
        Lifecycle stages: {clean_text(tool.get('lifecycle_stages'))}.
        Deployment: {clean_text(tool.get('deployment'))}.
        Targets: {clean_text(tool.get('targets'))}.
        Scores: agentic readiness {scores.get('agentic_readiness')}, MCP security {scores.get('mcp_security')}, runtime {scores.get('runtime')}, red team {scores.get('red_team')}, enterprise {scores.get('enterprise')}, lifecycle coverage {scores.get('lifecycle_coverage')}.
        Evidence confidence: {clean_text(tool.get('evidence_confidence'))}.
        ASI coverage depth: {clean_text(tool.get('asi_coverage_depth'))}.
        Maintainer notes: {tool.get('maintainer_notes')}.
        """
        make_doc(
            docs,
            title=f"Tool profile: {tool.get('name')}",
            doc_type="tool_profile",
            object_id=tid,
            local_path=f"data/tools.json#{tid}",
            url=url,
            tags=list(tool.get("agentic_owasp", [])) + list(tool.get("category", [])),
            text=text,
            metadata={"tool_id": tid, "scores": scores},
        )

    # Evidence records.
    for tid, records in sorted(evidence.get("tools", {}).items()):
        for i, ev in enumerate(records, start=1):
            text = f"""
            Evidence for tool {tid}. Type: {ev.get('type')}. Source: {ev.get('source')}.
            Claim: {ev.get('claim')}. Supports: {clean_text(ev.get('supports'))}.
            Confidence: {ev.get('confidence')}. Last verified: {ev.get('last_verified')}.
            """
            make_doc(
                docs,
                title=f"Evidence: {tid} #{i}",
                doc_type="evidence",
                object_id=f"{tid}:{i}",
                local_path=f"data/evidence.json#{tid}:{i}",
                url=ev.get("url") or f"data/evidence.json#{tid}:{i}",
                tags=[tid, ev.get("type", "")],
                text=text,
                metadata={"tool_id": tid, "evidence_type": ev.get("type")},
            )

    # Control matrix and lifecycle matrix.
    for row in controls.get("control_matrix", []):
        asi = row.get("asi", "")
        text = f"""
        ASI control mapping. Risk: {asi} {row.get('risk')}.
        Core controls: {clean_text(row.get('core_controls'))}.
        Tool capabilities: {clean_text(row.get('tool_capabilities'))}.
        Mapped tools: {clean_text(row.get('mapped_tools'))}.
        """
        make_doc(
            docs,
            title=f"Control mapping: {asi} {row.get('risk')}",
            doc_type="control_mapping",
            object_id=asi,
            local_path=f"data/controls.json#control_matrix:{asi}",
            tags=[asi, "control"],
            text=text,
            metadata=row,
        )

    for row in controls.get("asi_lifecycle_matrix", []):
        asi = row.get("asi", "")
        text = f"ASI lifecycle mapping for {asi} {row.get('risk')}. " + clean_text(row)
        make_doc(
            docs,
            title=f"ASI lifecycle mapping: {asi} {row.get('risk')}",
            doc_type="asi_lifecycle_mapping",
            object_id=asi,
            local_path=f"data/controls.json#asi_lifecycle_matrix:{asi}",
            tags=[asi, "lifecycle"],
            text=text,
            metadata=row,
        )

    # Use cases.
    for uc in controls.get("use_cases", []):
        text = f"Use case: {uc.get('name')}. Description: {uc.get('description')}. Recommended categories: {clean_text(uc.get('recommended_categories'))}. Suggested tools: {clean_text(uc.get('suggested_tools'))}."
        make_doc(
            docs,
            title=f"Use case: {uc.get('name')}",
            doc_type="use_case",
            object_id=uc.get("id", ""),
            local_path=f"data/controls.json#use_cases:{uc.get('id')}",
            tags=["use_case"],
            text=text,
            metadata=uc,
        )

    # Incidents.
    for inc in incidents.get("incidents", []):
        text = f"""
        Incident: {inc.get('name')}. Summary: {inc.get('summary')}.
        ASI risks: {clean_text(inc.get('asi'))}. Benchmark cases: {clean_text(inc.get('benchmark_cases'))}.
        Required controls: {clean_text(inc.get('required_controls'))}. Links: {clean_text(inc.get('links'))}.
        """
        make_doc(
            docs,
            title=f"Incident: {inc.get('name')}",
            doc_type="incident",
            object_id=inc.get("id", ""),
            local_path=f"data/incidents.json#{inc.get('id')}",
            url=(inc.get("links") or [""])[0] if isinstance(inc.get("links"), list) and inc.get("links") else "data/incidents.json",
            tags=list(inc.get("asi", [])) + ["incident"],
            text=text,
            metadata=inc,
        )

    # Reference architectures.
    for arch in architectures.get("architectures", []):
        text = f"""
        Reference architecture: {arch.get('title') or arch.get('name')}. Best for: {arch.get('best_for')}. Description: {arch.get('description')}.
        Threats: {clean_text(arch.get('threats'))}. Components: {clean_text(arch.get('components'))}.
        Controls: {clean_text(arch.get('controls'))}. Candidate tools: {clean_text(arch.get('candidate_tools'))}.
        Open gaps: {clean_text(arch.get('open_gaps'))}.
        """
        make_doc(
            docs,
            title=f"Reference architecture: {arch.get('title') or arch.get('name')}",
            doc_type="reference_architecture",
            object_id=arch.get("id", ""),
            local_path=f"data/reference_architectures.json#{arch.get('id')}",
            tags=list(arch.get("threats", [])) + ["architecture"],
            text=text,
            metadata=arch,
        )

    # Benchmark cases.
    for case in benchmarks.get("cases", []):
        text = f"""
        Benchmark case: {case.get('id')} {case.get('name')}.
        ASI risks: {clean_text(case.get('asi'))}. Attack type: {case.get('attack_type')}.
        Objective: {case.get('objective')}. Expected controls: {clean_text(case.get('expected_control'))}.
        Pass condition: {case.get('pass_condition')}. Severity: {case.get('severity')}.
        """
        make_doc(
            docs,
            title=f"Benchmark: {case.get('id')} {case.get('name')}",
            doc_type="benchmark_case",
            object_id=case.get("id", ""),
            local_path=f"benchmarks/mcp_security_benchmark_v01.json#{case.get('id')}",
            tags=list(case.get("asi", [])) + ["benchmark", case.get("attack_type", "")],
            text=text,
            metadata=case,
        )


    # Claim verification templates.
    for claim in claims.get("claims", []):
        text = f"""
        Claim template: {claim.get('title')}. Claim: {claim.get('claim')}.
        Mapped ASI risks: {clean_text(claim.get('mapped_asi'))}.
        Required evidence: {clean_text(claim.get('required_evidence'))}.
        Validation tests: {clean_text(claim.get('validation_tests'))}.
        Confidence rule: {claim.get('confidence_rule')}.
        """
        make_doc(
            docs,
            title=f"Claim template: {claim.get('title')}",
            doc_type="claim_template",
            object_id=claim.get("id", ""),
            local_path=f"data/claims.json#{claim.get('id')}",
            tags=list(claim.get("mapped_asi", [])) + ["claim", "evidence"],
            text=text,
            metadata=claim,
        )

    # Architecture templates.
    for tpl in arch_templates.get("templates", []):
        text = f"""
        Architecture template: {tpl.get('title')}. Triggers: {clean_text(tpl.get('triggers'))}.
        ASI risks: {clean_text(tpl.get('asi'))}. Components: {clean_text(tpl.get('components'))}.
        Controls: {clean_text(tpl.get('controls'))}. Mermaid: {tpl.get('mermaid')}.
        """
        make_doc(
            docs,
            title=f"Architecture template: {tpl.get('title')}",
            doc_type="architecture_template",
            object_id=tpl.get("id", ""),
            local_path=f"data/architecture_templates.json#{tpl.get('id')}",
            tags=list(tpl.get("asi", [])) + ["architecture_template"],
            text=text,
            metadata=tpl,
        )

    # Release / change log records.
    for rel in release_log.get("releases", []):
        text = f"""
        Release: {rel.get('release')} {rel.get('version')}. Summary: {rel.get('summary')}.
        Added features: {clean_text(rel.get('added_features'))}. Added files: {clean_text(rel.get('added_files'))}.
        Evidence updated: {clean_text(rel.get('evidence_updated'))}.
        """
        make_doc(
            docs,
            title=f"Release: {rel.get('release')} {rel.get('version')}",
            doc_type="release",
            object_id=rel.get("release", ""),
            local_path=f"data/releases/change_log.json#{rel.get('release')}",
            tags=["release", "change_log"],
            text=text,
            metadata=rel,
        )

    return {
        "meta": {
            "version": "v0.9",
            "description": "Grounding source index for LLM-assisted Q&A. Answers should cite source_id values and use only retrieved records.",
            "generated_from": [
                "data/tools.json",
                "data/evidence.json",
                "data/controls.json",
                "data/incidents.json",
                "data/reference_architectures.json",
                "benchmarks/mcp_security_benchmark_v01.json",
                "data/claims.json",
                "data/architecture_templates.json",
                "data/releases/change_log.json",
            ],
            "citation_policy": "Every non-trivial answer claim must cite retrieved source IDs like [S001]. If evidence is missing, say insufficient evidence.",
        },
        "sources": docs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/source_index.json")
    args = parser.parse_args()
    index = build_index()
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(index['sources'])} indexed sources to {out}")


if __name__ == "__main__":
    main()
