# Grounded answer

**Question:** Which tools should I evaluate for MCP runtime security and ASI02 tool misuse?

## Evidence-based findings
- …mmercial. Categories: AI-SPM; Agentic OWASP Mapping; Data Security; Guardrails; Runtime Defense. Framework support: LangChain/LangGraph: generic; LlamaIndex: generic; CrewAI: generic; AutoGen: generic; OpenAI Agents SDK: generic; Semantic Kernel: generic; MCP: generic. Agentic OWASP coverage: ASI01; ASI02; ASI03; ASI06; ASI09. Lifecycle stages: deploy; operate; monitor; govern. Deployment: enterprise; saas. Targets: … [S034](data/tools.json)
- Reference architecture: MCP Runtime Security Gateway. Best for: Production MCP clients, third-party MCP servers, and tool execution flows. Description: None. Threats: ASI02 Tool Misuse; ASI04 Agentic Supply Chain; ASI05 Unexpected Code Execution; ASI07 Insecure Inter-Agent Communication. Components: MCP Gateway / PEP; Tool Descriptor Validator; Policy Decision Point; Ephemeral Credential Broker; Sandboxed Tool Runtim… [S175](data/reference_architectures.json#mcp_runtime_security_gateway)
- … and ASI taxonomy support products. Useful shortlist item for goal hijack, tool misuse, and runtime adversarial validation.. Vendor type: commercial. License: Commercial. Categories: Agent Security; Agentic OWASP Mapping; Red Teaming; Runtime Defense. Framework support: LangChain/LangGraph: generic; LlamaIndex: generic; CrewAI: generic; AutoGen: generic; OpenAI Agents SDK: generic; Semantic Kernel: generic; MCP: gene… [S039](data/tools.json)
- ASI lifecycle mapping for ASI02 Tool Misuse and Exploitation. asi: ASI02; risk: Tool Misuse and Exploitation [S151](data/controls.json#asi_lifecycle_matrix:ASI02)
- … operate, monitor, and governance. Strong candidate category for agent posture, runtime policy, and tool-use controls.. Vendor type: commercial. License: Commercial. Categories: AI-SPM; Agent Security; Agentic OWASP Mapping; MCP Security; Runtime Defense. Framework support: LangChain/LangGraph: generic; LlamaIndex: generic; CrewAI: generic; AutoGen: generic; OpenAI Agents SDK: generic; Semantic Kernel: generic; MCP: … [S031](data/tools.json)
- …overn and ASI taxonomy support. Use as a candidate for agent inventory, policy, runtime and MCP-oriented review.. Vendor type: commercial. License: Commercial. Categories: AI-SPM; Agent Security; Agentic OWASP Mapping; MCP Security; Runtime Defense. Framework support: LangChain/LangGraph: generic; LlamaIndex: generic; CrewAI: generic; AutoGen: generic; OpenAI Agents SDK: generic; Semantic Kernel: generic; MCP: generi… [S038](data/tools.json)

## Candidate tools from the retrieved index
- **Prompt Security** — Agentic readiness 3.7, MCP security 2.9. Source: [S034](data/tools.json)
- **Striker** — Agentic readiness 3.9, MCP security 3.4. Source: [S039](data/tools.json)
- **Pillar Security** — Agentic readiness 4.7, MCP security 4.2. Source: [S031](data/tools.json)
- **SPLX** — Agentic readiness 4.3, MCP security 4.3. Source: [S038](data/tools.json)
- **ActiveFence AI Security** — Agentic readiness 3.1, MCP security 2.2. Source: [S001](data/tools.json)

## Sources
- [S034](data/tools.json) — Tool profile: Prompt Security
- [S175](data/reference_architectures.json#mcp_runtime_security_gateway) — Reference architecture: MCP Runtime Security Gateway
- [S039](data/tools.json) — Tool profile: Striker
- [S151](data/controls.json#asi_lifecycle_matrix:ASI02) — ASI lifecycle mapping: ASI02 Tool Misuse and Exploitation
- [S031](data/tools.json) — Tool profile: Pillar Security
- [S038](data/tools.json) — Tool profile: SPLX
- [S001](data/tools.json) — Tool profile: ActiveFence AI Security
- [S041](data/tools.json) — Tool profile: Trend Micro AI Security
- [S006](https://calypsoai.com) — Tool profile: CalypsoAI / F5 AI Security
- [S027](https://noma.security) — Tool profile: Noma Security
