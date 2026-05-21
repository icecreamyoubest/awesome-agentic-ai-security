#!/usr/bin/env python3
"""Small dependency-free retriever for the source index."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "by", "is", "are", "be", "as", "at", "this", "that", "which", "what", "how",
    "should", "can", "we", "i", "my", "our", "agent", "agents", "tool", "tools", "security", "ai", "llm",
}


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9_\-]+", text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def load_index(path: str = "data/source_index.json") -> Dict[str, Any]:
    full = ROOT / path
    if not full.exists():
        raise FileNotFoundError(f"Missing {full}. Run: python agents/build_source_index.py")
    with open(full, encoding="utf-8") as f:
        return json.load(f)


class SourceRetriever:
    def __init__(self, index: Dict[str, Any]):
        self.sources = index.get("sources", [])
        self.doc_tokens = []
        self.df = Counter()
        for src in self.sources:
            toks = tokenize(" ".join([src.get("title", ""), src.get("type", ""), " ".join(src.get("tags", [])), src.get("text", "")]))
            c = Counter(toks)
            self.doc_tokens.append(c)
            self.df.update(c.keys())
        self.n = max(len(self.sources), 1)

    def search(self, query: str, top_k: int = 8, doc_types: Iterable[str] | None = None) -> List[Dict[str, Any]]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        q_counter = Counter(q_tokens)
        allowed = set(doc_types or [])
        results = []
        q_lower = query.lower()
        for src, c in zip(self.sources, self.doc_tokens):
            if allowed and src.get("type") not in allowed:
                continue
            score = 0.0
            text_lower = (src.get("title", "") + " " + src.get("text", "") + " " + " ".join(src.get("tags", []))).lower()
            for tok, qtf in q_counter.items():
                if tok in c:
                    idf = math.log((self.n + 1) / (self.df[tok] + 0.5)) + 1
                    score += (1 + math.log(c[tok])) * idf * qtf
                if tok.upper().startswith("ASI") and tok.upper() in src.get("tags", []):
                    score += 3
            # small phrase boost
            for phrase in re.findall(r"[A-Za-z0-9][A-Za-z0-9_\- ]{3,}", query):
                phrase = phrase.lower().strip()
                if len(phrase.split()) >= 2 and phrase in text_lower:
                    score += 2.0
            if score > 0:
                item = dict(src)
                item["score"] = round(score, 4)
                item["snippet"] = make_snippet(src.get("text", ""), q_tokens)
                results.append(item)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def make_snippet(text: str, query_tokens: List[str], max_chars: int = 420) -> str:
    if len(text) <= max_chars:
        return text
    lower = text.lower()
    positions = [lower.find(t) for t in query_tokens if lower.find(t) >= 0]
    start = max(min(positions) - 80, 0) if positions else 0
    snippet = text[start : start + max_chars]
    if start > 0:
        snippet = "…" + snippet
    if start + max_chars < len(text):
        snippet += "…"
    return snippet
