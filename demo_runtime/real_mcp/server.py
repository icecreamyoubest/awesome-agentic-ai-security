
from __future__ import annotations
import json, sys
from demo_runtime.real_mcp.gateway import MCPGateway

def main():
    gateway = MCPGateway()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            print(json.dumps(gateway.handle(req)), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc":"2.0", "id": None, "error":{"code":-32700, "message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()
