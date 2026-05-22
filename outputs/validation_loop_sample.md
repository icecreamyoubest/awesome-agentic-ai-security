# Validation Loop Report: MCP + RAG Customer Support Agent

Enterprise customer support agent built with LangGraph. It uses MCP tools for CRM lookup, refund initiation, email sending, and ticket updates. It also uses a vector database for long-term support memory and retrieves external knowledge-base pages.

## Mapped ASI risks
- **ASI02** — Tool Misuse and Exploitation (High) — The system exposes tools or APIs that can be misused, over-invoked, or chained in unsafe ways.
- **ASI03** — Identity and Privilege Abuse (High) — Delegated access, OAuth, service identities, or agent-to-agent trust can create privilege-abuse paths.
- **ASI06** — Memory & Context Poisoning (High) — Memory, RAG, vector stores, or long context can be poisoned and reused across future reasoning cycles.
- **ASI07** — Insecure Inter-Agent Communication (High) — Inter-agent, MCP, A2A, or external protocol traffic requires authentication, integrity, and semantic validation.
- **ASI01** — Agent Goal Hijack (High) — Untrusted natural-language or external content can redirect agent goals, planning, or task selection.
- **ASI04** — Agentic Supply Chain Vulnerabilities (High) — Tools, MCP servers, packages, prompts, agent cards, or registries introduce a live supply-chain attack surface.
- **ASI08** — Cascading Failures (High) — Autonomous delegation, retries, or multi-agent fan-out can amplify one fault into a system-wide failure.
- **ASI05** — Unexpected Code Execution (RCE) (Medium) — The system can generate, execute, install, or route code/commands through tools or coding-agent workflows.
- **ASI10** — Rogue Agents (Medium) — Autonomous agents can drift, collude, self-replicate, or deviate from declared behavioral boundaries.

## Recommended tools
- **Pillar Security** — score 29.59 — ASI01, ASI02, ASI03, ASI04, ASI05, ASI06
- **SPLX** — score 28.0 — ASI01, ASI02, ASI03, ASI04, ASI05, ASI06
- **Noma Security** — score 27.06 — ASI01, ASI02, ASI03, ASI04, ASI06, ASI07
- **Prisma AIRS** — score 26.18 — ASI01, ASI02, ASI03, ASI04, ASI06, ASI07
- **Zenity** — score 25.93 — ASI01, ASI02, ASI03, ASI04, ASI06, ASI07
- **Striker** — score 24.26 — ASI01, ASI02, ASI03, ASI05, ASI06, ASI08
- **Cortex Cloud AI Security** — score 23.68 — ASI02, ASI03, ASI04, ASI05, ASI06, ASI08
- **HiddenLayer AISec Platform** — score 22.86 — ASI02, ASI03, ASI04, ASI05, ASI06, ASI08

## Coverage
- Required: ASI01, ASI02, ASI03, ASI04, ASI05, ASI06, ASI07, ASI08, ASI10
- Covered by recommendations: ASI01, ASI02, ASI03, ASI04, ASI05, ASI06, ASI07, ASI08, ASI10
- Gaps: none

## Benchmark plan
- **MCP-ASI01-005** —  — ASI: ASI01, ASI06
- **MCP-ASI02-004** —  — ASI: ASI02, ASI03
- **MCP-ASI04-009** —  — ASI: ASI04, ASI05
- **MCP-ASI05-002** —  — ASI: ASI05, ASI02
- **MCP-ASI07-003** —  — ASI: ASI07, ASI03
- **MCP-ASI08-008** —  — ASI: ASI08, ASI02
- **RAG-ASI06-007** —  — ASI: ASI06, ASI08
- **A2A-ASI07-006** —  — ASI: ASI07, ASI10

## Score update suggestions
- **Pillar Security**: validate A2A-ASI07-006, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003, MCP-ASI08-008, RAG-ASI06-007. If benchmark passes reproducibly, consider raising ASI coverage depth to 3 for the relevant risk and adding benchmark_backed evidence.
- **SPLX**: validate A2A-ASI07-006, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003, MCP-ASI08-008, RAG-ASI06-007. If benchmark passes reproducibly, consider raising ASI coverage depth to 3 for the relevant risk and adding benchmark_backed evidence.
- **Noma Security**: validate A2A-ASI07-006, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003, MCP-ASI08-008, RAG-ASI06-007. If benchmark passes reproducibly, consider raising ASI coverage depth to 3 for the relevant risk and adding benchmark_backed evidence.
- **Prisma AIRS**: validate A2A-ASI07-006, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003, MCP-ASI08-008, RAG-ASI06-007. If benchmark passes reproducibly, consider raising ASI coverage depth to 3 for the relevant risk and adding benchmark_backed evidence.
- **Zenity**: validate A2A-ASI07-006, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003, MCP-ASI08-008, RAG-ASI06-007. If benchmark passes reproducibly, consider raising ASI coverage depth to 3 for the relevant risk and adding benchmark_backed evidence.
- **Striker**: validate A2A-ASI07-006, MCP-ASI01-005, MCP-ASI02-004, MCP-ASI04-009, MCP-ASI05-002, MCP-ASI07-003, MCP-ASI08-008, RAG-ASI06-007. If benchmark passes reproducibly, consider raising ASI coverage depth to 3 for the relevant risk and adding benchmark_backed evidence.

## Next actions
- Run benchmark_plan cases against the target runtime or mock harness.
- Verify top vendor/tool claims using agents/claim_verifier.py.
- Generate architecture with agents/architecture_generator.py.
- Attach results to data/evidence.json and update confidence scores.
