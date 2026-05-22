from __future__ import annotations
from typing import Any, Dict

def read(arguments: Dict[str, Any]) -> Dict[str, Any]:
    path = arguments.get("path", "README.md")
    return {"tool": "file.read", "path": path, "content_preview": "demo file content only"}

def delete(arguments: Dict[str, Any]) -> Dict[str, Any]:
    return {"tool": "file.delete", "status": "simulated_delete", "path": arguments.get("path")}
