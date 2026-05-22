from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from demo_runtime.runtime import DemoAgentRuntime
from demo_runtime.benchmark_runner import run_demo_benchmark
from agents.grounded_qa_agent import (
    SourceRetriever,
    load_index,
    extractive_answer,
    ask_with_llm,
    add_citation_audit,
    validate_citations,
)
from agents.llm_client import LLMClientError
from agents.lifecycle_orchestrator import run_lifecycle
from adapters.adapter_test_runner import run_llm_guard_smoke
from demo_runtime.real_mcp.benchmark_runner import run_real_mcp_gateway_benchmark
from agents.enterprise_report_pack import generate_pack
from real_mcp_assessment.assess_mcp_server import assess_mcp_server

DATA_DIR = ROOT / "data"
SCENARIO_DIRS = [ROOT / "examples", ROOT / "scenario_templates"]


def read_json(path: Path, default: Any = None) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_dict_list(raw: Any, keys: Tuple[str, ...] = ("items", "data", "records")) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        for key in keys:
            value = raw.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        values = list(raw.values())
        if values and all(isinstance(x, dict) for x in values):
            return values
    return []


def load_tools() -> List[Dict[str, Any]]:
    return as_dict_list(read_json(DATA_DIR / "tools.json", []), keys=("tools", "items", "data", "catalog", "records"))


def load_scenarios() -> List[str]:
    values: List[str] = []
    for d in SCENARIO_DIRS:
        if d.exists():
            values.extend(str(p.relative_to(ROOT)) for p in sorted(d.glob("*.json")))
    return values


def list_tools() -> List[str]:
    out: List[str] = []
    for t in load_tools():
        tool_id = str(t.get("id", "")).strip()
        name = str(t.get("name", tool_id)).strip()
        org = str(t.get("org") or t.get("vendor") or t.get("company") or "").strip()
        if not tool_id and not name:
            continue
        label = f"{tool_id} — {name}" if tool_id else name
        if org:
            label += f" ({org})"
        out.append(label)
    return out


def parse_tool_id(tool_label: str) -> str:
    return (tool_label or "").split(" — ", 1)[0].strip()


