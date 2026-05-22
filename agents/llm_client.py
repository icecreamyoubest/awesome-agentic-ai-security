#!/usr/bin/env python3
"""Minimal optional LLM client.

Default project functionality does not require an LLM. This client supports an
OpenAI-compatible chat-completions endpoint using only Python stdlib so the
repo stays lightweight.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict, List, Optional


class LLMClientError(RuntimeError):
    pass


def chat_openai_compatible(
    *,
    messages: List[Dict[str, str]],
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.1,
    timeout: int = 60,
) -> str:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1/chat/completions").rstrip("/")
    if not api_key:
        raise LLMClientError("Missing API key. Set OPENAI_API_KEY or pass --api-key-env.")

    # If user provides a base URL ending in /v1, append /chat/completions.
    if base_url.endswith("/v1"):
        base_url = base_url + "/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise LLMClientError(f"LLM endpoint HTTP {e.code}: {detail}") from e
    except Exception as e:
        raise LLMClientError(f"LLM call failed: {e}") from e

    try:
        return body["choices"][0]["message"]["content"]
    except Exception as e:
        raise LLMClientError(f"Unexpected LLM response format: {body}") from e
