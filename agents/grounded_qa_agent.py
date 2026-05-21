#!/usr/bin/env python3
"""Grounded Q&A agent over the catalog source index.

The agent retrieves source records first, then optionally calls an LLM with only
those records as context. Answers are citation-checked against retrieved source
IDs to reduce hallucinations.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from .retriever import SourceRetriever, load_index
    from .llm_client import LLMClientError, chat_openai_compatible
except ImportError:  # script execution
    from retriever import SourceRetriever, load_index
    from llm_client import LLMClientError, chat_openai_compatible

ROOT = Path(__file__).resolve().parents[1]
CITATION_RE = re.compile(r"\[S\d{3}\]")

SYSTEM_PROMPT = """You are a grounded Agentic AI Security catalog assistant.
You must answer ONLY using the provided indexed sources.
Every non-trivial factual claim, tool recommendation, score statement, risk mapping, and control recommendation must cite at least one retrieved source ID like [S001].
Do not use outside knowledge. Do not invent tools, scores, vendor claims, or OWASP mappings.
If the retrieved sources are insufficient, say exactly which evidence is missing.
Prefer concise, structured answers with tables when helpful.
At the end, include a 'Sources' section listing cited source IDs and their titles.
"""


def source_link(src: Dict[str, Any]) -> str:
    url = src.get("url") or src.get("local_path") or ""
    if url.startswith("#"):
        return url
    return url


def format_source_context(sources: List[Dict[str, Any]]) -> str:
    blocks = []
    for src in sources:
        sid = src["source_id"]
        blocks.append(
            f"[{sid}] {src.get('title')}\n"
            f"Type: {src.get('type')}\n"
            f"Object ID: {src.get('object_id')}\n"
            f"URL: {source_link(src)}\n"
            f"Snippet: {src.get('snippet') or src.get('text')}"
        )
    return "\n\n".join(blocks)


def citation_markdown(src: Dict[str, Any]) -> str:
    sid = src["source_id"]
    url = source_link(src)
    title = src.get("title", sid)
    return f"[{sid}]({url}) — {title}"


def extractive_answer(question: str, sources: List[Dict[str, Any]]) -> str:
    if not sources:
        return "I could not find enough indexed evidence to answer this question. Add more sources to `data/source_index.json` and retry."

    lines = [f"# Grounded answer\n", f"**Question:** {question}\n"]
    lines.append("## Evidence-based findings")
    for src in sources[:6]:
        lines.append(f"- {src.get('snippet') or src.get('text')} [{src['source_id']}]({source_link(src)})")

    tool_sources = [s for s in sources if s.get("type") == "tool_profile"]
    if tool_sources:
        lines.append("\n## Candidate tools from the retrieved index")
        for src in tool_sources[:5]:
            meta = src.get("metadata", {})
            scores = meta.get("scores", {}) if isinstance(meta, dict) else {}
            lines.append(
                f"- **{src.get('title', '').replace('Tool profile: ', '')}** — "
                f"Agentic readiness {scores.get('agentic_readiness', 'n/a')}, "
                f"MCP security {scores.get('mcp_security', 'n/a')}. "
                f"Source: [{src['source_id']}]({source_link(src)})"
            )

    lines.append("\n## Sources")
    for src in sources:
        lines.append(f"- {citation_markdown(src)}")
    return "\n".join(lines) + "\n"


def validate_citations(answer: str, retrieved_sources: List[Dict[str, Any]]) -> Tuple[bool, List[str], List[str]]:
    retrieved_ids = {s["source_id"] for s in retrieved_sources}
    cited = sorted({m.group(0).strip("[]") for m in CITATION_RE.finditer(answer)})
    unknown = [sid for sid in cited if sid not in retrieved_ids]
    ok = bool(cited) and not unknown
    return ok, cited, unknown


def add_citation_audit(answer: str, sources: List[Dict[str, Any]]) -> str:
    ok, cited, unknown = validate_citations(answer, sources)
    audit = ["\n---\n## Citation audit"]
    if ok:
        audit.append(f"Passed. Cited retrieved sources: {', '.join(cited)}.")
    elif unknown:
        audit.append(f"Warning: answer cited source IDs not present in retrieved context: {', '.join(unknown)}.")
    else:
        audit.append("Warning: answer did not include source citations. Treat as unsupported unless reviewed.")
    audit.append("\n## Retrieved source index")
    for src in sources:
        audit.append(f"- {citation_markdown(src)}")
    return answer.rstrip() + "\n" + "\n".join(audit) + "\n"


def ask_with_llm(question: str, sources: List[Dict[str, Any]], *, model: str, base_url: str | None, api_key_env: str, temperature: float) -> str:
    context = format_source_context(sources)
    user = f"""Question:\n{question}\n\nRetrieved indexed sources:\n{context}\n\nAnswer using only these sources and cite source IDs like [S001]."""
    api_key = os.getenv(api_key_env)
    return chat_openai_compatible(
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}],
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Grounded Q&A over the Agentic AI Security catalog")
    parser.add_argument("--question", required=True)
    parser.add_argument("--index", default="data/source_index.json")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--provider", choices=["none", "openai-compatible"], default="none")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL"))
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--output", default="")
    parser.add_argument("--json-output", default="")
    parser.add_argument("--fallback-on-uncited", action="store_true", help="Use extractive answer if the LLM response has no valid citations")
    args = parser.parse_args()

    index = load_index(args.index)
    retriever = SourceRetriever(index)
    sources = retriever.search(args.question, top_k=args.top_k)

    if args.provider == "none":
        answer = extractive_answer(args.question, sources)
    else:
        try:
            answer = ask_with_llm(
                args.question,
                sources,
                model=args.model,
                base_url=args.base_url,
                api_key_env=args.api_key_env,
                temperature=args.temperature,
            )
        except LLMClientError as e:
            answer = f"LLM call failed: {e}\n\nFalling back to extractive answer.\n\n" + extractive_answer(args.question, sources)
        ok, _, _ = validate_citations(answer, sources)
        if args.fallback_on_uncited and not ok:
            answer = "LLM answer failed citation validation. Falling back to extractive answer.\n\n" + extractive_answer(args.question, sources)
        else:
            answer = add_citation_audit(answer, sources)

    result = {
        "question": args.question,
        "provider": args.provider,
        "model": args.model if args.provider != "none" else None,
        "retrieved_sources": [
            {
                "source_id": s["source_id"],
                "title": s.get("title"),
                "type": s.get("type"),
                "object_id": s.get("object_id"),
                "url": source_link(s),
                "score": s.get("score"),
            }
            for s in sources
        ],
        "answer": answer,
    }

    if args.output:
        out = ROOT / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(answer, encoding="utf-8")
        print(f"Answer written to: {out}")
    else:
        print(answer)

    if args.json_output:
        outj = ROOT / args.json_output
        outj.parent.mkdir(parents=True, exist_ok=True)
        outj.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON written to: {outj}")


if __name__ == "__main__":
    main()
