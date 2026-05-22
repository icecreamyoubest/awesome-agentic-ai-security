# Real MCP Server Risk Assessment

This module performs a schema-only risk assessment for real MCP-compatible HTTP JSON-RPC servers and Hugging Face / Gradio-style Spaces.

Default mode is safe discovery only:

```bash
python -m real_mcp_assessment.assess_mcp_server --server-url demo://local
python -m real_mcp_assessment.assess_mcp_server --server-url https://huggingface.co/spaces/OWNER/SPACE --mode gradio_config
python -m real_mcp_assessment.assess_mcp_server --server-url https://your-mcp-server.example.com/mcp --mode jsonrpc
```

The scanner attempts:

1. JSON-RPC `initialize` and `tools/list` for HTTP MCP-style endpoints.
2. Gradio `/config` discovery for Hugging Face Space URLs.
3. Static demo tools for `demo://local`.

It does not execute third-party tools by default. Controlled execution should only be used for systems you own or are explicitly authorized to test.

## v1.6 Connector Fixes

The real MCP assessment connector now supports several endpoint shapes:

- Generic Streamable HTTP JSON-RPC MCP endpoints, including `/mcp`, `/mcp/`, `/sse`, `/api/mcp`, and `/api/mcp/` variants.
- Hugging Face / Gradio MCP endpoints such as `https://OWNER-SPACE.hf.space/gradio_api/mcp/`.
- Hugging Face Space repository URLs such as `https://huggingface.co/spaces/OWNER/SPACE`, which are converted to `https://owner-space.hf.space` for runtime discovery.
- Gradio fallbacks via app-root `/config` and `/gradio_api/info`.
- Documentation/reference URLs such as OpenAI's MCP and connectors guide. These are treated as documentation references, not live MCP servers, and are assessed as integration guidance sources.

Discovery failures are now reported as `inconclusive` with `risk_score: null`, never as `risk_score: 0`. This prevents false low-risk conclusions when tool discovery fails.

Example:

```bash
python -m real_mcp_assessment.assess_mcp_server \
  --server-url https://developers.openai.com/api/docs/guides/tools-connectors-mcp \
  --mode auto
```

For Hugging Face Gradio MCP Spaces, prefer the trailing slash endpoint:

```bash
python -m real_mcp_assessment.assess_mcp_server \
  --server-url https://OWNER-SPACE.hf.space/gradio_api/mcp/ \
  --mode auto
```