def run_cli(args: List[str], timeout: int = 180) -> Tuple[str, str]:
    proc = subprocess.run(
        [sys.executable] + args,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return proc.stdout, proc.stderr


# ---------------------------------------------------------------------
# Productized Start Here / Golden Path
# ---------------------------------------------------------------------

GOLDEN_SCENARIO = "scenario_templates/enterprise_copilot_with_rag.json"


def start_here(choice: str) -> Tuple[str, str]:
    mapping = {
        "Secure an MCP + RAG agent": GOLDEN_SCENARIO,
        "Validate a vendor/tool claim": GOLDEN_SCENARIO,
        "Generate architecture review": GOLDEN_SCENARIO,
        "Run benchmark-backed demo": GOLDEN_SCENARIO,
    }
    scenario = mapping.get(choice, GOLDEN_SCENARIO)
    scenario_data = read_json(ROOT / scenario, {}) or {}
    md = ["# Recommended Demo Path", ""]
    md.append(f"**Selected path:** {choice}")
    md.append(f"**Scenario file:** `{scenario}`")
    md.append(f"**Scenario:** {scenario_data.get('name', 'Enterprise MCP + RAG Customer Support Agent')}")
    md.append("")
    md.append("## 3-minute Golden Path")
    md.append("1. Open **Full Lifecycle** and run the end-to-end lifecycle.")
    md.append("2. Open **Live Runtime** and try a blocked tool descriptor poisoning payload.")
    md.append("3. Open **Benchmark** and generate benchmark-backed evidence.")
    md.append("4. Open **Export / Validation Board** to review downloadable reports.")
    md.append("")
    md.append("## What this demo proves")
    md.append("- ASI risk mapping is generated from scenario structure.")
    md.append("- Policy gates block unsafe tool execution before runtime side effects.")
    md.append("- Benchmark results create validation evidence, not just vendor claims.")
    md.append("- Reports disclose limitations and residual risks.")
    return "\n".join(md), scenario


# ---------------------------------------------------------------------
# Full lifecycle orchestration
# ---------------------------------------------------------------------

def run_full_lifecycle_ui(scenario_path: str, claim_tool_label: str, claim: str, include_updates: bool) -> Tuple[str, str, str, str]:
    if not scenario_path:
        return "Select a scenario first.", "{}", "", ""
    tool_id = parse_tool_id(claim_tool_label) or "noma-security"
    result = run_lifecycle(
        scenario_path=scenario_path,
        output_dir="outputs/lifecycle_run",
        claim_tool=tool_id,
        claim=claim or "MCP discovery and runtime policy enforcement",
        run_updates=include_updates,
    )
    md_path = ROOT / result["report_markdown_path"]
    js_path = ROOT / result["report_json_path"]
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else "Lifecycle report was not generated."
    js = js_path.read_text(encoding="utf-8") if js_path.exists() else json.dumps(result, indent=2, ensure_ascii=False)
    return md, js, str(md_path), str(js_path)


# ---------------------------------------------------------------------
# Existing modules
# ---------------------------------------------------------------------

def advisor(scenario_path: str) -> Tuple[str, str]:
    if not scenario_path:
        return "Select a scenario first.", "{}"
    with tempfile.TemporaryDirectory() as td:
        md = Path(td) / "report.md"
        js = Path(td) / "report.json"
        stdout, stderr = run_cli([
            "agents/solution_validator_agent.py",
            "--scenario", scenario_path,
            "--output", str(md),
            "--json-output", str(js),
        ])
        markdown = md.read_text(encoding="utf-8") if md.exists() else f"Failed to generate report.\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
        payload = js.read_text(encoding="utf-8") if js.exists() else json.dumps({"stdout": stdout, "stderr": stderr}, indent=2)
        return markdown, payload


def demo_runtime_call(tool_name: str, user_prompt: str, descriptor: str, arguments_text: str, tool_output: str, oauth_text: str, human_approved: bool) -> Tuple[str, str]:
    try:
        args = json.loads(arguments_text or "{}")
        if not isinstance(args, dict):
            args = {"value": args}
    except Exception as e:
        return f"Invalid JSON arguments: {e}", "[]"
    runtime = DemoAgentRuntime()
    req = {
        "tool_name": tool_name,
        "user_prompt": user_prompt,
        "tool_descriptor": descriptor,
        "arguments": args,
        "tool_output": tool_output,
        "auth_context": {"oauth_response_text": oauth_text} if oauth_text else {},
        "human_approved": human_approved,
    }
    result = runtime.execute(req)
    decision = result.get("decision", {}) or {}
    md = ["# Demo Runtime Decision", ""]
    md.append(f"**Decision:** `{decision.get('decision', 'unknown')}`")
    md.append(f"**Reason code:** `{decision.get('reason_code', 'n/a')}`")
    md.append(f"**Reason:** {decision.get('reason', 'n/a')}")
    md.append(f"**Mapped ASI:** {', '.join(decision.get('asi', [])) or 'n/a'}")
    md.append(f"**Controls:** {', '.join(decision.get('controls', [])) or 'n/a'}")
    if result.get("result"):
        md.append("\n## Tool Result")
        md.append("```json\n" + json.dumps(result.get("result"), indent=2, ensure_ascii=False) + "\n```")
    audit = runtime.audit_tail(10)
    return "\n".join(md), json.dumps(audit, indent=2, ensure_ascii=False)


def run_live_benchmark() -> Tuple[str, str, str]:
    report = run_demo_benchmark(
        suite=str(ROOT / "benchmarks/mcp_security_benchmark_v01.jsonl"),
        output=str(ROOT / "validation_reports/demo_runtime_validation_report.json"),
    )
    summary = report.get("summary", {}) or {}
    passed = summary.get("passed", 0)
    total = summary.get("total_cases", 0)
    pr = summary.get("pass_rate", 0)
    pr_txt = f"{float(pr):.0%}" if isinstance(pr, (int, float)) else str(pr)
    md = ["# Benchmark-backed Validation Report", ""]
    md.append(f"**Target:** `{report.get('target', 'demo-runtime')}`")
    md.append(f"**Suite:** `{report.get('benchmark_suite', 'mcp_security_benchmark_v01')}`")
    md.append(f"**Pass rate:** {passed}/{total} = **{pr_txt}**")
    md.append("\n## Case Results")
    for r in report.get("results", []):
        status = "✅ PASS" if r.get("passed") else "❌ FAIL"
        md.append(f"- {status} `{r.get('case_id')}` — {r.get('attack_type')} → observed `{r.get('observed')}`")
    md.append("\n## Evidence")
    md.append("- `validation_reports/demo_runtime_validation_report.json`")
    md.append("- `validation_reports/demo_runtime_audit.jsonl`")
    return "\n".join(md), json.dumps(report, indent=2, ensure_ascii=False), str(ROOT / "validation_reports/demo_runtime_validation_report.json")


def grounded_qa(question: str, use_llm: bool, model: str, top_k: int) -> Tuple[str, str]:
    if not question or not question.strip():
        return "Ask a question first.", "{}"
    source_index_path = DATA_DIR / "source_index.json"
    if not source_index_path.exists():
        return "Source index not found. Run `python agents/build_source_index.py` first.", "{}"
    index = load_index(str(source_index_path))
    retriever = SourceRetriever(index)
    sources = retriever.search(question, top_k=int(top_k))
    if use_llm:
        try:
            answer = ask_with_llm(
                question,
                sources,
                model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                api_key_env="OPENAI_API_KEY",
                temperature=0.1,
            )
            ok, _, _ = validate_citations(answer, sources)
            if not ok:
                answer = "LLM answer did not pass citation audit. Falling back to extractive answer.\n\n" + extractive_answer(question, sources)
            else:
                answer = add_citation_audit(answer, sources)
        except LLMClientError as e:
            answer = f"LLM call failed: {e}\n\nFalling back to extractive answer.\n\n" + extractive_answer(question, sources)
        except Exception as e:
            answer = f"Unexpected LLM/Q&A error: {e}\n\nFalling back to extractive answer.\n\n" + extractive_answer(question, sources)
    else:
        answer = extractive_answer(question, sources)
    meta = {
        "retrieved_sources": [
            {"source_id": s.get("source_id"), "title": s.get("title"), "type": s.get("type"), "object_id": s.get("object_id"), "score": s.get("score"), "path": s.get("path")}
            for s in sources
        ]
    }
    return answer, json.dumps(meta, indent=2, ensure_ascii=False)


def verify_claim(tool_label: str, claim: str) -> Tuple[str, str]:
    if not tool_label:
        return "Select a tool first.", "{}"
    tool_id = parse_tool_id(tool_label)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "claim.json"
        stdout, stderr = run_cli(["agents/claim_verifier.py", "--tool", tool_id, "--claim", claim or "", "--output", str(out)])
        payload = read_json(out, {"stdout": stdout, "stderr": stderr}) or {}
    md = ["# Tool Claim Verification", ""]
    md.append(f"**Tool:** `{tool_id}`")
    md.append(f"**Claim:** {claim}")
    md.append(f"**Status:** {payload.get('current_status', payload.get('status', 'review required'))}")
    for key in ["mapped_asi", "required_evidence", "existing_evidence_types", "missing_evidence", "suggested_benchmark_tests", "next_step"]:
        val = payload.get(key)
        if val:
            md.append(f"\n## {key.replace('_', ' ').title()}")
            if isinstance(val, list):
                md.extend([f"- {x}" for x in val])
            else:
                md.append(str(val))
    return "\n".join(md), json.dumps(payload, indent=2, ensure_ascii=False)


def generate_architecture(scenario_path: str) -> Tuple[str, str, str]:
    if not scenario_path:
        return "Select a scenario first.", "{}", ""
    with tempfile.TemporaryDirectory() as td:
        md = Path(td) / "arch.md"
        js = Path(td) / "arch.json"
        stdout, stderr = run_cli(["agents/architecture_generator.py", "--scenario", scenario_path, "--output", str(md), "--json-output", str(js)])
        markdown = md.read_text(encoding="utf-8") if md.exists() else f"Failed.\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
        payload = js.read_text(encoding="utf-8") if js.exists() else json.dumps({"stdout": stdout, "stderr": stderr}, indent=2)
        export_path = ROOT / "outputs/generated_architecture_from_ui.md"
        write_text(export_path, markdown)
        return markdown, payload, str(export_path)


def load_validation_board() -> Tuple[str, str]:
    report_dir = ROOT / "validation_reports"
    report_dir.mkdir(exist_ok=True)
    reports = sorted(report_dir.glob("*.json"))
    md = ["# Validation Status Board", ""]
    rows = []
    for p in reports:
        data = read_json(p, {}) or {}
        summary = data.get("summary", {}) or {}
        rows.append({
            "report": p.name,
            "target": data.get("target", "n/a"),
            "suite": data.get("benchmark_suite", "n/a"),
            "pass_rate": summary.get("pass_rate", "n/a"),
            "passed": summary.get("passed", "n/a"),
            "total": summary.get("total_cases", "n/a"),
        })
    if rows:
        md.append("| Report | Target | Suite | Pass Rate | Passed / Total |")
        md.append("|---|---|---|---:|---:|")
        for r in rows:
            pr = r["pass_rate"]
            pr_txt = f"{pr:.0%}" if isinstance(pr, float) else str(pr)
            md.append(f"| `{r['report']}` | {r['target']} | {r['suite']} | {pr_txt} | {r['passed']} / {r['total']} |")
    else:
        md.append("No validation reports found yet. Run the benchmark tab first.")
    return "\n".join(md), json.dumps(rows, indent=2, ensure_ascii=False)


def export_demo_evidence() -> Tuple[str, str]:
    report = read_json(ROOT / "validation_reports/demo_runtime_validation_report.json", {}) or {}
    scenario = read_json(ROOT / GOLDEN_SCENARIO, {}) or {}
    summary = report.get("summary", {})
    md = ["# Demo Evidence Report", ""]
    md.append(f"**Scenario:** {scenario.get('name', 'Enterprise MCP + RAG Customer Support Agent')}")
    md.append("")
    md.append("## Tested risks")
    md.extend(["- ASI01 Agent Goal Hijack", "- ASI02 Tool Misuse and Exploitation", "- ASI04 Agentic Supply Chain Vulnerabilities", "- ASI05 Unexpected Code Execution", "- ASI06 Memory & Context Poisoning", "- ASI07 Insecure Inter-Agent Communication"])
    md.append("\n## Controls demonstrated")
    md.extend(["- Tool allowlist", "- Descriptor sanitization", "- Argument validation", "- HITL approval", "- Runtime audit logging", "- Benchmark-backed validation report"])
    md.append("\n## Benchmark result")
    if summary:
        pr = summary.get("pass_rate")
        pr_txt = f"{pr:.0%}" if isinstance(pr, float) else str(pr)
        md.append(f"- Passed: {summary.get('passed')} / {summary.get('total_cases')}")
        md.append(f"- Pass rate: {pr_txt}")
    else:
        md.append("- Benchmark report not found. Run the benchmark first.")
    md.append("\n## Limitations")
    md.append("- This validates the included demo runtime, not all third-party commercial tools.")
    md.append("- Vendor claims require independent benchmark execution and evidence review.")
    md.append("- The current runtime is MCP-style; full MCP protocol compatibility can be added in the next phase.")
    path = ROOT / "outputs/demo_evidence_report.md"
    write_text(path, "\n".join(md) + "\n")
    return "\n".join(md), str(path)



def run_llm_guard_adapter_ui() -> Tuple[str, str, str]:
    report = run_llm_guard_smoke()
    s = report.get("summary", {})
    md = ["# LLM Guard Adapter Smoke Validation", ""]
    md.append(f"**Result:** {s.get('passed')}/{s.get('total_cases')} passed ({float(s.get('pass_rate', 0)):.0%})")
    md.append("\n## Case Results")
    for r in report.get("results", []):
        status = "✅ PASS" if r.get("passed") else "❌ FAIL"
        md.append(f"- {status} `{r.get('id')}` expected `{r.get('expected')}`, observed `{r.get('observed')}`")
    path = ROOT / "validation_reports/llm_guard_adapter_validation_report.json"
    return "\n".join(md), json.dumps(report, indent=2, ensure_ascii=False), str(path)


def run_real_mcp_gateway_ui() -> Tuple[str, str, str]:
    report = run_real_mcp_gateway_benchmark()
    s = report.get("summary", {})
    md = ["# Real MCP Gateway Smoke Validation", ""]
    md.append(f"**Result:** {s.get('passed')}/{s.get('total_cases')} passed ({float(s.get('pass_rate', 0)):.0%})")
    md.append("\n## Case Results")
    for r in report.get("results", []):
        status = "✅ PASS" if r.get("passed") else "❌ FAIL"
        md.append(f"- {status} `{r.get('case_id')}` expected `{r.get('expected')}`, observed `{r.get('observed')}`")
    md.append("\n## Limitation")
    md.append("This is a lightweight JSON-RPC MCP gateway demo, not a full production MCP server.")
    path = ROOT / "validation_reports/real_mcp_gateway_validation_report.json"
    return "\n".join(md), json.dumps(report, indent=2, ensure_ascii=False), str(path)


def load_validation_status_board() -> Tuple[str, str]:
    status = read_json(DATA_DIR / "validation_status.json", {"targets": []}) or {"targets": []}
    md = ["# Validation Status Board", ""]
    md.append("| Target | Evidence | Benchmark | Runtime Tested | Status | Summary |")
    md.append("|---|---|---|---:|---|---|")
    for t in status.get("targets", []):
        md.append(f"| {t.get('name')} | {t.get('evidence')} | {t.get('benchmark')} | {t.get('runtime_tested')} | **{t.get('status')}** | {t.get('summary')} |")
    return "\n".join(md), json.dumps(status, indent=2, ensure_ascii=False)


def generate_enterprise_pack_ui(scenario_path: str) -> Tuple[str, str, str, str, str, str]:
    manifest = generate_pack(scenario_path or GOLDEN_SCENARIO)
    outdir = ROOT / "outputs/enterprise_review_pack"
    exec_path = outdir / "executive_summary.md"
    arch_path = outdir / "architecture_review.md"
    bench_path = outdir / "benchmark_validation_report.md"
    manifest_path = outdir / "manifest.json"
    md = exec_path.read_text(encoding="utf-8") if exec_path.exists() else "Pack generation failed."
    return md, json.dumps(manifest, indent=2, ensure_ascii=False), str(exec_path), str(arch_path), str(bench_path), str(manifest_path)


def show_claim_test_mapping() -> Tuple[str, str]:
    data = read_json(DATA_DIR / "claim_test_mapping.json", {"mappings": []}) or {"mappings": []}
    md = ["# Claim → Test → Evidence Mapping", ""]
    for m in data.get("mappings", []):
        md.append(f"## {m.get('claim_pattern')}")
        md.append(f"- **ASI:** {', '.join(m.get('mapped_asi', []))}")
        md.append(f"- **Controls:** {', '.join(m.get('required_controls', []))}")
        md.append(f"- **Benchmark cases:** {', '.join(m.get('benchmark_cases', []))}")
        md.append(f"- **Evidence required:** {', '.join(m.get('required_evidence', []))}")
        md.append("")
    return "\n".join(md), json.dumps(data, indent=2, ensure_ascii=False)


def assess_real_mcp_server_ui(
    server_url: str,
    mode: str,
    token: str,
    profile: str,
    timeout: float,
    connector_config: str,
    data_sensitivity: str,
    authorized: bool,
    allow_high_risk: bool,
) -> Tuple[str, str, str, str]:
    """Run universal MCP risk assessment and return Markdown, JSON, and downloadable reports."""
    target = (server_url or "demo://local").strip() or "demo://local"
    cfg = (connector_config or "").strip() or None
    try:
        report = assess_mcp_server(
            server_url=target,
            token=token or "",
            mode=mode or "auto",
            profile=profile or "schema_only",
            output_dir=str(ROOT / "outputs/mcp_assessments"),
            timeout=float(timeout or 45),
            connector_config=cfg,
            data_sensitivity=data_sensitivity or "medium",
            authorized=bool(authorized),
            allow_high_risk=bool(allow_high_risk),
        )
    except Exception as exc:
        payload = {"error": str(exc), "server_url": target, "mode": mode}
        return f"# MCP Assessment Failed\n\n`{exc}`", json.dumps(payload, indent=2, ensure_ascii=False), "", ""

    md_path = Path(report.get("markdown_report", ""))
    json_path = Path(report.get("json_report", ""))
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else "# MCP Assessment\n\nReport generation completed, but Markdown output was not found."
    return md, json.dumps(report, indent=2, ensure_ascii=False), str(md_path), str(json_path)

SCENARIOS = load_scenarios()
TOOLS = list_tools()
TOOL_CHOICES = ["crm.lookup", "email.draft", "file.read", "memory.search", "ticket.create", "crm.refund", "email.send", "file.delete", "shell.run", "package.install", "unknown.admin_helper"]


with gr.Blocks(title="Awesome Agentic AI Security — Lifecycle Validation Platform") as demo:
    gr.Markdown("""
# 🛡️ Awesome Agentic AI Security — Full Lifecycle Validation Platform

A runnable Agentic AI security validation platform that connects scenario intake, OWASP ASI risk mapping, tool recommendation, architecture generation, runtime policy enforcement, benchmark-backed validation, claim/evidence review, exportable reports, and continuous update review.
""")

    with gr.Tab("0. Start Here"):
        path_choice = gr.Radio(
            ["Secure an MCP + RAG agent", "Validate a vendor/tool claim", "Generate architecture review", "Run benchmark-backed demo"],
            value="Secure an MCP + RAG agent",
            label="What do you want to validate?",
        )
        start_btn = gr.Button("Show recommended path")
        start_md = gr.Markdown()
        selected_scenario = gr.Textbox(label="Scenario selected for lifecycle run", interactive=False)
        start_btn.click(start_here, inputs=[path_choice], outputs=[start_md, selected_scenario])
        demo.load(start_here, inputs=[path_choice], outputs=[start_md, selected_scenario])

    with gr.Tab("1. Full Lifecycle"):
        gr.Markdown("Run the complete lifecycle: scenario → risk map → architecture → runtime policy gate → benchmark → claim review → update review → exportable lifecycle report.")
        lifecycle_scenario = gr.Dropdown(SCENARIOS, value=GOLDEN_SCENARIO if GOLDEN_SCENARIO in SCENARIOS else (SCENARIOS[0] if SCENARIOS else None), label="Scenario")
        lifecycle_tool = gr.Dropdown(TOOLS, value=TOOLS[0] if TOOLS else None, label="Tool for claim review")
        lifecycle_claim = gr.Textbox(label="Claim to review", value="MCP discovery and runtime policy enforcement")
        lifecycle_updates = gr.Checkbox(label="Include update review / PR automation stage", value=True)
        lifecycle_btn = gr.Button("Run full lifecycle")
        lifecycle_md = gr.Markdown()
        lifecycle_json = gr.Code(language="json", label="Lifecycle JSON")
        lifecycle_md_file = gr.File(label="Download lifecycle Markdown")
        lifecycle_json_file = gr.File(label="Download lifecycle JSON")
        lifecycle_btn.click(run_full_lifecycle_ui, inputs=[lifecycle_scenario, lifecycle_tool, lifecycle_claim, lifecycle_updates], outputs=[lifecycle_md, lifecycle_json, lifecycle_md_file, lifecycle_json_file])

    with gr.Tab("2. Solution Advisor"):
        scenario = gr.Dropdown(SCENARIOS, value=GOLDEN_SCENARIO if GOLDEN_SCENARIO in SCENARIOS else (SCENARIOS[0] if SCENARIOS else None), label="Scenario")
        run_advisor = gr.Button("Generate solution validation report")
        advisor_md = gr.Markdown()
        advisor_json = gr.Code(language="json", label="Structured report JSON")
        run_advisor.click(advisor, inputs=[scenario], outputs=[advisor_md, advisor_json])

    with gr.Tab("3. Live Runtime"):
        gr.Markdown("This tab runs a real in-process demo runtime with policy gates before tool execution.")
        tool = gr.Dropdown(TOOL_CHOICES, value="crm.lookup", label="Tool")
        prompt = gr.Textbox(label="User prompt", value="Please check order ORD-1001.")
        descriptor = gr.Textbox(label="Tool descriptor", value="Safe CRM lookup tool for read-only order status.")
        args = gr.Code(language="json", label="Tool arguments", value='{"order_id":"ORD-1001"}')
        output = gr.Textbox(label="Optional tool output to sanitize", value="")
        oauth = gr.Textbox(label="Optional OAuth / auth response text", value="")
        approved = gr.Checkbox(label="Human approved high-impact action", value=False)
        run_runtime = gr.Button("Execute through policy gate")
        runtime_md = gr.Markdown()
        audit_json = gr.Code(language="json", label="Audit log tail")
        run_runtime.click(demo_runtime_call, inputs=[tool, prompt, descriptor, args, output, oauth, approved], outputs=[runtime_md, audit_json])

    with gr.Tab("4. Benchmark"):
        gr.Markdown("Runs the MCP security benchmark against the live demo runtime and produces a validation report.")
        run_bench = gr.Button("Run demo MCP benchmark")
        bench_md = gr.Markdown()
        bench_json = gr.Code(language="json", label="Validation report JSON")
        bench_file = gr.File(label="Download validation report JSON")
        run_bench.click(run_live_benchmark, outputs=[bench_md, bench_json, bench_file])

    with gr.Tab("5. Tool Claim Verifier"):
        tool_label = gr.Dropdown(TOOLS, value=TOOLS[0] if TOOLS else None, label="Tool")
        claim = gr.Textbox(label="Claim to validate", value="MCP discovery and runtime policy enforcement")
        verify = gr.Button("Verify claim")
        claim_md = gr.Markdown()
        claim_json = gr.Code(language="json", label="Claim verification JSON")
        verify.click(verify_claim, inputs=[tool_label, claim], outputs=[claim_md, claim_json])

    with gr.Tab("6. Architecture Generator"):
        arch_scenario = gr.Dropdown(SCENARIOS, value=GOLDEN_SCENARIO if GOLDEN_SCENARIO in SCENARIOS else (SCENARIOS[0] if SCENARIOS else None), label="Scenario")
        arch_btn = gr.Button("Generate reference architecture")
        arch_md = gr.Markdown()
        arch_json = gr.Code(language="json", label="Architecture JSON")
        arch_file = gr.File(label="Download architecture Markdown")
        arch_btn.click(generate_architecture, inputs=[arch_scenario], outputs=[arch_md, arch_json, arch_file])


    with gr.Tab("7. Validation Status"):
        gr.Markdown("Review which targets are benchmark-backed, partially validated, evidence-only, or still need claim review.")
        status_btn = gr.Button("Refresh validation status")
        status_md = gr.Markdown()
        status_json = gr.Code(language="json", label="Validation status JSON")
        status_btn.click(load_validation_status_board, outputs=[status_md, status_json])
        demo.load(load_validation_status_board, outputs=[status_md, status_json])

    with gr.Tab("8. Real MCP Gateway"):
        gr.Markdown("Runs a lightweight JSON-RPC MCP gateway benchmark with descriptor validation and policy-gated tool calls.")
        mcp_btn = gr.Button("Run real MCP gateway smoke benchmark")
        mcp_md = gr.Markdown()
        mcp_json = gr.Code(language="json", label="Real MCP gateway report JSON")
        mcp_file = gr.File(label="Download real MCP gateway report")
        mcp_btn.click(run_real_mcp_gateway_ui, outputs=[mcp_md, mcp_json, mcp_file])

    with gr.Tab("9. LLM Guard Adapter"):
        gr.Markdown("Runs the first real-tool adapter smoke test. Native llm-guard can be integrated; deterministic fallback scanners keep the demo stable.")
        lg_btn = gr.Button("Run LLM Guard adapter smoke test")
        lg_md = gr.Markdown()
        lg_json = gr.Code(language="json", label="Adapter report JSON")
        lg_file = gr.File(label="Download adapter report")
        lg_btn.click(run_llm_guard_adapter_ui, outputs=[lg_md, lg_json, lg_file])

    with gr.Tab("10. Enterprise Review Pack"):
        gr.Markdown("Generate an enterprise architecture review pack: executive summary, architecture review, ASI matrix, benchmark report, residual risk, and implementation roadmap.")
        pack_scenario = gr.Dropdown(SCENARIOS, value=GOLDEN_SCENARIO if GOLDEN_SCENARIO in SCENARIOS else (SCENARIOS[0] if SCENARIOS else None), label="Scenario")
        pack_btn = gr.Button("Generate enterprise review pack")
        pack_md = gr.Markdown()
        pack_json = gr.Code(language="json", label="Pack manifest")
        pack_exec = gr.File(label="Executive summary")
        pack_arch = gr.File(label="Architecture review")
        pack_bench = gr.File(label="Benchmark report")
        pack_manifest = gr.File(label="Manifest JSON")
        pack_btn.click(generate_enterprise_pack_ui, inputs=[pack_scenario], outputs=[pack_md, pack_json, pack_exec, pack_arch, pack_bench, pack_manifest])

    with gr.Tab("11. Claim-Test-Evidence"):
        gr.Markdown("Maps common AI security claims to OWASP ASI risks, required controls, benchmark cases, and evidence artifacts.")
        cte_btn = gr.Button("Load claim-test-evidence mapping")
        cte_md = gr.Markdown()
        cte_json = gr.Code(language="json", label="Mapping JSON")
        cte_btn.click(show_claim_test_mapping, outputs=[cte_md, cte_json])
        demo.load(show_claim_test_mapping, outputs=[cte_md, cte_json])


    with gr.Tab("12. Universal MCP Assessment"):
        gr.Markdown("""
Assess live MCP servers, Hugging Face / Gradio MCP Spaces, OpenAI-style MCP connector configs, and documentation references.

Default mode is safe schema/config review. Real execution measurement is available only when you explicitly select `safe_probe` or `authorized_runtime_validation` and acknowledge authorization.

Examples:
- `demo://local`
- `https://mcp-tools-deepseek-ocr-experimental.hf.space/gradio_api/mcp/`
- `https://huggingface.co/spaces/OWNER/SPACE`
- OpenAI connector config JSON pasted in the connector config field
""")
        mcp_assess_url = gr.Textbox(label="MCP server / HF Space / docs URL", value="demo://local")
        mcp_assess_mode = gr.Dropdown(["auto", "jsonrpc_streamable_http", "sse", "gradio_config", "gradio_info"], value="auto", label="Discovery mode")
        mcp_assess_profile = gr.Dropdown(["schema_only", "connector_config_review", "safe_probe", "authorized_runtime_validation", "offline_docs_review"], value="schema_only", label="Assessment profile")
        mcp_assess_timeout = gr.Slider(10, 120, value=45, step=5, label="Timeout seconds")
        mcp_assess_token = gr.Textbox(label="Optional bearer token", value="", type="password")
        mcp_connector_config = gr.Code(language="json", label="Optional OpenAI-style MCP connector config", value="")
        mcp_data_sensitivity = gr.Dropdown(["low", "medium", "high", "regulated"], value="medium", label="Data sensitivity")
        mcp_authorized = gr.Checkbox(label="I confirm I own or am authorized to execute probes against this MCP server", value=False)
        mcp_allow_high_risk = gr.Checkbox(label="Allow high-risk tool calls during authorized runtime validation only", value=False)
        mcp_assess_btn = gr.Button("Run universal MCP risk assessment")
        mcp_assess_md = gr.Markdown()
        mcp_assess_json = gr.Code(language="json", label="Assessment JSON")
        mcp_assess_md_file = gr.File(label="Download Markdown report")
        mcp_assess_json_file = gr.File(label="Download JSON report")
        mcp_assess_btn.click(
            assess_real_mcp_server_ui,
            inputs=[mcp_assess_url, mcp_assess_mode, mcp_assess_token, mcp_assess_profile, mcp_assess_timeout, mcp_connector_config, mcp_data_sensitivity, mcp_authorized, mcp_allow_high_risk],
            outputs=[mcp_assess_md, mcp_assess_json, mcp_assess_md_file, mcp_assess_json_file],
        )

    with gr.Tab("13. Grounded Q&A"):
        question = gr.Textbox(label="Question", value="Which tools should I evaluate for MCP runtime security and ASI02 tool misuse?")
        use_llm = gr.Checkbox(label="Use OpenAI-compatible LLM if OPENAI_API_KEY is configured", value=False)
        model = gr.Textbox(label="Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        topk = gr.Slider(3, 20, value=8, step=1, label="Top-K retrieved sources")
        ask = gr.Button("Ask grounded advisor")
        answer_md = gr.Markdown()
        sources_json = gr.Code(language="json", label="Retrieved sources")
        ask.click(grounded_qa, inputs=[question, use_llm, model, topk], outputs=[answer_md, sources_json])

    with gr.Tab("14. Export / Validation Board"):
        refresh = gr.Button("Refresh validation board")
        board_md = gr.Markdown()
        board_json = gr.Code(language="json", label="Reports")
        evidence_btn = gr.Button("Generate demo evidence report")
        evidence_md = gr.Markdown()
        evidence_file = gr.File(label="Download demo evidence report")
        refresh.click(load_validation_board, outputs=[board_md, board_json])
        evidence_btn.click(export_demo_evidence, outputs=[evidence_md, evidence_file])
        demo.load(load_validation_board, outputs=[board_md, board_json])

if __name__ == "__main__":
    demo.launch()
